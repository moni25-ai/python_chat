import shutil
import os
import re
import gspread
from google.oauth2.service_account import Credentials
import zipfile

# ─── CONFIGURACIÓN GENERAL ─────────────────────────
carpeta_chat = "."   # Ruta base del repositorio

palabras_clave_hojas = {
    "númerossupervisión": {"hoja": "Laprida", "cols": ["B","C","D"]},
    "arenales": {"hoja": "Arenales", "cols": ["B","C","D"]},
    "barra": {"hoja": "Laprida", "cols": ["E","F","G"]}
}

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

# ─── GOOGLE SHEETS ─────────────────────────
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# credenciales.json debe estar en el repositorio raíz
credenciales = Credentials.from_service_account_file(
    "./credenciales.json",
    scopes=scopes
)

cliente = gspread.authorize(credenciales)
spreadsheet = cliente.open("Beer and wheel tablero de control 2026")

# ─── PROCESAR ZIPS ─────────────────────────
carpeta_zip = "./archivos_zip"
procesados = os.path.join(carpeta_zip, "procesados")
os.makedirs(procesados, exist_ok=True)

for archivo_zip in os.listdir(carpeta_zip):
    if not archivo_zip.lower().endswith(".zip"):
        continue
    ruta_zip = os.path.join(carpeta_zip, archivo_zip)
    print(f"📦 Procesando ZIP: {archivo_zip}")

    with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
        zip_ref.extractall(carpeta_chat)
    print(f"✅ Archivos extraídos a {carpeta_chat}")

    shutil.move(ruta_zip, os.path.join(procesados, archivo_zip))
    print(f"➡️ ZIP movido a procesados")

# ─── DETECTAR TXT ─────────────────────────
txts = [f for f in os.listdir(carpeta_chat) if f.lower().endswith(".txt")]

for archivo_txt in txts:
    ruta_txt = os.path.join(carpeta_chat, archivo_txt)

    # Buscar hoja por palabra clave
    trabajo = None
    nombre_lower = archivo_txt.lower()
    for clave, info in palabras_clave_hojas.items():
        if clave.lower() in nombre_lower:
            trabajo = {"archivo": ruta_txt, "hoja": info["hoja"], "cols": info["cols"]}
            break

    if not trabajo:
        print(f"❌ No se pudo clasificar {archivo_txt}")
        os.remove(ruta_txt)
        continue

    archivo = trabajo["archivo"]
    nombre_hoja = trabajo["hoja"]
    cols = trabajo["cols"]

    print(f"\n➡️ Procesando {archivo_txt} → hoja {nombre_hoja}")

    # Leer TXT
    with open(archivo, "r", encoding="utf-8") as f:
        lineas = [l.rstrip() for l in f]

    # Regex
    regex_apertura_bloque = re.compile(
        r'^\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}\s*-\s*(.+?):\s*(\d{1,2}/\d{1,2})$'
    )
    regex_inicio = re.compile(r'^inicio\b', re.IGNORECASE)
    regex_fact = re.compile(r'\b(facturacion|facturación|fac|fact|factu)\b', re.IGNORECASE)
    regex_montos = re.compile(r'\$\s*\d[\d\.,]*k?|\b\d+(?:[\.,]\d+)?k\b', re.IGNORECASE)
    regex_mp = re.compile(r'\b(m\.?p\.?)\b', re.IGNORECASE)

    # Detectar bloques
    bloques = []
    bloque_actual = []
    bloque_activo = False
    fact_detectado = False

    for i, linea in enumerate(lineas):
        m = regex_apertura_bloque.match(linea)
        if m:
            nombre = m.group(1)
            fecha = m.group(2)
            inicio_encontrado = False
            for j in range(1, 5):
                if i + j >= len(lineas):
                    break
                t = lineas[i + j].strip()
                if t == "" or t == "_":
                    continue
                if regex_inicio.match(t):
                    inicio_encontrado = True
                    break
            if inicio_encontrado:
                bloque_actual = []
                bloque_activo = True
                fact_detectado = False
                fecha_actual = fecha
                nombre_actual = nombre
            else:
                bloque_activo = False
            continue

        if bloque_activo:
            bloque_actual.append(linea.strip())
            if regex_fact.search(linea):
                fact_detectado = True
            if fact_detectado:
                bloques.append((fecha_actual, nombre_actual, bloque_actual))
                bloque_activo = False

    # ────────────────────────────────────────────────
    #   📌 DETECTAR ÚLTIMA FILA CON DATOS
    # ────────────────────────────────────────────────
    hoja = spreadsheet.worksheet(nombre_hoja)

    col_mp = hoja.col_values(ord(cols[1]) - 64)
    col_ef = hoja.col_values(ord(cols[0]) - 64)
    col_fac = hoja.col_values(ord(cols[2]) - 64)

    ultima_fila = 0
    for i in range(len(col_mp)):
        if col_mp[i] or col_ef[i] or col_fac[i]:
            ultima_fila = i + 1

    print(f"📌 Última fila con datos: {ultima_fila}")

    # Fechas en col A
    fechas_hoja = hoja.col_values(1)
    fechas_pendientes = fechas_hoja[ultima_fila:]
    fechas_normalizadas = [normalizar_fecha(f) for f in fechas_pendientes]
    fechas_permitidas = set(fechas_normalizadas)

    filas_resultado = {}

    for fecha, nombre, bloque in bloques:
        nf = normalizar_fecha(fecha)
        print(f"\n🟦 Bloque detectado ({nf}) — {nombre}")
        print("\n".join(bloque))

        if nf not in fechas_permitidas:
            print("❌ Fecha no coincide con hoja (ignorada)")
            continue

        mp_val = None
        fact_val = None

        for linea in bloque:
            m_monto = regex_montos.search(linea)
            if m_monto:
                monto = normalizar_numero(m_monto.group())
                if regex_mp.search(linea):
                    mp_val = monto
                if regex_fact.search(linea):
                    fact_val = monto

        efectivo_val = None
        if mp_val is not None and fact_val is not None:
            efectivo_val = fact_val - mp_val

        print(f"💰 MP: {mp_val}  | FACT: {fact_val}  | EFECTIVO: {efectivo_val}")

        filas_resultado[nf] = [
            efectivo_val or "",
            mp_val or "",
            fact_val or ""
        ]

    # ─── Cargar datos ───────────────────────────────
    datos_actualizar = []
    for f in fechas_normalizadas:
        if f in filas_resultado:
            datos_actualizar.append(filas_resultado[f])
        else:
            print(f"🔴 No llegó información para {f}")
            datos_actualizar.append(["", "", ""])

    inicio = ultima_fila + 1
    fin = inicio + len(datos_actualizar) - 1
    rango = f"{cols[0]}{inicio}:{cols[2]}{fin}"

    hoja.update(rango, datos_actualizar)
    print(f"✅ Datos cargados en hoja {nombre_hoja}")

    # Borrar TXT procesado
    os.remove(archivo)
    print(f"🗑 TXT eliminado: {archivo_txt}")