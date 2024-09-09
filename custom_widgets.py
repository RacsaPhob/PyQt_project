from templates.create_label import Ui_Form as CreateLabelUi
from templates.save_widget import Ui_Form as SaveWidgetUi
from typing import Union, Tuple
import templates.project_win_rc
import templates.create_win_rc
from app_utils import get_shorter_directory
from PyQt5.QtWidgets import QDialog, QMessageBox

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui


class CreateLabel(QDialog, CreateLabelUi):
    def __init__(self, initial_text='', initial_color=(255, 255, 255), labels={}, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.initial_text = initial_text
        self.labels = labels

        self.pushButton.clicked.connect(self.confirm)
        self.BlueSlider.valueChanged.connect(self.slider_changed)
        self.RedSlider.valueChanged.connect(self.slider_changed)
        self.GreenSlider.valueChanged.connect(self.slider_changed)

        self.is_confirmed = False

        self.textEdit.setText(initial_text)
        self.RedSlider.setValue(initial_color[0])
        self.GreenSlider.setValue(initial_color[1])
        self.BlueSlider.setValue(initial_color[2])

    def slider_changed(self):
        color = self.get_color()
        if color:
            self.widget.setStyleSheet(f'background-color: rgb{color}')

    def validate(self):
        text = self.get_label_name()
        if not text:
            QMessageBox.warning(self, 'invalid label name', 'Choose a valid label name')
            return False

        if not (text == self.initial_text):
            for label in self.labels:
                if label[0] == text:
                    QMessageBox.warning(self, 'invalid label name', 'This label name already exist')
                    return False
        return True

    def confirm(self):
        """ Вызывается при нажатии на кнопку 'Confirm' """

        if self.validate():
            self.is_confirmed = True
            self.close()

    def closeEvent(self, event):
        """
            Если пользователь нажал на 'закрыть окно',
            методы-гетеры переопределяются, чтобы
            они возвращали None
        """

        if not self.is_confirmed:
            self.get_label_name = lambda: None
            self.get_color = lambda: None

        event.accept()

    def get_color(self) -> tuple:
        red = self.RedSlider.value()
        green = self.GreenSlider.value()
        blue = self.BlueSlider.value()
        return red, green, blue

    def get_label_name(self) -> str:
        return self.textEdit.toPlainText()


class LabelWidgetBase(QtWidgets.QScrollArea):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.labels = {}  # Здесь хранятся все метки с их названиями и цветов в виде [['text'], (color)],]

        self.plus_icon = QtGui.QIcon()
        self.edit_icon = QtGui.QIcon()
        self.plus_icon.addPixmap(QtGui.QPixmap(":/icons/images/plus_icon.png"))
        self.edit_icon.addPixmap(QtGui.QPixmap(":/icons/images/edit_icon.png"))

        self.setWidgetResizable(True)
        self.setObjectName("scrollArea")

        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_content = QtWidgets.QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_content)
        self.setWidget(self.scroll_widget)

        self.h_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.v_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

    def get_instance_from_layout(self, layout, instance_class):
        """Принимает слой и класс объекта который нужно вернуть"""
        children = layout.children()
        for child in children:

            if type(child) is instance_class:
                return child


