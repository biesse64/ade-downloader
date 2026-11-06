#!/usr/bin/env python3
"""
Download Fatture (Passive + Attive) - 100% AUTOMATIZZATO
Scarica entrambi i tipi con un'unica autenticazione SPID
VERSIONE: Esattamente come quella che funzionava a settembre
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

    # Estrai il mese dalla data iniziale
    dal_parts = dal.split('/')
    al_parts = al.split('/')
    mese = dal_parts[1]

    print(f"   Debug - Dal: {dal}")
    print(f"   Debug - Al: {al}")
    print(f"   Debug - Mese: {mese}")
    print("=" * 70 + "\n")

    # Crea cartelle per i diversi tipi, ORGANIZZATE PER MESE
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

            # ========== LOOP PER OGNI TIPO DI FATTURA ==========
            for tipo in tipi_fatture:
                label = "Fatture Passive (Ricevute)" if tipo == "ricevute" else "Fatture Attive (Emesse)"
                download_dir = download_dirs[tipo]

                # ========== STEP 5: NAVIGAZIONE ==========
                print("=" * 70)
                print(f"✓ STEP 5: {label.upper()}")
                print("=" * 70)

                print("   • Navigando...")
                page.goto(
                    f"https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/fatture/{tipo}",
                    wait_until="networkidle",
                    timeout=30000
                )
                print("   • Aspettando stabilizzazione pagina...")
                page.wait_for_timeout(4000)

                # Verifica che gli input siano presenti (aspetta gli ID, non il tipo)
                page.wait_for_selector("#dal, #al", timeout=10000)
                print("✅ Fatto\n")

                # ========== STEP 6: COMPILAZIONE DATE E RICERCA ==========
                print("=" * 70)
                print("✓ STEP 6: COMPILAZIONE DATE E RICERCA")
                print("=" * 70)

                print(f"   • Compilando date: {dal} - {al}...")

                # Usa JavaScript per compilare i campi - ESATTAMENTE COME L'ORIGINALE
                page.evaluate(f"""
                    () => {{
                        const dalInput = document.getElementById('dal');
                        const alInput = document.getElementById('al');

                        console.log('Dal input trovato:', !!dalInput, 'Valore attuale:', dalInput?.value);
                        console.log('Al input trovato:', !!alInput, 'Valore attuale:', alInput?.value);

                        if (dalInput) {{
                            console.log('Pulendo e compilando Dal con: {dal}');
                            dalInput.value = '';  // Clear
                            dalInput.value = '{dal}';
                            dalInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            dalInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            dalInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            console.log('Dal compilato. Nuovo valore:', dalInput.value);
                        }}

                        setTimeout(() => {{
                            if (alInput) {{
                                console.log('Pulendo e compilando Al con: {al}');
                                alInput.value = '';  // Clear
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

                # Trova tutti i pulsanti di download nella tabella
                buttons = page.locator("tr td:last-child button, tr td:last-child a").all()
                tot_files = len(buttons)

                if tot_files == 0:
                    print("❌ Nessun file trovato!")
                    print("   Verifica le date inserite")
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

                # ========== RIEPILOGO PER QUESTO TIPO ==========
                print("\n" + "=" * 70)
                print(f"📊 RIEPILOGO - {label}")
                print("=" * 70)
                print(f"✅ Scaricati:     {downloaded}/{tot_files} file")
                print(f"📁 Cartella:      {download_dir.absolute()}")
                print(f"📅 Periodo:       {dal} - {al}")

                if failed:
                    print(f"\n⚠️  Errori: {len(failed)} file")
                else:
                    print(f"\n🎉 Tutti i file scaricati correttamente!")

                print("=" * 70 + "\n")

            # ========== RIEPILOGO FINALE ==========
            print("\n" + "=" * 70)
            print("✅ OPERAZIONE COMPLETATA!")
            print("=" * 70)
            print(f"📁 Cartella principale: {Path('./fatture_ade').absolute()}")
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
