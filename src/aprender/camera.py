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

    # imagem: sua imagem já filtrada por HSV (tipo com cv2.inRange)

    # Encontra os contornos
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area > 100:  # ignora pequenos blobs
            # Retângulo que envolve o contorno
            x, y, w, h = cv2.boundingRect(contorno)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 5)  # desenha o retângulo (verde)

            # Centro do contorno
            M = cv2.moments(contorno)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                print(f"Centro do blob: ({cx}, {cy})")
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)  # marca o centro (azul)

    # Mostra o resultado
    cv2.imshow('Blobs detectados', frame)




    # Sai se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()           # Libera a câmera
cv2.destroyAllWindows() # Fecha todas as janelas