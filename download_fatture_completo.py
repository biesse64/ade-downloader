#!/usr/bin/env python3
"""
Download Fatture (Passive + Attive + Transfrontaliere emesse) - AUTOMATIZZATO
Supporta "Me stesso" e "Incaricato" (multi soggetto)
Date inserite via Angular internals
v2 - timeout aumentati, retry automatico, skip file già scaricati
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

TIMEOUT_NAV  = 60000   # navigazione pagine
TIMEOUT_SEL  = 40000   # attesa selettori
TIMEOUT_DL   = 90000   # attesa download
MAX_RETRY    = 3       # tentativi per file


def set_date_input(page, field_id, value):
    parts = value.split("/")
    gg, mm, aaaa = parts[0], parts[1], parts[2]
    iso = f"{aaaa}-{mm}-{gg}"
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


def ripristina_lista(page, url, dal, al):
    """Torna alla lista fatture e rilancia la ricerca."""
    try:
        page.goto(url, wait_until="networkidle", timeout=TIMEOUT_NAV)
        page.wait_for_timeout(2000)
    except Exception:
        pass
    try:
        set_date_input(page, "dal", dal)
        page.wait_for_timeout(300)
        set_date_input(page, "al", al)
        page.wait_for_timeout(300)
        page.locator(
            "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')"
        ).first.click()
        try:
            page.wait_for_selector(
                "tr td:last-child button, tr td:last-child a",
                timeout=TIMEOUT_SEL
            )
        except Exception:
            pass
        page.wait_for_timeout(1000)
    except Exception:
        pass


def download_sezione(page, label, url, download_dir, dal, al):
    print("=" * 70)
    print(f"✓ {label.upper()}")
    print("=" * 70)

    # Controlla file già presenti nella cartella
    gia_presenti = set(f.name for f in download_dir.glob("*") if f.is_file())
    if gia_presenti:
        print(f"ℹ️  File già presenti nella cartella: {len(gia_presenti)}")

    page.goto(url, wait_until="networkidle", timeout=TIMEOUT_NAV)
    page.wait_for_timeout(3000)
    page.wait_for_selector(
        "button.btn-primary:has-text('Cerca'), button[type='submit']:has-text('Cerca')",
        timeout=TIMEOUT_SEL
    )
    print("✅ Pagina caricata\n")
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

    def cerca():
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
                timeout=TIMEOUT_SEL
            )
        except Exception:
            pass
        page.wait_for_timeout(1000)
        return page.locator("tr td:last-child button, tr td:last-child a").count()

    tot_files = cerca()
    if tot_files == 0:
        print("❌ Nessun file trovato per questo intervallo di date.")
        return 0, 0

    print(f"\n📥 Trovati {tot_files} file\n")
    downloaded = 0
    skipped    = 0
    failed     = []

    for i in range(tot_files):
        print(f"   [{i+1:2}/{tot_files}] ", end="", flush=True)

        success = False
        for tentativo in range(MAX_RETRY):
            if tentativo > 0:
                print(f"      ↩️  Retry {tentativo}/{MAX_RETRY-1}... ", end="", flush=True)
                ripristina_lista(page, url, dal, al)

            try:
                page.locator("tr td:last-child button, tr td:last-child a").nth(i).click()
                page.wait_for_selector(
                    "button:has-text('Download file fattura'), "
                    "a:has-text('Download file fattura'), "
                    "a[href*='.xml'], a[href*='.p7m']",
                    timeout=TIMEOUT_SEL
                )
                with page.expect_download(timeout=TIMEOUT_DL) as download_info:
                    dl_btn = page.locator(
                        "button:has-text('Download file fattura'), "
                        "a:has-text('Download file fattura')"
                    )
                    if dl_btn.count() > 0:
                        dl_btn.first.click()
                    else:
                        page.locator("a[href*='.xml'], a[href*='.p7m']").first.click()
                download = download_info.value
                fname = download.suggested_filename
                file_path = download_dir / fname

                # Skip se già presente
                if fname in gia_presenti:
                    download.cancel()
                    print(f"⏭️  già presente ({fname})")
                    skipped += 1
                    success = True
                    page.go_back()
                    page.wait_for_timeout(1500)
                    ripristina_lista(page, url, dal, al)
                    break

                download.save_as(str(file_path))
                gia_presenti.add(fname)
                print(f"✅ {fname}")
                downloaded += 1
                success = True
                page.go_back()
                page.wait_for_timeout(2000)
                ripristina_lista(page, url, dal, al)
                break

            except Exception as e:
                err_short = str(e).split('\n')[0][:80]
                if tentativo < MAX_RETRY - 1:
                    print(f"⚠️  {err_short}")
                    page.wait_for_timeout(3000)
                else:
                    print(f"❌ {err_short}")
                    failed.append((i + 1, str(e)))
                    try:
                        ripristina_lista(page, url, dal, al)
                    except Exception:
                        pass

    print("\n" + "=" * 70)
    print(f"📊 RIEPILOGO - {label}")
    print(f"✅ Scaricati: {downloaded}/{tot_files}  ⏭️  Saltati: {skipped}  📁 {download_dir.absolute()}")
    if failed:
        print(f"⚠️  Errori su {len(failed)} file:")
        for idx, _ in failed:
            print(f"   - file #{idx}")
    else:
        print("🎉 Tutti i file scaricati!")
    print("=" * 70 + "\n")
    return downloaded, tot_files


def main():
    print("=" * 70)
    print("📥 DOWNLOAD FATTURE - PASSIVE / ATTIVE / TRANSFRONTALIERE")
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
        piva_incaricante = input(
            "\n🏢 P.IVA / Codice fiscale soggetto incaricante (es. 04089410288): "
        ).strip()
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
    print("3. Entrambe (Passive + Attive)")
    print("4. Tutte (Passive + Attive + Transfrontaliere emesse)")
    print("=" * 70)

    scelta = input("\nScegli (1/2/3/4): ").strip()
    scarica_passive      = scelta in ("1", "3", "4")
    scarica_attive       = scelta in ("2", "3", "4")
    scarica_transfrontal = scelta in ("4",)

    if scelta not in ("1", "2", "3", "4"):
        print("❌ Scelta non valida!")
        return

    if scelta in ("1", "2", "3"):
        includi_tf = input("\n🌍 Includi Fatture Transfrontaliere Emesse? (s/n): ").strip().lower()
        if includi_tf == "s":
            scarica_transfrontal = True

    print("\n📅 INSERISCI LE DATE (formato GG/MM/AAAA):")
    dal = input("   Dal: ").strip()
    al  = input("   Al:  ").strip()
    mese = dal.split("/")[1]
    anno = dal.split("/")[2]

    base = Path(f"./fatture_ade/{piva_label}/{anno}/{mese}")
    dirs = {
        "passive":          base / "passive",
        "attive":           base / "attive",
        "transfrontaliere": base / "transfrontaliere_emesse",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    BASE_URL = "https://ivaservizi.agenziaentrate.gov.it/cons/cons-web"
    urls = {
        "passive":          f"{BASE_URL}/fatture/ricevute",
        "attive":           f"{BASE_URL}/fatture/emesse",
        "transfrontaliere": f"{BASE_URL}/transfrontaliere/emesse",
    }

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            print("\n📡 Apertura AdE...")
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/instr/InstradamentofcWeb/home",
                wait_until="load", timeout=TIMEOUT_NAV
            )
            print("✅ Pagina caricata\n")
            print("🔐 LOGIN SPID — completa manualmente...\n")
            page.wait_for_selector("input[value='meStesso']", timeout=300000)
            print("✅ Login completato!\n")

            if usa_incaricato:
                print(f"👤 Selezione 'Incaricato'...")
                page.click("input[value='incaricato']")
                page.wait_for_timeout(500)
                page.click("button[type='submit']:has-text('Procedi'), button.btn-primary:has-text('Procedi')")
                page.wait_for_timeout(2000)
                print(f"   Selezione P.IVA {piva_incaricante}...")
                page.wait_for_selector("select#incaricante", timeout=TIMEOUT_SEL)
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
                page.click("button[type='submit']:has-text('Procedi'), button.btn-primary:has-text('Procedi')")
                page.wait_for_timeout(2000)
                page.wait_for_selector("button:has-text('Conferma')", timeout=TIMEOUT_SEL)
                page.click("button:has-text('Conferma')")
                page.wait_for_timeout(3000)
                page.wait_for_load_state("networkidle", timeout=TIMEOUT_NAV)
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

            if scarica_passive:
                download_sezione(page, "Fatture Passive (Ricevute)", urls["passive"], dirs["passive"], dal, al)
            if scarica_attive:
                download_sezione(page, "Fatture Attive (Emesse)", urls["attive"], dirs["attive"], dal, al)
            if scarica_transfrontal:
                download_sezione(page, "Fatture Transfrontaliere Emesse", urls["transfrontaliere"], dirs["transfrontaliere"], dal, al)

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
