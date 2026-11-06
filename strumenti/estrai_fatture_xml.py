import os
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd
from datetime import datetime

print("=== ESTRATTORE FATTURE XML DANEA PER MAC ===")

# 1. PARAMETRI DI INPUT
print("Trascina qui la CARTELLA che contiene i file XML delle tue fatture (Inviate o Ricevute):")
cartella_input = input("Percorso Cartella: ").strip().replace("\\", "")

if not os.path.exists(cartella_input):
    print("[ERRORE] Il percorso specificato non esiste.")
    exit()

data_inizio_str = input("Data inizio monitoraggio (AAAA-MM-GG) [es. 2026-08-01]: ").strip()
data_fine_str = input("Data fine monitoraggio (AAAA-MM-GG) [es. 2026-08-31]: ").strip()

try:
    data_inizio = datetime.strptime(data_inizio_str, "%Y-%m-%d").date()
    data_fine = datetime.strptime(data_fine_str, "%Y-%m-%d").date()
except ValueError:
    print("[ERRORE] Formato data errato. Usa AAAA-MM-GG.")
    exit()

# Cartelle di output
OUTPUT_DIR = "./estrazioni_mensili"
os.makedirs(OUTPUT_DIR, exist_ok=True)

struttura_emesse = []
struttura_ricevute = []

# Namespace standard della Fatturazione Elettronica SDI
ns = {'p': 'http://agenziaentrate.gov.it'}

print("\nAnalisi dei file XML in corso...")

# 2. LETTURA DEI FILE XML NELLA CARTELLA
for radice, cartelle, files in os.walk(cartella_input):
    for file in files:
        if file.lower().endswith('.xml'):
            percorso_completo = os.path.join(radice, file)
            try:
                tree = ET.parse(percorso_completo)
                root = tree.getroot()
                
                # Estrazione dati temporali
                data_doc_xml = root.find('.//Data', ns)
                if data_doc_xml is None:
                    continue
                
                data_doc = datetime.strptime(data_doc_xml.text, "%Y-%m-%d").date()
                
                # Filtro sulle date scelte dall'utente
                if not (data_inizio <= data_doc <= data_fine):
                    continue
                
                # Lettura dettagli Fattura
                numero_doc = root.find('.//Numero', ns)
                totale_doc = root.find('.//ImportoTotaleDocumento', ns)
                
                numero = numero_doc.text if numero_doc is not None else "N/D"
                totale = float(totale_doc.text) if totale_doc is not None else 0.0
                
                # Chi emette (Cedente)
                cedente = root.find('.//CedentePrestatore//Denominazione', ns)
                if cedente is None:
                    cedente = root.find('.//CedentePrestatore//Cognome', ns)
                nome_cedente = cedente.text if cedente is not None else "Sconosciuto"
                
                # Chi riceve (Cessionario)
                cessionario = root.find('.//CessionarioCommittente//Denominazione', ns)
                if cessionario is None:
                    cessionario = root.find('.//CessionarioCommittente//Cognome', ns)
                nome_cessionario = cessionario.text if cessionario is not None else "Sconosciuto"
                
                record = {
                    "File": file,
                    "Numero": numero,
                    "Data": data_doc.strftime("%Y-%m-%d"),
                    "Mittente": nome_cedente,
                    "Destinatario": nome_cessionario,
                    "Totale €": totale
                }
                
                # Identifica se la fattura è Emessa o Ricevuta 
                # (Sostituisci 'IL_TUO_NOME_AZIENDA' o lascia che decida in base alla logica della cartella)
                if "ricev" in percorso_completo.lower() or "passive" in percorso_completo.lower():
                    struttura_ricevute.append(record)
                else:
                    struttura_emesse.append(record)
                    
            except Exception as e:
                # Salta file corrotti o non conformi allo standard SDI
                continue

# 3. GENERAZIONE EXCEL E FILE ZIP
excel_emesse = "temp_emesse.xlsx"
excel_ricevute = "temp_ricevute.xlsx"

if struttura_emesse:
    pd.DataFrame(struttura_emesse).to_excel(excel_emesse, index=False)
    with zipfile.ZipFile(os.path.join(OUTPUT_DIR, "fatture_emesse.zip"), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(excel_emesse, f"Report_Emesse_{data_inizio_str}_al_{data_fine_str}.xlsx")
    os.remove(excel_emesse)
    print(f" -> Creato ZIP Emesse con {len(struttura_emesse)} fatture.")

if struttura_ricevute:
    pd.DataFrame(struttura_ricevute).to_excel(excel_ricevute, index=False)
    with zipfile.ZipFile(os.path.join(OUTPUT_DIR, "fatture_ricevute.zip"), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(excel_ricevute, f"Report_Ricevute_{data_inizio_str}_al_{data_fine_str}.xlsx")
    os.remove(excel_ricevute)
    print(f" -> Creato ZIP Ricevute con {len(struttura_ricevute)} fatture.")

print("\n[PROCEDURA COMPLETATA] Controlla la cartella 'estrazioni_mensili' sul tuo Mac!")
