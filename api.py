import requests, json
from datetime import datetime
from pathlib import Path
from filelock import FileLock
from config import obtener_url_backend, PENDIENTES_FILE, ENDPOINTS
from auth import obtener_token_valido, renovar_access_token
from security import cifrar_bytes, descifrar_bytes 

def hacer_request_con_token(metodo, url, **kwargs):
    tokens = obtener_token_valido()
    if not tokens or not tokens.get("access_token"):
        raise Exception("No se pudo obtener un access token válido. Necesita autenticación manual o revisar credenciales.")
    headers = kwargs.pop('headers', {})
    headers['Authorization'] = f"Bearer {tokens['access_token']}"
    kwargs['headers'] = headers
    try:
        respuesta = requests.request(metodo, url, **kwargs)
        if respuesta.status_code == 401:
            new_tokens = None
            if tokens.get('refresh_token'):
                new_tokens = renovar_access_token(tokens['refresh_token'])
            if new_tokens and new_tokens.get("access_token"):
                headers['Authorization'] = f"Bearer {new_tokens['access_token']}"
                kwargs['headers'] = headers
                respuesta = requests.request(metodo, url, **kwargs)
            else:
                raise Exception("Access token expirado y no se pudo refrescar. Sesión inválida.")
        return respuesta
    except requests.exceptions.RequestException as e:
        raise e
    except Exception as e:
        raise e

def enviar_datos(endpoint, payload):
    ruta = ENDPOINTS.get(endpoint)
    if not ruta:
        return False, f"Endpoint '{endpoint}' no válido."
    url = f"{obtener_url_backend()}/{ruta}"
    metodo = "POST" 
    if endpoint == "salida" or endpoint == "hora_extra_fin":
        metodo = "PATCH"
    elif endpoint == "descanso_fin":
        metodo = "PUT"
    try:
        response = hacer_request_con_token(metodo, url, json=payload, timeout=15)       
        if response.status_code in (200, 201):
            data = response.json()
            mensaje = data.get("mensaje", "Registro exitoso.")
            detalles = []
            for clave in ["Hora de entrada", "Hora de salida", "Hora de inicio", "Hora final"]:
                if clave in data:
                    detalles.append(f"{clave}: {data[clave]}")
            if detalles:
                mensaje += "\n" + " | ".join(detalles)
            return True, mensaje
        else:
            try:
                error = response.json().get("error") or response.json().get("mensaje", "")
            except Exception:
                error = f"Error desconocido del servidor. Código: {response.status_code}"
            return False, f"Fallo al registrar:\n{error}"
    except requests.exceptions.RequestException:
        guardar_pendiente(endpoint, payload)
        return False, "No se pudo conectar con el servidor.\nGuardado localmente."
    except Exception as e:
        return False, f"Error de autenticación o inesperado: {e}"

def guardar_pendiente(endpoint, payload):
    pendientes = []
    lock = FileLock(f"{PENDIENTES_FILE}.lock")
    with lock:
        if Path(PENDIENTES_FILE).exists():
            with open(PENDIENTES_FILE, "rb") as f:
                datos_cifrados = f.read()
            try:
                datos_descifrados_bytes = descifrar_bytes(datos_cifrados)
                pendientes = json.loads(datos_descifrados_bytes.decode('utf-8'))
            except Exception as e:
                pendientes = []
                Path(PENDIENTES_FILE).unlink(missing_ok=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metodo = "POST"
        if endpoint == "salida" or endpoint == "hora_extra_fin":
            metodo = "PATCH"
        elif endpoint == "descanso_fin":
            metodo = "PUT"
        pendientes.append({
            "endpoint": endpoint,
            "metodo": metodo,
            "payload": {**payload, "now": now_str},
            "timestamp": datetime.now().isoformat()
        })
        datos_json_bytes = json.dumps(pendientes, indent=2).encode('utf-8')
        datos_cifrados = cifrar_bytes(datos_json_bytes)
        with open(PENDIENTES_FILE, "wb") as f:
            f.write(datos_cifrados)

def reenviar_pendientes():
    if not Path(PENDIENTES_FILE).exists():
        return
    lock = FileLock(f"{PENDIENTES_FILE}.lock")
    with lock:
        with open(PENDIENTES_FILE, "rb") as f:
            datos_cifrados = f.read()
        try:
            datos_descifrados_bytes = descifrar_bytes(datos_cifrados)
            pendientes = json.loads(datos_descifrados_bytes.decode('utf-8'))
        except Exception as e:
            Path(PENDIENTES_FILE).unlink(missing_ok=True)
            return
    nuevos_pendientes = []
    for registro in pendientes:
        endpoint = registro.get("endpoint")
        metodo = registro.get("metodo", "POST")
        payload = registro.get("payload", {})
        ruta = ENDPOINTS.get(endpoint)
        if not ruta:
            continue
        url = f"{obtener_url_backend()}/{ruta}"
        try:
            response = hacer_request_con_token(metodo, url, json=payload, timeout=15)
            if response.status_code not in (200, 201):
                nuevos_pendientes.append(registro)
        except requests.exceptions.RequestException:
            nuevos_pendientes.extend(pendientes[pendientes.index(registro):])
            break
        except Exception as e:
            nuevos_pendientes.append(registro)
    if nuevos_pendientes:
        with lock:
            datos_json_bytes = json.dumps(nuevos_pendientes, indent=2).encode('utf-8')
            datos_cifrados = cifrar_bytes(datos_json_bytes)
            with open(PENDIENTES_FILE, "wb") as f:
                f.write(datos_cifrados)
    else:
        Path(PENDIENTES_FILE).unlink(missing_ok=True)

def get_notificaciones_no_leidas_cliente(id_empleado):
    url = f"{obtener_url_backend()}/api/notificaciones/empleado/{id_empleado}/no-leidas"
    try:
        response = hacer_request_con_token("GET", url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        return []

def marcar_notificaciones_leidas_cliente(lista_ids_notificaciones):
    url = f"{obtener_url_backend()}/api/notificaciones/marcar-leidas-masivo"
    payload = {"notification_ids": lista_ids_notificaciones}
    try:
        response = hacer_request_con_token("PATCH", url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False