# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math
from typing import Optional, Dict, Tuple, Any 
from src.backend.colorfilter import ColorFilter


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