# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np

class Ui_HSVFilterWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("HSVFilterWindow")
        MainWindow.resize(600, 400)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        # label de pré-visualização
        self.label_output = QtWidgets.QLabel(self.centralwidget)
        self.label_output.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label_output)

        # grid de sliders e labels
        self.gridLayout = QtWidgets.QGridLayout()
        # H Min
        self.label_h_min = QtWidgets.QLabel("H Min: 0", self.centralwidget)
        self.slider_h_min = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_h_min.setMaximum(179)
        self.gridLayout.addWidget(self.label_h_min, 0, 0)
        self.gridLayout.addWidget(self.slider_h_min, 0, 1)
        # H Max
        self.label_h_max = QtWidgets.QLabel("H Max: 179", self.centralwidget)
        self.slider_h_max = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_h_max.setMaximum(179)
        self.slider_h_max.setValue(179)
        self.gridLayout.addWidget(self.label_h_max, 1, 0)
        self.gridLayout.addWidget(self.slider_h_max, 1, 1)
        # S Min
        self.label_s_min = QtWidgets.QLabel("S Min: 0", self.centralwidget)
        self.slider_s_min = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_s_min.setMaximum(255)
        self.gridLayout.addWidget(self.label_s_min, 2, 0)
        self.gridLayout.addWidget(self.slider_s_min, 2, 1)
        # S Max
        self.label_s_max = QtWidgets.QLabel("S Max: 255", self.centralwidget)
        self.slider_s_max = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_s_max.setMaximum(255)
        self.slider_s_max.setValue(255)
        self.gridLayout.addWidget(self.label_s_max, 3, 0)
        self.gridLayout.addWidget(self.slider_s_max, 3, 1)
        # V Min
        self.label_v_min = QtWidgets.QLabel("V Min: 0", self.centralwidget)
        self.slider_v_min = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_v_min.setMaximum(255)
        self.gridLayout.addWidget(self.label_v_min, 4, 0)
        self.gridLayout.addWidget(self.slider_v_min, 4, 1)
        # V Max
        self.label_v_max = QtWidgets.QLabel("V Max: 255", self.centralwidget)
        self.slider_v_max = QtWidgets.QSlider(Qt.Horizontal, self.centralwidget)
        self.slider_v_max.setMaximum(255)
        self.slider_v_max.setValue(255)
        self.gridLayout.addWidget(self.label_v_max, 5, 0)
        self.gridLayout.addWidget(self.slider_v_max, 5, 1)

        # botões Reset e Aplicar
        self.btn_reset = QtWidgets.QPushButton("Reset", self.centralwidget)
        self.btn_aplicar = QtWidgets.QPushButton("Aplicar", self.centralwidget)
        self.gridLayout.addWidget(self.btn_reset, 6, 0)
        self.gridLayout.addWidget(self.btn_aplicar, 6, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        # combo de filtros
        self.combo_filtro = QtWidgets.QComboBox(self.centralwidget)
        self.combo_filtro.addItems(["laranja", "azul", "verde", "rosa", "amarelo"])
        self.verticalLayout.addWidget(self.combo_filtro)

        MainWindow.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


class HSVFilterWindow(QtWidgets.QMainWindow):
    valores_aplicados = pyqtSignal(dict)

    def __init__(self, filtros_iniciais: dict, parent=None):
        super().__init__(parent)
        self.ui = Ui_HSVFilterWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Calibração HSV — Múltiplos Filtros")

        # usa o dict que vem do MainWindow (mesma instância)
        self.filtros = filtros_iniciais

        # mapa de sliders
        self.sliders = {
            "h_min": self.ui.slider_h_min,
            "h_max": self.ui.slider_h_max,
            "s_min": self.ui.slider_s_min,
            "s_max": self.ui.slider_s_max,
            "v_min": self.ui.slider_v_min,
            "v_max": self.ui.slider_v_max,
        }

        # conexões
        self.ui.combo_filtro.currentTextChanged.connect(self.carregar_filtro)
        for chave, s in self.sliders.items():
            s.valueChanged.connect(lambda val, k=chave: self._on_slider_change(k, val))
        self.ui.btn_reset.clicked.connect(self.reset)
        self.ui.btn_aplicar.clicked.connect(self.aplicar)

        # frame e timer
        self.current_frame = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(60)

        # inicializa sliders com a cor selecionada
        self.carregar_filtro(self.ui.combo_filtro.currentText())

    def _on_slider_change(self, chave, valor):
        # atualiza dict e label, e reprocessa imagem
        self.filtros[self.ui.combo_filtro.currentText()][chave] = valor
        getattr(self.ui, f"label_{chave}").setText(f"{chave.upper().replace('_',' ')}: {valor}")
        self._processar_imagem()

    def reset(self):
        # zera min e coloca max nos max
        for chave, s in self.sliders.items():
            s.setValue(0 if "_min" in chave else s.maximum())

    def aplicar(self):
        # emite TODO o dict de filtros e fecha
        self.valores_aplicados.emit(self.filtros)
        self.close()

    def receber_frame(self, frame):
        self.current_frame = frame.copy()
        self._processar_imagem()

    def _on_timer(self):
        if self.current_frame is not None:
            self._processar_imagem()

    def carregar_filtro(self, nome: str):
        # carrega os valores do dict nos sliders e labels
        vals = self.filtros[nome]
        for chave, s in self.sliders.items():
            s.blockSignals(True)
            s.setValue(vals[chave])
            getattr(self.ui, f"label_{chave}").setText(f"{chave.upper().replace('_',' ')}: {vals[chave]}")
            s.blockSignals(False)
        self._processar_imagem()

    def _processar_imagem(self):
        if self.current_frame is None:
            return
        hsv = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2HSV)
        nome = self.ui.combo_filtro.currentText()
        vals = self.filtros[nome]
        low = np.array([vals["h_min"], vals["s_min"], vals["v_min"]])
        high= np.array([vals["h_max"], vals["s_max"], vals["v_max"]])
        mask = cv2.inRange(hsv, low, high)
        res  = cv2.bitwise_and(self.current_frame, self.current_frame, mask=mask)

        # exibe no label_output
        img = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        qimg = QImage(img.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self.ui.label_output.width(),
            self.ui.label_output.height(),
            Qt.KeepAspectRatio
        )
        self.ui.label_output.setPixmap(pix)
