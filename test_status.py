from lib.wrapp_terminal import status_line

current_status = "Čekám..."

def log(*values):
    print("\r\033[K", end="")  # skryje aktuální status
    print(*values)             # běžná zpráva nad ním
    status_line(current_status)  # status se znovu vykreslí dole

current_status = "Zpracovávám 1/3"
status_line(current_status)

log("Soubor a.txt hotov.")
current_status = "Zpracovávám 2/3"
status_line(current_status)
