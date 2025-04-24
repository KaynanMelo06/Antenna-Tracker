# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from interface import Ui_MainWindow

class HSVApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.cap = cv2.VideoCapture(0)  # Inicia a câmera

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Atualiza o frame a cada ~30ms

        # Mapeia os sliders e labels da interface
        self.sliders = {
            'h_min': self.ui.slider_h_min,
            'h_max': self.ui.slider_h_max,
            's_min': self.ui.slider_s_min,
            's_max': self.ui.slider_s_max,
            'v_min': self.ui.slider_v_min,
            'v_max': self.ui.slider_v_max,
        }
        
        self.labels = {
            'h_min': self.ui.label_h_min,
            'h_max': self.ui.label_h_max,
            's_min': self.ui.label_s_min,
            's_max': self.ui.label_s_max,
            'v_min': self.ui.label_v_min,
            'v_max': self.ui.label_v_max,
        }

        # Conecta os sliders para atualizar os labels
        self.connect_sliders()

    def connect_sliders(self):
        """Conecta cada slider ao seu label correspondente"""
        self.ui.slider_h_min.valueChanged.connect(
            lambda v: self.ui.label_h_min.setText(f"H Min: {v}"))
        self.ui.slider_h_max.valueChanged.connect(
            lambda v: self.ui.label_h_max.setText(f"H Max: {v}"))
        self.ui.slider_s_min.valueChanged.connect(
            lambda v: self.ui.label_s_min.setText(f"S Min: {v}"))
        self.ui.slider_s_max.valueChanged.connect(
            lambda v: self.ui.label_s_max.setText(f"S Max: {v}"))
        self.ui.slider_v_min.valueChanged.connect(
            lambda v: self.ui.label_v_min.setText(f"V Min: {v}"))
        self.ui.slider_v_max.valueChanged.connect(
            lambda v: self.ui.label_v_max.setText(f"V Max: {v}"))

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Lê os valores dos sliders
        h_min = self.sliders['h_min'].value()
        h_max = self.sliders['h_max'].value()
        s_min = self.sliders['s_min'].value()
        s_max = self.sliders['s_max'].value()
        v_min = self.sliders['v_min'].value()
        v_max = self.sliders['v_max'].value()

        # Aplica a máscara HSV
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Mostra na interface
        self.show_image(result)

    def show_image(self, img):
        # Converte imagem do OpenCV (BGR) para QImage (RGB) e exibe no QLabel
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, channel = img.shape
        step = channel * width
        q_img = QImage(img.data, width, height, step, QImage.Format_RGB888)
        self.ui.label_output.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        self.cap.release()  # Libera a câmera ao fechar
        cv2.destroyAllWindows()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HSVApp()
    window.show()
    sys.exit(app.exec_())