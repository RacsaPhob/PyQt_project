from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QShortcut
from templates.create_win import Ui_MainWindow
from app_utils import get_shorter_directory, check_coincidence, create_label_directory
from custom_widgets import LabelCreature
import os
import traceback
import sys
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook
class CreateWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.project_name = ''
        self.lb_directory = ''
        self.ds_directory = ''
        self.setupUi(self)
        self.label_creature = LabelCreature(self)
        self.label_creature.setGeometry(QtCore.QRect(755, 480, 310, 211))

        self.initial_label_directory = os.path.dirname(os.path.abspath(__file__)) + '/projects/'
        self.show_label_directory.setText(get_shorter_directory(self.initial_label_directory))
        self.make_connections()

    def make_connections(self):
        self.directory_but.clicked.connect(self.directory_clicked)
        self.continue_button.clicked.connect(self.continue_clicked)
        self.label_but.clicked.connect(self.labels_clicked)

        back_shortcut = QShortcut(QKeySequence('Esc'), self)
        back_shortcut.activated.connect(self.go_back)

    def directory_clicked(self):
        self.ds_directory = QFileDialog.getExistingDirectory(self)
        if not self.ds_directory:
            return

        self.continue_button.setEnabled(True)
        self.show_images_directory.setText(get_shorter_directory(self.ds_directory))

    def labels_clicked(self):
        self.lb_directory = QFileDialog.getExistingDirectory(self)
        if not self.lb_directory:
            return
        self.show_label_directory.setText(self.lb_directory)

    def continue_clicked(self):
        if self.validate_data():
            if not self.lb_directory:
                self.lb_directory = create_label_directory(os.getcwd(), self.project_name)

            self.main_win.create_project(self.project_name, self.lb_directory, self.ds_directory, self.label_creature.labels)
            self.main_win.show_project(self.project_name)
            self.clean_data()


    def go_back(self):
        self.main_win.show_start()

    def validate_data(self) -> bool:
        """ Проводит проверку всех полей. Если все проверки пройдены возвращает True.
            Иначе False и высылает уведомление об ошибке"""

        self.project_name = self.project_name_edit.text()
        if not self.project_name_edit.text():
            QMessageBox.warning(self, 'invalid project name', 'choose a valid project name')
            return False

        if check_coincidence(self.project_name):
            QMessageBox.warning(self, 'This name is already in use', 'choose another project name')
            return False

        return True

    def clean_data(self):
        self.project_name_edit.setText('')
        self.show_images_directory.setText('/...')
        self.project_name = ''
        self.lb_directory = ''
        self.ds_directory = ''
        self.label_creature = LabelCreature(self)
        self.label_creature.setGeometry(QtCore.QRect(755, 480, 310, 211))
