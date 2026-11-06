from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    page = browser.new_page()
    
    page.goto("https://ivaservizi.agenziaentrate.gov.it/cons/cons-web/?v=1729602560401#/fatture/ricevute")
    
    print("1️⃣  Completa il login SPID, poi premi INVIO")
    input()
    with open("1_dopo_spid_radiobox.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✅ Salvato: 1_dopo_spid_radiobox.html\n")
    
    print("2️⃣  Clicca il radiobox per confermare identità, poi premi INVIO")
    input()
    with open("2_pagina_conferma.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✅ Salvato: 2_pagina_conferma.html\n")
    
    print("3️⃣  Seleziona 'Fatture ed altri dati IVA', poi premi INVIO")
    input()
    with open("3_fatture_altri_dati_iva.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✅ Salvato: 3_fatture_altri_dati_iva.html\n")
    
    print("4️⃣  Seleziona 'Fatture ricevute', poi premi INVIO")
    input()
    with open("4_fatture_ricevute.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✅ Salvato: 4_fatture_ricevute.html\n")
    
    print("5️⃣  Riempi le date e clicca Cerca, poi premi INVIO")
    input()
    with open("5_risultati_lista.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("✅ Salvato: 5_risultati_lista.html\n")
    
    print("✅ Tutti gli HTML salvati! Caricali ora")
    
    browser.close()