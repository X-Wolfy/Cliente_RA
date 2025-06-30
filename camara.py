import cv2, time
from pyzbar import pyzbar
from qr_utils import desencriptar_qr

def escanear_qr(timeout=15):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    inicio = time.time()
    id_empleado = None
    ventana_ancho = 800
    ventana_alto = 600
    while time.time() - inicio < timeout:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (ventana_ancho, ventana_alto))
        alto, ancho = frame.shape[:2]
        margen_x = int(ancho * 0.2)
        margen_y = int(alto * 0.2)
        x1, y1 = margen_x, margen_y
        x2, y2 = ancho - margen_x, alto - margen_y
        blur = cv2.GaussianBlur(frame, (51, 51), 0)
        blended = blur.copy()
        blended[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
        cv2.rectangle(blended, (x1, y1), (x2, y2), (0, 255, 0), 2)
        roi = frame[y1:y2, x1:x2]
        qr_detectados = pyzbar.decode(roi)
        for qr in qr_detectados:
            contenido = qr.data.decode("utf-8")
            id_empleado = desencriptar_qr(contenido)
            if id_empleado:
                cap.release()
                cv2.destroyAllWindows()
                return id_empleado
        cv2.imshow("Escanear QR", blended)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    return None