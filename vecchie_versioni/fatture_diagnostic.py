#!/usr/bin/env python3
"""
DIAGNOSTIC VERSION - Per capire cosa sta succedendo sulla pagina
Ferma prima di cercare gli input e ti lascia ispezionare manualmente
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def main():
    print("=" * 70)
    print("🔍 DIAGNOSTIC MODE - ANALISI PAGINA")
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

            # ========== STEP 5: NAVIGATE TO FATTURE RICEVUTE ==========
            print("=" * 70)
            print("🔍 DIAGNOSTIC: Navigazione a Fatture Ricevute")
            print("=" * 70)

            print("   • Navigando a fatture/ricevute...")
            page.goto(
                f"https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/#/fatture/ricevute",
                wait_until="networkidle",
                timeout=30000
            )
            print("   • Pagina caricata, aspettando 6 secondi...\n")
            page.wait_for_timeout(6000)  # Aspetta di più

            # ========== DIAGNOSTIC INSPECTION ==========
            print("=" * 70)
            print("📋 ISPEZIONE PAGINA")
            print("=" * 70)

            # Cerca vari tipi di input
            search_queries = [
                ("input[type='text']", "Input type='text'"),
                ("input[type='date']", "Input type='date'"),
                ("input#dal", "Input id='dal'"),
                ("input#al", "Input id='al'"),
                ("[placeholder*='GG']", "Input con placeholder 'GG'"),
                ("[placeholder*='dal']", "Input con placeholder 'dal'"),
                ("input", "Tutti gli input"),
                (".form-control", "Form control class"),
                ("form", "Tutti i form"),
            ]

            for selector, description in search_queries:
                count = page.locator(selector).count()
                print(f"\n   {description} ({selector}): {count} trovati")

                if count > 0 and count <= 5:
                    elements = page.locator(selector).all()
                    for i, elem in enumerate(elements, 1):
                        try:
                            tag = elem.evaluate("el => el.tagName")
                            id_attr = elem.evaluate("el => el.id || 'N/A'")
                            type_attr = elem.evaluate("el => el.type || 'N/A'")
                            placeholder = elem.evaluate("el => el.placeholder || 'N/A'")
                            visible = elem.is_visible()

                            print(f"      [{i}] <{tag} id='{id_attr}' type='{type_attr}' placeholder='{placeholder}' visible={visible}>")
                        except:
                            print(f"      [{i}] (non ispezionabile)")

            # Esegui JavaScript per controllare il DOM
            print("\n" + "=" * 70)
            print("🔧 JAVASCRIPT INSPECTION")
            print("=" * 70)

            dom_info = page.evaluate("""
                () => {
                    return {
                        pageTitle: document.title,
                        currentUrl: window.location.href,
                        bodyClasses: document.body.className,
                        inputDal: document.getElementById('dal'),
                        inputAl: document.getElementById('al'),
                        formInputs: document.querySelectorAll('input').length,
                        visibleInputs: Array.from(document.querySelectorAll('input'))
                            .filter(el => el.offsetParent !== null)
                            .length,
                        angularRoot: !!document.querySelector('[ng-app]') || !!document.querySelector('[ng-controller]'),
                    };
                }
            """)

            print(f"\n   Titolo pagina: {dom_info['pageTitle']}")
            print(f"   URL: {dom_info['currentUrl']}")
            print(f"   Body class: {dom_info['bodyClasses']}")
            print(f"   Input#dal esiste: {dom_info['inputDal'] is not None}")
            print(f"   Input#al esiste: {dom_info['inputAl'] is not None}")
            print(f"   Tot input nel DOM: {dom_info['formInputs']}")
            print(f"   Input visibili: {dom_info['visibleInputs']}")
            print(f"   Angular framework: {dom_info['angularRoot']}")

            # Screenshot
            print("\n" + "=" * 70)
            screenshot_path = "/tmp/ade_diagnostic.png"
            page.screenshot(path=screenshot_path)
            print(f"✅ Screenshot salvato: {screenshot_path}")

            print("\n" + "=" * 70)
            print("ℹ️  ISTRUZIONI MANUALI")
            print("=" * 70)
            print("""
1. Guarda il browser che si è aperto
2. Se vedi i campi di input per le date:
   → I selettori sono giusti, il problema è il timing
   → Aumentiamo il wait_for_timeout

3. Se NON vedi i campi:
   → Il sito potrebbe aver cambiato la struttura
   → Ispeziona manualmente con F12 e dammi i selettori attuali

4. Se vedi un errore:
   → La pagina potrebbe non aver caricato completamente
   → Potrebbe essere necessario attendere un evento specifico
            """)

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
