# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from src.ui.filtro_hsv import HSVFilterWindow
from src.backend.colorfilter import ColorFilter
from src.backend.control.pid import PID
from src.backend.comm.serial import Serial

class MainWindow(QMainWindow):
    # Signal para envio de frames à janela de calibração
    frame_available = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        #self.serial = Serial('COM3')  # Inicializa a comunica��o serial
        self.pid = PID(0, 0)
        self.setWindowTitle("Antenna Tracker")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        self._setup_filters()
        self._setup_ui()
        self._setup_camera()
        self.calibration_window = None

    def _setup_filters(self):
        # Inicializa os ranges HSV para cada cor
        self.filters_hsv = {
            "laranja": {"h_min": 10, "h_max": 25,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "azul":    {"h_min": 100,"h_max": 130,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "verde":   {"h_min": 35, "h_max": 85,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "rosa":    {"h_min": 140,"h_max": 170,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "amarelo": {"h_min": 25, "h_max": 35,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
        }
        self.pid = PID(0, 0)
        # self.serial = Serial('COM3')
        self.filter_proc = ColorFilter()

    def _setup_ui(self):
        # Configuração da interface principal
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Label para frame original
        self.label_original = QLabel("Original")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label_original)

        # Label para frame filtrado
        self.label_filtered = QLabel("Filtrado")
        self.label_filtered.setAlignment(Qt.AlignCenter)
        self.label_filtered.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label_filtered)

        # ComboBox de seleção de filtro
        self.combo_filter = UpComboBox()
        for color in list(self.filters_hsv.keys()) + ["todos"]:
            self.combo_filter.addItem(color)
        self.combo_filter.setCurrentText("todos")
        layout.addWidget(self.combo_filter)

        # Botão para abrir janela de calibração
        btn_calibrate = QPushButton("Calibrar HSV")
        btn_calibrate.clicked.connect(self.open_calibration)
        layout.addWidget(btn_calibrate)

    def _setup_camera(self):
        # Inicializa captura de vídeo e timer
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(30)
        self.frame_available.connect(self._send_frame_to_calibrator)

    def open_calibration(self):
        # Cria ou reutiliza a janela de calibração
        if self.calibration_window is None:
            self.calibration_window = HSVFilterWindow(self.filters_hsv, self)
            self.calibration_window.valores_aplicados.connect(self._update_filters)
        else:
            self.calibration_window.filtros = self.filters_hsv
            current = self.calibration_window.ui.combo_filtro.currentText()
            self.calibration_window.carregar_filtro(current)
        self.calibration_window.show()

    def _update_filters(self, new_filters):
        # Atualiza os ranges HSV com os valores calibrados
        self.filters_hsv = new_filters

    def _send_frame_to_calibrator(self, frame):
        # Envia frame à janela de calibração se aberta
        if self.calibration_window and self.calibration_window.isVisible():
            self.calibration_window.receber_frame(frame)

    def _update_frame(self):
        # Captura e processa o frame atual
        ret, frame = self.cap.read()
        if not ret:
            return
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)

        selected = self.combo_filter.currentText()
        if selected == "todos":
            for vals in self.filters_hsv.values():
                m = self.filter_proc.hsv_filter(
                    hsv,
                    (vals["h_min"], vals["h_max"]),
                    (vals["s_min"], vals["s_max"]),
                    (vals["v_min"], vals["v_max"])
                )
                mask_total = cv2.bitwise_or(mask_total, m)
        else:
            vals = self.filters_hsv[selected]
            mask_total = self.filter_proc.hsv_filter(
                hsv,
                (vals["h_min"], vals["h_max"]),
                (vals["s_min"], vals["s_max"]),
                (vals["v_min"], vals["v_max"])
            )

        contoured = self.filter_proc.apply_contours(mask_total, frame.copy())
        filtered = cv2.bitwise_and(frame, frame, mask=mask_total)

        self.frame_available.emit(frame)
        self._display(self.label_original, contoured)
        self._display(self.label_filtered, filtered)

    def _display(self, label, img):
        # Converte e exibe imagem no QLabel
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(label.width(), label.height(), Qt.KeepAspectRatio)
        label.setPixmap(pix)

    def closeEvent(self, event):
        # Libera recursos ao fechar
        self.cap.release()
        cv2.destroyAllWindows()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())