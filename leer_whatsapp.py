import shutil
import os
import re
import csv
import gspread
from google.oauth2.service_account import Credentials

# ─── CONFIGURACIÓN GENERAL ─────────────────────────
trabajos = [
    {"archivo": "C:/Python_Chat/semana_1.txt", "hoja": "Laprida", "cols": ["B","C","D"]},
    {"archivo": "C:/Python_Chat/semana_arenales1.txt", "hoja": "Arenales", "cols": ["B","C","D"]},
    {"archivo": "C:/Python_Chat/semana1_barra.txt", "hoja": "Laprida", "cols": ["E","F","G"]}
]

descargas = "C:/Users/lusam/Downloads"
carpeta_chat = "C:/Python_Chat"
fila_inicio = 34
mes_filtro = 2   # Febrero
dia_inicio = 1
dia_fin = 17

# ─── FUNCIONES ─────────────────────────
def normalizar_numero(texto):
    texto = texto.lower().replace("$", "").replace(" ", "").replace(",", "")
    if texto.endswith("k"):
        numero = texto[:-1].replace(".", "")
        return int(float(numero) * 1000)
    return int(texto.replace(".", ""))

def normalizar_fecha(fecha):
    fecha = fecha.strip()
    if "/" in fecha:
        partes = fecha.split("/")
    elif "-" in fecha:
        partes = fecha.split("-")
    else:
        return None
    if len(partes) != 2:
        return None
    try:
        dia = int(partes[0])
        mes = int(partes[1])
    except:
        return None
    return f"{dia:02d}-{mes:02d}"

# ─── EXPRESIONES REGULARES ─────────────────────────
regex_apertura_bloque = re.compile(
    r'^\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}\s*-\s*(.+?):\s*(\d{1,2}/\d{1,2})$'
)
regex_inicio = re.compile(r'^inicio\b', re.IGNORECASE)
regex_fact = re.compile(r'\b(facturacion|facturación|fac|fact|factu)\b', re.IGNORECASE)
regex_montos = re.compile(r'\$\s*\d[\d\.,]*k?|\b\d+(?:[\.,]\d+)?k\b', re.IGNORECASE)
regex_mp = re.compile(r'\b(m\.?p\.?)\b', re.IGNORECASE)
regex_efectivo = re.compile(r'\befectivo\b', re.IGNORECASE)

# ─── GOOGLE SHEETS ─────────────────────────
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credenciales = Credentials.from_service_account_file(
    "C:/Python_Chat/credenciales.json",
    scopes=scopes
)
cliente = gspread.authorize(credenciales)
spreadsheet = cliente.open("Beer and wheel tablero de control 2026")

