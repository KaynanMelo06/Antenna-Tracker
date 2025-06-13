import numpy as np
import cv2
from typing import Tuple

class ColorFilter:
    def __init__(self) -> None:
        self.BLOB_AREA_THRESHOLD = 100  # Limite de �rea para considerar um blob

    def hsv_filter(
        self,
        hsv_image: np.ndarray,
        hue_range: Tuple[int, int],
        saturation_range: Tuple[int, int],
        value_range: Tuple[int, int],
    ) -> np.ndarray:
        # Define os limites inferior e superior para filtro HSV
        lower = np.array([hue_range[0], saturation_range[0], value_range[0]])
        upper = np.array([hue_range[1], saturation_range[1], value_range[1]])

        # Cria mascara binaria baseada nos limites
        mask = cv2.inRange(hsv_image, lower, upper)

        return mask
    
    def apply_contours(self, mask: np.ndarray, frame: np.ndarray) -> np.ndarray:
        # Encontra os contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.BLOB_AREA_THRESHOLD:
                # Desenha o retangulo que envolve o objeto
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # desenha o ret�ngulo (verde)

                # Desenha o centro do objeto
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -4)  # marca o centro (azul)
        return frame  # , cx, cy linha 118 main.py

