#!/usr/bin/env python3
"""
Debug script per verificare connettività e Playwright
"""

import sys
import time
import subprocess

print("=" * 70)
print("🔍 DEBUG FATTURE - VERIFICA SISTEMA")
print("=" * 70)

# Test 1: Python version
print("\n1️⃣  Verifica Python...")
try:
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print("   ✅ Python OK\n")
except Exception as e:
    print(f"   ❌ Errore: {e}\n")
    sys.exit(1)

# Test 2: Connettività internet
print("2️⃣  Verifica connettività internet...")
try:
    result = subprocess.run(["ping", "-c", "1", "8.8.8.8"], timeout=5, capture_output=True)
    if result.returncode == 0:
        print("   ✅ Connessione internet OK\n")
    else:
        print("   ⚠️  Ping fallito (ma potrebbe essere bloccato)\n")
except Exception as e:
    print(f"   ⚠️  Errore ping: {e}\n")

# Test 3: Connettività AdE
print("3️⃣  Verifica connettività AdE...")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(("ivaservizi.agenziaentrate.gov.it", 443))
    sock.close()
    if result == 0:
        print("   ✅ Connessione AdE OK\n")
    else:
        print(f"   ❌ Connessione AdE fallita (code: {result})\n")
except Exception as e:
    print(f"   ❌ Errore: {e}\n")

# Test 4: Playwright import
print("4️⃣  Verifica Playwright...")
try:
    from playwright.sync_api import sync_playwright
    print("   ✅ Playwright importato correttamente\n")
except ImportError as e:
    print(f"   ❌ Errore import Playwright: {e}\n")
    print("   Prova: pip install playwright\n")
    sys.exit(1)

# Test 5: Firefox launch
print("5️⃣  Verifica lancio Firefox...")
try:
    with sync_playwright() as p:
        print("   • Launching Firefox (headless)...")
        browser = p.firefox.launch(headless=True)
        print("   ✅ Firefox lanciato correttamente")
        
        print("   • Creando contesto...")
        context = browser.new_context()
        page = context.new_page()
        print("   ✅ Contesto e pagina creati\n")
        
        context.close()
        browser.close()
except Exception as e:
    print(f"   ❌ Errore: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Accesso a pagina web
print("6️⃣  Verifica accesso a pagina web...")
try:
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("   • Navigando a Google...")
        page.goto("https://www.google.com", timeout=10000)
        print("   ✅ Accesso OK\n")
        
        context.close()
        browser.close()
except Exception as e:
    print(f"   ❌ Errore accesso pagina: {e}\n")
    import traceback
    traceback.print_exc()

print("=" * 70)
print("✅ DEBUG COMPLETATO")
print("=" * 70)
