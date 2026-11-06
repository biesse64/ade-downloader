#!/usr/bin/env python3
"""
Download Fatture (Passive + Attive) - AUTOMATIZZATO
Supporta "Me stesso" e "Incaricato" (multi soggetto)
Date inserite via Angular internals
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def set_date_input(page, field_id, value):
    """
    Imposta un campo <input type="date"> usando il setter nativo del browser.
    value formato: GG/MM/AAAA  es. '01/09/2026'
    Firefox su macOS visualizza type="date" come MM/DD/YYYY, quindi
    per ottenere DD/MM/AAAA visivo dobbiamo passare YYYY-DD-MM come valore ISO
    in modo che Firefox lo mostri come MM/DD = giorno/mese corretto.
    """
    parts = value.split("/")   # ['01', '09', '2026']
    gg, mm, aaaa = parts[0], parts[1], parts[2]
    # Il campo type="date" vuole YYYY-MM-DD — il sito legge questo valore dal DOM
    # Firefox lo visualizza come MM/DD/YYYY ma il valore interno è corretto
    iso = f"{aaaa}-{mm}-{gg}"  # '2026-09-01'

    page.evaluate("""
        ([fieldId, isoValue]) => {
            const el = document.getElementById(fieldId);
            if (!el) return;
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(el, isoValue);
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    """, [field_id, iso])

def main():
    print("=" * 70)
    print("📥 DOWNLOAD FATTURE - PASSIVE E/O ATTIVE")
    print("=" * 70)

    print("\n👤 UTENZA DI LAVORO:")
    print("=" * 70)
    print("1. Me stesso")
    print("2. Incaricato (altra P.IVA che gestisci)")
    print("=" * 70)

    scelta_utenza = input("\nScegli (1/2): ").strip()
    if scelta_utenza not in ("1", "2"):
        print("❌ Scelta non valida!")
        return

    usa_incaricato = (scelta_utenza == "2")

    if usa_incaricato:
        piva_incaricante = input("\n🏢 P.IVA / Codice fiscale del soggetto incaricante (es. 04089410288): ").strip()
        if not piva_incaricante:
            print("❌ P.IVA non inserita!")
            return
        piva_label = piva_incaricante
    else:
        piva_label = "mestesso"

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

    print("\n📅 INSERISCI LE DATE (formato GG/MM/AAAA):")
    dal = input("   Dal: ").strip()
    al  = input("   Al:  ").strip()
    mese = dal.split("/")[1]

    download_dirs = {
        "ricevute": Path(f"./fatture_ade/{piva_label}/{mese}/passive"),
        "emesse":   Path(f"./fatture_ade/{piva_label}/{mese}/attive")
    }
    for dir_path in download_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            print("\n📡 Apertura AdE...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/instr/InstradamentofcWeb/home",
                wait_until="load", timeout=30000
            )
            print("✅ Pagina caricata\n")

            print("🔐 STEP 1: LOGIN SPID — completa manualmente...\n")
            page.wait_for_selector("input[value='meStesso']", timeout=300000)
            print("✅ Login completato!\n")

            if usa_incaricato:
                # --- STEP 1: seleziona radio "Incaricato" → Procedi ---
                print(f"👤 Selezione 'Incaricato'...")
                page.click("label:has-text('Incaricato'), div:has-text('Incaricato') input[type='radio']")
                page.wait_for_timeout(500)
                page.click("button:has-text('Procedi')")
                page.wait_for_timeout(3000)

                # --- STEP 2: dropdown "Codice fiscale del soggetto che ti ha incaricato" ---
                # Aspetta che compaia il select
                print(f"   Selezione P.IVA {piva_incaricante} dal dropdown...")
                page.wait_for_selector("select", timeout=15000)

                # Seleziona per valore (P.IVA) o, se non esiste quel valore, prende la prima opzione valida
                selected = page.evaluate(f"""
                    () => {{
                        const sel = document.querySelector('select');
                        if (!sel) return false;
                        // prova match esatto sul valore
                        const opt = Array.from(sel.options).find(o =>
                            o.value.trim() === '{piva_incaricante}' ||
                            o.text.trim()  === '{piva_incaricante}'
                        );
                        if (opt) {{
                            sel.value = opt.value;
                        }} else {{
                            // prende la prima opzione non vuota
                            const first = Array.from(sel.options).find(o => o.value.trim() !== '');
                            if (first) sel.value = first.value;
                        }}
                        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return sel.value;
                    }}
                """)
                print(f"   Dropdown impostato: {selected}")
                page.wait_for_timeout(500)

                # Procedi (step 2)
                page.click("button:has-text('Procedi')")
                page.wait_for_timeout(2000)

                # --- STEP 3: pagina riepilogo → Conferma ---
                page.wait_for_selector("button:has-text('Conferma')", timeout=15000)
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)
                print("✅ Soggetto incaricante confermato!\n")

                # Aspetta home cons-web / servizi
                page.wait_for_url("**/cons/**", timeout=30000)
            else:
                # Me stesso
                page.click("input[value='meStesso']")
                time.sleep(0.5)
                page.click("button:has-text('Procedi')")
                page.wait_for_timeout(2000)
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)

            # Naviga alla home cons-web (funziona sia per meStesso che per incaricato)
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/home",
                wait_until="networkidle", timeout=30000
            )
            page.wait_for_timeout(2000)
            print("✅ Home caricata\n")

            for tipo in tipi_fatture:
                label = "Fatture Passive (Ricevute)" if tipo == "ricevute" else "Fatture Attive (Emesse)"
                download_dir = download_dirs[tipo]

                print("=" * 70)
                print(f"✓ {label.upper()}")
                print("=" * 70)

                # Naviga alla pagina fatture cliccando il link dalla home
                clicked = page.evaluate(f"""
                    () => {{
                        const links = Array.from(document.querySelectorAll('a'));
                        const link = links.find(a =>
                            a.href.includes('/fatture/{tipo}') ||
                            a.textContent.toLowerCase().includes('{tipo}')
                        );
                        if (link) {{ link.click(); return true; }}
                        return false;
                    }}
                """)

                if clicked:
                    page.wait_for_timeout(5000)
                else:
                    page.goto(
                        f"https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/fatture/{tipo}",
                        wait_until="networkidle", timeout=30000
                    )
                    page.wait_for_timeout(5000)

                page.wait_for_selector("button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')", timeout=20000)
                print("✅ Pagina fatture caricata\n")

                # ===== INSERIMENTO DATE =====
                print(f"📅 Inserimento date: {dal} → {al}...")

                set_date_input(page, "dal", dal)
                page.wait_for_timeout(400)
                set_date_input(page, "al", al)
                page.wait_for_timeout(400)

                # Clicca Cerca
                page.locator("button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')").first.click()
                page.wait_for_timeout(4000)
                print("✅ Date inserite e ricerca avviata!\n")

                # ========== DOWNLOAD ==========
                print("\n⏳ DOWNLOAD IN CORSO...")

                def cerca_fatture():
                    """Re-inserisce le date e clicca Cerca, ritorna il numero di righe trovate."""
                    set_date_input(page, "dal", dal)
                    page.wait_for_timeout(300)
                    set_date_input(page, "al", al)
                    page.wait_for_timeout(300)
                    page.locator("button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')").first.click()
                    # Aspetta che appaiano i risultati (tabella o messaggio "nessun risultato")
                    try:
                        page.wait_for_selector(
                            "table tr td, [class*='risultat'], h2:has-text('Fatture individuate'), "
                            "h3:has-text('Fatture individuate'), p:has-text('nessun')",
                            timeout=15000
                        )
                    except:
                        pass
                    page.wait_for_timeout(1000)
                    return page.locator("tr td:last-child button, tr td:last-child a").count()

                tot_files = cerca_fatture()

                if tot_files == 0:
                    print("❌ Nessun file trovato! Verifica le date.")
                    continue

                print(f"\n📥 Trovati {tot_files} file\n")

                downloaded = 0
                failed = []

                for i in range(tot_files):
                    try:
                        print(f"   [{i+1:2}/{tot_files}] ", end="", flush=True)

                        # Clicca la riga i-esima della lista
                        page.locator("tr td:last-child button, tr td:last-child a").nth(i).click()

                        # Aspetta bottone download o qualsiasi indicatore di pagina caricata
                        page.wait_for_selector(
                            "button:has-text('Download file fattura'), "
                            "a:has-text('Download file fattura'), "
                            "a[href*='.xml'], a[href*='.p7m']",
                            timeout=20000
                        )

                        with page.expect_download() as download_info:
                            dl_btn = page.locator(
                                "button:has-text('Download file fattura'), "
                                "a:has-text('Download file fattura')"
                            )
                            if dl_btn.count() > 0:
                                dl_btn.first.click()
                            else:
                                page.locator("a[href*='.xml'], a[href*='.p7m']").first.click()

                        download = download_info.value
                        file_path = download_dir / download.suggested_filename
                        download.save_as(str(file_path))
                        print(f"✅ {download.suggested_filename}")
                        downloaded += 1

                        # Torna alla lista e re-cerca
                        page.go_back()
                        page.wait_for_timeout(2000)
                        set_date_input(page, "dal", dal)
                        page.wait_for_timeout(400)
                        set_date_input(page, "al", al)
                        page.wait_for_timeout(400)
                        page.locator("button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')").first.click()
                        try:
                            page.wait_for_selector("tr td:last-child button, tr td:last-child a", timeout=15000)
                        except:
                            pass
                        page.wait_for_timeout(1000)

                    except Exception as e:
                        err_short = str(e).split('\n')[0]
                        print(f"❌ {err_short}")
                        failed.append((i+1, str(e)))
                        try:
                            page.go_back()
                            page.wait_for_timeout(2000)
                            set_date_input(page, "dal", dal)
                            page.wait_for_timeout(400)
                            set_date_input(page, "al", al)
                            page.wait_for_timeout(400)
                            page.locator("button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')").first.click()
                            try:
                                page.wait_for_selector("tr td:last-child button, tr td:last-child a", timeout=15000)
                            except:
                                pass
                            page.wait_for_timeout(1000)
                        except:
                            pass

                print("\n" + "=" * 70)
                print(f"📊 RIEPILOGO - {label}")
                print(f"✅ Scaricati: {downloaded}/{tot_files}  📁 {download_dir.absolute()}")
                if failed:
                    print(f"⚠️  Errori: {len(failed)}")
                else:
                    print("🎉 Tutti i file scaricati!")
                print("=" * 70 + "\n")

                if len(tipi_fatture) > 1:
                    page.goto(
                        "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/home",
                        wait_until="networkidle", timeout=30000
                    )
                    page.wait_for_timeout(2000)

            print("\n✅ OPERAZIONE COMPLETATA!")
            print(f"📁 {Path(f'./fatture_ade/{piva_label}').absolute()}\n")

        except Exception as e:
            print(f"\n❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
