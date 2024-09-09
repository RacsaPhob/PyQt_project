from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QShortcut
from PyQt5 import QtCore
from templates.project_win import Ui_MainWindow
import traceback
from custom_widgets import LabelPicker, FinishWidget
from canvas import Canvas
from app_utils import (add_labels_to_file, filter_dir, add_label_objects_to_table,
                       get_labels, set_last_image_to_project, get_labels_for_image,
                       save_all_labels)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
import sys


def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook


class ProjectWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, main_win):
        super().__init__()
        self.setupUi(self)
        self.main_win = main_win

        self.listdir = []
        self.rects_dicts = {}
        self.canvas = None
        self.image_count = 0

        self.project_name = ''
        self.directory = ''
        self.current_image_absolute = ''
        self.lb_directory = ''

        self.make_connections()

    def make_connections(self):
        self.PreviousBut.clicked.connect(lambda: self.next_prev_clicked(-1))
        self.NextBut.clicked.connect(lambda: self.next_prev_clicked(1))
        self.CloseBut.clicked.connect(self.main_win.show_start)

        next_shortcut = QShortcut(QKeySequence('n'), self)
        next_shortcut.activated.connect(lambda: self.next_prev_clicked(1))

        back_shortcut = QShortcut(QKeySequence('b'), self)
        back_shortcut.activated.connect(lambda: self.next_prev_clicked(-1))

        for number in range(1, 10):
            number_shortcut = QShortcut(QKeySequence(str(number)), self)
            number_shortcut.activated.connect(lambda n=number: self.number_clicked(n))

        esc_shortcut = QShortcut(QKeySequence('Esc'), self)
        esc_shortcut.activated.connect(self.main_win.show_start)

        self.go_toBut.clicked.connect(self.go_to)
        self.ConfirmBut.clicked.connect(self.finish_pressed)

    def finish_pressed(self):
        widget = FinishWidget(self)
        widget.exec_()


    def number_clicked(self, number):
        """Нажатие на цифры на клавиатуре 0-9"""
        self.label_picker.radio_container.buttons()[number-1].click()


    def keyPressEvent(self, event):
        if event.key() == 16777249:  # Ctrl
            self.canvas.panning = True


    def keyReleaseEvent(self, event):
        if event.key() == 16777249:
            self.canvas.panning = False
    def go_to(self):
        """ Вызывается при нажатии на go_toBut. Берет значение из spinBox и меняет изображение"""
        value = self.spinBox.value()
        self.image_count = value - 1

        # Имитируем нажатие на next или previous, но с шагом 0, т.к. мы уже изменили image_count
        self.next_prev_clicked(0)

    def get_image(self, image_count):
        """ Принимает номер п/п изображения из listdir. Если номер больше длины списка, отчёт идёт сначала.
            Возвращает абсолютный путь к изображению"""

        if image_count >= len(self.listdir):
            image_count = image_count - len(self.listdir) - 1

        current_image = self.listdir[image_count]
        return current_image

    def show_image(self, image_count):
        """ Принимает порядковый номер изображения из listdir. Меняет атрибуты холста под новое изображение"""

        self.current_image_absolute = self.get_image(self.image_count)
        if not (self.current_image_absolute in self.rects_dicts):
            self.rects_dicts[self.current_image_absolute] = {}

        self.canvas.set_image(self.current_image_absolute)
        self.canvas.set_rect_dict(self.rects_dicts[self.current_image_absolute])
        self.canvas.prepare_images([self.get_image(i) for i in range(image_count-3, image_count + 4)])

        self.label.setText(f'{self.image_count+1}/{len(self.listdir)}')

    def save_labels(self, label_data: dict):
        """ Принимает словарь из rects_dict. Вызывает ф-ию из db_utils со всеми параметрами"""

        add_labels_to_file(path=self.listdir[self.image_count].split('.')[0] + '.txt',
                           label_data=label_data,
                           image_size=self.canvas.canvas_size,
                           lb_directory=self.lb_directory + '\\')

        add_label_objects_to_table(path=self.listdir[self.image_count],
                                   label_data=label_data,
                                   project_name=self.project_name)

    def next_prev_clicked(self, action: int):
        """ Вызывается при нажатии на next или previous. Принимает действие(-1, 0, 1) и изменяет image_count,
            чтобы он был в пределах len(self.listdir) и меняет изображение на холсте"""
        self.save_labels(self.rects_dicts[self.current_image_absolute])
        self.image_count += action
        if self.image_count >= len(self.listdir):
            self.image_count = len(self.listdir) - 1

        if self.image_count < 0:
            self.image_count = len(self.rects_dicts) - 1

        self.show_image(self.image_count)

        set_last_image_to_project(self.project_name, self.image_count)

    def complete_project(self, d):
        d = d or self.lb_directory
        save_all_labels(self.project_name,d)

    def set_project(self, name, ds_directory, lb_directory, image_count, *args, **kwargs):
        """ Устанавливает данные о проекте. Принимает название проекта, директорию датасета и меток.
            Создаёт первоначальный холст с первым изображением"""

        self.project_name = name
        self.directory = ds_directory
        self.lb_directory = lb_directory
        self.listdir = filter_dir(ds_directory)
        self.image_count = image_count

        for dir in self.listdir:
            rects_data = get_labels_for_image(dir, self.project_name)
            rects_dict = {}
            for rect_data in rects_data:
                if not rect_data[0] in rects_dict.keys():

                    rects_dict[rect_data[0]] = []

                rect = QtCore.QRect(rect_data[1], rect_data[2], rect_data[3], rect_data[4])
                rects_dict[rect_data[0]].append(rect)
            self.rects_dicts[dir] = rects_dict


        initial_data = get_labels(name)
        self.label_picker = LabelPicker(self, initial_data=initial_data)
        self.label_picker.setGeometry(self.scrollArea.geometry())

        self.canvas = Canvas(self.label_picker, parent=self.widget)

        self.show_image(self.image_count)
        self.canvas.set_rect_dict(self.rects_dicts[self.listdir[self.image_count]])

