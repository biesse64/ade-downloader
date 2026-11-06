#!/usr/bin/env python3
"""
Download Fatture (Passive + Attive) - 100% AUTOMATIZZATO
Scarica entrambi i tipi con un'unica autenticazione SPID
VERSIONE CHROMIUM CON TIMEOUT AUMENTATI
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def main():
    print("=" * 70)
    print("📥 DOWNLOAD FATTURE - PASSIVE E/O ATTIVE")
    print("=" * 70)
    
    # ========== SCELTA TIPO FATTURE ==========
    print("\n📋 QUALE TIPO DI FATTURE VUOI SCARICARE?")
    print("=" * 70)
    print("1. Solo Fatture Passive (Ricevute)")
    print("2. Solo Fatture Attive (Emesse)")
    print("3. Entrambe")
    print("=" * 70)
    
    scelta = input("\nScegli (1/2/3): ").strip()
    
    tipi_fatture = []
    if scelta == "1":
        tipi_fatture = ["ricevute"]
    elif scelta == "2":
        tipi_fatture = ["emesse"]
    elif scelta == "3":
        tipi_fatture = ["ricevute", "emesse"]
    else:
        print("❌ Scelta non valida!")
        return
    
    # ========== INPUT DELLE DATE ==========
    print("\n📅 INSERISCI LE DATE:")
    print("=" * 70)
    dal = input("   Dal (GG/MM/YYYY): ").strip()
    al = input("   Al  (GG/MM/YYYY): ").strip()
    
    dal_parts = dal.split('/')
    al_parts = al.split('/')
    mese = dal_parts[1]
    
    print(f"   Debug - Dal: {dal}")
    print(f"   Debug - Al: {al}")
    print("=" * 70 + "\n")
    
    # Crea cartelle
    download_dirs = {
        "ricevute": Path(f"./fatture_ade/{mese}/passive"),
        "emesse": Path(f"./fatture_ade/{mese}/attive")
    }
    
    for dir_path in download_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
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
            
            # ========== STEP 4: NAVIGAZIONE ==========
            print("=" * 70)
            print("✓ STEP 4: FATTURE ELETTRONICHE")
            print("=" * 70)
            
            print("   • Navigando...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/home",
                wait_until="load",
                timeout=30000
            )
            page.wait_for_timeout(2000)
            print("✅ Fatto\n")
            
            # ========== LOOP PER OGNI TIPO DI FATTURA ==========
            for tipo in tipi_fatture:
                label = "Fatture Passive (Ricevute)" if tipo == "ricevute" else "Fatture Attive (Emesse)"
                download_dir = download_dirs[tipo]
                
                # ========== NAVIGAZIONE ==========
                print("=" * 70)
                print(f"✓ {label.upper()}")
                print("=" * 70)
                
                print("   • Navigando...")
                page.goto(
                    f"https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/fatture/{tipo}",
                    wait_until="networkidle",
                    timeout=30000
                )
                print("   • Aspettando pagina (30 secondi)...")
                page.wait_for_timeout(8000)
                
                # AUMENTATO A 30 SECONDI INVECE DI 10
                try:
                    page.wait_for_selector("input[type='text']", timeout=30000)
                    print("✅ Campi trovati\n")
                except:
                    print("⚠️  Campi input non trovati")
                    print("   Prova ad aprire il browser manualmente e verifica la pagina\n")
                    continue
                
                # ========== COMPILAZIONE DATE ==========
                print("=" * 70)
                print("✓ COMPILAZIONE DATE")
                print("=" * 70)
                
                print(f"   • Compilando date: {dal} - {al}...")
                
                page.evaluate(f"""
                    () => {{
                        const dalInput = document.getElementById('dal');
                        const alInput = document.getElementById('al');
                        
                        if (dalInput) {{
                            dalInput.value = '';
                            dalInput.value = '{dal}';
                            dalInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            dalInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            dalInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        }}
                        
                        setTimeout(() => {{
                            if (alInput) {{
                                alInput.value = '';
                                alInput.value = '{al}';
                                alInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                alInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                alInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                alInput.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
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
                
                # ========== DOWNLOAD AUTOMATICO ==========
                print("=" * 70)
                print("⏳ DOWNLOAD AUTOMATICO IN CORSO...")
                print("=" * 70)
                
                buttons = page.locator("tr td:last-child button, tr td:last-child a").all()
                tot_files = len(buttons)
                
                if tot_files == 0:
                    print("❌ Nessun file trovato!")
                    continue
                
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
                        file_path = download_dir / download.suggested_filename
                        download.save_as(str(file_path))
                        
                        print(f"✅ {download.suggested_filename}")
                        downloaded += 1
                        
                        page.go_back()
                        page.wait_for_url(f"**/{tipo}", timeout=10000)
                        page.wait_for_load_state("load")
                        
                        time.sleep(0.3)
                        
                    except Exception as e:
                        print(f"❌")
                        failed.append((i, str(e)))
                        try:
                            page.go_back()
                        except:
                            pass
                
                # RIEPILOGO
                print("\n" + "=" * 70)
                print(f"📊 RIEPILOGO - {label}")
                print("=" * 70)
                print(f"✅ Scaricati:     {downloaded}/{tot_files} file")
                print(f"📁 Cartella:      {download_dir.absolute()}")
                print(f"📅 Periodo:       {dal} - {al}\n")
            
            print("=" * 70)
            print("✅ OPERAZIONE COMPLETATA!")
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
