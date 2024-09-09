import sqlite3 as sq
import os
from typing import Tuple
allowed_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.ico']


def do_sql_response(response: str, params=()) -> list:
    with sq.connect('data/projects.db') as con:
        cur = con.cursor()
        cur.execute(response, params)
        return cur.fetchall()


def create_projects_dir():
    """Создаёт папку 'projects', если его нет"""

    if not (os.path.exists('projects')):
        os.mkdir('projects')


def create_tables():
    """Создаёт таблицы в бд, если их нет"""

    with sq.connect('data/projects.db') as con:
        cur = con.cursor()

        is_existing = cur.execute(
            '''
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='projects';
            ''')
        if not (is_existing.fetchone()):
            cur.execute(
                '''
                CREATE TABLE projects (
                name VARCHAR,
                ds_directory TEXT,
                lb_directory TEXT,
                last_image INTEGER DEFAULT 0,
                id INTEGER PRIMARY KEY
                )
                ''')

            cur.execute(
                """
                CREATE TABLE label_files (
                filename TEXT,
                project_id INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
                """)

            cur.execute(
                """
                CREATE TABLE labels (
                name VARCHAR,
                color_hex VARCHAR,
                project_id INTEGER,
                id INTEGER PRIMARY KEY,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
                """)

            cur.execute(
                """
                CREATE TABLE label_objects (
                
                label_id INTEGER,
                x INTEGER,
                y INTEGER,
                width INTEGER,
                height INTEGER,
                label_file TEXT,
                project_id INTEGER,
                FOREIGN KEY (label_id) REFERENCES labels(id),
                FOREIGN KEY (label_file) REFERENCES label_files(name),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
                """)


def add_project(name, lb_directory: str, ds_directory: str):
    """Создаёт запись в бд в таблице проектов"""

    sql = ''' INSERT INTO projects(name, ds_directory, lb_directory)
              VALUES(?,?,?) '''
    do_sql_response(sql, (name, ds_directory, lb_directory))


def get_project_id_by_name(name: str):
    sql = """
          SELECT id FROM projects
          WHERE name LIKE ?
          """
    result = do_sql_response(sql, (name,))
    if result:
        return result[0][0]


def get_label_id_by_name(name: str, project_id: str):
    sql = """
          SELECT id FROM labels
          WHERE name = ? and project_id = ?
          """
    return do_sql_response(sql, (name, project_id))[0][0]


def get_label_name_by_id(id):
    sql = """
          SELECT name FROM labels
          WHERE id = ?
          """
    return do_sql_response(sql, (id, ))[0][0]


def create_label_directory(basedir: str, name: str) -> str:
    """Создаёт первоначальную директорию для меток в папке projects"""

    create_projects_dir()
    d = basedir + '\\projects\\' + name
    if not os.path.exists(d):
        os.mkdir(d)
    return d


def get_shorter_directory(directory: str) -> str:
    """
        Принимает путь к файлу и возвращает его укороченную версию.
        Пример: C:/Users/Admin/Desktop/pyQT/projects/ ->
                .../Admin/Desktop/pyQT/projects/
    """

    directory = directory.replace(os.sep, '/')
    if len(directory) >= 33:
        while len(directory) >= 30:
            directory = directory.split('/', 1)[1]
        directory = '.../' + directory
    return directory


def add_label_file_into_table(filename: str, project_id: int):
    """Добавляет данный о текстовом файле метки в таблицу"""

    sql = ''' INSERT INTO label_files(filename, project_id)
              VALUES(?,?) '''
    do_sql_response(sql, (filename, project_id))


def add_label_files_to_table(directory, project_name):
    project_id = get_project_id_by_name(project_name)
    for path in filter_dir(directory):
        add_label_file_into_table(path, project_id)


def filter_dir(dir_path):
    """ Принимает строку с директорией и возвращает список с путями всех изображений в этой директории"""

    listdir = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]
    new_listdir = []
    for dir_path in listdir:
        _, extension = os.path.splitext(dir_path)
        if extension in allowed_extensions:
            new_listdir.append(dir_path)

    return new_listdir


