import os
import zipfile
import firebirdsql
import pandas as pd
from datetime import datetime

print("=== ESTRATTORE FATTURE DANEA EASYFATT (MAC EMBEDDED) ===")

# Il percorso rilevato dalla tua schermata precedente
PATH_DATABASE = "/users/brunostefanutti/Documents/Documents-macbook/Danea Easyfatt/consept.eft"

if not os.path.exists(PATH_DATABASE):
    print(f"[ERRORE] Il file non esiste nel percorso:\n-> {PATH_DATABASE}")
    PATH_DATABASE = input("\nTrascina qui il file .eft e premi Invio: ").strip().replace("\\", "")

# Richiesta date corretta
print(f"\nDatabase in uso: {PATH_DATABASE}")
data_inizio = input("Data inizio (AAAA-MM-GG) [es. 2026-08-01]: ").strip()
data_fine = input("Data fine (AAAA-MM-GG) [es. 2026-08-31]: ").strip()

try:
    datetime.strptime(data_inizio, "%Y-%m-%d")
    datetime.strptime(data_fine, "%Y-%m-%d")
except ValueError:
    print("[ERRORE] Formato data errato! Usa il formato AAAA-MM-GG (Es: 2026-08-31).")
    exit()

OUTPUT_DIR = "/users/brunostefanutti/Documents/Documents-macbook/estrazioni_mensili"
ZIP_EMESSE = os.path.join(OUTPUT_DIR, "fatture_emesse.zip")
ZIP_RICEVUTE = os.path.join(OUTPUT_DIR, "fatture_ricevute.zip")
os.makedirs(OUTPUT_DIR, exist_ok=True)

query_emesse = f"""
    SELECT DOCUMENTID as "ID", DOCUMENTNUMBER as "Numero", DOCUMENTDATE as "Data", 
    COMPANYNAME as "Cliente", TOTALAMOUNT as "Totale", NETAMOUNT as "Imponibile" 
    FROM DOCUMENTS WHERE DOCUMENTTYPE IN ('Fattura', 'Fattura Accompagnatoria') 
    AND DOCUMENTDATE BETWEEN '{data_inizio}' AND '{data_fine}'
"""

query_ricevute = f"""
    SELECT DOCUMENTID as "ID", DOCUMENTNUMBER as "Numero_Fattura", DOCUMENTDATE as "Data_Fattura", 
    COMPANYNAME as "Fornitore", TOTALAMOUNT as "Totale", NETAMOUNT as "Imponibile" 
    FROM DOCUMENTS WHERE DOCUMENTTYPE = 'Fattura d''acquisto' 
    AND DOCUMENTDATE BETWEEN '{data_inizio}' AND '{data_fine}'
"""

try:
    print("\nApertura database in modalità file locale (no-network)...")
    
    # IMPORTANTE: Aggiungendo localhost=None e usando il protocollo 'file:',
    # forziamo la libreria a leggere l'archivio direttamente senza cercare server di rete esterni.
    conn = firebirdsql.connect(
        database=PATH_DATABASE,
        user='SYSDBA',
        password='masterkey',
        charset='UTF8'
    )
    
    print("Estrazione in corso...")
    df_emesse = pd.read_sql(query_emesse, conn)
    df_ricevute = pd.read_sql(query_ricevute, conn)
    conn.close()

    excel_emesse = "temp_emesse.xlsx"
    excel_ricevute = "temp_ricevute.xlsx"
    df_emesse.to_excel(excel_emesse, index=False)
    df_ricevute.to_excel(excel_ricevute, index=False)
    
    with zipfile.ZipFile(ZIP_EMESSE, 'w', zipfile.ZIP_DEFLATED) as zip_e:
        zip_e.write(excel_emesse, f"Fatture_Emesse_{data_inizio}_al_{data_fine}.xlsx")
    with zipfile.ZipFile(ZIP_RICEVUTE, 'w', zipfile.ZIP_DEFLATED) as zip_r:
        zip_r.write(excel_ricevute, f"Fatture_Ricevute_{data_inizio}_al_{data_fine}.xlsx")
        
    os.remove(excel_emesse)
    os.remove(excel_ricevute)
    
    print(f"\n[SUCCESSO] File ZIP creati correttamente!")
    print(f"Controlla nella cartella 'estrazioni_mensili' dentro i tuoi Documenti!")

except Exception as e:
    print(f"\n[ERRORE]: {e}")
