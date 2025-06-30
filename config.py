import json, os
from pathlib import Path
from dotenv import load_dotenv
from security import cifrar_config_archivo, descifrar_config_archivo, obtener_fernet

load_dotenv()

CONFIG_ENC_FILE = Path("config.json.enc")
CONFIG_RAW_FILE = Path("config.json")
PENDIENTES_FILE = Path("registros_pendientes/pendientes.json.enc")
DEFAULT_URL = os.getenv("API_URL_BACKEND", "http://127.0.0.1:5000")

def _get_default_client_credentials():
    usuario = os.getenv("CLIENT_USERNAME", "usuario_defecto")
    contrasena = os.getenv("CLIENT_PASSWORD", "contrasena_defecto")
    return usuario, contrasena

def cargar_config():
    if not CONFIG_ENC_FILE.exists():
        if CONFIG_RAW_FILE.exists():
            cifrar_config_archivo(CONFIG_RAW_FILE, CONFIG_ENC_FILE)
            CONFIG_RAW_FILE.unlink(missing_ok=True)
        else:
            default_usuario, default_contrasena = _get_default_client_credentials()
            default_config_data = {
                "URL_BACKEND": DEFAULT_URL,
                "USUARIO": default_usuario,
                "CONTRASENA": default_contrasena
            }
            with open(CONFIG_RAW_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config_data, f, indent=2)
            cifrar_config_archivo(CONFIG_RAW_FILE, CONFIG_ENC_FILE)
            CONFIG_RAW_FILE.unlink(missing_ok=True)
    config_data = descifrar_config_archivo(CONFIG_ENC_FILE)
    if not config_data:
        raise Exception("Fallo al cargar o descifrar la configuración. Archivo corrupto o clave incorrecta.")
    return config_data

def guardar_config(url_backend):
    config_actual = cargar_config()
    config_actual["URL_BACKEND"] = url_backend
    guardar_config_cifrada(config_actual)

def guardar_config_cifrada(config_data):
    try:
        f = obtener_fernet()
    except ValueError:
        raise Exception("Clave Fernet no configurada. No se puede cifrar la configuración.")
    datos_json_bytes = json.dumps(config_data).encode('utf-8')
    datos_cifrados = f.encrypt(datos_json_bytes)
    with open(CONFIG_ENC_FILE, "wb") as f_out:
        f_out.write(datos_cifrados)

def obtener_url_backend():
    return cargar_config()["URL_BACKEND"]

def obtener_usuario_cliente():
    return cargar_config().get("USUARIO", _get_default_client_credentials()[0])

def obtener_contrasena_cliente():
    return cargar_config().get("CONTRASENA", _get_default_client_credentials()[1])

ENDPOINTS = {
    "entrada": "api/asistencias/entrada",
    "salida": "api/asistencias/salida",
    "descanso_inicio": "api/descansos/inicio",
    "descanso_fin": "api/descansos/fin",
    "hora_extra_inicio": "api/horas_extra/registrar",
    "hora_extra_fin": "api/horas_extra/finalizar"
}