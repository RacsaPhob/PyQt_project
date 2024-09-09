from PyQt5 import QtCore

from custom_widgets import LabelCreature
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QShortcut, QPushButton
from app_utils import (check_coincidence, get_project, get_labels,
                       get_shorter_directory, update_project_data, delete_project)
from create_win import CreateWindow
import traceback
import sys
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook

style = '''QPushButton {
                background-color: red;
                border: 1px solid black;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }'''
class SettingsWindow(CreateWindow):
    def __init__(self, main_win):
        super().__init__(main_win)

        self.continue_button.setText('Save')
        self.continue_button.setEnabled(True)
        self.continue_button.clicked.disconnect()
        self.continue_button.clicked.connect(self.save)

        self.directory_but.setEnabled(False)

        self.continue_button.move(750, 790)
        self.delete_button = QPushButton('delete', self)
        self.delete_button.setGeometry(750, 710, 321, 61)

        self.delete_button.setStyleSheet(style)
        self.delete_button.clicked.connect(self.delete_project)

    def go_back(self):
        self.main_win.show_continue()

    def delete_project(self):
        """Удаляет проект из базы данных"""
        success = True
        try:
            delete_project(self.old_name)
        except:
            success = False
            QMessageBox.critical(self, 'Ошибка', 'Произошла ошибка при удалении проекта')

        if success:
            self.main_win.show_continue()


    def set_project(self, project_name):
        """Подставляет данные проекта в форму. Принимает название проекта."""
        self.old_name = project_name
        project_data = get_project(project_name)[0]

        self.project_name_edit.setText(project_name)
        self.ds_dir = project_data[1]
        self.show_images_directory.setText(get_shorter_directory(self.ds_dir))

        self.lb_dir = project_data[2]
        self.show_label_directory.setText(get_shorter_directory(self.lb_dir))

        self.label_creature.deleteLater()
        self.label_creature = LabelCreature(self, get_labels(project_name))
        self.label_creature.setGeometry(QtCore.QRect(755, 480, 310, 211))
        self.old_labels = self.label_creature.labels.copy()

    def save(self):
        """Проверяет и сохраняет в бд данные"""
        new_name = self.project_name_edit.text()
        # если название изменено, но оно уже есть в бд, выводит ошибку
        if check_coincidence(new_name) and new_name!= self.old_name:
            QMessageBox.warning(self, 'This name is already in use', 'choose another project name')
            return

        if not new_name:
            QMessageBox.warning(self, 'invalid project name', 'choose a valid project name')
            return

        self.lb_directory = self.lb_directory or self.lb_dir

        self.ds_directory = self.ds_directory or self.ds_dir

        update_project_data(self.old_name, new_name, self.lb_directory, self.old_labels, self.label_creature.labels)

