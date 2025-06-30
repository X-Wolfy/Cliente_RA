import tkinter as tk
from tkinter import messagebox
from config import cargar_config, guardar_config

def abrir_config_ventana():
    config_actual = cargar_config()
    url_actual = config_actual["URL_BACKEND"]
    ventana = tk.Toplevel()
    ventana.title("Configuración del Servidor")
    ventana.geometry("400x150")
    tk.Label(ventana, text="URL del servidor (IP:Puerto):").pack(pady=10)
    entrada_url = tk.Entry(ventana, width=40)
    entrada_url.insert(0, url_actual)
    entrada_url.pack(pady=5)
    def guardar():
        nueva_url = entrada_url.get().strip()
        if not nueva_url.startswith("http"):
            messagebox.showerror("Error", "La URL debe comenzar con http:// o https://")
            return
        guardar_config(nueva_url)
        messagebox.showinfo("Configuración", "URL del servidor guardada.")
        ventana.destroy()
    tk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)