class LabelCreature(LabelWidgetBase):

    def __init__(self, main_win, initial_data=()):
        super().__init__(main_win)
        label_widget_layout = QtWidgets.QHBoxLayout()

        self.LabelColor = QtWidgets.QPushButton()
        self.LabelColor.setText('')
        self.LabelColor.setIcon(self.plus_icon)
        self.LabelColor.setIconSize(QtCore.QSize(20, 20))

        # label_widget_layout.addItem(self.h_spacer)
        label_widget_layout.addWidget(self.LabelColor)

        self.initial_label_widget = QtWidgets.QWidget()
        self.initial_label_widget.setLayout(label_widget_layout)

        self.scroll_content.addWidget(self.initial_label_widget)

        self.scroll_content.addItem(self.v_spacer)

        self.LabelColor.clicked.connect(lambda: self.color_clicked(instance=self.LabelColor))

        self.set_initial_data(initial_data)

    def color_clicked(self, *args, instance):

        layout = instance.parent()
        Qlabel = self.get_instance_from_layout(layout, QtWidgets.QLabel)

        if not Qlabel:  # Если пользователь создаёт метку
            create_label = CreateLabel(labels=self.labels)
        # Если пользователь изменяет существующую метку
        # получаем первоначальный цвет и текст который будет в виджете
        else:
            label_name = self.get_instance_from_layout(layout, QtWidgets.QLabel).text()
            initial_color = self.labels.get(label_name)

            create_label = CreateLabel(initial_text=label_name, initial_color=initial_color, labels=self.labels)

        create_label.exec_()
        color = create_label.get_color()
        name = create_label.get_label_name()

        if name:
            if Qlabel:  # Если была изменена существующая метка, сохраняем изменения
                if name != label_name:
                    self.labels.pop(label_name)

            else:
                self.add_rest_show_label_widgets(layout)
                self.add_new_create_label_but()

            self.labels[name] = color
            self.change_show_label_widgets(layout, name, color)

    def add_rest_show_label_widgets(self, layout):
        for child in layout.children():
            if type(child) is QtWidgets.QPushButton:
                child.deleteLater()

        label_text = QtWidgets.QLabel(text='Create label', )
        label_text.setAlignment(QtCore.Qt.AlignRight)
        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Demi")
        font.setPointSize(15)
        label_text.setFont(font)

        label_color = QtWidgets.QWidget()

        label_but = QtWidgets.QPushButton()
        label_but.setIcon(self.edit_icon)
        label_but.setIconSize(QtCore.QSize(20, 20))
        label_but.clicked.connect(lambda: self.color_clicked(instance=label_but))

        layout.layout().addWidget(label_text, stretch=5)
        layout.layout().addWidget(label_color, stretch=2)
        layout.layout().addWidget(label_but, stretch=1)

    def change_show_label_widgets(self, layout, name, color):
        """ Изменяет виджеты чтобы они отображали изменённые данные метки"""

        ShowLabel = self.get_instance_from_layout(layout, QtWidgets.QLabel)
        ShowColor = self.get_instance_from_layout(layout, QtWidgets.QWidget)

        ShowLabel.setText(name)
        style = f'background-color: rgb{color}'
        ShowColor.setStyleSheet(style)

    def add_new_create_label_but(self):
        """ Добавляет в конец scroll area кнопку для создания новой метки"""

        label_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()

        label_but = QtWidgets.QPushButton()
        label_but.setIcon(self.plus_icon)
        label_but.setIconSize(QtCore.QSize(20, 20))
        label_but.clicked.connect(lambda: self.color_clicked(instance=label_but))

        # layout.addItem(self.h_spacer)
        layout.addWidget(label_but)

        label_widget.setLayout(layout)

        self.scroll_content.removeItem(self.v_spacer)
        self.scroll_content.addWidget(label_widget)
        self.scroll_content.addItem(self.v_spacer)

    def set_initial_data(self, initial_data):
        self.initial_label_widget.deleteLater()
        self.scroll_content.removeItem(self.v_spacer)

        for name, color in initial_data:
            layout = QtWidgets.QHBoxLayout()
            widget = QtWidgets.QWidget()
            widget.setLayout(layout)
            self.labels[name] = color
            self.add_rest_show_label_widgets(widget)
            self.change_show_label_widgets(widget, name, color)
            self.scroll_content.addWidget(widget)
        self.add_new_create_label_but()


class LabelPicker(LabelWidgetBase):
    def __init__(self, main_win, initial_data=()):
        super().__init__(main_win)
        self.radio_container = QtWidgets.QButtonGroup()

        for name, color in initial_data:
            self.labels[name] = color
            self.add_rest_show_label_widgets(name, color)

        self.scroll_content.addItem(self.v_spacer)

    def add_rest_show_label_widgets(self, name, color):
        layout = QtWidgets.QHBoxLayout()
        radio = QtWidgets.QRadioButton()
        self.radio_container.addButton(radio)
        radio.click()

        label_text = QtWidgets.QLabel(text=name)
        label_text.setAlignment(QtCore.Qt.AlignRight)
        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Demi")
        font.setPointSize(15)
        label_text.setFont(font)

        label_color = QtWidgets.QWidget()
        style = f'background-color: rgb{color}'
        label_color.setStyleSheet(style)

        layout.layout().addWidget(radio, stretch=1)
        layout.layout().addWidget(label_text, stretch=5)
        layout.layout().addWidget(label_color, stretch=2)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.scroll_content.addWidget(widget)

    def get_active_label(self) -> Union[Tuple[None, None], Tuple[str, tuple]]:
        """ Ищет слой с активным RadioButton и возвращает информацию о метке с неё"""
        r_buttons = self.radio_container.buttons()
        if not r_buttons:
            return None, None

        for radio in r_buttons:
            if radio.isChecked():
                layout = radio.parent()
                show_label = self.get_instance_from_layout(layout, QtWidgets.QLabel)
                label_text = show_label.text()
                label_color = self.labels.get(label_text)
                return label_text, label_color


class FinishWidget(QDialog, SaveWidgetUi):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.d = ''
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/images/directory-Photoroom.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(50, 50))

        self.pushButton.clicked.connect(self.dir_clicked)
        self.pushButton_2.clicked.connect(self.save)

    def dir_clicked(self):
        self.d = QtWidgets.QFileDialog.getExistingDirectory(self)
        d_shorted = get_shorter_directory(self.d)
        self.label_2.setText(d_shorted)

    def save(self):
        self.parent.complete_project(self.d)
        self.close()
