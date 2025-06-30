import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

clave_qr = os.getenv("CLAVE_QR")

if not clave_qr:
    raise ValueError("No se encontró 'CLAVE_QR' en el archivo .env. Asegúrate de que esté configurada.")

fernet = Fernet(clave_qr.encode())

def desencriptar_qr(qr_string):
    try:
        contenido = fernet.decrypt(qr_string.encode()).decode()
        if contenido.startswith("empleado/"):
            return int(contenido.split("/")[1])
        return None
    except Exception as e:
        return None