def check_coincidence(name: str) -> bool:
    """Принимает название проекта. Возвращает True, если совпадение найдено"""

    sql = '''
            SELECT * FROM projects
            WHERE name LIKE ?
            '''
    if do_sql_response(sql, (name,)):
        return True


def _rect_to_yolo(rect, image_size: list) -> tuple:
    """Принимает Qrect и размер изображения. Возвращает информацию о метке в формате YOLO"""

    center_point = rect.center()
    center_x = center_point.x() / image_size[0]
    center_y = center_point.y() / image_size[1]
    width = abs(rect.width() / image_size[0])
    height = abs(rect.height() / image_size[1])
    return str(center_x), str(center_y), str(width), str(height)


def _list_to_yolo(l: list, image_size: list) -> tuple:
    map(int, l)
    center_x = l[0] + l[2] / 2
    center_y = l[1] + l[3] / 2
    width = abs((l[2]) / image_size[0])
    height = abs(l[3] / image_size[1])
    return str(center_x), str(center_y), str(width), str(height)


def add_labels_to_file(path: str, label_data: dict, image_size: list, lb_directory: str):
    """Создаёт текстовые файлы с данными о метке и добавляет информацию в них"""

    filename = os.path.basename(path)
    with open(file=lb_directory+filename, mode='w') as file:
        for label_name, rects in label_data.items():
            for rect in rects:
                if hasattr(rect, 'getRect'):
                    rect_yolo = _rect_to_yolo(rect, image_size)
                else:
                    rect_yolo = _list_to_yolo(rect, image_size)

                str_to_write = str(label_name) + ' ' + ' '.join(rect_yolo) + '\n'
                file.write(str_to_write)


def add_label_object_to_table(name: str, rect, filename: str, project_id: str):
    """ Добавляет новую запись в таблицу label_objects"""
    label_id = get_label_id_by_name(name, project_id)
    params = (label_id,
              rect.x(),
              rect.y(),
              rect.width(),
              rect.height(),
              filename,
              project_id)

    sql = ''' SELECT * from label_objects
              WHERE label_id = ? and x= ? and y = ? and width = ? and height = ? and label_file =? and project_id=?'''

    if not do_sql_response(sql, params):
        sql = ''' INSERT INTO label_objects(label_id, x, y, width, height, label_file, project_id)
                  VALUES(?,?,?,?,?,?,?) '''

        do_sql_response(sql, params)


def add_label_objects_to_table(path, label_data, project_name):
    project_id = get_project_id_by_name(project_name)
    for label_name, rects in label_data.items():
        for rect in rects:
            add_label_object_to_table(label_name, rect, path, project_id)


def _rgb_to_hex(color: tuple) -> str:
    return '#%02x%02x%02x' % color


def _hex_to_rgb(color: str) -> tuple:
    value = color.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def add_label_to_table(name: str, color: tuple, project_id: int):
    color_hex = _rgb_to_hex(color)

    sql = ''' INSERT INTO labels(name, color_hex, project_id )
              VALUES(?,?,?) '''
    do_sql_response(sql, (name, color_hex, project_id))


def add_labels_to_table(data: dict, project_name: str):
    """Добавляет данные о метке в бд(название и цвет)"""
    project_id = get_project_id_by_name(project_name)
    for name, color in data.items():
        add_label_to_table(name, color, project_id)


def set_last_image_to_project(project_name: str, value: int):
    """Устанавливает значение в поле last_image в данных о проекте"""
    project_id = get_project_id_by_name(project_name)
    sql = '''
          UPDATE projects
          SET last_image = ?
          WHERE id = ?
          '''
    do_sql_response(sql, (value, project_id))


