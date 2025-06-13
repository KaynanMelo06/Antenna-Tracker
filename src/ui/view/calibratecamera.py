# calibrate.py

import cv2
import numpy as np
from typing import Sequence, Tuple

class CameraCalibrator:
    def __init__(
        self,
        fx: float,
        fy: float,
        cx: float,
        cy: float,
        dist_coeffs: Sequence[float],
        image_size: Tuple[int, int],
    ) -> None:
        """
        Inicializa o calibrador com parâmetros intrínsecos e coeficientes de distorção.

        Args:
            fx, fy: focais em pixels
            cx, cy: centro óptico em pixels
            dist_coeffs: lista ou array [k1, k2, p1, p2, k3]
            image_size: tupla (width, height)
        """
        # Matriz intrínseca
        self.intrinsic = np.array([
            [fx,  0, cx],
            [ 0, fy, cy],
            [ 0,  0,  1]
        ], dtype=np.float32)

        # Coeficientes de distorção
        self.dist_coeffs = np.array(dist_coeffs, dtype=np.float32)
        self.image_size = image_size

        # Gera mapas de remapeamento
        self._compute_maps()

    def _compute_maps(self) -> None:
        w, h = self.image_size
        # Matriz de câmera otimizada para reduzir pixels pretos
        self.new_cam_mtx, _ = cv2.getOptimalNewCameraMatrix(
            self.intrinsic, self.dist_coeffs,
            (w, h), 1, (w, h)
        )
        
        R = np.eye(3, dtype=np.float32)
        
        # Mapas de remapeamento
        self.distort_map1, self.distort_map2 = cv2.initUndistortRectifyMap(
            self.intrinsic, self.dist_coeffs, R, self.new_cam_mtx, (w, h), cv2.CV_16SC2
        )
        
    def undistort(self, frame: np.ndarray) -> np.ndarray:
        """
        Aplica o remapeamento pré-computado a cada frame capturado.
        """
        return cv2.remap(
            frame,
            self.distort_map1,
            self.distort_map2,
            interpolation=cv2.INTER_LINEAR
        )