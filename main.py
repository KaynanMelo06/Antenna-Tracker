# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()     #win.showFullScreen() # abre em tela cheia  | #win.show() # abre em modo janela
    sys.exit(app.exec_())