import requests, os, json
from dotenv import load_dotenv
from security import guardar_token_cifrado, cargar_token_cifrado
from config import obtener_url_backend, obtener_usuario_cliente, obtener_contrasena_cliente

load_dotenv()

CLIENT_LOGIN_ENDPOINT = "/authentication/client-login"
CLIENT_REFRESH_ENDPOINT = "/authentication/client-refresh"

def guardar_tokens(access_token, refresh_token):
    tokens = {"access_token": access_token, "refresh_token": refresh_token}
    guardar_token_cifrado(tokens)

def cargar_tokens():
    tokens = cargar_token_cifrado()
    return tokens if tokens else None

def autenticar_con_backend():
    api_base_url = obtener_url_backend()
    login_url = f"{api_base_url}{CLIENT_LOGIN_ENDPOINT}"
    usuario = obtener_usuario_cliente()
    contrasena = obtener_contrasena_cliente()
    try:
        response = requests.post(login_url, json={"usuario": usuario, "contraseña": contrasena}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            if access_token and refresh_token:
                guardar_tokens(access_token, refresh_token)
                return {"access_token": access_token, "refresh_token": refresh_token}
            else:
                return None
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError:
        return None

def renovar_access_token(current_refresh_token):
    api_base_url = obtener_url_backend()
    refresh_url = f"{api_base_url}{CLIENT_REFRESH_ENDPOINT}"
    headers = {"Authorization": f"Bearer {current_refresh_token}"}
    try:
        response = requests.post(refresh_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            if new_access_token:
                current_tokens = cargar_tokens()
                if current_tokens:
                    guardar_tokens(new_access_token, current_tokens["refresh_token"])
                    return {"access_token": new_access_token, "refresh_token": current_tokens["refresh_token"]}
                else:
                    return None
            else:
                return None
        elif response.status_code == 401:
            return None
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError:
        return None

def obtener_token_valido():
    tokens = cargar_tokens()
    if not tokens:
        return autenticar_con_backend()
    if not tokens.get("access_token"):
        if tokens.get("refresh_token"):
            refreshed_tokens = renovar_access_token(tokens["refresh_token"])
            if refreshed_tokens:
                return refreshed_tokens
        return autenticar_con_backend()
    return tokens