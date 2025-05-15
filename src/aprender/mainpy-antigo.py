# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from src.backend.control.pid import PID
from src.backend.comm.serial import Serial
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QWidget, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from src.ui.filtro_hsv import HSVFilterWindow
from src.backend.colorfilter import ColorFilter

#Classe para que o menu de seleção de filtros na janela principal seja somente para cima
class UpComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        pos = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(pos.x(), pos.y() - popup.height())

class MainWindow(QMainWindow):
    frame_disponivel = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Janela Principal")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)

        # Inicializações
        self.pid = PID(0, 0)
        # self.serial = Serial('COM3')
        self.filtro = ColorFilter()

        # Dicionário de filtros HSV
        self.filtros_hsv = {
            "laranja": {"h_min": 10, "h_max": 25,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "azul":    {"h_min": 100, "h_max": 130,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "verde":   {"h_min": 35,  "h_max": 85,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "rosa":    {"h_min": 140, "h_max": 170, "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "amarelo": {"h_min": 25,  "h_max": 35,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
        }

        # Layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout = QVBoxLayout(self.central_widget)

        # Labels de imagem
        self.label_original = QLabel("[Imagem Original]")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label_original)

        self.label_filtrada = QLabel("[Imagem Filtrada]")
        self.label_filtrada.setAlignment(Qt.AlignCenter)
        self.label_filtrada.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label_filtrada)

        # ComboBox de seleção de filtro
        self.combo_filtro_main = QComboBox()
        # adiciona todas as cores e a opção "todos"
        for cor in list(self.filtros_hsv.keys()) + ["todos"]:
            self.combo_filtro_main.addItem(cor)
        self.combo_filtro_main.setCurrentText("todos")
        self.layout.addWidget(self.combo_filtro_main)

        # Botão para abrir janela de calibração
        self.btn_abrir_filtro = QPushButton("Abrir Filtro HSV")
        self.btn_abrir_filtro.clicked.connect(self.abrir_filtro)
        self.layout.addWidget(self.btn_abrir_filtro)

        # Captura de vídeo
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)

        # Sinal para enviar frame à calibração
        self.frame_disponivel.connect(self.enviar_frame_para_filtro)
        self.janela_filtro = None

    def abrir_filtro(self):
        if self.janela_filtro is None:
            self.janela_filtro = HSVFilterWindow(self.filtros_hsv, self)
            self.janela_filtro.valores_aplicados.connect(self.atualizar_filtro)
        else:
            # atualiza o dict e recarrega sliders
            self.janela_filtro.filtros = self.filtros_hsv
            cor = self.janela_filtro.ui.combo_filtro.currentText()
            self.janela_filtro.carregar_filtro(cor)
        self.janela_filtro.show()

    def atualizar_filtro(self, novos_filtros: dict):
        self.filtros_hsv = novos_filtros

    def enviar_frame_para_filtro(self, frame):
        if self.janela_filtro and self.janela_filtro.isVisible():
            self.janela_filtro.receber_frame(frame)

    def atualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)

        selecionado = self.combo_filtro_main.currentText()
        if selecionado == "todos":
            # aplica todos os filtros
            for vals in self.filtros_hsv.values():
                mask = self.filtro.hsv_filter(
                    hsv,
                    (vals["h_min"], vals["h_max"]),
                    (vals["s_min"], vals["s_max"]),
                    (vals["v_min"], vals["v_max"])
                )
                mascara_total = cv2.bitwise_or(mascara_total, mask)
        else:
            # aplica só o filtro selecionado
            vals = self.filtros_hsv[selecionado]
            mascara_total = self.filtro.hsv_filter(
                hsv,
                (vals["h_min"], vals["h_max"]),
                (vals["s_min"], vals["s_max"]),
                (vals["v_min"], vals["v_max"])
            )

        frame_contornos = self.filtro.apply_contours(mascara_total, frame.copy())
        frame_filtrado = cv2.bitwise_and(frame, frame, mask=mascara_total)

        self.frame_disponivel.emit(frame)
        self.mostrar_imagem(self.label_original, frame_contornos)
        self.mostrar_imagem(self.label_filtrada, frame_filtrado)

    def mostrar_imagem(self, label, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qimg).scaled(
            label.width(), label.height(), Qt.KeepAspectRatio
        ))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
