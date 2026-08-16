# Yiit — y3nda image/infilt tools

`yiit.py` je příkazový nástroj projektu y3nda pro vytváření a úpravy obrázků
a pro jednoduché vložení bitů do obrazového kanálu. Používá třídu `Image21`,
Pillow a NumPy. Vyžaduje Python 3.10 nebo novější; pro nástroje kompatibilní
s Pythonem 3.6 slouží `ycct.py`.

> Vkládání dat pracuje s paritou hodnot RGB kanálu. Je vhodné pro experimenty
> a demonstrace, nikoli jako bezpečné ukrytí či šifrování citlivých dat.

## Instalace a spuštění

Z kořene projektu nainstalujte závislosti a zobrazte nápovědu:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe .\yiit.py -h
```

V aktivovaném virtuálním prostředí stačí:

```powershell
python .\yiit.py -h
```

V Linuxu nebo macOS použijte `python3 yiit.py`. Kompletní dostupné příkazy
ukáže `-h`; ukázky přímo v terminálu vypíše `-e` nebo `--examples`.

## Pracovní adresář

Výchozí konfigurace `yt.json` určuje pracovní adresář položkou `subdir`.
V aktuální konfiguraci je to `project_test`. Každý holý název souboru se proto
čte nebo vytvoří v tomto adresáři:

```powershell
python .\yiit.py create image.png 100x100
# vytvoří .\project_test\image.png
```

Cesta, která obsahuje adresář, je explicitní a zůstává relativní k aktuálnímu
adresáři (nebo může být absolutní):

```powershell
python .\yiit.py create .\jinam\image.png 100x100
# vytvoří .\jinam\image.png
```

Příkazy `create` a `copy` případně vytvoří chybějící rodičovské adresáře pro
výstupní soubor.

Stejné pravidlo platí pro vstupní i výstupní soubory příkazů `copy`, `embed`,
`extract`, `info`, `noise` a `border`. Jinou konfiguraci lze zvolit volbou
`--config`:

```powershell
python .\yiit.py --config .\moje_konfigurace.json create image.png 100x100
```

## Vytvoření a kopie obrázku

### `create`

Vytvoří nový bílý RGB obrázek. Rozměr se zapisuje jako `ŠÍŘKAxVÝŠKA`.

```powershell
python .\yiit.py create carrier.png 800x600
```

Původní zkratka `crea` nadále funguje:

```powershell
python .\yiit.py crea carrier.png 800x600
```

### `copy`

Zkopíruje obrázek do nového souboru. Volba `--zoom` zvětší každý zdrojový
pixel celočíselným faktorem.

```powershell
python .\yiit.py copy carrier.png carrier-copy.png
python .\yiit.py copy carrier.png carrier-2x.png --zoom 2
```

## Úpravy obrázku

Následující příkazy **přepisují zadaný obrazový soubor**. Před použitím si
proto vytvořte kopii.

### `noise`

Upraví každý pixel vybraného RGB kanálu náhodnou hodnotou v rozsahu
`-RANGE` až `+RANGE`. Výchozí kanál je `R` a výchozí rozsah `10`.

```powershell
python .\yiit.py noise carrier.png --channel G --range 5
```

Kanály lze zapisovat malými i velkými písmeny: `R`, `G`, `B`. Starší názvy
`-f` a `--fill` jsou zachované jako alias pro `--range`.

### `border`

Nakreslí okraj o zadané šířce a RGB barvě.

```powershell
python .\yiit.py border carrier.png --thickness 3 --color 255 128 0
```

Zkratka `bord` je stále podporovaná.

## Vložení a vytažení dat

`embed` nastaví paritu hodnot pixelů tak, aby nesla jednotlivé bity vstupních
dat. `extract` stejnou paritu přečte a vypíše výsledek jako hexadecimální
text. Oba příkazy pracují v jednom kanálu a od zadané souřadnice.

### Vložení (`embed`)

Připravte textový soubor obsahující pouze hexadecimální znaky, například
`payload.hex` s obsahem `0F`.

```powershell
python .\yiit.py embed carrier.png payload.hex --x 0 --y 0 --channel R
```

Příkaz přepíše `carrier.png`. Pokud je vstupních bitů více než dostupných
pixelů od zvoleného místa, Image21 data nehlásí jako chybu a přebytek se
neuloží. Pro spolehlivý výsledek proto používejte dostatečně velký obrázek.

### Vložení textu

Místo souboru lze předat přímo text v uvozovkách. Yiit jej zakóduje jako UTF-8,
takže podporuje i české znaky:

```powershell
python .\yiit.py embed carrier.png "pokusný text do dat" --x 0 --y 0 --channel R
```

Pokud druhý argument odkazuje na existující soubor, Yiit jej automaticky čte
jako hexadecimální vstup. Neexistující cesta se vyhodnotí jako text. Volbou
`--text` lze text vynutit i v případě, že stejnojmenný soubor existuje;
`--hex-file` naopak vyžaduje existující hexadecimální soubor.

### Vytažení (`extract`)

Z téhož obrázku načtete osm bitů takto:

```powershell
python .\yiit.py extract carrier.png --x 0 --y 0 --length 8 --channel R
# 0F
```

`--length` je počet bitů, nikoli počet hexadecimálních znaků. Výchozí délka
je 32 bitů. Původní názvy `ibin` a `pbin` fungují jako aliasy pro `embed` a
`extract`; zachované jsou také krátké volby `-x`, `-y` a `-l`.

## Informace o obrázku

`info` vypíše velikost souboru, rozlišení, barevný režim a kontrolní součty
MD5 a SHA-256.

```powershell
python .\yiit.py info carrier.png
```

## Verze a verbózní režim

Výpis verzí Yiit a používaných knihoven:

```powershell
python .\yiit.py -V
# stejné: --ver, --version nebo lib
```

`-v` znamená verbose, nikoli version. Diagnostické zprávy se vypisují na
standardní chybový výstup, a tak nemění například hexadecimální výsledek
`extract`. Volbu lze opakovat pro více detailů.

```powershell
python .\yiit.py -v info carrier.png
python .\yiit.py -vv extract carrier.png --length 8
```

U `extract` lze `-v` napsat i za pod-příkaz. K hexadecimálnímu výsledku se
na standardní chybový výstup doplní interpretace jako UTF-8 text. Pokud je
načtena delší oblast než uložený text, koncové nulové bajty se v tomto
diagnostickém výpisu vynechají.

```powershell
python .\yiit.py extract carrier.png -v --length 128 --channel R
```

## Přehled příkazů

| Příkaz | Účel | Přepisuje vstup |
|---|---|---|
| `create IMAGE WIDTHxHEIGHT` | vytvoří nový bílý RGB obrázek | ne |
| `copy SOURCE DESTINATION` | zkopíruje nebo zvětší obrázek | ne |
| `noise IMAGE` | přidá náhodnou změnu do kanálu | ano |
| `border IMAGE` | nakreslí barevný okraj | ano |
| `embed IMAGE HEX_FILE_OR_TEXT` | vloží hex data ze souboru nebo UTF-8 text | ano |
| `extract IMAGE` | načte bity a vypíše hex | ne |
| `info IMAGE` | zobrazí metadata a kontrolní součty | ne |
