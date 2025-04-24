# -*- coding: utf-8 -*-

import cv2
import numpy as np

def nothing(x):
    pass

# Janela para trackbars
cv2.namedWindow("Controles HSV")
cv2.resizeWindow("Controles HSV", 400, 300)

# Cria as trackbars
cv2.createTrackbar("H Min", "Controles HSV", 0, 179, nothing)
cv2.createTrackbar("H Max", "Controles HSV", 179, 179, nothing)
cv2.createTrackbar("S Min", "Controles HSV", 0, 255, nothing)
cv2.createTrackbar("S Max", "Controles HSV", 255, 255, nothing)
cv2.createTrackbar("V Min", "Controles HSV", 0, 255, nothing)
cv2.createTrackbar("V Max", "Controles HSV", 255, 255, nothing)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Lê os valores das trackbars
    h_min = cv2.getTrackbarPos("H Min", "Controles HSV")
    h_max = cv2.getTrackbarPos("H Max", "Controles HSV")
    s_min = cv2.getTrackbarPos("S Min", "Controles HSV")
    s_max = cv2.getTrackbarPos("S Max", "Controles HSV")
    v_min = cv2.getTrackbarPos("V Min", "Controles HSV")
    v_max = cv2.getTrackbarPos("V Max", "Controles HSV")

    # Cria a máscara
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)
    resultado = cv2.bitwise_and(frame, frame, mask=mask)

    # Mostra os resultados
    cv2.imshow("Camera", frame)
    cv2.imshow("Mascara", mask)
    cv2.imshow("Filtrado", resultado)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
