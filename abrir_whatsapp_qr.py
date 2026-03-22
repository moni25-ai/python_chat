from selenium import webdriver
from selenium.webdriver.edge.service import Service
import time

# ─── RUTA DEL DRIVER ─────────────────────────
service = Service("C:/Python_Chat/msedgedriver.exe")

# ─── OPCIONES DEL NAVEGADOR ─────────────────────────
options = webdriver.EdgeOptions()

# Perfil exclusivo para Selenium
options.add_argument(r"user-data-dir=C:\Users\lusam\AppData\Local\Microsoft\Edge\User Data")
options.add_argument(r"profile-directory=selenium")  # cambia "Selenium" si tu perfil tiene otro nombre

# ─── ABRIR EDGE ─────────────────────────
driver = webdriver.Edge(service=service, options=options)

# ─── IR A WHATSAPP WEB ─────────────────────────
driver.get("https://web.whatsapp.com")

print("⌛ Si es la primera vez, escanea el QR en WhatsApp Web...")
print("💡 Una vez escaneado, la sesión quedará guardada en este perfil y no pedirá QR nuevamente.")

# Espera larga para que puedas escanear QR
time.sleep(120)


