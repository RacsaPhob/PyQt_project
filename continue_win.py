from PyQt5.QtGui import QKeySequence
from templates.continue_win import Ui_MainWindow
import templates.continue_win_rc
from PyQt5.QtWidgets import (QMainWindow, QShortcut, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy)
from app_utils import get_projects, filter_dir, get_project
from PyQt5 import QtGui, QtCore

import traceback
import sys
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook
class ContinueWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, main_win):
        super().__init__()
        self.setupUi(self)
        self.main_win = main_win
        self.row_count = 5
        self.rows = []

        self.h_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.v_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.scroll_layout = QVBoxLayout()

        self.scrollAreaWidgetContents.setLayout(self.scroll_layout)

        self.pushButton.clicked.connect(self.go_back)
        back_shortcut = QShortcut(QKeySequence('Esc'), self)
        back_shortcut.activated.connect(self.go_back)

    def go_back(self):
        self.main_win.show_start()

    def load_projects(self):
        """Загружает данные о проектах, создаёт виджеты и добавляет их в слой"""
        for row in self.rows:
            while row.layout().count():  # пока в слое есть виджеты
                child = row.layout().takeAt(0)  # взять первый виджет из слоя
                if child and child.widget():  # проверка, что это widget а не item
                    child.widget().deleteLater()
            self.scroll_layout.removeWidget(row)
        self.rows.clear()
        self.make_new_row()

        projects = get_projects()
        count = 0
        for name, dir, _, image_count, id in projects:

                count += 1
                if len(self.projects_row.children()) % (self.row_count + 1) == 0:
                    self.projects_row_layout.addItem(self.h_spacer)

                    self.make_new_row()

                dirs = filter_dir(dir)
                if len(dirs) > 0:
                    curent_image = dirs[image_count]
                else:
                    curent_image = ':/icons/images/image_not_found.jpg'
                widget = self.make_project_widget(name, curent_image)
                self.projects_row_layout.addWidget(widget)


        self.projects_row_layout.addItem(self.h_spacer)

    def make_new_row(self):
        """ Создаёт новый слой для виджетов проектов"""
        self.scroll_layout.removeItem(self.v_spacer)
        self.projects_row = QWidget()
        self.projects_row_layout = QHBoxLayout()
        self.projects_row.setLayout(self.projects_row_layout)
        self.scroll_layout.addWidget(self.projects_row)
        self.rows.append(self.projects_row)
        self.scroll_layout.addItem(self.v_spacer)

    def make_project_widget(self, name: str, image_path: str) -> QWidget:
        project_widget = QWidget()
        project_widget_layout = QVBoxLayout()

        project_label = QLabel(name)
        project_label.setAlignment(QtCore.Qt.AlignCenter)

        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Demi")
        font.setPointSize(16)

        project_label.setFont(font)

        image_pixmap = QtGui.QPixmap()
        image_pixmap.load(image_path)
        image_pixmap = image_pixmap.scaled(283, 283, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

        image_widget = QLabel()
        image_widget.setPixmap(image_pixmap)

        # Переопределяем метод вызываемый при нажатии по виджету
        image_widget.mousePressEvent = lambda _: self.main_win.show_project(name)

        settings_but = QPushButton()
        settings_but.clicked.connect(lambda: self.go_settings(name))

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/settings_1264592.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        settings_but.setIcon(icon)

        project_widget_layout.addWidget(project_label)
        project_widget_layout.addWidget(image_widget)
        project_widget_layout.addWidget(settings_but)

        project_widget.setLayout(project_widget_layout)

        return project_widget

    def go_settings(self, project_name):
        self.main_win.show_settings(project_name)
