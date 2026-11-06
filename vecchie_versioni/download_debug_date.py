#!/usr/bin/env python3
"""
DEBUG DATES - Per capire come compilare correttamente i campi data
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def main():
    print("=" * 70)
    print("🔍 DEBUG DATES - ANALISI CAMPI DATA")
    print("=" * 70)

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

            # ========== LOGIN SPID ==========
            print("🔐 Completa il login SPID manualmente...")
            page.wait_for_selector("input[value='meStesso']", timeout=300000)
            print("✅ Login completato!\n")

            # ========== STEP 2 ==========
            print("Completando step 2...")
            page.click("input[value='meStesso']")
            time.sleep(0.5)
            page.click("button:has-text('Procedi')")
            page.wait_for_timeout(2000)

            # ========== STEP 3 ==========
            print("Completando step 3...")
            page.click("button:has-text('Conferma')")
            page.wait_for_timeout(3000)

            # ========== STEP 4 ==========
            print("Navigando alla home...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/home",
                wait_until="domcontentloaded",
                timeout=30000
            )
            page.wait_for_timeout(3000)

            # ========== NAVIGA A RICEVUTE ==========
            print("Navigando a fatture ricevute...")
            href = page.evaluate("""
                () => {
                    const link = Array.from(document.querySelectorAll('a'))
                        .find(el => el.textContent.includes('Le tue fatture ricevute'));
                    return link ? link.href : null;
                }
            """)
            page.goto(href, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # ========== DEBUG INPUT ==========
            print("\n" + "=" * 70)
            print("🔍 ANALISI CAMPI DATA")
            print("=" * 70)

            # Ispeziona gli input
            input_info = page.evaluate("""
                () => {
                    const dal = document.getElementById('dal');
                    const al = document.getElementById('al');

                    return {
                        dal: {
                            exists: !!dal,
                            type: dal?.type,
                            value: dal?.value,
                            placeholder: dal?.placeholder,
                            pattern: dal?.pattern,
                            minDate: dal?.getAttribute('min'),
                            maxDate: dal?.getAttribute('max'),
                            className: dal?.className,
                            id: dal?.id,
                            name: dal?.name,
                            parent: dal?.parentElement?.outerHTML?.substring(0, 200)
                        },
                        al: {
                            exists: !!al,
                            type: al?.type,
                            value: al?.value,
                            placeholder: al?.placeholder,
                            pattern: al?.pattern,
                            minDate: al?.getAttribute('min'),
                            maxDate: al?.getAttribute('max'),
                            className: al?.className,
                            id: al?.id,
                            name: al?.name
                        }
                    };
                }
            """)

            print(f"\nInput DAL:")
            for key, val in input_info['dal'].items():
                print(f"  {key}: {val}")

            print(f"\nInput AL:")
            for key, val in input_info['al'].items():
                print(f"  {key}: {val}")

            # ========== TEST DIVERSI METODI ==========
            print("\n" + "=" * 70)
            print("🧪 TEST METODI DI COMPILAZIONE")
            print("=" * 70)

            test_date_dal = "01/09/2026"
            test_date_al = "30/09/2026"

            # Metodo 1: JavaScript direct (originale)
            print(f"\n1️⃣  METODO 1: JavaScript diretto")
            print(f"   Impostando: {test_date_dal}")
            page.evaluate(f"""
                () => {{
                    const dal = document.getElementById('dal');
                    dal.value = '{test_date_dal}';
                    dal.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    dal.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    dal.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                }}
            """)
            page.wait_for_timeout(500)

            val_after_method1 = page.evaluate("() => document.getElementById('dal').value")
            print(f"   Valore dopo: {val_after_method1}")
            print(f"   ✅ Funziona" if val_after_method1 == test_date_dal else f"   ❌ NON FUNZIONA - valore diverso!")

            # Reset
            page.evaluate("() => document.getElementById('dal').value = ''")
            page.wait_for_timeout(300)

            # Metodo 2: page.fill()
            print(f"\n2️⃣  METODO 2: page.fill()")
            print(f"   Impostando: {test_date_dal}")
            try:
                page.fill("#dal", test_date_dal)
                page.wait_for_timeout(500)
                val_after_method2 = page.evaluate("() => document.getElementById('dal').value")
                print(f"   Valore dopo: {val_after_method2}")
                print(f"   ✅ Funziona" if val_after_method2 == test_date_dal else f"   ❌ NON FUNZIONA - valore diverso!")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

            # Reset
            page.evaluate("() => document.getElementById('dal').value = ''")
            page.wait_for_timeout(300)

            # Metodo 3: Keyboard typing
            print(f"\n3️⃣  METODO 3: Keyboard typing")
            print(f"   Impostando: {test_date_dal}")
            try:
                page.click("#dal")
                page.keyboard.press("Control+A")
                page.keyboard.type(test_date_dal)
                page.wait_for_timeout(500)
                val_after_method3 = page.evaluate("() => document.getElementById('dal').value")
                print(f"   Valore dopo: {val_after_method3}")
                print(f"   ✅ Funziona" if val_after_method3 == test_date_dal else f"   ❌ NON FUNZIONA - valore diverso!")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

            # ========== TEST CLICK SU CERCA ==========
            print("\n" + "=" * 70)
            print("📋 PROVA: Compila via metodo più sicuro e clicca cerca")
            print("=" * 70)

            # Reset e riempi con il metodo migliore
            page.evaluate("() => { document.getElementById('dal').value = ''; document.getElementById('al').value = ''; }")
            page.wait_for_timeout(300)

            print(f"Impostando date: {test_date_dal} - {test_date_al}")
            page.fill("#dal", test_date_dal)
            page.wait_for_timeout(300)
            page.fill("#al", test_date_al)
            page.wait_for_timeout(300)

            # Verifica i valori
            final_dal = page.evaluate("() => document.getElementById('dal').value")
            final_al = page.evaluate("() => document.getElementById('al').value")

            print(f"\nValori finali:")
            print(f"  Dal input: {final_dal}")
            print(f"  Al input: {final_al}")

            # Prendi uno screenshot
            screenshot_path = "/tmp/ade_date_input.png"
            page.screenshot(path=screenshot_path)
            print(f"\n✅ Screenshot salvato: {screenshot_path}")

            print("\n" + "=" * 70)
            print("⏸️  PAUSA MANUALE")
            print("=" * 70)
            print("Guarda il browser e verifica cosa vedi nei campi data.")
            print("Quali date mostra? Sono quelle che abbiamo impostato?")
            print("\nPoi premi INVIO per cliccare 'Cerca' e vedere i risultati")
            input("\n▶️  Premi INVIO...")

            # Click cerca
            print("\nCiccando 'Cerca'...")
            page.click("button:has-text('Cerca')")
            page.wait_for_timeout(4000)

            # Mostra i risultati
            results = page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('tr');
                    const tableInfo = document.querySelector('table')?.textContent;
                    return {
                        rowCount: rows.length,
                        firstFewRows: Array.from(rows).slice(0, 3).map(r => r.textContent.substring(0, 100))
                    };
                }
            """)

            print(f"\nRisultati trovati:")
            print(f"  Righe nella tabella: {results['rowCount']}")
            print(f"  Prime righe:")
            for i, row in enumerate(results['firstFewRows'], 1):
                print(f"    [{i}] {row}...")

            print("\n▶️  Premi INVIO per chiudere...")
            input()

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
