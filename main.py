# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from src.ui.filtro_hsv import HSVFilterWindow  # Importar a janela do filtro HSV
from src.backend.colorfilter import ColorFilter


class MainWindow(QMainWindow):

    frame_disponivel = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Janela Principal")
        self.setGeometry(100, 100, 800, 600)
        
        # Valores padrão do filtro HSV
        self.filtro_hsv = {
            "h_min": 0, "h_max": 179,
            "s_min": 0, "s_max": 255,
            "v_min": 0, "v_max": 255
        }
        
        # Configurar interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Labels para exibir as imagens
        self.label_original = QLabel("[Imagem Original]")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_original)
        
        self.label_filtrada = QLabel("[Imagem Filtrada]")
        self.label_filtrada.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_filtrada)
        
        # Botão para abrir o filtro HSV
        self.btn_abrir_filtro = QPushButton("Abrir Filtro HSV")
        self.btn_abrir_filtro.clicked.connect(self.abrir_filtro)
        self.layout.addWidget(self.btn_abrir_filtro)
        
        # Captura de vídeo e timer
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)
        self.filtro = ColorFilter()

        self.frame_disponivel.connect(self.enviar_frame_para_filtro)

    def atualizar_filtro(self, valores):
        # Atualiza os valores do filtro HSV
        self.filtro_hsv = {
            "h_min": valores["h_min"],
            "h_max": valores["h_max"],
            "s_min": valores["s_min"],
            "s_max": valores["s_max"],
            "v_min": valores["v_min"],
            "v_max": valores["v_max"]
        }
        print("Valores do filtro atualizados:", self.filtro_hsv)
        
    def abrir_filtro(self):
        self.janela_filtro = HSVFilterWindow(self.filtro_hsv, self)
        self.janela_filtro.valores_aplicados.connect(self.atualizar_filtro)
        self.janela_filtro.show()

    

    def enviar_frame_para_filtro(self, frame):
        #Envia o frame para a janela de calibração se estiver aberta
        if hasattr(self, 'janela_filtro') and self.janela_filtro.isVisible():
            self.janela_filtro.receber_frame(frame)

    def atualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = self.filtro.hsv_filter(
            hsv,
            (self.filtro_hsv["h_min"], self.filtro_hsv["h_max"]),
            (self.filtro_hsv["s_min"], self.filtro_hsv["s_max"]),
            (self.filtro_hsv["v_min"], self.filtro_hsv["v_max"])
        )
        frame_contornos = self.filtro.apply_contours(mask, frame.copy())
        frame_filtrado = cv2.bitwise_and(frame, frame, mask=mask)

        # Enviar frame para a janela de calibração
        self.frame_disponivel.emit(frame)

        # Exibir na interface principal
        self.mostrar_imagem(self.label_original, frame_contornos)
        self.mostrar_imagem(self.label_filtrada, frame_filtrado)


    def mostrar_imagem(self, label, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())