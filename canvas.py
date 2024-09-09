from typing import Dict, Union
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PyQt5.QtCore import Qt, QPoint, QRect, QThread, pyqtSignal
import sys
import traceback
from PIL import Image
from io import BytesIO


class ImageThread(QThread):
    signal = pyqtSignal(str, BytesIO)

    def __init__(self, image_path: str, size: tuple):
        super().__init__()
        self.image_path = image_path
        self.size = size

    def run(self):
        image = Image.open(self.image_path)
        image_scaled = image.resize(self.size)

        buffer = BytesIO()
        image_scaled.save(buffer, 'PNG')
        buffer.seek(0)
        self.signal.emit(self.image_path, buffer)


def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook


class Canvas(QLabel):
    def __init__(self, label_widget, parent=None):
        super().__init__(parent)
        self.handle_offset_pos = QPoint()
        self.label_widget = label_widget

        self.pixmap_dict: Dict[str, QPixmap] = {}  # Готовые pixmap`ы с загруженными изображениями
        self.images_dict: Dict[str, Union[BytesIO, QThread]] = {}  # Изображения в виде потока I/O или ссылки на поток QThread
        self.rect_dict: Dict[str, QRect] = {}  # Метки для активного изображения.

        self.canvas_size = (1500, 950)
        self.setFixedSize(*self.canvas_size)

        self.drawing = False
        self.last_point = QPoint()
        self.current_point = QPoint()

        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.panning = False  # Режим панорамы. Пользователь может перемещаться по фото мышью


    def paintEvent(self, event):

        painter = QPainter(self)
        # Рисуем текущее состояние изображения на экран с учетом масштаба и смещения
        source_rect = QRect(self.offset_x, self.offset_y,
                            self.canvas_size[0] / self.scale_factor,
                            self.canvas_size[1] / self.scale_factor)
        painter.drawPixmap(self.rect(), self.temp_pixmap, source_rect)

    def mousePressEvent(self, event):
        """ Если нажата лкм и нет режима панорамы, активируем режим рисования и запрашиваем текущие
            название метки и его цвет"""
        if event.button() == Qt.LeftButton and not (self.panning):
            self.drawing = True
            self.label_text, self.color = self.label_widget.get_active_label()
        self.last_point = event.pos()


    def mouseMoveEvent(self, event):
        """ Вызывается при движении мыши. Если зажата ЛКМ и пользователь выбрал метку,
        сохраняем текущие координаты мыши для второй точки Rect и рисуем его. """
        if self.drawing and self.color:
            self.current_point = event.pos()

            # Рисуем линию на временном изображении
            self.temp_pixmap = self.pixmap.copy()
            self.draw_rect(self.temp_pixmap, self.last_point, self.current_point)

        else:
            # Ручное изменение смещения
            point = event.pos()
            handle_offset_x = (point.x() - self.last_point.x()) / self.scale_factor
            handle_offset_y = (point.y() - self.last_point.y()) / self.scale_factor

            # корректируем смещение с учётом панорамирования
            self.offset_x -= handle_offset_x
            self.offset_y -= handle_offset_y
            self.restrict_offset()

            self.last_point = event.pos()
            self.update()


    def mouseReleaseEvent(self, event):
        """ Вызывается при отжатии кнопок мыши. Если пользователь отжал ЛКМ и до этого нажимал ЛКМ в поле
        холста и имеется активная метка (гарантирует, что пользователь рисовал Rect), рисует Rect на основном
        холсте. """
        if event.button() == Qt.LeftButton and self.drawing and self.color:
            self.drawing = False

            # Сохранение линии на основном изображении
            self.draw_rect(self.pixmap, self.last_point, event.pos())

    def draw_rect(self, pm: QPixmap, point1: QPoint, point2: QPoint):
        """ Принимает pixmap, на котором будет рисоваться Rect (временный или основной), и две точки,
            по координатам которых и будет рисоваться Rect. """
        painter = QPainter(pm)
        painter.setPen(QPen(QColor(*self.color, 255), 5))

        point1_temp = QPoint()  # Создаём новую начальную точку, чтобы не обновлять оригинальную
        point1_temp.setX(point1.x() / self.scale_factor + self.offset_x)
        point1_temp.setY(point1.y() / self.scale_factor + self.offset_y)

        point2.setX(point2.x() / self.scale_factor + self.offset_x)
        point2.setY(point2.y() / self.scale_factor + self.offset_y)
        rect = QRect(point1_temp, point2)

        if pm == self.pixmap:  # Если обновлен основной холст, обновляем словарь с метками для этого изображения
            if not self.label_text in self.rect_dict:
                self.rect_dict[self.label_text] = []
            self.rect_dict[self.label_text].append(rect)

        painter.drawRect(rect)
        self.update()


    def set_image(self, image_path):
        if image_path in self.pixmap_dict:
            self.pixmap = self.pixmap_dict[image_path]
            if image_path in self.images_dict:
                del self.images_dict[image_path]
        else:
            self.pixmap = QPixmap()
            self.pixmap_dict[image_path] = self.pixmap
            buffer = self.images_dict.get(image_path)
            if not isinstance(buffer, BytesIO):
                image = Image.open(image_path)
                image_scaled = image.resize(self.canvas_size)
                buffer = BytesIO()
                image_scaled.save(buffer, 'PNG')
                buffer.seek(0)
            self.pixmap.loadFromData(buffer.getvalue())

        self.temp_pixmap = self.pixmap.copy()
        self.update()

    def restrict_offset(self):
        """ Редактирует смещение так, чтобы оно не выходило за пределы изображения"""
        self.offset_x = max(0, self.offset_x)
        self.offset_y = max(0, self.offset_y)

        max_offset_x = self.temp_pixmap.width() - self.canvas_size[0] / self.scale_factor
        max_offset_y = self.temp_pixmap.height() - self.canvas_size[1] / self.scale_factor

        self.offset_x = min(max_offset_x, self.offset_x)
        self.offset_y = min(max_offset_y, self.offset_y)


    def wheelEvent(self, event):
        """ Обработка событий колесика мыши для изменения масштаба изображения. """
        old_scale = self.scale_factor
        if event.angleDelta().y() > 0 and self.scale_factor < 10:
            self.scale_factor *= 1.1
        elif event.angleDelta().y() < 0 and self.scale_factor > 1:
            self.scale_factor /= 1.1

        # Центрирование изображения относительно точки под курсором мыши
        mouse_pos = event.pos()
        self.offset_x = self.offset_x + (mouse_pos.x() / old_scale - mouse_pos.x() / self.scale_factor)
        self.offset_y = self.offset_y + (mouse_pos.y() / old_scale - mouse_pos.y() / self.scale_factor)

        self.restrict_offset()
        self.update()

    def tread_out(self, path, buffer):
        """ Вызывается когда изображение заканчивает подготовку. Меняет его состояние в images_dict"""
        self.images_dict[path] = buffer

    def prepare_images(self, images: list):
        """ Подготавливает список изображений. Подготовка идёт в отдельном потоке.
            Изначально в images_dict хранится ссылка на поток, а не само изображение"""

        for image_path in images:
            if not (image_path in {**self.images_dict, **self.pixmap_dict}):
                thread = ImageThread(image_path, self.canvas_size)
                thread.signal.connect(self.tread_out)
                thread.start()
                self.images_dict[image_path] = thread

    def set_rect_dict(self, rect_dict: dict):
        """ В rect_dict хранятся раннее созданные пользователем rects, чтобы их выводить,
            на случай если пользователь вернётся к изображению в котором были метки"""

        self.rect_dict = rect_dict
        colors_dict = self.label_widget.labels

        painter = QPainter(self.pixmap)
        for label, rects in self.rect_dict.items():
            color = colors_dict.get(label)
            painter.setPen(QPen(QColor(*color, 255), 5))
            for rect in rects:
                painter.drawRect(rect)

        self.temp_pixmap = self.pixmap.copy()
        self.update()
