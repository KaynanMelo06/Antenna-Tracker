# -*- coding: utf-8 -*-

import cv2 # Biblioteca para captura de vídeo
import numpy as np

# Abre a câmera padrão (geralmente a webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erro ao abrir a camera")
    exit()

while True:
    ret, frame = cap.read()  # Captura frame a frame
    if not ret:
        break

     # Converte o frame de BGR para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Faixa de cor azul em HSV
    lower_blue = np.array([100, 150, 50])   # tom, saturação, valor
    upper_blue = np.array([140, 255, 255])

    # Cria uma máscara só com os pixels na faixa azul
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Aplica a máscara ao frame original
    resultado = cv2.bitwise_and(frame, frame, mask=mask)

    # Mostra os frames
    cv2.imshow("Original", frame)
    cv2.imshow("Mascara Azul", mask)
    cv2.imshow("Resultado", resultado)


    # Sai se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()           # Libera a câmera
cv2.destroyAllWindows() # Fecha todas as janelas