def get_labels(project_name: str) -> Tuple[str, tuple]:
    """Принимает название проекта. Возвращает итератор с данными о каждой метке проекта(название и цвет)"""
    project_id = get_project_id_by_name(project_name)
    sql = '''
          SELECT name, color_hex FROM labels
          WHERE project_id LIKE ?
          '''

    result = do_sql_response(sql, (project_id,))
    for name, color in result:
        color = _hex_to_rgb(color)
        yield name, color


def get_projects() -> list:
    """Возвращает данные о всех проектах"""
    sql = """
            SELECT * FROM projects
          """
    return do_sql_response(sql)


def get_project(project_name: str) -> list:
    """Возвращает данные об определенном проекте по заданному имени"""
    project_id = get_project_id_by_name(project_name)
    sql = """
          SELECT * from projects
          WHERE id = ?  
          """

    return do_sql_response(sql, (project_id,))


def get_labels_for_image(path_to_image: str, project_name: str):
    """Принимает имя изображения и название проекта. Возвращает генератор с метками для этого изображения"""
    project_id = get_project_id_by_name(project_name)
    sql = """
          SELECT * from label_objects
          WHERE label_file = ? and project_id = ?  
          """
    results = do_sql_response(sql, (path_to_image, project_id))
    for result in results:
        result = list(result)
        result[0] = get_label_name_by_id(result[0])
        yield result
    return


def get_label_files(project_id) -> list:
    """ Возвращает пути к файлам изображений заданного проекта."""
    sql = '''
          SELECT filename from label_files
          WHERE project_id = ?  
          '''
    return do_sql_response(sql, (project_id,))


def update_project_data(old_name: str, new_name: str, lb_dir: str, old_labels: dict, new_labels: dict):
    """ Обновляет данные о проекте: название, путь к меткам, название и цвет меток.
        В old_labels хранятся метки до обновления, по ним сверяются обновленные метки из new_labels."""
    project_id = get_project_id_by_name(old_name)
    sql = """
          UPDATE projects
          SET name = ?, lb_directory = ?
          WHERE id = ?
          """
    params = (new_name, lb_dir, project_id)
    do_sql_response(sql, params)
    update_labels_data(old_labels, new_labels, project_id)  # обновить существующие метки и оставить только новые
    add_labels_to_table(new_labels, project_name=new_name)  # new_labels содержит теперь обновленную информацию


def update_labels_data(old_labels: dict, new_labels: dict, project_id: str):
    """ Сопоставляет старые метки с обновленными. Обновляет данные существующих
        меток и удаляет их из new_labels, чтобы там остались только созданные метки"""
    for i in range(len(old_labels)):
        old_label = list(old_labels.items())[i]
        new_label = list(new_labels.items())[i]
        del new_labels[new_label[0]]
        label_id = get_label_id_by_name(str(old_label[0]), project_id)
        update_label_data(label_id, new_label)


def update_label_data(label_id: str, data: tuple):
    """ Обновляет значения полей имени и цвета у метки"""
    color_hex = _rgb_to_hex(data[1])
    sql = """
          UPDATE labels
          SET name = ?, color_hex = ?
          WHERE id = ?
          """
    do_sql_response(sql, (data[0], color_hex, label_id))


def delete_project(project_name: str):
    """Удаляет проект из бд"""
    project_id = get_project_id_by_name(project_name)
    sql = """DELETE FROM projects WHERE id = ?"""
    do_sql_response(sql, (project_id,))


def save_all_labels(project_name: str, dir: str):
    """Сохраняет сразу все метки проекта в заданную директорию"""
    project_id = get_project_id_by_name(project_name)
    label_files = get_label_files(project_id)
    for label_file in label_files:
        labels_dict = {}
        labels_data = get_labels_for_image(label_file[0], project_name)
        for label_data in labels_data:

            label_name = label_data[0]
            if label_name not in labels_dict:
                labels_dict[label_name] = []

            labels_dict[label_name].append(label_data[1:5])

        filename = label_file[0].split('.')[0] + '.txt'  # Получаем название файла и меняем расш. на .txt
        add_labels_to_file(filename, labels_dict, [1500, 900], dir)
