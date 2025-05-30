# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import math
from typing import Optional, Dict, Tuple, Any 
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
from src.ui.view.calibratecamera import CameraCalibrator


class UpComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()  
        popup = self.view().window()
        geo = popup.geometry()
        # ponto superior esquerdo do combo no global
        top_left = self.mapToGlobal(self.rect().topLeft())
        # reposiciona o popup para abrir pra cima
        popup.move(top_left.x(), top_left.y() - geo.height())
        
class VisionProcessor:
    """
    Classe responsável pelo processamento de imagens: detecção de centróides,
    cálculo de ângulos e desenho de vetores com base em filtros HSV.
    """
    def __init__(self, filters_hsv: Dict[str, Dict[str, int]], filter_proc: ColorFilter) -> None:
        """
        Inicializa com os ranges HSV e o objeto ColorFilter.

        :param filters_hsv: Dicionário de parâmetros HSV para cada cor.
        :param filter_proc: Instância de ColorFilter para aplicar máscaras.
        """
        self.filters_hsv = filters_hsv
        self.filter_proc = filter_proc

    @staticmethod
    def encontrar_centroid(contorno: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Calcula o centróide de um contorno.

        :param contorno: Contorno em formato numpy.ndarray.
        :return: Tupla (x, y) do centróide ou None se inválido.
        """
        M = cv2.moments(contorno)
        if M.get("m00", 0) == 0:
            return None
        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

    def calcular_angulo_robo(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Processa o frame para encontrar os centróides das cores 'amarelo', 'rosa' e 'verde',
        calcula o vetor entre 'amarelo' e o ponto médio entre 'rosa' e 'verde',
        e retorna um dicionário com centros, vetor e ângulo.

        :param frame: Imagem BGR capturada pela câmera.
        :return: Dicionário {'centros':..., 'vetor':..., 'angulo':...} ou None.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        centroids: Dict[str, Tuple[int, int]] = {}
        for cor in ("rosa", "verde", "amarelo"):
            f = self.filters_hsv[cor]
            lower = np.array([f["h_min"], f["s_min"], f["v_min"]])
            upper = np.array([f["h_max"], f["s_max"], f["v_max"]])
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
            conts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if conts:
                cent = self.encontrar_centroid(max(conts, key=cv2.contourArea))
                if cent:
                    centroids[cor] = cent
        if all(k in centroids for k in ("amarelo", "rosa", "verde")):
            cx_a, cy_a = centroids["amarelo"]
            cx_r, cy_r = centroids["rosa"]
            cx_v, cy_v = centroids["verde"]
            mx, my = (cx_r + cx_v) // 2, (cy_r + cy_v) // 2
            vx, vy = mx - cx_a, my - cy_a
            ang = -math.degrees(math.atan2(vy, vx))
            return {"centros": centroids, "vetor": (vx, vy), "angulo": ang}
        return None

    def calcular_vetor_laranja(
        self,
        hsv: np.ndarray,
        contoured: np.ndarray,
        res: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Desenha uma seta do ponto médio de 'rosa' e 'verde' até o centróide do objeto laranja,
        se disponível.

        :param hsv: Imagem em HSV.
        :param contoured: Imagem BGR já com contornos desenhados.
        :param res: Resultado do cálculo de ângulo principal.
        :return: Imagem anotada com a seta laranja.
        """
        if res is None:
            return contoured
        f = self.filters_hsv["laranja"]
        mask = self.filter_proc.hsv_filter(
            hsv,
            (f["h_min"], f["h_max"]),
            (f["s_min"], f["s_max"]),
            (f["v_min"], f["v_max"])
        )
        conts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if conts and all(c in res["centros"] for c in ("rosa", "verde")):
            cent_o = self.encontrar_centroid(max(conts, key=cv2.contourArea))
            if cent_o:
                cx_o, cy_o = cent_o
                (cx_r, cy_r) = res["centros"]["rosa"]
                (cx_v, cy_v) = res["centros"]["verde"]
                mx, my = (cx_r + cx_v) // 2, (cy_r + cy_v) // 2
                cv2.arrowedLine(contoured, (mx, my), (cx_o, cy_o), (0,165,255), 2, tipLength=0.2)
                ang_o = -math.degrees(math.atan2(cy_o - my, cx_o - mx))
                cv2.putText(
                    contoured,
                    f"{ang_o:.1f}°",
                    (cx_o + 5, cy_o - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0,0,0),
                    2
                )
        return contoured


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
            "azul":    {"h_min": 100,"h_max": 130,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "verde":   {"h_min": 35, "h_max": 85,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "rosa":    {"h_min": 140,"h_max": 170,"s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
            "amarelo": {"h_min": 25, "h_max": 35,  "s_min": 100, "s_max": 255, "v_min": 100, "v_max": 255},
        }
        self.filter_proc = ColorFilter()
        self.vision = VisionProcessor(self.filters_hsv, self.filter_proc)
        self.pid = PID(0, 0)
        # self.serial = Serial('COM3')  linux: '/dev/ttyUSB0'
        

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

    def _desenhar_vetores(self, sem_distorcao: np.ndarray, contornado: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(sem_distorcao, cv2.COLOR_BGR2HSV)
        res = self.vision.calcular_angulo_robo(sem_distorcao)
        if res:
            vx, vy = res["vetor"]
            ang = res["angulo"]
            cx_a, cy_a = res["centros"]["amarelo"]
            pt0 = (cx_a, cy_a)
            pt1 = (cx_a + int(vx*1.5), cy_a + int(vy*1.5))
            cv2.arrowedLine(contornado, pt0, pt1, (255,0,0), 2, tipLength=0.2)
            cv2.putText(contornado, f"{ang:.1f}°", (pt1[0]+5, pt1[1]-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
        contornado = self.vision.calcular_vetor_laranja(hsv, contornado, res)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()     #win.showFullScreen() # abre em tela cheia  | #win.show() # abre em modo janela
    sys.exit(app.exec_())