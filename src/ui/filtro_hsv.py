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
        central = QtWidgets.QWidget(MainWindow)
        layout = QtWidgets.QVBoxLayout(central)

        # Preview label
        self.label_output = QtWidgets.QLabel("Preview")
        self.label_output.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_output)

        # Grid of sliders
        grid = QtWidgets.QGridLayout()
        self.sliders = {}
        components = [("h_min", 179), ("h_max", 179), ("s_min", 255),
                      ("s_max", 255), ("v_min", 255), ("v_max", 255)]
        for i, (name, maxv) in enumerate(components):
            lbl = QtWidgets.QLabel(f"{name.upper()}: 0")
            sld = QtWidgets.QSlider(Qt.Horizontal)
            sld.setMaximum(maxv)
            if "max" in name:
                sld.setValue(maxv)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(sld, i, 1)
            self.sliders[name] = (lbl, sld)

        # Reset and Apply buttons
        self.btn_reset = QtWidgets.QPushButton("Reset")
        self.btn_apply = QtWidgets.QPushButton("Apply")
        grid.addWidget(self.btn_reset, len(components), 0)
        grid.addWidget(self.btn_apply, len(components), 1)
        layout.addLayout(grid)

        # Color selection combo
        self.combo_filtro = QtWidgets.QComboBox()
        self.combo_filtro.addItems(["laranja", "verde", "rosa", "amarelo"])
        layout.addWidget(self.combo_filtro)

        MainWindow.setCentralWidget(central)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

class HSVFilterWindow(QtWidgets.QMainWindow):
    valores_aplicados = pyqtSignal(dict)

    def __init__(self, filtros_iniciais, parent=None):
        super().__init__(parent)
        self.ui = Ui_HSVFilterWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("HSV Calibration")

        # Shared filters dict
        self.filtros = filtros_iniciais

        # Connect signals
        self.ui.combo_filtro.currentTextChanged.connect(self.load_filter)
        for name, (lbl, sld) in self.ui.sliders.items():
            sld.valueChanged.connect(lambda val, n=name: self.on_slider_change(n, val))
        self.ui.btn_reset.clicked.connect(self.reset_sliders)
        self.ui.btn_apply.clicked.connect(self.apply_filters)

        # Live preview timer
        self.current_frame = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(60)

        self.load_filter(self.ui.combo_filtro.currentText())

    def load_filter(self, filter_name):
        # Load values into sliders and labels
        settings = self.filtros[filter_name]
        if filter_name not in self.filtros:
            return
        settings = self.filtros[filter_name]
        for name, (lbl, sld) in self.ui.sliders.items():
            sld.blockSignals(True)
            sld.setValue(settings[name])
            lbl.setText(f"{name.upper()}: {settings[name]}")
            sld.blockSignals(False)

    def on_slider_change(self, name, value):
        # Update dict and label
        current = self.ui.combo_filtro.currentText()
        self.filtros[current][name] = value
        lbl, _ = self.ui.sliders[name]
        lbl.setText(f"{name.upper()}: {value}")

    def reset_sliders(self):
        # Reset sliders to defaults
        for name, (lbl, sld) in self.ui.sliders.items():
            default = 0 if "min" in name else sld.maximum()
            sld.setValue(default)

    def apply_filters(self):
        # Emit updated filters and close
        self.valores_aplicados.emit(self.filtros)
        self.close()

    def receber_frame(self, frame):
        # Receive frame for preview
        self.current_frame = frame.copy()

    def update_preview(self):
        # Apply filter to frame and display
        if self.current_frame is None:
            return
        hsv = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2HSV)
        name = self.ui.combo_filtro.currentText()
        vals = self.filtros[name]
        low = np.array([vals["h_min"], vals["s_min"], vals["v_min"]])
        high = np.array([vals["h_max"], vals["s_max"], vals["v_max"]])
        mask = cv2.inRange(hsv, low, high)
        result = cv2.bitwise_and(self.current_frame, self.current_frame, mask=mask)

        rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img).scaled(
            self.ui.label_output.width(),
            self.ui.label_output.height(),
            Qt.KeepAspectRatio
        )
        self.ui.label_output.setPixmap(pix)
    
    def closeEvent(self, event):
        super().closeEvent(event)
        # avisa o parent de que não há mais janela de calibração aberta
        if hasattr(self.parent(), 'calibration_window'):
            self.parent().calibration_window = None