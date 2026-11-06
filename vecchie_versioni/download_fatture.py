from playwright.sync_api import sync_playwright
from pathlib import Path
import time

DOWNLOAD_DIR = Path("./fatture_ade")
DOWNLOAD_DIR.mkdir(exist_ok=True)

print("🚀 Avvio Firefox...")

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    
    try:
        print("📡 Connessione a AdE...")
        page.goto("https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/?v=1729602560401#/fatture/ricevute", 
                  wait_until="load", timeout=30000)
        
        print("✅ Pagina caricata!")
        
        print("\n⏸️  PAUSA — Tu fai:")
        print("   1. Completa login SPID")
        print("   2. Seleziona le date")
        print("   3. Clicca 'Cerca'")
        print("   4. Premi INVIO quando la tabella è caricata")
        
        input("\n▶️  Premi INVIO...")
        
        print("⏳ Scaricamento in corso...")
        
        # Trova tutti i pulsanti di download nella lista
        buttons = page.locator("tr td:last-child button, tr td:last-child a").all()
        
        print(f"📥 Trovati {len(buttons)} file da scaricare\n")
        
        for i, button in enumerate(buttons):
            print(f"   [{i+1}/{len(buttons)}] Scarico...")
            
            # Clicca il pulsante blu
            button.click()
            
            # Aspetta che si apra la pagina di dettaglio
            page.wait_for_url("**/dettaglio/**", timeout=10000)
            page.wait_for_load_state("load")
            
            # Clicca "Download file fattura"
            with page.expect_download() as download_info:
                page.click("button:has-text('Download file fattura')")
            
            # Salva il file
            download = download_info.value
            file_path = DOWNLOAD_DIR / download.suggested_filename
            download.save_as(str(file_path))
            print(f"       ✅ {download.suggested_filename}")
            
            # Torna indietro
            page.go_back()
            page.wait_for_url("**/ricevute", timeout=10000)
            page.wait_for_load_state("load")
            
            time.sleep(0.3)
        
        print(f"\n✅ Completato! {len(buttons)} file scaricati in {DOWNLOAD_DIR}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        input("Premi INVIO per chiudere...")
    
    finally:
        context.close()
        browser.close()