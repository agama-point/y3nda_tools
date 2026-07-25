# Terminálové sekvence: VT100 a ANSI

## Základ: VT100

VT100 byl hardwarový textový terminál firmy Digital Equipment Corporation
(DEC), uvedený v roce 1978. Nezobrazoval grafické okno jako dnešní aplikace:
komunikoval se vzdáleným počítačem po sériové lince a na obrazovce vykresloval
znaky. Vedle běžného textu rozuměl také řídicím sekvencím, které umožnily
pohyb kurzoru, smazání části obrazovky nebo změnu způsobu zobrazení textu.

Tento způsob ovládání se stal velmi vlivný. Moderní terminály už obvykle nejsou
fyzické VT100, ale jejich emulátory zachovávají kompatibilní způsob práce.
Proto se často mluví o „VT100-style“ nebo „ANSI“ terminálu.

## Řídicí sekvence

Řídicí sekvence typicky začínají znakem Escape (`ESC`, v Pythonu `"\033"`)
a následným `[`; tato kombinace se označuje jako CSI (*Control Sequence
Introducer*). Například:

| Sekvence | Význam |
| --- | --- |
| `\r` | Vrátí kurzor na začátek současného řádku. |
| `\033[2J` | Smaže obrazovku. |
| `\033[H` | Přesune kurzor do levého horního rohu. |
| `\033[K` | Smaže text od kurzoru do konce řádku. |
| `\033[31m` | Zapne červenou barvu textu. |
| `\033[0m` | Vrátí formátování na výchozí stav. |

Například tento Python kód vypíše červený text a pak formátování ukončí:

```python
print("\033[31mError\033[0m")
```

Bez závěrečného `\033[0m` by další text v terminálu mohl zůstat červený.

## Barvy

Původní VT100 barevný nebyl. Barevné sekvence jsou běžnou součástí dnešního
ANSI/xterm ekosystému. Základní paleta má osm normálních a osm jasných barev:

```text
30 black       31 red       32 green     33 yellow
34 blue        35 magenta   36 cyan      37 white
90 bright black ...                         97 bright white
```

Barva se nastaví sekvencí `\033[<kód>m`. Příklady:

```python
print("\033[32mSuccess\033[0m")           # green
print("\033[93mWarning\033[0m")           # bright yellow
print("\033[95mViolet message\033[0m")    # bright magenta
```

Mnohé moderní emulátory navíc podporují 256 barev a RGB (*true color*),
například `\033[38;5;208m` nebo `\033[38;2;255;128;0m`. To už není vhodné
považovat za jistotu v každém terminálu; pro malé CLI nástroje je 16 barev
nejpřenosnější volba.

## Moderní použití

Tyto sekvence podporují například Windows Terminal, současný PowerShell,
terminál ve VS Code, xterm, GNOME Terminal, macOS Terminal nebo iTerm2. Používají
se zejména pro:

- barevné logy a úrovně `INFO`, `WARNING`, `ERROR`;
- průběhové ukazatele, které přepisují jeden řádek;
- jednoduchá textová rozhraní, tabulky a zvýraznění výsledků;
- nástroje pro vývojáře, instalátory a příkazové aplikace.

Jednoduchý progress bar lze vytvořit návratem na začátek řádku a smazáním jeho
zbytku:

```python
import time

for percent in range(101):
    print(f"\rWorking: {percent:3d} %\033[K", end="", flush=True)
    time.sleep(0.03)
print()
```

Výstup přesměrovaný do souboru nebo do prostředí, které není skutečným
terminálem, nemusí řídicí sekvence interpretovat. Pro takové prostředí je lepší
barvy a dynamické překreslování vypnout.

## Modul `lib/wrapp_terminal.py`

Lokální modul [`lib/wrapp_terminal.py`](lib/wrapp_terminal.py) poskytuje malou, nezávislou
vrstvu nad těmito sekvencemi:

- `ansi_enabled()` zjistí, zda je výstup skutečný ANSI terminál;
- `colors_enabled()` navíc respektuje proměnnou prostředí `NO_COLOR`;
- `color_text(text, color)` vrátí obarvený text, pouze pokud je podporován
  terminálový výstup;
- `Terminal().print(color, ...)` vypíše barevný řádek;
- krátké funkce `r()`, `g()`, `b()`, `y()`, `w()`, `m()`, `c()` a `v()` jsou
  pohodlné aliasy pro nejčastější barvy;
- `style_text()` a `Terminal().style()` umí kromě barvy také tučné, tlumené
  nebo podtržené písmo a barvu pozadí;
- `strip_ansi()` odstraní řídicí sekvence před zápisem do čistého logu;
- `terminal_width()` vrátí dostupnou šířku terminálu;
- `progress_bar()` vytvoří textový progress bar a `spinner()` vybere další
  znak spinneru;
- `clear_line()`, `cursor_up()`, `cursor_down()`, `hide_cursor()` a
  `show_cursor()` poskytují základní řízení obrazovky;
- `status_line(text)` přepíše aktuální řádek pomocí `\r` a `\033[K`;
- `StatusLine` spravuje trvalý stavový řádek a umí vložit běžný log nad něj.

Pokud výstup není terminál (například je přesměrován do souboru), barvy se
nevypisují a `status_line()` přejde na obyčejný řádek. V logu tedy nezůstanou
neinterpretované řídicí sekvence.

Příklad použití modulu:

```python
from lib.wrapp_terminal import color_text, status_line

print(color_text("Starting download", "cyan"))
status_line(color_text("[##########----------] 50 %", "green"))
print()  # Finish the status line and move to a new line.
```

### Formátování a logování během průběhu

```python
from lib.wrapp_terminal import StatusLine, style_text

print(style_text("Warning", fg="bright_yellow", bold=True))

status = StatusLine()
status.update("[##########----------] 50 %")
status.log("downloaded file_01.zip")  # log is printed above the status
status.finish("Done")
```

`StatusLine.finish()` vždy ukončí dynamický řádek novým řádkem. Pokud program
skrývá kurzor, je vhodné ho vrátit i při chybě:

```python
from lib.wrapp_terminal import hide_cursor, show_cursor

hide_cursor()
try:
    # Long-running terminal work.
    pass
finally:
    show_cursor()
```
