# -*- coding: utf-8 -*-
# Declaração de codificação para suportar caracteres especiais
import sys  # Módulo para funcionalidades do sistema
import cv2  # OpenCV para processamento de imagem
import numpy as np  # NumPy para operações numéricas
from PyQt5.QtWidgets import QApplication, QMainWindow  # Componentes básicos do Qt
from PyQt5.QtCore import QTimer, Qt  # Temporizador e constantes Qt
from PyQt5.QtGui import QImage, QPixmap  # Classes para manipulação de imagens
from interface import Ui_MainWindow  # Interface gerada pelo Qt Designer

class HSVApp(QMainWindow):
    def __init__(self):
        super().__init__()  # Inicializa a classe base QMainWindow
        
        # Configuração da interface do usuário
        self.ui = Ui_MainWindow()  # Cria instância da interface
        self.ui.setupUi(self)  # Configura a interface na janela principal

        # Valores padrão para reset
        self.default_values = {
            'h_min': 0,
            'h_max': 179,
            's_min': 0,
            's_max': 255,
            'v_min': 0,
            'v_max': 255
        }

        # Inicializa a captura de vídeo da webcam (dispositivo 0)
        self.cap = cv2.VideoCapture(0)

        # Configuração do temporizador para atualização contínua
        self.timer = QTimer()  # Cria um temporizador Qt
        self.timer.timeout.connect(self.update_frame)  # Conecta ao método de atualização
        self.timer.start(30)  # Intervalo de atualização em ms (~33fps)

        # Dicionário para acesso fácil aos sliders da interface
        self.sliders = {
            'h_min': self.ui.slider_h_min,  # Slider de Hue mínimo
            'h_max': self.ui.slider_h_max,  # Slider de Hue máximo
            's_min': self.ui.slider_s_min,  # Slider de Saturação mínimo
            's_max': self.ui.slider_s_max,  # Slider de Saturação máximo
            'v_min': self.ui.slider_v_min,  # Slider de Valor (brilho) mínimo
            'v_max': self.ui.slider_v_max   # Slider de Valor (brilho) máximo
        }
        
        # Dicionário para acesso fácil aos labels de valores
        self.labels = {
            'h_min': self.ui.label_h_min,  # Label para H Min
            'h_max': self.ui.label_h_max,  # Label para H Max
            's_min': self.ui.label_s_min,  # Label para S Min
            's_max': self.ui.label_s_max,  # Label para S Max
            'v_min': self.ui.label_v_min,  # Label para V Min
            'v_max': self.ui.label_v_max   # Label para V Max
        }

        # Configura as conexões entre sliders e labels
        self.connect_sliders()
        
        # Conecta o botão de reset
        self.ui.btn_reset.clicked.connect(self.reset_values)

    def reset_values(self):
        #Reseta todos os sliders para os valores padrão#
        for key, slider in self.sliders.items():
            slider.setValue(self.default_values[key])
        
        # Atualiza os labels manualmente (opcional, pois os valueChanged devem disparar)
        for key, label in self.labels.items():
            label.setText(f"{key.split('_')[0].upper()} {key.split('_')[1]}: {self.default_values[key]}")

    def connect_sliders(self):
        #Conecta cada slider ao seu label correspondente para atualização em tempo real
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
        #Captura e processa cada frame da câmera#
        # Lê um frame da câmera
        ret, frame = self.cap.read()
        if not ret:  # Se falhar ao capturar o frame
            return  # Sai da função

        # Converte o frame de BGR (OpenCV) para HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Obtém os valores atuais dos sliders
        h_min = self.sliders['h_min'].value()  # Valor atual do Hue mínimo
        h_max = self.sliders['h_max'].value()  # Valor atual do Hue máximo
        s_min = self.sliders['s_min'].value()  # Valor atual da Saturação mínima
        s_max = self.sliders['s_max'].value()  # Valor atual da Saturação máxima
        v_min = self.sliders['v_min'].value()  # Valor atual do Valor mínimo
        v_max = self.sliders['v_max'].value()  # Valor atual do Valor máximo

        # Define os limites inferior e superior para filtro HSV
        lower = np.array([h_min, s_min, v_min])  # Limite inferior (H,S,V)
        upper = np.array([h_max, s_max, v_max])  # Limite superior (H,S,V)
        
        # Cria máscara binária baseada nos limites
        mask = cv2.inRange(hsv, lower, upper)
        
        # Aplica a máscara ao frame original
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Exibe o resultado processado
        self.show_image(result)

    def show_image(self, img):
        #Exibe uma imagem OpenCV no QLabel da interface#
        # Converte de BGR (OpenCV) para RGB (Qt)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Obtém dimensões da imagem
        height, width, channel = img.shape
        step = channel * width  # Calcula bytes por linha
        
        # Cria QImage a partir dos dados numpy
        q_img = QImage(img.data, width, height, step, QImage.Format_RGB888)
        
        # Converte para QPixmap e exibe no label
        self.ui.label_output.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        #Método chamado ao fechar a janela#
        self.cap.release()  # Libera o dispositivo de captura
        cv2.destroyAllWindows()  # Fecha janelas OpenCV
        event.accept()  # Aceita o evento de fechamento

if __name__ == '__main__':
    # Ponto de entrada principal
    app = QApplication(sys.argv)  # Cria aplicação Qt
    window = HSVApp()  # Instancia a janela principal
    window.show()  # Mostra a janela
    sys.exit(app.exec_())  # Loop principal e tratamento de saída