# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QSizePolicy, QComboBox, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from src.ui.filtro_hsv import HSVFilterWindow
from src.backend.colorfilter import ColorFilter
from src.backend.control.pid import PID
#from src.backend.comm.serial import Serial

class UpComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()  
        popup = self.view().window()
        geo = popup.geometry()
        # ponto superior esquerdo do combo no global
        top_left = self.mapToGlobal(self.rect().topLeft())
        # reposiciona o popup para abrir pra cima
        popup.move(top_left.x(), top_left.y() - geo.height())

class MainWindow(QMainWindow):
    # Signal para envio de frames à janela de calibração
    frame_available = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        #self.serial = Serial('COM3')  # Inicializa a comunicação serial
        self.pid = PID(0, 0)
        self.setWindowTitle("Antenna Tracker")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        self._setup_filters()
        self._setup_ui()
        self._setup_camera()
        self.calibration_window = None
        self.showFullScreen()
        #Keybinds para fechar o FullScreen
        esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc.activated.connect(self.close)

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
        # self.serial = Serial('COM3')  linux: '/dev/ttyUSB0'
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
        self.cap = cv2.VideoCapture(0) # ('/dev/video2') para camera externa e (0) para webcam 
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
            self.calibration_window.load_filter(current)
        self.calibration_window.show()
        # (Re)cria a janela de calibração se necessário
        selected = self.combo_filter.currentText()
        if self.calibration_window is None or not self.calibration_window.isVisible():
            self.calibration_window = HSVFilterWindow(self.filters_hsv, self)
            self.calibration_window.valores_aplicados.connect(self._update_filters)
        # Atualiza o combo e carrega os sliders para o filtro selecionado
        self.calibration_window.ui.combo_filtro.setCurrentText(selected)
        if selected in self.filters_hsv:
            self.calibration_window.load_filter(selected)


    def _update_filters(self, new_filters):
        # Atualiza os ranges HSV com os valores calibrados
        self.filters_hsv = new_filters

    def _send_frame_to_calibrator(self, frame):
        # Envia frame à janela de calibração se aberta
        if self.calibration_window and self.calibration_window.isVisible():
            self.calibration_window.receber_frame(frame)

    def encontrar_centroid(self, contorno):
        M = cv2.moments(contorno)
        if M["m00"] == 0:
            return None
        return (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))

    def calcula_vetor_angulo(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        centroids = {}
        # percorre cada cor de interesse (rosa, verde, amarelo) *MUDE AS TAGS/ID's MANUALMENTE AQUI* 
        for cor in ["rosa", "verde", "amarelo"]:
            f = self.filters_hsv[cor]
            lower = np.array([f["h_min"], f["s_min"], f["v_min"]])
            upper = np.array([f["h_max"], f["s_max"], f["v_max"]])
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
            conts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not conts:
                continue
            c = max(conts, key=cv2.contourArea)
            cent = self.encontrar_centroid(c)
            if cent:
                centroids[cor] = cent

        if all(k in centroids for k in ("amarelo","rosa","verde")):
            cx_a, cy_a = centroids["amarelo"]
            cx_r, cy_r = centroids["rosa"]
            cx_v, cy_v = centroids["verde"]
            # ponto médio das duas frentes
            mx, my = (cx_r + cx_v)//2, (cy_r + cy_v)//2
            vx, vy = mx - cx_a, my - cy_a
            angulo = math.degrees(math.atan2(vy, vx))
            return {"vetor": (vx, vy), "angulo": angulo, "centros": centroids}
        return None

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

        # calcula e desenha vetor de ângulo
        res = self.calcula_vetor_angulo(frame)
        if res:
            vx, vy = res["vetor"]
            ang = res["angulo"]
            cx_a, cy_a = res["centros"]["amarelo"]
            pt0 = (cx_a, cy_a)
            pt1 = (cx_a + int(vx*1.5), cy_a + int(vy*1.5))
            cv2.arrowedLine(contoured, pt0, pt1, (255,0,0), 2, tipLength=0.2)
            cv2.putText(contoured, f"{ang:.1f}°", (pt1[0]+5, pt1[1]-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

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
    win.show()     #win.showFullScreen() # abre em tela cheia  | #win.show() # abre em modo janela
    sys.exit(app.exec_())
