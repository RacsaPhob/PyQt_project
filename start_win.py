from PyQt5.QtWidgets import QMainWindow
from templates.start_win import Ui_MainWindow
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from pyautogui import size
size = size()


class StartWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.setupUi(self)

        self.mainLabel.setGeometry(0, 0, size[0], 250)
        self.label.setGeometry(0, size[1] - 250, size[0], 250)

        self.make_connections()

    def make_connections(self):
        self.createButton.clicked.connect(self.create_clicked)
        self.proceedButton.clicked.connect(self.proceed_clicked)

        esc_shortcut = QShortcut(QKeySequence('Esc'), self)
        esc_shortcut.activated.connect(self.main_win.close)

    def create_clicked(self):
        self.main_win.show_create()

    def proceed_clicked(self):
        self.main_win.show_continue()
