#!/usr/bin/env python3
"""
Debug dettagliato per Firefox - mostra esattamente dove si blocca
"""

import sys
import time
from playwright.sync_api import sync_playwright

print("=" * 70)
print("🔍 DEBUG FIREFOX DETTAGLIATO")
print("=" * 70)

try:
    print("\n1️⃣  Inizializzazione Playwright...")
    with sync_playwright() as p:
        print("   ✅ Playwright inizializzato\n")
        
        print("2️⃣  Lanciamento Firefox (con timeout 15 secondi)...")
        print("   (Se si blocca qui, il problema è Firefox)")
        
        start_time = time.time()
        try:
            browser = p.firefox.launch(headless=False, timeout=15000)
            elapsed = time.time() - start_time
            print(f"   ✅ Firefox lanciato in {elapsed:.2f}s\n")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Errore dopo {elapsed:.2f}s: {e}\n")
            raise
        
        print("3️⃣  Creazione contesto...")
        context = browser.new_context(accept_downloads=True)
        print("   ✅ Contesto creato\n")
        
        print("4️⃣  Creazione pagina...")
        page = context.new_page()
        print("   ✅ Pagina creata\n")
        
        print("5️⃣  Navigazione a pagina semplice (Google)...")
        print("   (Se si blocca qui, il problema è la connettività)")
        try:
            page.goto("https://www.google.com", timeout=10000, wait_until="load")
            print("   ✅ Google caricato\n")
        except Exception as e:
            print(f"   ⚠️  Errore caricamento Google: {e}\n")
            print("   Provo AdE...\n")
        
        print("6️⃣  Navigazione a AdE...")
        print("   (Se si blocca qui, il problema è AdE o rete)")
        try:
            page.goto(
                "https://ivaservizi.agenziaentrate.gov.it/instr/InstradamentofcWeb/home",
                timeout=15000,
                wait_until="load"
            )
            print("   ✅ AdE caricato\n")
            
            # Scatta uno screenshot
            print("7️⃣  Scatto screenshot...")
            screenshot_data = page.screenshot()
            print(f"   ✅ Screenshot preso ({len(screenshot_data)} bytes)\n")
            
        except Exception as e:
            print(f"   ⚠️  Errore: {e}\n")
        
        print("8️⃣  Chiusura...")
        context.close()
        browser.close()
        print("   ✅ Chiuso\n")
        
        print("=" * 70)
        print("✅ TEST COMPLETATO CON SUCCESSO")
        print("=" * 70)
        
except KeyboardInterrupt:
    print("\n\n⏸️  INTERROTTO DALL'UTENTE (Ctrl+C)")
    print("Il blocco era in uno dei passaggi sopra\n")
except Exception as e:
    print(f"\n❌ ERRORE CRITICO: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
