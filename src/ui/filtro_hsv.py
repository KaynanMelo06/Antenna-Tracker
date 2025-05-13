# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 400)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_output = QtWidgets.QLabel(self.centralwidget)
        self.label_output.setAlignment(QtCore.Qt.AlignCenter)
        self.label_output.setObjectName("label_output")
        self.verticalLayout.addWidget(self.label_output)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.slider_v_min = QtWidgets.QSlider(self.centralwidget)
        self.slider_v_min.setMaximum(255)
        self.slider_v_min.setOrientation(QtCore.Qt.Horizontal)
        self.slider_v_min.setObjectName("slider_v_min")
        self.gridLayout.addWidget(self.slider_v_min, 4, 2, 1, 1)
        self.slider_s_max = QtWidgets.QSlider(self.centralwidget)
        self.slider_s_max.setMaximum(255)
        self.slider_s_max.setProperty("value", 255)
        self.slider_s_max.setOrientation(QtCore.Qt.Horizontal)
        self.slider_s_max.setObjectName("slider_s_max")
        self.gridLayout.addWidget(self.slider_s_max, 3, 2, 1, 1)
        self.slider_v_max = QtWidgets.QSlider(self.centralwidget)
        self.slider_v_max.setMaximum(255)
        self.slider_v_max.setProperty("value", 255)
        self.slider_v_max.setOrientation(QtCore.Qt.Horizontal)
        self.slider_v_max.setObjectName("slider_v_max")
        self.gridLayout.addWidget(self.slider_v_max, 6, 2, 1, 1)
        self.slider_h_max = QtWidgets.QSlider(self.centralwidget)
        self.slider_h_max.setMaximum(179)
        self.slider_h_max.setProperty("value", 179)
        self.slider_h_max.setOrientation(QtCore.Qt.Horizontal)
        self.slider_h_max.setObjectName("slider_h_max")
        self.gridLayout.addWidget(self.slider_h_max, 1, 2, 1, 1)
        self.slider_s_min = QtWidgets.QSlider(self.centralwidget)
        self.slider_s_min.setMaximum(255)
        self.slider_s_min.setOrientation(QtCore.Qt.Horizontal)
        self.slider_s_min.setObjectName("slider_s_min")
        self.gridLayout.addWidget(self.slider_s_min, 2, 2, 1, 1)
        self.slider_h_min = QtWidgets.QSlider(self.centralwidget)
        self.slider_h_min.setMaximum(179)
        self.slider_h_min.setOrientation(QtCore.Qt.Horizontal)
        self.slider_h_min.setObjectName("slider_h_min")
        self.gridLayout.addWidget(self.slider_h_min, 0, 2, 1, 1)
        self.label_v_max = QtWidgets.QLabel(self.centralwidget)
        self.label_v_max.setObjectName("label_v_max")
        self.gridLayout.addWidget(self.label_v_max, 6, 0, 1, 1)
        self.label_s_min = QtWidgets.QLabel(self.centralwidget)
        self.label_s_min.setObjectName("label_s_min")
        self.gridLayout.addWidget(self.label_s_min, 2, 0, 1, 1)
        self.label_s_max = QtWidgets.QLabel(self.centralwidget)
        self.label_s_max.setObjectName("label_s_max")
        self.gridLayout.addWidget(self.label_s_max, 3, 0, 1, 1)
        self.label_v_min = QtWidgets.QLabel(self.centralwidget)
        self.label_v_min.setObjectName("label_v_min")
        self.gridLayout.addWidget(self.label_v_min, 4, 0, 1, 1)
        self.label_h_min = QtWidgets.QLabel(self.centralwidget)
        self.label_h_min.setObjectName("label_h_min")
        self.gridLayout.addWidget(self.label_h_min, 0, 0, 1, 1)
        self.label_h_max = QtWidgets.QLabel(self.centralwidget)
        self.label_h_max.setObjectName("label_h_max")
        self.gridLayout.addWidget(self.label_h_max, 1, 0, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 7, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        self.combo_filtro = QtWidgets.QComboBox(self.centralwidget)
        self.combo_filtro.addItems(["laranja", "azul"])  # Pode ser dinâmico depois
        self.verticalLayout.addWidget(self.combo_filtro)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Controles HSV"))
        self.label_output.setText(_translate("MainWindow", "[Imagem Aqui]"))
        self.label_v_max.setText(_translate("MainWindow", "V Max: 255"))
        self.label_s_min.setText(_translate("MainWindow", "S Min: 0"))
        self.label_s_max.setText(_translate("MainWindow", "S Max: 255"))
        self.label_v_min.setText(_translate("MainWindow", "V Min: 0"))
        self.label_h_min.setText(_translate("MainWindow", "H Min: 0"))
        self.label_h_max.setText(_translate("MainWindow", "H Max: 179"))
        self.pushButton_2.setText(_translate("MainWindow", "Reset"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))


class HSVFilterWindow(QtWidgets.QMainWindow):
    valores_aplicados = pyqtSignal(dict)
    
    def __init__(self, valores_iniciais_dict, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Calibracao HSV - Multiplos Filtros")

        self.filtros = valores_iniciais_dict  # dicionário: {"laranja": {...}, "azul": {...}}
        self.nome_filtro_atual = self.ui.combo_filtro.currentText()

        self.ui.combo_filtro.currentTextChanged.connect(self.trocar_filtro)

        # Inicializa sliders com os valores do primeiro filtro
        self.sliders = {
            "h_min": self.ui.slider_h_min,
            "h_max": self.ui.slider_h_max,
            "s_min": self.ui.slider_s_min,
            "s_max": self.ui.slider_s_max,
            "v_min": self.ui.slider_v_min,
            "v_max": self.ui.slider_v_max,
        }

        for key, slider in self.sliders.items():
            slider.valueChanged.connect(lambda val, k=key: self.atualizar_valor(k, val))

        self.current_frame = None
        self.carregar_filtro(self.nome_filtro_atual)
        
        self.ui.pushButton.setText("Aplicar")
        self.ui.pushButton.clicked.connect(self.aplicar)
        self.ui.pushButton_2.clicked.connect(self.reset)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar_imagem)
        self.timer.start(60)
    
    def atualizar_label(self, chave, valor):
        label = getattr(self.ui, f"label_{chave}")
        label.setText(f"{chave.upper().replace('_', ' ')}: {valor}")
    
    def reset(self):
        for key, slider in self.sliders.items():
            slider.setValue(0 if "min" in key else slider.maximum())
    
    def aplicar(self):
        valores = {key: slider.value() for key, slider in self.sliders.items()}
        self.valores_aplicados.emit(valores)
        self.close() #comente esta linha para manter a janela aberta
    
    def receber_frame(self, frame):
        #Recebe o frame da janela principal
        self.current_frame = frame.copy()
        self.processar_imagem()
    
    def processar_imagem(self):
        #Aplica o filtro HSV e exibe a imagem
        if self.current_frame is None:
            return
        
        # Converter para HSV
        hsv = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2HSV)
        
        # Obter valores dos sliders
        lower = np.array([
            self.sliders["h_min"].value(),
            self.sliders["s_min"].value(),
            self.sliders["v_min"].value()
        ])
        
        upper = np.array([
            self.sliders["h_max"].value(),
            self.sliders["s_max"].value(),
            self.sliders["v_max"].value()
        ])
        
        # Aplicar máscara
        mask = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(self.current_frame, self.current_frame, mask=mask)
        
        # Exibir imagem processada
        self.mostrar_imagem(result)
    
    def mostrar_imagem(self, img):
        #Converte OpenCV para QPixmap e exibe no label
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.ui.label_output.setPixmap(pixmap.scaled(
        self.ui.label_output.width(),
        self.ui.label_output.height(),
        Qt.KeepAspectRatio
        ))
    
    def atualizar_imagem(self):
        #Atualiza a imagem sempre que houver mudança nos sliders
        if self.current_frame is not None:
            self.processar_imagem()

    def trocar_filtro(self, nome):
        self.nome_filtro_atual = nome
        self.carregar_filtro(nome)

    def carregar_filtro(self, nome):
        valores = self.filtros[nome]
        for key, val in valores.items():
            self.sliders[key].blockSignals(True)
            self.sliders[key].setValue(val)
            self.sliders[key].blockSignals(False)
            self.atualizar_label(key, val)
        self.processar_imagem()

    def atualizar_valor(self, chave, valor):
        self.filtros[self.nome_filtro_atual][chave] = valor
        self.atualizar_label(chave, valor)
        self.processar_imagem()

    def aplicar(self):
        self.valores_aplicados.emit(self.filtros)
        self.close()
