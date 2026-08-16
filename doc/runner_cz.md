# Runner — spouštění projektových flow

`runner.py` spouští ověřené příkazy Pythonu uložené v textovém *flow* souboru.
Povoluje pouze skripty `.py` uvnitř projektu a flow před spuštěním kompletně
ověří.

```powershell
python .\runner.py -h
python .\runner.py .\project_test\flow_ycct.txt
python .\runner.py .\project_test\flow_yiit.txt
python .\runner.py --dry-run .\project_test\flow_yiit.txt
```

Pracovní adresář určuje `yt.json` položkou `subdir` (v aktuální konfiguraci
`project_test`). Při předání holého názvu flow hledá runner soubor nejdřív v
kořeni projektu a potom v tomto pracovním adresáři. Nápověda `-h` vypíše
aktuální cestu konfigurace, pracovní adresář i stav logování.

Bez argumentu runner hledá `flow_example.txt`; pokud soubor neexistuje, skončí
s vysvětlující chybou. Volba `--dry-run` příkazy pouze ověří a nevykoná je.
