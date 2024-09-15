import cv2
import numpy as np

# Capturar imagen de la cámara
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    
    # Convertir la imagen a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Aplicar desenfoque para eliminar ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detección de bordes usando Canny
    edges = cv2.Canny(blurred, 50, 150)

    # Encontrar contornos en la imagen
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Dibujar contornos detectados
    for contour in contours:
        # Aproximar contornos para encontrar rectángulos
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:  # Si tiene 4 lados, podría ser un rectángulo
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtrar según tamaño para evitar contornos pequeños
            if w > 50 and h > 20:  # Ajustar estos valores según tu caso
                # Dibujar un rectángulo verde alrededor del área detectada
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Extraer y mostrar solo la parte del rectángulo
                roi = frame[y:y+h, x:x+w]
                cv2.imshow('ROI', roi)

    # Mostrar la imagen con los contornos
    cv2.imshow("Frame", frame)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera la cámara y cierra las ventanas
cap.release()
cv2.destroyAllWindows()
