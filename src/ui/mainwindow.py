# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import math
from typing import Optional, Dict, Tuple, Any 
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QSizePolicy, QShortcut, QComboBox, QHBoxLayout, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import json, os
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from src.ui.filtro_hsv import HSVFilterWindow
from src.backend.colorfilter import ColorFilter
from src.backend.control.pid import PID
from src.backend.comm.serial import Serial
from src.ui.view.calibratecamera import CameraCalibrator
from src.backend.visionprocessor import VisionProcessor

class MainWindow(QMainWindow):
    """
    Janela principal da aplicação que gerencia a interface, loop de câmera
    e delega o processamento de imagens ao VisionProcessor.
    """
    # Signal para envio de frames à janela de calibração
    frame_available = pyqtSignal(np.ndarray)

    def __init__(self):
        """
        Inicializa filtros, componentes da UI, câmera e atalhos de teclado.
        """
        super().__init__()
        # Configura a status bar para mostrar alertas
        self.statusBar().showMessage("Envio serial: PAUSADO")
        self.serial = Serial('/dev/ttyUSB0') #linux: '/dev/ttyUSB0' windows: 'COM3' # Inicializa a comunicação serial
        self.pid = PID(0, 0)
        self.sending = False
        # Atalho para ligar/desligar envio serial
        self.shortcut_toggle = QShortcut(QKeySequence("k"), self)
        self.shortcut_toggle.activated.connect(self.toggle_sending)
        
        # --- Parâmetros do PID (ajuste conforme experimentação) ---
        self.kp = 1.950    # Ganho proporcional
        self.ki = 0.000    # Ganho integral (se for usar termo I)
        self.kd = 0.200    # Ganho derivativo
        self.outmin = -150  # Saída mínima (por exemplo, velocidade/motor de -100)
        self.outmax = 150   # Saída máxima (por exemplo, velocidade/motor de +100)
        self.setWindowTitle("Antenna Tracker")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        self._setup_filters()
        # Tenta carregar configurações salvas (PID + HSV)
        self.load_config()
        self._setup_ui()
        self._setup_camera()
        self.calibration_window = None
        self.showFullScreen()
        self.vision: VisionProcessor
        #Keybinds para fechar o FullScreen
        esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc.activated.connect(self.close)
        


    def _setup_filters(self):
        """
        Configura os ranges HSV, instância o ColorFilter e o VisionProcessor.
        """
        # Inicializa os ranges HSV para cada cor
        self.filters_hsv = {
            "laranja": {"h_min": 10, "h_max": 25,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "verde":   {"h_min": 35, "h_max": 85,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "rosa":    {"h_min": 140,"h_max": 170,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "amarelo": {"h_min": 25, "h_max": 35,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
        }
        self.filter_proc = ColorFilter()
        self.vision = VisionProcessor(self.filters_hsv, self.filter_proc)
        

    def _setup_ui(self):
        """
        Constrói e organiza todos os widgets do Qt para visualização e controles.
        """
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
        self.combo_filter = QComboBox()
        for color in list(self.filters_hsv.keys()) + ["todos"]:
            self.combo_filter.addItem(color)
        self.combo_filter.setCurrentText("todos")
        layout.addWidget(self.combo_filter)

        # Botão para abrir janela de calibração
        btn_calibrate = QPushButton("Calibrar HSV")
        btn_calibrate.clicked.connect(self.open_calibration)
        layout.addWidget(btn_calibrate)
        
    def _setup_camera(self):
        """
        Inicializa o dispositivo de captura, calibrador e timer para atualizações de frame.
        """
        # Inicializa captura de vídeo e timer
        self.cap = cv2.VideoCapture('/dev/video2') # ('/dev/video2') para camera externa e (0) para webcam
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        desired_w = 1280
        desired_h = 720
        # 1) Parâmetros de calibração (substitua pelos seus valores)
        fx, fy = 1261.5, 1252.74
        cx, cy = 648.357, 413.334
        # k1, k2, p1, p2, k3
        dist_coeffs = [-0.674575, 0.290729, -0.0169976, -0.000485822, 0.526821]
        # Resolução dos frames
        image_size = (desired_w, desired_h)
        # 2) Inicializa o calibrador
        self.calibrator = CameraCalibrator(fx, fy, cx, cy, dist_coeffs, image_size)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(1) #(15)quanto menor mais fluido a imagem (fps)
        self.frame_available.connect(self._send_frame_to_calibrator)
         
    # === métodos novos para salvar/carregar configuração ===
    def load_config(self):
        """Carrega ganhos do PID e ranges HSV de config.json, se existir."""
        cfg_file = "config.json"
        if not os.path.exists(cfg_file):
            return
        try:
            with open(cfg_file, "r") as f:
                cfg = json.load(f)
            # — HSV filters (só se já tiver chamado self._setup_filters()) —
            for cor, params in cfg.get("filters_hsv", {}).items():
                if cor in self.filters_hsv:
                    for key, val in params.items():
                        if key in self.filters_hsv[cor]:
                            self.filters_hsv[cor][key] = int(val)
        except Exception as e:
            print(f"Erro ao carregar config.json: {e}")

    def save_config(self):
        """Salva ganhos do PID em config.json."""
        cfg = {
            "filters_hsv": self.filters_hsv
        }
        try:
            with open("config.json", "w") as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")

    def update_pid_param(self, name: str, value: float):
        """Atualiza um ganho do PID e salva imediatamente."""
        setattr(self, name, value)
        self.save_config()

    def open_calibration(self):
        """
        Abre ou atualiza a janela de calibração HSV com os filtros atuais.
        """
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

    def _update_filters(self, new_filters: Dict[str, Dict[str, int]])-> None:
        """
        Recebe novos ranges HSV proveniente da janela de calibração.

        :param new_filters: Dicionário atualizado de filtros HSV.
        """
        # Atualiza os ranges HSV com os valores calibrados
        self.filters_hsv = new_filters
        # salva imediatamente no config.json
        self.save_config()

    def _send_frame_to_calibrator(self, frame: np.ndarray) -> None:
        """
        Envia o frame atual para a janela de calibração caso esteja visível.
        """
        # Envia frame à janela de calibração se aberta
        if self.calibration_window and self.calibration_window.isVisible():
            self.calibration_window.receber_frame(frame)



    def _update_frame(self) -> None:
        """
        Loop principal: captura, corrige distorção, aplica filtros, desenha vetores
        e atualiza a UI.
        """
        frame = self._capturar_frame()
        if frame is None:
            return

        sem_distorcao = self._remover_distorcao(frame)
        contornado, filtrado = self._processar_filtros(sem_distorcao)
        anotado = self._desenhar_vetores(sem_distorcao, contornado)
        self._exibir_frames(sem_distorcao, filtrado, anotado)

    def _capturar_frame(self) -> Optional[np.ndarray]:
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def _remover_distorcao(self, frame: np.ndarray) -> np.ndarray:
        return self.calibrator.undistort(frame)

    def _processar_filtros(self, sem_distorcao: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        hsv = cv2.cvtColor(sem_distorcao, cv2.COLOR_BGR2HSV)
        mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        selecionado = self.combo_filter.currentText()
        if selecionado == "todos":
            for vals in self.filters_hsv.values():
                m = self.filter_proc.hsv_filter(
                    hsv,
                    (vals["h_min"], vals["h_max"]),
                    (vals["s_min"], vals["s_max"]),
                    (vals["v_min"], vals["v_max"])
                )
                mascara_total = cv2.bitwise_or(mascara_total, m)
        else:
            vals = self.filters_hsv[selecionado]
            mascara_total = self.filter_proc.hsv_filter(
                hsv,
                (vals["h_min"], vals["h_max"]),
                (vals["s_min"], vals["s_max"]),
                (vals["v_min"], vals["v_max"])
            )
        contornado = self.filter_proc.apply_contours(mascara_total, sem_distorcao.copy())
        filtrado = cv2.bitwise_and(sem_distorcao, sem_distorcao, mask=mascara_total)
        return contornado, filtrado

    def toggle_sending(self):
        """
        Inverte a flag de envio:
        - Se estiver ativando, o PID voltará a mandar comandos no próximo frame.
        - Se estiver desativando, envia imediatamente V=0 para parar o robô.
        """
        self.sending = not self.sending
        if self.sending:
            msg = "Envio serial: ATIVADO"
            self.setWindowTitle("Antenna Tracker — ENVIANDO")
        else:
            msg = "Envio serial: PAUSADO"
            self.setWindowTitle("Antenna Tracker — PAUSADO")
            # Envia comando de parada: left=0, right=0 (ID 3)
            self.serial.sendData(3, 0, 0)
        self.statusBar().showMessage(msg)


    def _desenhar_vetores(self, sem_distorcao: np.ndarray, contornado: np.ndarray) -> np.ndarray:
        # 1) Converte para HSV e obtém dados de orientação do robô (ângulo atual)
        hsv = cv2.cvtColor(sem_distorcao, cv2.COLOR_BGR2HSV)
        res = self.vision.calcular_angulo_robo(sem_distorcao)

        if res:
            # === 1.1) Desenha seta azul mostrando a orientação atual do robô ===
            vx, vy = res["vetor"]         # vetor que indica “frente do robô”
            ang = res["angulo"]           # ângulo atual do robô (em graus)
            cx_a, cy_a = res["centros"]["amarelo"]
            pt0 = (cx_a, cy_a)
            pt1 = (cx_a + int(vx*1.5), cy_a + int(vy*1.5))
            cv2.arrowedLine(contornado, pt0, pt1, (255, 0, 0), 2, tipLength=0.2)
            cv2.putText(contornado, f"{ang:.1f}°", (pt1[0] + 5, pt1[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # === 1.2) Calcula agora o ângulo para o ponto laranja (setpoint) ===
            f_orange = self.filters_hsv["laranja"]
            mask_o = self.filter_proc.hsv_filter(
                hsv,
                (f_orange["h_min"], f_orange["h_max"]),
                (f_orange["s_min"], f_orange["s_max"]),
                (f_orange["v_min"], f_orange["v_max"])
            )
            conts_o, _ = cv2.findContours(mask_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ang_o = None  # ângulo alvo (ou None se não detectar)

            # Para calcular ang_o, precisamos do centróide do laranja e do ponto médio entre rosa e verde
            if conts_o and all(c in res["centros"] for c in ("rosa", "verde")):
                cent_o = VisionProcessor.encontrar_centroid(max(conts_o, key=cv2.contourArea))
                if cent_o:
                    cx_o, cy_o = cent_o
                    # ponto médio entre rosa e verde:
                    cx_r, cy_r = res["centros"]["rosa"]
                    cx_v, cy_v = res["centros"]["verde"]
                    mx, my = (cx_r + cx_v) // 2, (cy_r + cy_v) // 2

                    # seta laranja (visualização)
                    cv2.arrowedLine(contornado, (mx, my), (cx_o, cy_o),
                                    (0, 165, 255), 2, tipLength=0.2)
                    ang_o = -math.degrees(math.atan2(cy_o - my, cx_o - mx))
                    cv2.putText(
                        contornado,
                        f"{ang_o:.1f}°",
                        (cx_o + 5, cy_o - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 0),
                        2
                    )

            # === 1.3) Se detectamos o ângulo atual (ang) e o ângulo alvo (ang_o), chamamos o PID ===
            if ang is not None and ang_o is not None:
                # process(input=ang, setpoint=ang_o)
                controle = self.pid.process(
                    self.kp,
                    self.ki,
                    self.kd,
                    self.outmin,
                    self.outmax,
                    ang,
                    ang_o
                )
                
                # currSpeed = 400
                
                # if (ang >= 90.0 ):
                #     ang = 180.0 - ang
                #     leftspeed = -1 * currSpeed + controle
                #     rightspeed = -1 * currSpeed
                # elif(ang <= 0.0 and ang >=-90.0):
                #     ang = -1 * ang
                #     leftspeed = currSpeed
                #     rightspeed = currSpeed - controle
                # elif(ang < -90.0):
                #     ang = 180.0 + ang
                #     leftspeed = -1 * currSpeed
                #     rightspeed = -1 * currSpeed + controle
                # else:
                #     leftspeed = currSpeed - controle
                #     rightspeed = currSpeed
                
                # === gira em torno do próprio eixo para “olhar” a bola ===
                # controle já é a saída do PID que mede (ang, ang_o)
                leftspeed  = int(-controle)
                rightspeed = int(+controle)
                                                
                # envia comandos de movimento ou de parada, conforme o flag
                if self.sending:
                    # PID manda a velocidade calculada
                    self.serial.sendData(3, int(leftspeed), int(rightspeed))
                else:
                    # enquanto estiver pausado, garanta que o robô receba 0,0 a cada frame
                    self.serial.sendData(3, 0, 0)
                

                
                # Mostra o valor de controle na tela (pode comentar/remover se não quiser exibir)
                cv2.putText(
                    contornado,
                    f"Ctr: {controle:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

                # Exemplo de envio via serial (descomente e ajuste caso use hardware):
                #cmd = f"{controle:.0f}\n".encode()
                #self.serial.write(cmd)

        return contornado

    def _exibir_frames(self, sem_distorcao: np.ndarray, filtrado: np.ndarray, anotado: np.ndarray) -> None:
        self.frame_available.emit(sem_distorcao)
        self._display(self.label_original, anotado)
        self._display(self.label_filtered, filtrado)
            
            
    def _display(self, label: QLabel, img: np.ndarray) -> None:
        """
        Converte imagem BGR para QPixmap e exibe no QLabel.

        :param label: QLabel que receberá a imagem.
        :param img: Frame BGR a ser exibido.
        """
        # Converte imagem BGR para QPixmap para exibição no Qt
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(label.width(), label.height(), Qt.KeepAspectRatio)
        label.setPixmap(pix)

    def closeEvent(self, event: Any) -> None:
        """
        Libera a câmera e fecha janelas OpenCV ao encerrar.
        """
        # Garante liberação de recursos ao fechar
        self.cap.release()
        cv2.destroyAllWindows()
        super().closeEvent(event)