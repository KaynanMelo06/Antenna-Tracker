# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class AntennaTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurações iniciais
        self.setWindowTitle("Rastreador de Antena")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        # Labels para exibição
        self.image_label = QLabel()
        self.angle_label = QLabel("Angulo: 0")
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.angle_label)
        
        # Cores das tags (HSV)
        self.tag_x_color = {
            'lower': np.array([0, 100, 100]),  # Exemplo: Vermelho
            'upper': np.array([10, 255, 255])
        }
        self.tag_y_color = {
            'lower': np.array([60, 100, 100]),  # Exemplo: Verde
            'upper': np.array([80, 255, 255])
        }
        
        # Captura de vídeo
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def detect_tags(self, frame):
        #Detecta as tags X e Y e retorna seus centros."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Máscaras para as tags
        mask_x = cv2.inRange(hsv, self.tag_x_color['lower'], self.tag_x_color['upper'])
        mask_y = cv2.inRange(hsv, self.tag_y_color['lower'], self.tag_y_color['upper'])
        
        # Encontra contornos
        contours_x, _ = cv2.findContours(mask_x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_y, _ = cv2.findContours(mask_y, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calcula centros
        center_x = self.get_center(contours_x)
        center_y = self.get_center(contours_y)
        
        return center_x, center_y

    def get_center(self, contours):
        #Retorna o centro do maior contorno encontrado."""
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return None

    def calculate_angle(self, center_x, center_y):
        #Calcula o ângulo entre as tags (em graus)."""
        if center_x and center_y:
            dx = center_y[0] - center_x[0]
            dy = center_y[1] - center_x[1]
            angle = math.degrees(math.atan2(dy, dx))
            return angle if angle >= 0 else angle + 360
        return 0

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Detecta tags e calcula ângulo
        center_x, center_y = self.detect_tags(frame)
        angle = self.calculate_angle(center_x, center_y)
        
        # Desenha marcadores
        if center_x:
            cv2.circle(frame, center_x, 10, (0, 0, 255), -1)  # Tag X (vermelho)
        if center_y:
            cv2.circle(frame, center_y, 10, (0, 255, 0), -1)  # Tag Y (verde)
        
        # Exibe ângulo
        self.angle_label.setText(f"Ângulo: {angle:.2f}°")
        
        # Mostra a imagem
        self.display_image(frame)

    def display_image(self, img):
        #Converte e exibe a imagem do OpenCV no QLabel."""
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AntennaTracker()
    window.show()
    sys.exit(app.exec_())