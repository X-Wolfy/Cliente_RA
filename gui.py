import requests, os
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer
from camara import escanear_qr
from api import enviar_datos, reenviar_pendientes, get_notificaciones_no_leidas_cliente, marcar_notificaciones_leidas_cliente
from config_window import abrir_config_ventana
from config import cargar_config, obtener_url_backend

def verificar_conexion():
    config = cargar_config()
    url_base = obtener_url_backend()
    ping_url = f"{url_base}/ping"
    try:
        response = requests.get(ping_url, timeout=5)
        if response.status_code == 200:
            mensaje = f"Conexión exitosa \nConectado a: {url_base}"
            mostrar_mensaje_temporal(True, mensaje)
        else:
            mensaje = f"Error de conexión \nEl servidor respondió con código {response.status_code}"
            mostrar_mensaje_temporal(False, mensaje)
    except requests.exceptions.RequestException as e:
        mensaje = f"Sin conexión \nNo se pudo conectar al servidor en {url_base}\nDetalle: {e}"
        mostrar_mensaje_temporal(False, mensaje)

def cargar_imagen(nombre_archivo, tamaño):
    try:
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_icono = os.path.join(ruta_base, "icons", nombre_archivo)
        imagen = Image.open(ruta_icono)
        resized_imagen = imagen.resize(tamaño, Image.LANCZOS)
        return ImageTk.PhotoImage(resized_imagen)
    except Exception as e:
        return None
    
def mostrar_mensaje_temporal(es_exito, mensaje, gif_type='default', duration_ms=3500):
        app = QApplication([])

        ventana = QWidget()
        ventana.setWindowTitle("Resultado")
        ventana.setFixedSize(500, 400)
        ventana.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
        ventana.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        gif_label = QLabel()
        gif_label.setFixedSize(250, 250)
        gif_label.setAlignment(Qt.AlignCenter)

        gif_path = ""
        if gif_type == 'notification':
            gif_path = "icons/notificacion.gif"
        elif es_exito:
            gif_path = "icons/exito.gif"
        else:
            gif_path = "icons/error.gif"

        if not os.path.exists(gif_path):
            gif_path = "icons/error.gif"

        movie = QMovie(gif_path)
        movie.setScaledSize(gif_label.size())
        gif_label.setMovie(movie)
        movie.start()

        layout.addWidget(gif_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        text_label = QLabel(mensaje)
        text_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        text_label.setWordWrap(True)
        text_label.setMaximumWidth(360)

        if gif_type == 'notification':
            text_label.setStyleSheet("color: black; font-size: 20px;")
        elif es_exito:
            text_label.setStyleSheet("color: green; font-size: 20px;")
        else:
            text_label.setStyleSheet("color: red; font-size: 20px;")

        layout.addWidget(text_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        ventana.setLayout(layout)
        ventana.setWindowModality(Qt.ApplicationModal)
        ventana.show()

        QTimer.singleShot(duration_ms, ventana.close)
        app.exec_()

def iniciar_interfaz():
    ventana = tk.Tk()
    ventana.resizable(False, False)
    ventana.title("Registro de Asistencia")
    ventana.geometry("750x580")
    ventana.configure(bg="white")
    ventana.iconbitmap(default="icons/icono.ico")

    fuente_boton = tkfont.Font(family="Helvetica", size=24, weight="bold")
    
    def cargar_icono_seguro(nombre_archivo, tamaño):
        try:
            return cargar_imagen(nombre_archivo, tamaño)
        except Exception as e:
            return None
    
    iconos = {
        "entrada": cargar_icono_seguro("entrada.png", (128, 128)),
        "salida": cargar_icono_seguro("salida.png", (128, 128)),
        "descanso_inicio": cargar_icono_seguro("descanso_inicio.png", (128, 128)),
        "descanso_fin": cargar_icono_seguro("descanso_fin.png", (128, 128)),
        "hora_extra_inicio": cargar_icono_seguro("hora_extra_inicio.png", (128, 128)),
        "hora_extra_fin": cargar_icono_seguro("hora_extra_fin.png", (128, 128)),
    }
    
    iconos_menu = {
    "configuracion": cargar_icono_seguro("configuracion.png", (20, 20)),
    "conexion": cargar_icono_seguro("conexion.png", (20, 20))
    }

    colores = {
        "entrada": "#81b7d8",
        "salida": "#a1ccb4",
        "descanso_inicio": "#a1ccb4",
        "descanso_fin": "#81b7d8",
        "hora_extra_inicio": "#81b7d8",
        "hora_extra_fin": "#a1ccb4"
    }

    toolbar = tk.Frame(ventana, bg="#f8f9fa", bd=1, relief=tk.FLAT)
    toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10), padx=10)

    btn_config = tk.Button(toolbar, image=iconos_menu["configuracion"], text="Configuración", compound="left",
                        command=abrir_config_ventana, bg="#f8f9fa", bd=0, font=("Helvetica", 15))
    btn_config.pack(side=tk.LEFT)

    btn_conexion = tk.Button(toolbar, image=iconos_menu["conexion"], text="Verificar conexión", compound="left",
                            command=verificar_conexion, bg="#f8f9fa", bd=0, font=("Helvetica", 15))
    btn_conexion.pack(side=tk.RIGHT)

    contenedor = tk.Frame(ventana, bg="white")
    contenedor.pack(expand=True)

    acciones = {
        "Registrar Entrada": "entrada",
        "Registrar Salida": "salida",
        "Inicio de cafetería": "descanso_inicio",
        "Fin de cafetería": "descanso_fin",
        "Iniciar Hora Extra": "hora_extra_inicio",
        "Finalizar Hora Extra": "hora_extra_fin"
    }

    def manejar_accion(accion):
        reenviar_pendientes()
        id_empleado = escanear_qr()
        if id_empleado is None:
            mostrar_mensaje_temporal(False, "QR inválido o no detectado a tiempo.")
            return
        notificaciones_no_leidas = get_notificaciones_no_leidas_cliente(id_empleado)
        if notificaciones_no_leidas:
            ids_notificaciones_mostradas = []
            for notif in notificaciones_no_leidas:
                mensaje_notif = notif.get('Mensaje', 'Mensaje de notificación vacío.')
                mostrar_mensaje_temporal(True, mensaje_notif, gif_type='notification', duration_ms=7000)
                ids_notificaciones_mostradas.append(notif.get('IdNotificacion'))
            if ids_notificaciones_mostradas:
                marcar_notificaciones_leidas_cliente(ids_notificaciones_mostradas)
        payload = { "IdEmpleado": id_empleado }
        exito, mensaje = enviar_datos(accion, payload)
        mostrar_mensaje_temporal(exito, mensaje, gif_type='default', duration_ms=3500)

    fila, columna = 0, 0
    for texto, clave in acciones.items():
        color = colores.get(clave, "#ddd")
        imagen = iconos.get(clave)
        boton = tk.Button(
            contenedor,
            text=texto,
            image=imagen,
            compound="left",
            command=lambda v=clave: manejar_accion(v),
            font=fuente_boton,
            bg=color,
            fg="white",
            activebackground=color,
            relief=tk.FLAT,
            wraplength=180,
            justify="left",
            height=150,
            padx=20
        )
        boton.image = imagen
        boton.grid(row=fila, column=columna, padx=10, pady=10, sticky="ew")
        columna += 1
        if columna == 2:
            columna = 0
            fila += 1
            
    ventana.mainloop()