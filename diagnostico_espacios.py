import gspread
from google.oauth2.service_account import Credentials

# --- Conexión ---
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
cred = Credentials.from_service_account_file(
    "C:/Python_Chat/credenciales.json",
    scopes=scopes
)
client = gspread.authorize(cred)
ss = client.open("Beer and wheel tablero de control 2026")

def es_fecha_valida(valor):
    import re
    patron = re.compile(r'^\d{2}-\d{2}$')
    return bool(patron.match(valor))

def revisar_hoja(nombre):
    print(f"\n🔎 Revisando hoja: {nombre}")
    print("----------------------------------------")

    hoja = ss.worksheet(nombre)
    fechas = hoja.col_values(1)

    for i, valor in enumerate(fechas, start=1):
        original = valor
        limpio = valor.strip()

        # Detecta espacios antes o después
        if original != limpio:
            print(f"Fila {i}: '{original}' — ⚠️ Tiene espacios al inicio o final")

        # Detecta espacios en medio (01 -03 ó 01- 03)
        if " " in limpio:
            print(f"Fila {i}: '{valor}' — ⚠️ Tiene espacios dentro de la fecha")

        # Detecta fechas mal formateadas
        if limpio and not es_fecha_valida(limpio) and not limpio.lower().startswith("total"):
            print(f"Fila {i}: '{valor}' — ❌ Formato inválido")

    print("✔️ Revisión completada.")

# Revisar ambas
revisar_hoja("Laprida")
revisar_hoja("Arenales")