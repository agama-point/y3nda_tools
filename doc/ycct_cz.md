# YCCT — y3nda code/cypher tools

`ycct.py` je příkazový nástroj projektu y3nda pro rychlé převody textu a
číselných hodnot, jednoduché šifry, práci s mnemotechnickými slovníky a
spouštění souborů s postupem (*flow*). Pracuje s Pythonem 3.6 a novějším.

> Jde o pomůcku pro učení, experimenty a převody dat. Šifry ROT13, Polybiův
> čtverec, leetspeak a XOR samy o sobě nepředstavují bezpečné moderní šifrování.

## Instalace a spuštění

Po instalaci závislostí podle `README.md` se příkaz spouští z kořene projektu:

```powershell
.\venv\Scripts\python.exe .\ycct.py -h
```

V aktivovaném virtuálním prostředí stačí:

```powershell
python .\ycct.py -h
```

V Linuxu nebo macOS:

```bash
python3 ycct.py -h
```

Bez parametrů vypíše nástroj krátkou radu k použití. Úplný seznam voleb zobrazí
`-h` nebo `--help`.

## Základní převody a šifry

Parametr `-c` (také `--cipher` nebo `--code`) vybere operaci. Text lze předat
jako poslední parametr; není-li uveden, načte se soubor `data.txt` z pracovního
adresáře nastaveného v `yt.json`.

### ROT13

ROT13 posune anglická písmena o 13 pozic. Opakované použití vrátí původní text.

```powershell
python .\ycct.py -c rot13 "AGAMA"
# NTNZN
```

### Polybiův čtverec

Písmena převede na dvojice souřadnic `11` až `55`; souřadnice oddělené
mezerami naopak dekóduje zpět na velká písmena.

```powershell
python .\ycct.py -c polybius agama
# 11 22 11 32 11

python .\ycct.py -c polybius "11 22 11 32 11"
# AGAMA
```

### Leetspeak

Převede text na variantu leetspeaku.

```powershell
python .\ycct.py -c leet "Hello y3nda"
```

### XOR

XOR používá hexadecimální klíč `XEY_HEX` ze souboru `.env` v pracovním
adresáři. Klíč musí být neprázdný a mít sudý počet hexadecimálních znaků.

```text
# project_test/.env
XEY_HEX=deadbeef
```

```powershell
python .\ycct.py -c xor "tajny text"
python .\ycct.py -c xor .\project_test\ciphertext.hex
```

Stejná operace se stejným klíčem slouží také k obrácení výsledku. Klíč ani
soubor `.env` neukládejte do veřejného repozitáře.

Existující soubor s příponou `.hex` se načte jako hexadecimální vstup (holý
název se hledá v pracovním adresáři z `yt.json`). Jeho obsah musí být neprázdný
a mít sudý počet hexadecimálních znaků. Neexistující `něco.hex` se nadále
zpracuje jako obyčejný text.

## Všechny vhodné převody

Volba `-a` zobrazí sadu převodů podle typu vstupu. Pro běžný text vypíše ROT13,
XOR, Base58, Bech32 a UTF-8 reprezentaci v hexadecimálním tvaru. Pro
hexadecimální vstup vypíše XOR, číslo a binární řetězec.

```powershell
python .\ycct.py -a "AGAMA"
python .\ycct.py -a deadbeef
```

Protože součástí výstupu je XOR, potřebují oba příklady platný `XEY_HEX` v
souboru `.env` pracovního adresáře.

## Mnemotechnické slovníky

Volba `-m` vyhledá slovo nebo index ve slovnících CIP, SLIP-0039 a BIP-0039.
Indexy jsou číslované od nuly. Při hledání slova se ukáže jeho index a binární
zápis, při hledání indexu odpovídající slovo a také hexadecimální, Bech32 a
kostková reprezentace indexu.

```powershell
python .\ycct.py -m abandon
python .\ycct.py -m 0
```

## Pracovní adresář a konfigurace

Výchozí konfigurace je `yt.json`. Položka `subdir` určuje pracovní adresář
(v aktuální konfiguraci `project_test`) a položka `log` zapíná zápis výstupu do
`log.txt` v tomto adresáři.

```powershell
python .\ycct.py --status
python .\ycct.py --config .\moje_konfigurace.json --status
```

Stavový výpis obsahuje konfiguraci a pracovní adresář, dále název a stručný
popis počítače, operační systém, verzi běžícího Pythonu, celkovou paměť a
celkovou i volnou kapacitu disku pracovního adresáře.

Volba `-d` zobrazí hexadecimální výpis souboru `data.txt` pracovního adresáře:

```powershell
python .\ycct.py -d
```

## Flow soubory

Volba `-r` spustí soubor s postupem. Bez názvu souboru se hledá `flow.txt` v
kořeni projektu nebo v pracovním adresáři; cestu lze předat přímo.

```powershell
python .\ycct.py -r
python .\ycct.py -r .\project_test\flow_cipher.txt
python .\runner.py .\project_test\flow_ycct.txt
```

Samostatný `runner.py` přijímá stejný název flow souboru a také `--dry-run`.
Podrobnosti o aktuálním `yt.json`, pracovním adresáři a pořadí hledání souborů
zobrazí `python .\runner.py -h`.

Aktuální ukázka `project_test/flow_ycct.txt` ověřuje verze, status, síť,
převody, mnemonic i hexdump pomocí `ycct.py`.

## Informace o prostředí

```powershell
# verze YCCT a použitých modulů
python .\ycct.py -V

# konfigurace, pracovní adresář a lokální systémové informace
python .\ycct.py --status

# lokální IPv4, ověření HTTPS přístupu a jeden ping na 8.8.8.8
python .\ycct.py --net
```

Síťová kontrola může selhat nebo být filtrována firewallem; netýká se to funkcí
pro místní převody a šifry.

## Verbózní výstup

`-v` (nebo `--verbose`) zapne diagnostické zprávy na standardním chybovém
výstupu, takže nemění vlastní výsledek převodu. Volbu lze opakovat; `-vv`
zobrazí další informace o zvolené operaci a konfiguraci.

```powershell
python .\ycct.py -v -c rot13 AGAMA
python .\ycct.py -vv --status
```

Pro výpis verzí používejte `-V`, `--ver` nebo `--version`; `-v` již verzi
nevypisuje.
