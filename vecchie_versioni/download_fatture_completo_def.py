#!/usr/bin/env python3
"""
Download Fatture (Passive + Attive + Transfrontaliere emesse) - AUTOMATIZZATO
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
    """
    parts = value.split("/")   # ['01', '09', '2026']
    gg, mm, aaaa = parts[0], parts[1], parts[2]
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


def download_sezione(page, label, url, download_dir, dal, al):
    """
    Scarica tutti i file di una sezione fatture (ricevute / emesse / transfrontaliere).
    Stessa logica per tutte le sezioni: cerca per data → click riga → download → torna.
    """
    print("=" * 70)
    print(f"✓ {label.upper()}")
    print("=" * 70)

    # Naviga direttamente alla pagina per URL
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    page.wait_for_selector(
        "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')",
        timeout=20000
    )
    print("✅ Pagina caricata\n")

    # ===== INSERIMENTO DATE =====
    print(f"📅 Inserimento date: {dal} → {al}...")
    set_date_input(page, "dal", dal)
    page.wait_for_timeout(400)
    set_date_input(page, "al", al)
    page.wait_for_timeout(400)

    page.locator(
        "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')"
    ).first.click()
    page.wait_for_timeout(4000)
    print("✅ Date inserite e ricerca avviata!\n")

    # ========== FUNZIONE CERCA ==========
    def cerca():
        """Re-inserisce le date e clicca Cerca, ritorna il numero di righe trovate."""
        set_date_input(page, "dal", dal)
        page.wait_for_timeout(300)
        set_date_input(page, "al", al)
        page.wait_for_timeout(300)
        page.locator(
            "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')"
        ).first.click()
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

    tot_files = cerca()

    if tot_files == 0:
        print("❌ Nessun file trovato per questo intervallo di date.")
        return 0, 0

    print(f"\n📥 Trovati {tot_files} file\n")

    downloaded = 0
    failed = []

    for i in range(tot_files):
        try:
            print(f"   [{i+1:2}/{tot_files}] ", end="", flush=True)

            # Clicca la riga i-esima
            page.locator("tr td:last-child button, tr td:last-child a").nth(i).click()

            # Aspetta il bottone download
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

            # Torna alla lista e ri-cerca
            page.go_back()
            page.wait_for_timeout(2000)
            set_date_input(page, "dal", dal)
            page.wait_for_timeout(400)
            set_date_input(page, "al", al)
            page.wait_for_timeout(400)
            page.locator(
                "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')"
            ).first.click()
            try:
                page.wait_for_selector(
                    "tr td:last-child button, tr td:last-child a", timeout=15000
                )
            except:
                pass
            page.wait_for_timeout(1000)

        except Exception as e:
            err_short = str(e).split('\n')[0]
            print(f"❌ {err_short}")
            failed.append((i + 1, str(e)))
            try:
                page.go_back()
                page.wait_for_timeout(2000)
                set_date_input(page, "dal", dal)
                page.wait_for_timeout(400)
                set_date_input(page, "al", al)
                page.wait_for_timeout(400)
                page.locator(
                    "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')"
                ).first.click()
                try:
                    page.wait_for_selector(
                        "tr td:last-child button, tr td:last-child a", timeout=15000
                    )
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

    return downloaded, tot_files


