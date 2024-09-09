from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from start_win import StartWindow
from create_win import CreateWindow
from project_win import ProjectWindow
from continue_win import ContinueWindow
from settings_win import SettingsWindow
from app_utils import (create_tables, add_project, add_label_files_to_table,
                       create_projects_dir, get_project, add_labels_to_table)
from PyQt5.QtGui import QIcon
import sys

import templates.icon


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.showMaximized()
        self.setMinimumSize(1920, 1080)
        self.setWindowIcon(QIcon(":/icon/images/main_icon.ico"))

        self.start_win = StartWindow(self)
        self.create_win = CreateWindow(self)
        self.project_win = ProjectWindow(self)
        self.continue_win = ContinueWindow(self)
        self.settings_win = SettingsWindow(self)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.start_win)
        self.stacked_widget.addWidget(self.create_win)
        self.stacked_widget.addWidget(self.project_win)
        self.stacked_widget.addWidget(self.continue_win)
        self.stacked_widget.addWidget(self.settings_win)

        self.setCentralWidget(self.stacked_widget)
        create_projects_dir()
        create_tables()

    def show_create(self):
        self.stacked_widget.setCurrentWidget(self.create_win)

    def show_start(self):
        self.stacked_widget.setCurrentWidget(self.start_win)

    def create_project(self, project_name, label_directory, dataset_directory, labels):
        add_project(project_name, label_directory, dataset_directory)
        add_label_files_to_table(dataset_directory, project_name)
        add_labels_to_table(labels, project_name)

    def show_project(self, name=''):
        if name:
            data = get_project(name)[0]
            self.project_win.set_project(*data)
        self.stacked_widget.setCurrentWidget(self.project_win)

    def show_continue(self):
        self.continue_win.load_projects()
        self.stacked_widget.setCurrentWidget(self.continue_win)
        self.stacked_widget.setCurrentWidget(self.continue_win)

    def show_settings(self, project_name):
        self.settings_win.set_project(project_name)
        self.stacked_widget.setCurrentWidget(self.settings_win)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