# ─── PROCESAR CADA ARCHIVO ─────────────────────────
for trabajo in trabajos:
    archivo = trabajo["archivo"]
    nombre_hoja = trabajo["hoja"]
    cols = trabajo["cols"]

    # ─── MOVER ARCHIVO AUTOMÁTICAMENTE ─────────
    os.makedirs(carpeta_chat, exist_ok=True)
    if not os.path.exists(archivo):
        ruta_descarga = os.path.join(descargas, os.path.basename(archivo))
        if os.path.exists(ruta_descarga):
            shutil.move(ruta_descarga, archivo)
            print(f"✅ {os.path.basename(archivo)} movido automáticamente a {carpeta_chat}")
        else:
            print(f"❌ No se encontró el archivo {os.path.basename(archivo)} en Descargas")
            continue

    print(f"\n➡️ Procesando {archivo} → hoja {nombre_hoja} (columnas {cols})")

    # ─── LEER ARCHIVO ─────────────────────────
    with open(archivo, "r", encoding="utf-8") as f:
        lineas = [l.rstrip() for l in f]

    # ─── DETECTAR BLOQUES ─────────────────────────
    bloques = []
    bloque_actual = []
    bloque_activo = False
    fact_detectado = False
    fecha_actual = ""
    nombre_actual = ""

    for i, linea in enumerate(lineas):
        linea_limpia = linea.strip()
        m = regex_apertura_bloque.match(linea_limpia)
        if m:
            nombre_actual = m.group(1)
            fecha_actual = m.group(2)
            inicio_encontrado = False
            for j in range(1,5):
                if i + j >= len(lineas):
                    break
                linea_test = lineas[i+j].strip()
                if linea_test == "" or linea_test == "_":
                    continue
                if regex_inicio.match(linea_test):
                    inicio_encontrado = True
                    break
            if inicio_encontrado:
                bloque_actual = []
                bloque_activo = True
                fact_detectado = False
            else:
                bloque_activo = False
            continue
        if bloque_activo:
            bloque_actual.append(linea_limpia)
            if regex_fact.search(linea_limpia):
                fact_detectado = True
            if fact_detectado:
                bloques.append((fecha_actual, nombre_actual, bloque_actual))
                bloque_activo = False

    # ─── FILTRAR BLOQUES POR FEBRERO ─────────
    bloques_filtrados = []
    for fecha, nombre, bloque in bloques:
        nf = normalizar_fecha(fecha)
        if nf is None:
            continue
        dia, mes = map(int, nf.split("-"))
        if mes == mes_filtro and dia_inicio <= dia <= dia_fin:
            bloques_filtrados.append((fecha, nombre, bloque))

    bloques_filtrados.sort(key=lambda x: tuple(int(p) for p in normalizar_fecha(x[0]).split("-")))
    print("Bloques detectados (filtrados por rango):", len(bloques_filtrados))

    # ─── CALCULAR MP, EFECTIVO, FACTURACION ─────────
    filas = []
    bloques_sin_coincidencia = []
    for fecha, nombre, bloque in bloques_filtrados:
        mp_valor = None
        fact_valor = None
        efectivo_existe = any(regex_efectivo.search(l) for l in bloque)
        for i, linea in enumerate(bloque):
            m_monto = regex_montos.search(linea)
            if m_monto:
                monto_normalizado = normalizar_numero(m_monto.group())
                bloque[i] = regex_montos.sub(str(monto_normalizado), linea)
                if regex_mp.search(linea):
                    mp_valor = monto_normalizado
                if regex_fact.search(linea):
                    fact_valor = monto_normalizado
        if mp_valor is not None and fact_valor is not None:
            efectivo_final = fact_valor - mp_valor
            if not efectivo_existe:
                posicion = len(bloque)
                for i, linea in enumerate(bloque):
                    if regex_fact.search(linea):
                        posicion = i
                        break
                bloque.insert(posicion, f"Efectivo {efectivo_final}")
        else:
            efectivo_final = None
        filas.append([fecha, mp_valor, efectivo_final, fact_valor])

        # mostrar bloque
        print(f"\n──────── BLOQUE {nombre} ────────")
        print(f"Fecha: {fecha}")
        for linea in bloque:
            print(linea)
        print(f"→ MP: {mp_valor}, Efectivo: {efectivo_final}, Facturación: {fact_valor}")

    # ─── BACKUP CSV ─────────────────────────
    ruta_csv = f"c:/python_chat/backup_{os.path.basename(archivo).split('.')[0]}.csv"
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["fecha", "mp", "efectivo", "facturacion"])
        for fila in filas:
            escritor.writerow(fila)
    print(f"✅ Backup guardado en {ruta_csv}")

    # ─── ACTUALIZAR GOOGLE SHEETS ─────────
    hoja = spreadsheet.worksheet(nombre_hoja)
    fechas_hoja_raw = hoja.col_values(1)[fila_inicio-1:]
    fechas_hoja_norm = [normalizar_fecha(f.strip()) for f in fechas_hoja_raw if f.strip()]

    filas_dict = {normalizar_fecha(f[0]): f for f in filas}

    datos_actualizar = []
    for f in fechas_hoja_raw:
        nf = normalizar_fecha(f.strip())
        if nf in filas_dict:
            fila = filas_dict[nf]
            # asignar según columnas de este archivo
            if cols == ["E","F","G"]:
                efectivo_valor = fila[2] if fila[2] else ""
                mp_valor = fila[1] if fila[1] else ""
                fact_valor = fila[3] if fila[3] else ""
            else:
                mp_valor = fila[1] if fila[1] else ""
                efectivo_valor = fila[2] if fila[2] else ""
                fact_valor = fila[3] if fila[3] else ""
        else:
            mp_valor = ""
            efectivo_valor = ""
            fact_valor = ""
            bloques_sin_coincidencia.append(nf)
        datos_actualizar.append([efectivo_valor, mp_valor, fact_valor])

    # construir rango según columnas y fila_inicio
    rango = f"{cols[0]}{fila_inicio}:{cols[2]}{fila_inicio + len(datos_actualizar) - 1}"
    hoja.update(rango, datos_actualizar)
    print(f"✅ Datos cargados correctamente en hoja {nombre_hoja}")

    if bloques_sin_coincidencia:
        print("\n⚠️ Bloques sin coincidencia en hoja:")
        for b in bloques_sin_coincidencia:
            print(f"\033[91m{b}\033[0m")
    else:
        print("\n✅ Todos los bloques encontraron coincidencia con la hoja")