def main():
    print("=" * 70)
    print("📥 DOWNLOAD FATTURE - PASSIVE / ATTIVE / TRANSFRONTALIERE")
    print("=" * 70)

    # ---- UTENZA ----
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
        piva_incaricante = input(
            "\n🏢 P.IVA / Codice fiscale del soggetto incaricante (es. 04089410288): "
        ).strip()
        if not piva_incaricante:
            print("❌ P.IVA non inserita!")
            return
        piva_label = piva_incaricante
    else:
        piva_label = "mestesso"

    # ---- TIPO FATTURE ----
    print("\n📋 QUALE TIPO DI FATTURE VUOI SCARICARE?")
    print("=" * 70)
    print("1. Solo Fatture Passive (Ricevute)")
    print("2. Solo Fatture Attive (Emesse)")
    print("3. Entrambe (Passive + Attive)")
    print("4. Tutte (Passive + Attive + Transfrontaliere emesse)")
    print("=" * 70)

    scelta = input("\nScegli (1/2/3/4): ").strip()

    scarica_passive       = scelta in ("1", "3", "4")
    scarica_attive        = scelta in ("2", "3", "4")
    scarica_transfrontal  = scelta in ("4",)

    if scelta not in ("1", "2", "3", "4"):
        print("❌ Scelta non valida!")
        return

    # Opzione separata per transfrontaliere se non già inclusa
    if scelta in ("1", "2", "3"):
        includi_tf = input(
            "\n🌍 Includi anche Fatture Transfrontaliere Emesse? (s/n): "
        ).strip().lower()
        if includi_tf == "s":
            scarica_transfrontal = True

    # ---- DATE ----
    print("\n📅 INSERISCI LE DATE (formato GG/MM/AAAA):")
    dal = input("   Dal: ").strip()
    al  = input("   Al:  ").strip()
    mese = dal.split("/")[1]

    # ---- CARTELLE ----
    base = Path(f"./fatture_ade/{piva_label}/{mese}")
    dirs = {
        "passive":        base / "passive",
        "attive":         base / "attive",
        "transfrontaliere": base / "transfrontaliere_emesse",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # ---- URL ----
    BASE_URL = "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web"
    urls = {
        "passive":          f"{BASE_URL}/fatture/ricevute",
        "attive":           f"{BASE_URL}/fatture/emesse",
        "transfrontaliere": f"{BASE_URL}/transfrontaliere/emesse",
    }

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, channel="firefox")
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

            # ---- CONFIGURAZIONE UTENZA ----
            if usa_incaricato:
                print(f"👤 Selezione 'Incaricato'...")
                page.click("input[value='incaricato']")
                page.wait_for_timeout(500)
                page.click(
                    "button[type='submit']:has-text('Procedi'), "
                    "button.btn-primary:has-text('Procedi')"
                )
                page.wait_for_timeout(2000)

                print(f"   Selezione P.IVA {piva_incaricante}...")
                page.wait_for_selector("select#incaricante", timeout=15000)
                page.wait_for_timeout(400)

                selected = page.evaluate(f"""
                    () => {{
                        const sel = document.getElementById('incaricante');
                        if (!sel) return 'select non trovato';
                        const opt = Array.from(sel.options).find(o =>
                            o.text.trim() === '{piva_incaricante}' ||
                            o.value.includes('{piva_incaricante}')
                        );
                        if (!opt) return 'opzione non trovata';
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLSelectElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(sel, opt.value);
                        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'ok: ' + opt.text.trim();
                    }}
                """)
                print(f"   Dropdown: {selected}")
                page.wait_for_timeout(400)

                page.click(
                    "button[type='submit']:has-text('Procedi'), "
                    "button.btn-primary:has-text('Procedi')"
                )
                page.wait_for_timeout(2000)

                page.wait_for_selector("button:has-text('Conferma')", timeout=15000)
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)

                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(1000)
                print("✅ Soggetto incaricante confermato!\n")

            else:
                page.click("input[value='meStesso']")
                time.sleep(0.5)
                page.click("button:has-text('Procedi')")
                page.wait_for_timeout(2000)
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)

            print("✅ Configurazione utenza completata\n")

            # ---- DOWNLOAD SEZIONI ----
            if scarica_passive:
                download_sezione(
                    page,
                    label="Fatture Passive (Ricevute)",
                    url=urls["passive"],
                    download_dir=dirs["passive"],
                    dal=dal, al=al
                )

            if scarica_attive:
                download_sezione(
                    page,
                    label="Fatture Attive (Emesse)",
                    url=urls["attive"],
                    download_dir=dirs["attive"],
                    dal=dal, al=al
                )

            if scarica_transfrontal:
                download_sezione(
                    page,
                    label="Fatture Transfrontaliere Emesse",
                    url=urls["transfrontaliere"],
                    download_dir=dirs["transfrontaliere"],
                    dal=dal, al=al
                )

            print("\n✅ OPERAZIONE COMPLETATA!")
            print(f"📁 {base.absolute()}\n")

        except Exception as e:
            print(f"\n❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
