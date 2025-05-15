# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from src.backend.control.pid import PID
from src.backend.comm.serial import Serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from src.ui.filtro_hsv import HSVFilterWindow  # Importar a janela do filtro HSV
from src.backend.colorfilter import ColorFilter
from PyQt5.QtWidgets import QSizePolicy


class MainWindow(QMainWindow):

    frame_disponivel = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        #self.serial = Serial('COM3')  # Inicializa a comunica��o serial
        self.pid = PID(0, 0)
        self.setWindowTitle("Janela Principal")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        #self.setGeometry(100, 100, 500, 300)
        self.filtro = ColorFilter()
        
        # Valores padr�o do filtro HSV
        self.filtros_hsv = {
            "laranja": {
                "h_min": 10, "h_max": 25,
                "s_min": 100, "s_max": 255,
                "v_min": 100, "v_max": 255
            },
            "azul": {   
                "h_min": 100, "h_max": 130,
                "s_min": 100, "s_max": 255,
                "v_min": 100, "v_max": 255
            }
        }
        
        # Configurar interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Labels para exibir as imagens
        self.label_original = QLabel("[Imagem Original]")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label_original)
        
        self.label_filtrada = QLabel("[Imagem Filtrada]")
        self.label_filtrada.setAlignment(Qt.AlignCenter)
        self.label_filtrada.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label_filtrada)
        
        # Bot�o para abrir o filtro HSV
        self.btn_abrir_filtro = QPushButton("Abrir Filtro HSV")
        self.btn_abrir_filtro.clicked.connect(self.abrir_filtro)
        self.layout.addWidget(self.btn_abrir_filtro)

         # Captura de v�deo e timer
        self.cap = cv2.VideoCapture(0) #0 para webcam e 1 para c�mera externa
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)

        self.frame_disponivel.connect(self.enviar_frame_para_filtro)

    def run(self):
        pass
        

    def atualizar_filtro(self, valores):
        # Atualiza os valores do filtro HSV
        self.filtros_hsv = {
            "laranja": {
                (valores["h_min"], valores["h_max"]),
                (valores["s_min"], valores["s_max"]),
                (valores["v_min"], valores["v_max"])
            },
            "azul": {
                "h_min": 100, "h_max": 130,
                "s_min": 100, "s_max": 255,
                "v_min": 100, "v_max": 255
            }
        }
        #print("Valores do filtro atualizados:", self.filtro_hsv)
        
        
    def abrir_filtro(self):
        self.janela_filtro = HSVFilterWindow(self.filtros_hsv, self)
        self.janela_filtro.valores_aplicados.connect(self.atualizar_filtro)
        self.janela_filtro.show()

    

    def enviar_frame_para_filtro(self, frame):
        #Envia o frame para a janela de calibra��o se estiver aberta
        if hasattr(self, 'janela_filtro') and self.janela_filtro.isVisible():
            self.janela_filtro.receber_frame(frame)

    def atualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret: return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)

        for nome, valores in self.filtros_hsv.items():
            mask = self.filtro.hsv_filter(
                hsv,
                (valores["h_min"], valores["h_max"]),
                (valores["s_min"], valores["s_max"]),
                (valores["v_min"], valores["v_max"])
            )
            mascara_total = cv2.bitwise_or(mascara_total, mask)
            
        #frame_contornos, cx, cy = self.filtro.apply_contours(mascara_total, frame.copy())
        #linha 35 colorfilter.py
        frame_contornos = self.filtro.apply_contours(mascara_total, frame.copy())
        frame_filtrado = cv2.bitwise_and(frame, frame, mask=mascara_total)

        self.frame_disponivel.emit(frame)
        self.mostrar_imagem(self.label_original, frame_contornos)
        self.mostrar_imagem(self.label_filtrada, frame_filtrado)


    def mostrar_imagem(self, label, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_img))
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()  # Ou self.showNormal() para voltar ao tamanho original

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    #window.showFullScreen()  # <- Modo tela cheia
    window.show()
    sys.exit(app.exec_())