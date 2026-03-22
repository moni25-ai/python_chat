from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

# ─── RUTA DEL DRIVER ─────────────────────────
service = Service("C:/Python_Chat/msedgedriver.exe")

# ─── OPCIONES DEL NAVEGADOR ─────────────────────────
options = webdriver.EdgeOptions()
options.add_argument(r"user-data-dir=C:\Users\lusam\AppData\Local\Microsoft\Edge\User Data")
options.add_argument(r"profile-directory=selenium")  # perfil activo

# ─── ABRIR EDGE ─────────────────────────
driver = webdriver.Edge(service=service, options=options)

# ─── IR A WHATSAPP WEB ─────────────────────────
driver.get("https://web.whatsapp.com")
print("⌛ Esperando a que cargue WhatsApp Web...")
time.sleep(50)  # espera a que cargue la sesión y los chats completamente

# ─── CONFIGURACIONES ─────────────────────────
chat_name = "Karen (Tú)"  # nombre del chat
emoji = "☑️"  # emoji a reaccionar
mes_filtro = "3"  # filtramos solo mensajes de marzo

try:
    # ─── BUSCAR EL CHAT POR NOMBRE ─────────────────────────
    search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
    search_box.click()
    search_box.send_keys(chat_name)
    time.sleep(3)
    search_box.send_keys("\n")  # presiona ENTER para abrir el chat
    time.sleep(3)

    # ─── BUSCAR EL MENSAJE ─────────────────────────
    mensaje_encontrado = False
    # recorre cada burbuja de mensaje entrante
    mensajes = driver.find_elements(By.XPATH, '//div[contains(@class,"message-in")]')
    for msg in mensajes:
        # unimos todo el texto dentro de la burbuja
        texto_completo = " ".join([span.text for span in msg.find_elements(By.XPATH, './/span')])
        texto_completo = texto_completo.replace("\n", " ").strip()
        
        # verificamos que el mensaje sea de marzo
        if f"/{mes_filtro}" in texto_completo:
            # buscamos "2/3" y "Inicio" en cualquier parte del mensaje
            if "2/3" in texto_completo and "Inicio" in texto_completo:
                msg.click()  # seleccionar el mensaje
                time.sleep(1)
                msg.send_keys(emoji)
                mensaje_encontrado = True
                print("✅ Emoji agregado al mensaje.")
                break

    if not mensaje_encontrado:
        print(f"⚠️ No se encontró ningún mensaje de marzo que coincida con '2/3' y 'Inicio'.")

except NoSuchElementException:
    print(f"⚠️ No se encontró el chat '{chat_name}'. Revisa que esté correcto y que el chat exista.")

time.sleep(5)
driver.quit()