import gspread
from google.oauth2.service_account import Credentials
import re

# Configuración Google Sheets
cred = Credentials.from_service_account_file(
    "C:/Python_Chat/credenciales.json",
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(cred)
ss = client.open("Beer and wheel tablero de control 2026")

# Hojas a revisar
hojas = ["Laprida", "Arenales"]

regex_fecha = re.compile(r"^\d{2}-\d{2}$")

for hoja_nombre in hojas:
    hoja = ss.worksheet(hoja_nombre)
    fechas = hoja.col_values(1)

    print(f"\n🔎 Revisando hoja: {hoja_nombre}")
    print("-" * 40)

    duplicadas = set()
    vistas = set()
    errores = []

    for i, valor in enumerate(fechas, start=1):
        v = valor.strip()

        # Saltar casilleros vacíos
        if v == "":
            continue

        # Revisar formato
        if not regex_fecha.match(v):
            errores.append((i, v, "❌ Formato inválido"))
            continue

        # Revisar duplicados
        if v in vistas:
            duplicadas.add(v)
        else:
            vistas.add(v)

    # Resultado
    if errores:
        print("❗ Errores encontrados:")
        for fila, valor, msg in errores:
            print(f"Fila {fila}: '{valor}' — {msg}")
    else:
        print("✅ No hay errores de formato en las fechas.")

    if duplicadas:
        print("\n❗ Fechas duplicadas:")
        for d in duplicadas:
            print(f"- {d}")
    else:
        print("✅ No hay fechas duplicadas.")