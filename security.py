import json, os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_FERNET_KEY_STR = os.getenv("FERNET_KEY")

if not _FERNET_KEY_STR:
    raise ValueError("No se encontró 'FERNET_KEY' en el archivo .env. Por favor, generela y agreguela.")

_FERNET_KEY_BYTES = _FERNET_KEY_STR.encode('utf-8')

def obtener_fernet():
    return Fernet(_FERNET_KEY_BYTES)

def cifrar_bytes(datos_bytes):
    f = obtener_fernet()
    return f.encrypt(datos_bytes)

def descifrar_bytes(datos_cifrados_bytes):
    f = obtener_fernet()
    return f.decrypt(datos_cifrados_bytes)

def guardar_token_cifrado(token_data):
    f = obtener_fernet()
    datos_json_bytes = json.dumps(token_data).encode('utf-8')
    datos_cifrados = f.encrypt(datos_json_bytes)
    with open('tokens.json.enc', 'wb') as f_out:
        f_out.write(datos_cifrados)

def cargar_token_cifrado():
    try:
        with open('tokens.json.enc', 'rb') as f_in:
            datos_cifrados = f_in.read()
        f = obtener_fernet()
        datos_descifrados_bytes = f.decrypt(datos_cifrados)
        return json.loads(datos_descifrados_bytes.decode('utf-8'))
    except Exception as e:
        return None

def cifrar_config_archivo(origen_path, destino_path):
    f = obtener_fernet()
    with open(origen_path, 'r', encoding='utf-8') as f_in:
        datos_json = json.load(f_in)
    datos_json_bytes = json.dumps(datos_json).encode('utf-8')
    datos_cifrados = f.encrypt(datos_json_bytes)
    with open(destino_path, 'wb') as f_out:
        f_out.write(datos_cifrados)

def descifrar_config_archivo(archivo_cifrado_path):
    try:
        with open(archivo_cifrado_path, 'rb') as f_in:
            datos_cifrados = f_in.read()
        f = obtener_fernet()
        datos_descifrados_bytes = f.decrypt(datos_cifrados)
        return json.loads(datos_descifrados_bytes.decode('utf-8'))
    except Exception as e:
        return None