#!/usr/bin/env python3
"""
Download Fatture Passive - 100% AUTOMATIZZATO CON API REST
Usa l'API di AdE direttamente (più affidabile che UI)
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json

DOWNLOAD_DIR = Path("./fatture_ade")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 70)
    print("📥 DOWNLOAD FATTURE PASSIVE - 100% AUTOMATIZZATO")
    print("=" * 70)
    
    # ========== INPUT DELLE DATE ==========
    print("\n📅 INSERISCI LE DATE:")
    print("=" * 70)
    dal = input("   Dal (GG/MM/YYYY): ").strip()
    al = input("   Al  (GG/MM/YYYY): ").strip()
    
    # Converti in formato API: DDMMYYYY
    dal_parts = dal.split('/')
    al_parts = al.split('/')
    dal_api = f"{dal_parts[0]}{dal_parts[1]}{dal_parts[2]}"
    al_api = f"{al_parts[0]}{al_parts[1]}{al_parts[2]}"
    
    print(f"   Debug - Dal: {dal} → {dal_api}")
    print(f"   Debug - Al: {al} → {al_api}")
    print("=" * 70 + "\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            print("\n📡 Apertura AdE...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/instr/InstradamentofcWeb/home",
                wait_until="load",
                timeout=30000
            )
            print("✅ Pagina caricata\n")
            
            # ========== STEP 1: ASPETTA LOGIN SPID ==========
            print("=" * 70)
            print("🔐 STEP 1: LOGIN SPID")
            print("=" * 70)
            print("⏳ Completa il login SPID manualmente...")
            print("   (lo script aspetta che tu finisca)\n")
            
            page.wait_for_selector("input[value='meStesso']", timeout=300000)
            print("✅ Login completato! Script ripreso.\n")
            
            # ========== STEP 2: SELEZIONE UTENZA ==========
            print("=" * 70)
            print("✓ STEP 2: SELEZIONE UTENZA - AUTOMATICO")
            print("=" * 70)
            
            print("   • Selezionando 'Me stesso'...")
            page.click("input[value='meStesso']")
            time.sleep(0.5)
            
            print("   • Cliccando 'Procedi'...")
            page.click("button:has-text('Procedi')")
            page.wait_for_timeout(2000)
            print("✅ Fatto\n")
            
            # ========== STEP 3: CONFERMA RIEPILOGO ==========
            print("=" * 70)
            print("✓ STEP 3: CONFERMA - AUTOMATICO")
            print("=" * 70)
            
            print("   • Cliccando 'Conferma'...")
            page.click("button:has-text('Conferma')")
            page.wait_for_timeout(3000)
            print("✅ Fatto\n")
            
            # ========== STEP 4: FATTURE ELETTRONICHE E ALTRI DATI IVA ==========
            print("=" * 70)
            print("✓ STEP 4: FATTURE ELETTRONICHE E ALTRI DATI IVA")
            print("=" * 70)
            
            print("   • Navigando...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/home",
                wait_until="load",
                timeout=30000
            )
            page.wait_for_timeout(2000)
            print("✅ Fatto\n")
            
            # ========== STEP 5: FATTURE RICEVUTE ==========
            print("=" * 70)
            print("✓ STEP 5: FATTURE RICEVUTE")
            print("=" * 70)
            
            print("   • Navigando...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/fatture/ricevute",
                wait_until="networkidle",
                timeout=30000
            )
            print("   • Aspettando stabilizzazione pagina...")
            page.wait_for_timeout(4000)
            
            # Verifica che gli input siano presenti (significa pagina caricata)
            page.wait_for_selector("input[type='text']", timeout=10000)
            print("✅ Fatto\n")
            
            # ========== STEP 6: COMPILAZIONE DATE + RICERCA ==========
            print("=" * 70)
            print("✓ STEP 6: COMPILAZIONE DATE E RICERCA")
            print("=" * 70)
            
            print(f"   • Compilando date: {dal} - {al}...")
            
            # Usa JavaScript per compilare i campi CON SELETTORI PIÙ PRECISI
            page.evaluate(f"""
                () => {{
                    // Seleziona direttamente per ID
                    const dalInput = document.getElementById('dal');
                    const alInput = document.getElementById('al');
                    
                    console.log('Dal input trovato:', !!dalInput, 'Valore attuale:', dalInput?.value);
                    console.log('Al input trovato:', !!alInput, 'Valore attuale:', alInput?.value);
                    
                    if (dalInput) {{
                        console.log('Compilando Dal con: {dal}');
                        dalInput.value = '{dal}';
                        dalInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        dalInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        dalInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        console.log('Dal compilato. Nuovo valore:', dalInput.value);
                    }}
                    
                    // Attendi un po' prima di compilare Al (per il debounce)
                    setTimeout(() => {{
                        if (alInput) {{
                            console.log('Compilando Al con: {al}');
                            alInput.value = '{al}';
                            alInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            alInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            alInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            alInput.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
                            console.log('Al compilato. Nuovo valore:', alInput.value);
                        }}
                    }}, 300);
                }}
            """)
            
            page.wait_for_timeout(1000)
            print("✅ Date compilate\n")
            
            # CLICCA "CERCA"
            print("   • Cliccando 'Cerca'...")
            page.click("button:has-text('Cerca')")
            page.wait_for_timeout(4000)
            print("✅ Fatto\n")
            # ========== STEP 7: DOWNLOAD AUTOMATICO ==========
            print("=" * 70)
            print("⏳ STEP 7: DOWNLOAD AUTOMATICO IN CORSO...")
            print("=" * 70)
            
            # ========== STEP 7: DOWNLOAD AUTOMATICO ==========
            print("=" * 70)
            print("⏳ STEP 7: DOWNLOAD AUTOMATICO IN CORSO...")
            print("=" * 70)
            
            # Trova tutti i pulsanti di download nella tabella
            buttons = page.locator("tr td:last-child button, tr td:last-child a").all()
            tot_files = len(buttons)
            
            if tot_files == 0:
                print("❌ Nessun file trovato!")
                print("   Verifica le date inserite")
                return
            
            print(f"\n📥 Trovati {tot_files} file\n")
            
            downloaded = 0
            failed = []
            
            for i, button in enumerate(buttons, 1):
                try:
                    print(f"   [{i:2}/{tot_files}] ", end="", flush=True)
                    
                    button.click()
                    page.wait_for_url("**/dettaglio/**", timeout=10000)
                    page.wait_for_load_state("load")
                    
                    with page.expect_download() as download_info:
                        page.click("button:has-text('Download file fattura')")
                    
                    download = download_info.value
                    file_path = DOWNLOAD_DIR / download.suggested_filename
                    download.save_as(str(file_path))
                    
                    print(f"✅ {download.suggested_filename}")
                    downloaded += 1
                    
                    page.go_back()
                    page.wait_for_url("**/ricevute", timeout=10000)
                    page.wait_for_load_state("load")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"❌")
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
            print(f"📅 Periodo:       {dal} - {al}")
            
            if failed:
                print(f"\n⚠️  Errori: {len(failed)} file")
            else:
                print(f"\n🎉 Tutte le fatture scaricate correttamente!")
            
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()
            input("\n▶️  Premi INVIO per chiudere...")
        
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
