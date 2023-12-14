import sys
from PyQt5.QtWidgets import *
from window import AppWindow

app = QApplication(sys.argv)
gui = AppWindow()
gui.show()
sys.exit(app.exec_())