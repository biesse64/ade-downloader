#!/usr/bin/env python3
"""
Download automatico Fatture Passive - Agenzia delle Entrate
Workflow completo: SPID → Selezione utenza → Conferma → Fatture → Download batch
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

DOWNLOAD_DIR = Path("./fatture_ade")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 70)
    print("📥 DOWNLOAD AUTOMATICO FATTURE PASSIVE - AGENZIA DELLE ENTRATE")
    print("=" * 70)
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            print("\n📡 Connessione a AdE...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/?v=1729602560401#/fatture/ricevute",
                wait_until="load",
                timeout=30000
            )
            print("✅ Pagina caricata!\n")
            
            # ========== STEP 1: LOGIN SPID ==========
            print("=" * 70)
            print("⏸️  STEP 1: LOGIN SPID")
            print("=" * 70)
            print("📲 Completa l'autenticazione con SPID")
            input("\n▶️  Premi INVIO quando il login è completato...")
            
            # ========== STEP 2: SELEZIONE UTENZA ==========
            print("\n" + "=" * 70)
            print("⏸️  STEP 2: SELEZIONE UTENZA")
            print("=" * 70)
            print("🔄 Selezionando 'Me stesso'...")
            
            try:
                # Clicca il radiobox "Me stesso"
                page.click("input[value='meStesso']")
                time.sleep(0.5)
                
                # Clicca il pulsante "Procedi"
                page.click("button:has-text('Procedi')")
                page.wait_for_timeout(2000)
                print("✅ Utenza selezionata")
            except Exception as e:
                print(f"⚠️  Errore Step 2: {e}")
                print("   Prosegui manualmente...")
                input("\n▶️  Premi INVIO quando sei avanti...")
            
            # ========== STEP 3: CONFERMA RIEPILOGO ==========
            print("\n" + "=" * 70)
            print("⏸️  STEP 3: CONFERMA RIEPILOGO")
            print("=" * 70)
            print("🔄 Confermando identità...")
            
            try:
                # Clicca il pulsante "Conferma"
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)
                print("✅ Identità confermata")
            except Exception as e:
                print(f"⚠️  Errore Step 3: {e}")
                print("   Prosegui manualmente...")
                input("\n▶️  Premi INVIO quando sei avanti...")
            
            # ========== STEP 4: NAVIGAZIONE A FATTURE RICEVUTE ==========
            print("\n" + "=" * 70)
            print("⏸️  STEP 4: NAVIGAZIONE A FATTURE RICEVUTE")
            print("=" * 70)
            print("🔄 Cercando la sezione Fatture Ricevute...")
            
            input("\n▶️  Seleziona le date e clicca 'Cerca', poi premi INVIO...")
            
            # ========== STEP 5: DOWNLOAD BATCH ==========
            print("\n" + "=" * 70)
            print("⏳ STEP 5: DOWNLOAD AUTOMATICO IN CORSO...")
            print("=" * 70)
            
            # Trova tutti i pulsanti di download nella lista
            buttons = page.locator("tr td:last-child button, tr td:last-child a").all()
            tot_files = len(buttons)
            
            if tot_files == 0:
                print("❌ Nessun file trovato!")
                print("   Verifica di aver cliccato 'Cerca' correttamente")
                browser.close()
                return
            
            print(f"\n📥 Trovati {tot_files} file da scaricare\n")
            
            downloaded = 0
            failed = []
            
            for i, button in enumerate(buttons, 1):
                try:
                    print(f"   [{i:2}/{tot_files}] ", end="", flush=True)
                    
                    # Clicca il pulsante blu nella lista
                    button.click()
                    page.wait_for_url("**/dettaglio/**", timeout=10000)
                    page.wait_for_load_state("load")
                    
                    # Scarica il file dalla pagina di dettaglio
                    with page.expect_download() as download_info:
                        page.click("button:has-text('Download file fattura')")
                    
                    download = download_info.value
                    file_path = DOWNLOAD_DIR / download.suggested_filename
                    download.save_as(str(file_path))
                    
                    print(f"✅ {download.suggested_filename}")
                    downloaded += 1
                    
                    # Torna indietro alla lista
                    page.go_back()
                    page.wait_for_url("**/ricevute", timeout=10000)
                    page.wait_for_load_state("load")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"❌ {str(e)[:50]}")
                    failed.append((i, str(e)))
                    try:
                        page.go_back()
                    except:
                        pass
            
            # ========== RIEPILOGO FINALE ==========
            print("\n" + "=" * 70)
            print("📊 RIEPILOGO OPERAZIONE")
            print("=" * 70)
            print(f"✅ Scaricati:     {downloaded}/{tot_files} file")
            print(f"📁 Cartella:      {DOWNLOAD_DIR.absolute()}")
            
            if failed:
                print(f"\n⚠️  Non scaricati:   {len(failed)} file")
                for idx, err in failed[:3]:  # Mostra i primi 3 errori
                    print(f"   - File #{idx}: {err[:60]}")
                if len(failed) > 3:
                    print(f"   ... e altri {len(failed)-3}")
            else:
                print(f"\n🎉 Tutte le fatture scaricate correttamente!")
            
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERRORE CRITICO: {e}")
            import traceback
            traceback.print_exc()
            input("\n▶️  Premi INVIO per chiudere...")
        
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
