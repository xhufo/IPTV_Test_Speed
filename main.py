import sys, os

from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

basedir = os.path.dirname(__file__)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setWindowIcon(QIcon(os.path.join(basedir, "icons", "kenan.ico")))
    # app.setWindowIcon(QtGui.QIcon('kenan.ico'))
    #print(os.path.join(basedir, "icons", "kenan.ico"))
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
