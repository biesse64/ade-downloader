# AdE downloader

Scarica in blocco dal portale **Fatture e Corrispettivi** dell'Agenzia delle Entrate le fatture
**passive** (ricevute), **attive** (emesse) e **transfrontaliere emesse** di un periodo, invece di
aprirle una a una. Si usa ogni mese per mandare le fatture al commercialista.

## Uso

```
./avvia.sh                      # oppure: python3 download_fatture_completo.py
```

1. Scegli cosa scaricare (passive, attive, entrambe) e le date (GG/MM/AAAA).
2. Si apre Firefox sul portale: fai il **login SPID** a mano (una sola volta per sessione).
3. Scegli **Me stesso** oppure **Incaricato** e indica la P.IVA del soggetto per cui operi.
4. Il resto è automatico: ricerca per date, apertura di ogni fattura, download dei file.

I file finiscono in `fatture_ade/<soggetto>/<anno>/<mese>/passive|attive|transfrontaliere_emesse/`.
Un file già scaricato viene saltato, quindi si può rilanciare sullo stesso periodo.
Timeout ampi e fino a 3 tentativi per file (versione 2).

Prima installazione:
```
python3 -m pip install playwright
python3 -m playwright install firefox
```
`avvia.sh` usa il Python 3.13 di python.org (`/Library/Frameworks/Python.framework/...`).

## Altri file

- `strumenti/estrai_fatture.py`: estrae emesse e ricevute di un periodo dall'archivio di Danea
  Easyfatt (Firebird) in Excel e zip.
- `strumenti/estrai_fatture_xml.py`: estrae le fatture di un periodo da una cartella di file XML
  in `estrazioni_mensili/`.
- `vecchie_versioni/`: versioni precedenti e script di diagnosi, tenuti per riferimento. Non servono
  per l'uso.

## Cosa NON va nel repository

Le fatture scaricate (`fatture_ade/`), le estrazioni, le pagine HTML salvate dal portale e le
schermate: contengono dati personali e fiscali. Lo impedisce `.gitignore`. Le credenziali SPID non
sono mai salvate: il login si fa a mano nel browser.
