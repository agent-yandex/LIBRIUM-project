from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sqlite3
import os
import fitz
import datetime
import shutil
from werkzeug.security import generate_password_hash, check_password_hash


class AddError(Exception):
    def message(self):
        return 'Введите название'


class PushButton(QPushButton):
    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(size.height() * 2)
        size.setHeight(size.height() * 2)
        return size


class PasswordError(Exception):
    pass


class LenNewPasswordError(PasswordError):
    def message(self):
        return 'Слишком короткий пароль!'


class SimpleNewPasswordError(PasswordError):
    def message(self):
        return 'Слишком простой пароль!'


class UnequalNewPassword(PasswordError):
    def message(self):
        return 'Пароли не равны!'


class LoginError(Exception):
    pass


class RepetitiveLoginError(LoginError):
    def message(self):
        return 'Такой логин уже существует!'


class FailureLoginError(LoginError):
    def message(self):
        return 'Введите логин!'


class EnterError(Exception):
    def message(self):
        return 'Неверный логин или пароль!'


class Window(QMainWindow):
    def __init__(self):
        super().__init__(windowTitle='LIBRIUM')
        self.setMinimumSize(QSize(1000, 500))
        self.initUI()

    def initUI(self):
        '''объявление пунктов меню'''
        self.now_login = ''
        self.menuBar().setNativeMenuBar(False)
        self.menuBar().addAction('Главное', self.main_window)
        self.menuBar().addAction(
            'Войти / Регистрация', self.enter_window)
        self.menuBar().addAction('About', qApp.aboutQt)
        self.findChild(QAction).setEnabled(False)
        try:
            os.mkdir('Images')
        except Exception:
            pass
        self.hello_page()

    def hello_page(self):
        '''стартовая страница при загрузке приложения'''
        widget = QWidget()
        image_layout = QVBoxLayout()
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignVCenter)
        image = QImage('system/logo.png').scaled(217, 50)
        label = QLabel(pixmap=QPixmap(image))

        title = QLabel('Проект LIBRIUM')
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        info_layout.addWidget(title, alignment=Qt.AlignCenter)
        info_layout.addWidget(QLabel('Наша команда приветсвует Вас!'),
                              alignment=Qt.AlignCenter)
        info_layout.addWidget(QLabel(''))
        info_layout.addWidget(
            QLabel('Целью проекта LIBRIUM является создание оптимальных условий для',
                   alignment=Qt.AlignCenter))
        info_layout.addWidget(
            QLabel('хранения грамот, дипломов, сертификатов и дургих достижений.'),
            alignment=Qt.AlignCenter)
        info_layout.addWidget(QLabel(''))
        info_layout.addWidget(
            QLabel('Благодаря этому приложению Вам открывается широкий спектр для'),
            alignment=Qt.AlignCenter)
        info_layout.addWidget(
            QLabel('удобного, быстрого и надежного сбережения Ваших наград.'),
            alignment=Qt.AlignCenter)
        info_layout.addWidget(QLabel(''))
        slogan = QLabel('С LIBRIUM Ваши победы в надежных руках!')
        font = slogan.font()
        font.setBold(True)
        slogan.setFont(font)
        info_layout.addWidget(slogan, alignment=Qt.AlignCenter)

        image_layout.addLayout(info_layout)
        image_layout.addWidget(label, alignment=Qt.AlignLeft | Qt.AlignBottom)
        widget.setLayout(image_layout)
        self.setCentralWidget(widget)

        self.statusBar().showMessage(
            'Для использования войдите или зарегистрируйтесь')
        self.paint_statusBar(self.statusBar())

    def main_window(self):
        '''основна страница проекта'''
        self.statusBar().showMessage(f'User - {self.now_login}')
        self.paint_statusBar(self.statusBar(), False)
        query = '''
            SELECT image FROM Portfolio, UserID
            WHERE user = UserID.id
            AND UserID.login = ?'''
        with sqlite3.connect('librium2.db') as con:
            self.result = [i[0] for i in con.execute(query,
                                                     (self.now_login, )).fetchall()][::-1]
        self.end_variants = []
        self.filters = []

        self.setMinimumSize(QSize(1000, 500))

        # окно с фильтрами
        widget = QWidget()
        self.setCentralWidget(widget)
        self.main_layout = QHBoxLayout()
        self.actions_layout = QVBoxLayout()
        self.viewer_layout = QVBoxLayout()
        self.filter_group = QGroupBox('Фильтры')
        filter_layout = QVBoxLayout()
        filter_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self.actions_layout)
        self.main_layout.addLayout(self.viewer_layout)

        '''установка фильтров'''

        self.actions_layout.addWidget(self.filter_group)
        self.actions_layout.addStretch()

        # фильтр по дате
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignLeft)
        self.date1 = QDateTimeEdit(QDate.currentDate(),
                                   calendarPopup=True)
        self.date2 = QDateTimeEdit(QDate.currentDate(),
                                   calendarPopup=True)
        row.addWidget(QCheckBox('Дата', clicked=self.changed_check))
        row.addWidget(self.date1)
        row.addWidget(QLabel('по'))
        row.addWidget(self.date2)
        filter_layout.addLayout(row)

        # фильтр по учреждению
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignLeft)
        row.addWidget(QCheckBox('Учреждение', clicked=self.changed_check))
        self.institutions = QComboBox()
        query = '''SELECT title FROM Institution'''
        with sqlite3.connect('librium2.db') as con:
            titles = con.execute(query).fetchall()
        self.institutions.addItems(i[0] for i in titles)
        row.addWidget(self.institutions)
        filter_layout.addLayout(row)

        # фильтр по важности
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignLeft)
        row.addWidget(QCheckBox('Важность', clicked=self.changed_check))
        self.importance = QComboBox()
        self.importance.addItems(('Высокая', 'Средняя', 'Низкая'))
        row.addWidget(self.importance)
        filter_layout.addLayout(row)

        # фильтр по оригинальности
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignLeft)
        row.addWidget(QCheckBox('Оригинальность',
                                clicked=self.changed_check))
        self.originaly = QComboBox()
        self.originaly.addItems(('Копия', 'Оригинал'))
        row.addWidget(self.originaly)
        filter_layout.addLayout(row)

        # фильтр по предмету
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignLeft)
        row.addWidget(QCheckBox('Предмет', clicked=self.changed_check))
        self.category = QComboBox()
        query = '''SELECT title FROM Category'''
        with sqlite3.connect('librium2.db') as con:
            categories = con.execute(query).fetchall()
        self.category.addItems(i[0] for i in categories)
        row.addWidget(self.category)
        filter_layout.addLayout(row)

        self.filter_group.setLayout(filter_layout)

        self.create_port_button = PushButton('Создать портфолио',
                                             clicked=self.create_port)
        self.create_port_button.setStyleSheet(
            '''QPushButton {background-color: rgb(30, 144, 255);
                border-radius: 11px}''')
        self.create_port_button.setAutoDefault(False)
        self.actions_layout.addWidget(self.create_port_button)

        '''создание окна просмотра дипломов'''

        self.scroll = QScrollArea()
        self.viewer_layout.addWidget(self.scroll)
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)
        self.scroll_widget.setLayout(self.scroll_layout)

        for i in range(len(self.result)):
            name = self.result[i]
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignCenter)

            check = QCheckBox(str(i), clicked=self.choose_any)
            check.setStyleSheet("""QCheckBox{font-size:1px;
                color:white}""")

            row.addWidget(check)
            but_image = QPushButton(str(i), clicked=self.info_dialog)
            but_image.setIcon(QIcon(f'Images/{self.now_login}/{name}'))
            but_image.setIconSize(QSize(391, 594))
            but_image.setStyleSheet('''QPushButton{border: 0px solid;
                font-size:1px; color:white}''')
            row.addWidget(but_image)
            self.scroll_layout.addLayout(row)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(QPushButton('+ Добавить',
                                             clicked=self.add_document_dialog))
        buttons_layout.addWidget(QPushButton('Удалить выбранные',
                                             clicked=self.delete_fails))
        buttons_layout.addWidget(QCheckBox('Выделить все',
                                           clicked=self.choose_any))
        self.viewer_layout.addLayout(buttons_layout)

        widget.setLayout(self.main_layout)

    def delete_fails(self):
        query = '''
            DELETE FROM Portfolio
            WHERE image = ?
            AND user = (SELECT id FROM UserID WHERE login = ?)'''
        for image in self.end_variants:
            with sqlite3.connect('librium2.db') as con:
                con.execute(query, (image, self.now_login))
                os.remove(f"Images/{self.now_login}/{image}")
        self.end_variants = []
        query = '''
            SELECT image FROM Portfolio, UserID
            WHERE user = UserID.id
            AND UserID.login = ?'''
        with sqlite3.connect('librium2.db') as con:
            self.result = [i[0] for i in con.execute(query,
                                                     (self.now_login, )).fetchall()][::-1]
        self.update_viewer()

    def info_dialog(self):
        '''диалоговое окно со всей информацией о дипломе'''
        dialog = QDialog()
        image_layout = QVBoxLayout()
        image_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        dialog.setLayout(image_layout)

        name = self.result[int(self.sender().text())]
        image = QImage(f'Images/{self.now_login}/{name}').scaled(300, 300*2**0.5)
        image_layout.addWidget(QLabel(pixmap=QPixmap(image)))

        query = '''
            SELECT name, data, Institution.title, Importance.title,
            Originaly.title, Category.title 
            FROM Portfolio, Institution, Importance, Originaly, Category
            WHERE image = ?
            AND institute = Institution.id
            AND importance = Importance.id
            AND originality = Originaly.id
            AND category = Category.id
        '''
        with sqlite3.connect('librium2.db') as con:
            result = con.execute(query, (name, )).fetchall()[0]
        names = ['Название:', 'Дата:', 'Учреждение:', 'Важность:',
                 'Оригинальность:', 'Предмет:']

        image_layout.addLayout(layout)

        for i in range(len(names)):
            label = QLabel(names[i])
            label.setStyleSheet(
                'QLabel{color: rgb(49, 104, 244);font-weight: bold}')
            layout.addWidget(label, i, 0)

        for i in range(len(result)):
            layout.addWidget(QLabel(result[i]), i, 1)

        dialog.exec()

    def add_document_dialog(self):
        '''диалоговое окно для добавления награды в приложение'''
        self.file_name = ''
        dialog = QDialog()
        image_layout = QVBoxLayout()
        image_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        dialog.setLayout(image_layout)

        image_layout.addWidget(QPushButton('Загрузить документ',
                                           clicked=self.get_image_file))
        image_layout.addWidget(QPushButton('Скрыть',
                                           clicked=self.get_image_file))
        self.image_label = QLabel()
        image_layout.addWidget(self.image_label)
        image_layout.addLayout(layout)

        layout.addWidget(QLabel('Название'), 0, 0)
        self.name = QLineEdit()
        layout.addWidget(self.name, 0, 1, alignment=Qt.AlignCenter)

        layout.addWidget(QLabel('Дата получения'), 1, 0)
        self.date = QDateTimeEdit(QDate.currentDate(),
                                  calendarPopup=True)
        layout.addWidget(self.date, 1, 1)

        query = '''SELECT title FROM Institution'''
        with sqlite3.connect('librium2.db') as con:
            institutions = [i for i in con.execute(query)]
        self.institutions_count = len(institutions)

        self.institutions_add = QComboBox()
        self.institutions_add.addItems(i[0] for i in institutions)
        layout.addWidget(QLabel('Учреждение'), 2, 0)
        layout.addWidget(self.institutions_add, 2, 1)

        self.new_institution = QLineEdit()
        layout.addWidget(self.new_institution, 3, 0, alignment=Qt.AlignCenter)
        layout.addWidget(QPushButton('Добавить учреждение',
                                     clicked=self.add_institution), 3, 1)

        layout.addWidget(QLabel('Важность'), 4, 0)
        self.importance_new = QComboBox()
        self.importance_new.addItems(('Высокая', 'Средняя', 'Низкая'))
        layout.addWidget(self.importance_new, 4, 1)

        layout.addWidget(QLabel('Оригинальность'), 5, 0)
        self.original_new = QComboBox()
        self.original_new.addItems(('Копия', 'Оригинал'))
        layout.addWidget(self.original_new, 5, 1)

        query = '''SELECT title FROM Category'''
        with sqlite3.connect('librium2.db') as con:
            categories = [i for i in con.execute(query)]
        self.categories_count = len(categories)

        self.categories_add = QComboBox()
        self.categories_add.addItems(i[0] for i in categories)
        layout.addWidget(QLabel('Предмет'), 6, 0)
        layout.addWidget(self.categories_add, 6, 1)

        self.new_category = QLineEdit()
        layout.addWidget(self.new_category, 7, 0, alignment=Qt.AlignCenter)
        layout.addWidget(QPushButton('Добавить прдемет',
                                     clicked=self.add_category), 7, 1)

        button = PushButton('Добавить награду',
                            clicked=self.add_document)
        button.setStyleSheet(
            '''QPushButton {background-color: rgb(30, 144, 255);
                border-radius: 11px}''')
        image_layout.addWidget(button)

        dialog.exec()

    def add_document(self):
        new_file_name = self.name.text() + '.' + self.file_name.split('.')[-1]
        if self.name.text() and self.file_name:
            # with sqlite3.connect('librium2.db') as con:
            #     count = len(con.execute(
            #         'SELECT id FROM Portfolio').fetchall()) + 1

            with sqlite3.connect('librium2.db') as con:
                user = con.execute('SELECT id FROM UserID WHERE login = ?',
                                   (self.now_login, )).fetchall()[0][0]

            with sqlite3.connect('librium2.db') as con:
                institute = con.execute('SELECT id FROM Institution WHERE title = ?',
                                        (self.institutions_add.currentText(), )).fetchall()[0][0]

            with sqlite3.connect('librium2.db') as con:
                importance = con.execute('SELECT id FROM Importance WHERE title = ?',
                                         (self.importance_new.currentText(), )).fetchall()[0][0]

            with sqlite3.connect('librium2.db') as con:
                originaly = con.execute('SELECT id FROM Originaly WHERE title = ?',
                                        (self.original_new.currentText(), )).fetchall()[0][0]

            with sqlite3.connect('librium2.db') as con:
                category = con.execute('SELECT id FROM Category WHERE title = ?',
                                       (self.categories_add.currentText(), )).fetchall()[0][0]

            query = '''
                INSERT into Portfolio
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            '''
            data_tuple = (int(user),
                          self.date.dateTime().toString('dd.MM.yyyy'),
                          int(institute), int(importance), int(
                              originaly), int(category),
                          new_file_name, self.name.text())
            with sqlite3.connect('librium2.db') as con:
                con.execute(query, data_tuple)
            os.system(f"cp '{self.file_name}' 'Images/{self.now_login}/{new_file_name}'")
            self.name.clear()
            self.image_label.clear()
            self.file_name = ''

            for i in self.findChildren(QCheckBox):
                i.setChecked(False)
            query = '''
                SELECT image FROM Portfolio, UserID
                WHERE user = UserID.id
                AND UserID.login = ?'''
            with sqlite3.connect('librium2.db') as con:
                self.result = [i[0] for i in con.execute(query,
                                                         (self.now_login, )).fetchall()][::-1]
            self.update_viewer()
        else:
            self.paint_line_edit(self.name)

    def add_category(self):
        '''добавление предмета в базу данных'''
        try:
            if not self.new_category.text():
                raise AddError
            self.paint_line_edit(self.new_category, False)
            self.categories_count += 1
            query = '''
                INSERT INTO Category
                VALUES (?, ?)
            '''
            data_tuple = (self.categories_count,
                          self.new_category.text())
            with sqlite3.connect('librium2.db') as con:
                con.execute(query, data_tuple)
            self.categories_add.addItem(self.new_category.text())
            self.category.addItem(self.new_category.text())
            self.new_category.clear()
        except AddError as ex:
            self.paint_line_edit(self.new_category)

    def add_institution(self):
        '''добавление организации в бд'''
        try:
            if not self.new_institution.text():
                raise AddError
            self.paint_line_edit(self.new_institution, False)
            self.institutions_count += 1
            query = '''
                INSERT INTO Institution
                VALUES (?, ?)
            '''
            data_tuple = (self.institutions_count,
                          self.new_institution.text())
            with sqlite3.connect('librium2.db') as con:
                con.execute(query, data_tuple)
            self.institutions_add.addItem(self.new_institution.text())
            self.institutions.addItem(self.new_institution.text())
            self.new_institution.clear()
        except AddError as ex:
            self.paint_line_edit(self.new_institution)

    def get_image_file(self):
        '''загрузка изображения для добавления награды'''
        if self.sender().text() == 'Загрузить документ':
            self.file_name = QFileDialog.getOpenFileName(
                self, 'Open image file')[0]
            if self.file_name:
                if self.file_name.split('.')[-1] == 'pdf':
                    doc = fitz.open(self.file_name)
                    page = doc[0]
                    pix = page.get_pixmap()
                    self.file_name = self.file_name[:-3] + 'png'
                    pix.save(self.file_name)

                image = QImage(self.file_name).scaled(300, 300*2**0.5)
                self.image_label.setPixmap(QPixmap(image))
        elif self.sender().text() == 'Скрыть':
            if self.file_name:
                self.image_label.clear()
                self.sender().setText('Показать')
        else:
            if self.file_name:
                image = QImage(self.file_name).scaled(300, 300*2**0.5)
                self.image_label.setPixmap(QPixmap(image))
                self.sender().setText('Скрыть')

    def choose_any(self):
        '''занесение выделенного диплома в список'''
        if self.sender().text() == 'Выделить все':
            if self.sender().isChecked():
                for i in self.findChildren(QCheckBox)[5:-1]:
                    i.setChecked(True)
                    self.end_variants = self.result
            else:
                for i in self.findChildren(QCheckBox)[5:-1]:
                    i.setChecked(False)
                    self.end_variants = []
        else:
            if self.sender().isChecked():
                self.end_variants.append(self.result[
                    int(self.sender().text())])
            else:
                self.end_variants.pop(
                    self.end_variants.index(self.result[
                        int(self.sender().text())]))

    def create_port(self):
        '''создание полноценного портфолио на рабочем столе'''
        name, ok_pressed = QInputDialog.getText(self, "Путь к папке LIBRIUM",
                                                'Введите имя папки')
        if ok_pressed:
            if name:
                if self.end_variants:
                    file_name = f'/Users/nikita/Desktop/LIBRIUM-{name}'
                    if not os.path.exists(file_name):
                        os.mkdir(file_name)
                    else:
                        shutil.rmtree(file_name)
                        os.mkdir(file_name)

                    self.create_port_button.setText('Создать портфолио')
                    for el in self.end_variants:
                        os.system(f"cp 'Images/{self.now_login}/{el}' '{file_name}/{el}'")
                else:
                    self.create_port_button.setText('ДИПЛОМЫ НЕ ВЫБРАНЫ!')
            else:
                self.create_port_button.setText('ВЫ НЕ ВВЕЛИ НАЗВАНИЕ ПАПКИ!')

    def update_viewer(self):
        '''обновление окна просмотра дипломов'''
        self.scroll_widget.deleteLater()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)
        self.scroll_widget.setLayout(self.scroll_layout)

        for i in range(len(self.result)):
            name = self.result[i]
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignCenter)

            check = QCheckBox(str(i), clicked=self.choose_any)
            check.setStyleSheet("""QCheckBox{font-size:1px;
                color:white}""")

            row.addWidget(check)
            but_image = QPushButton(str(i), clicked=self.info_dialog)
            but_image.setStyleSheet('''QPushButton{border: 0px solid;
                                    font-size:1px; color:white}''')
            but_image.setIcon(QIcon(f'Images/{self.now_login}/{name}'))
            but_image.setIconSize(QSize(391, 594))
            row.addWidget(but_image)
            self.scroll_layout.addLayout(row)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)

    def changed_check(self):
        '''фильтровка дипломов'''
        if self.sender().isChecked():
            self.filters.append(self.sender().text())
        else:
            self.filters.pop(self.filters.index(self.sender().text()))
        query = '''
            SELECT image FROM Portfolio, UserID
            WHERE user = UserID.id
            AND UserID.login = ?'''
        with sqlite3.connect('librium2.db') as con:
            self.result = [i[0] for i in
                           con.execute(query, (self.now_login, )).fetchall()][::-1]
        for f in self.filters:
            variants = []
            if f == 'Дата':
                day1, month1, year1 = map(
                    int, self.date1.dateTime().toString('dd.MM.yyyy').split('.'))
                day2, month2, year2 = map(
                    int, self.date2.dateTime().toString('dd.MM.yyyy').split('.'))
                d1 = datetime.date(year1, month1, day1)
                d2 = datetime.date(year2, month2, day2)
                days = [i for i in [d1 + datetime.timedelta(days=x)
                                    for x in range((d2-d1).days + 1)]]
                query = '''
                        SELECT data, image FROM Portfolio, UserID
                        WHERE user = UserID.id
                        AND UserID.login = ?
                    '''
                with sqlite3.connect('librium2.db') as con:
                    all_variants = con.execute(
                        query, (self.now_login, )).fetchall()
                for data, image in all_variants:
                    for d in days:
                        if data == d.strftime('%d.%m.%Y'):
                            variants.append(image)
                            break

            elif f == 'Учреждение':
                institute = self.institutions.currentText()
                query = '''
                    SELECT image 
                    FROM Portfolio, UserID, Institution
                    WHERE user = UserID.id
                    AND UserID.login = ?
                    AND institute = Institution.id
                    AND Institution.title = ?
                '''
                data_tuple = (self.now_login, institute)
                with sqlite3.connect('librium2.db') as con:
                    variants = [i[0] for i in
                                con.execute(query, data_tuple).fetchall()]

            elif f == 'Важность':
                important = self.importance.currentText()
                query = '''
                    SELECT image FROM Portfolio, UserID, Importance
                    WHERE user = UserID.id
                    AND UserID.login = ?
                    AND importance = Importance.id
                    AND Importance.title = ?
                '''
                data_tuple = (self.now_login, important)
                with sqlite3.connect('librium2.db') as con:
                    variants = [i[0] for i in
                                con.execute(query, data_tuple).fetchall()]

            elif f == 'Оригинальность':
                original = self.originaly.currentText()
                query = '''
                    SELECT image FROM Portfolio, UserID, Originaly
                    WHERE user = UserID.id
                    AND UserID.login = ?
                    AND originality = Originaly.id
                    AND Originaly.title = ?
                '''
                data_tuple = (self.now_login, original)
                with sqlite3.connect('librium2.db') as con:
                    variants = [i[0] for i in
                                con.execute(query, data_tuple).fetchall()]

            elif f == 'Предмет':
                category = self.category.currentText()
                query = '''
                    SELECT image FROM Portfolio, UserID, Category
                    WHERE user = UserID.id
                    AND UserID.login = ?
                    AND category = Category.id
                    AND Category.title = ?
                '''
                data_tuple = (self.now_login, category)
                with sqlite3.connect('librium2.db') as con:
                    variants = [i[0] for i in
                                con.execute(query, data_tuple).fetchall()]
            self.result = [i for i in self.result if i in variants]
        self.update_viewer()

    def enter_window(self):
        '''окно для входа в систему | интерфейс'''
        self.statusBar().clearMessage()
        self.paint_statusBar(self.statusBar(), False)
        widget = QWidget()
        image_layout = QVBoxLayout()
        image_layout.setAlignment(Qt.AlignCenter)
        layout = QGridLayout()
        self.setCentralWidget(widget)

        image = QImage('system/registration.png').scaled(100, 100)
        label = QLabel(pixmap=QPixmap(image))
        image_layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addWidget(QLabel('Впервые у нас?'), 0, 0)
        layout.addWidget(QPushButton(
            'Регистрация', clicked=self.registration_window), 0, 1)

        self.login_string = QLineEdit()
        self.password_string = QLineEdit()

        layout.addWidget(QLabel('Введите логин:'), 1, 0)
        layout.addWidget(self.login_string, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(QLabel('Введите пароль:'), 2, 0)
        layout.addWidget(self.password_string, 2, 1, alignment=Qt.AlignCenter)
        image_layout.addLayout(layout)
        image_layout.addWidget(QPushButton('Войти',
                                           clicked=self.enter_chek))
        widget.setLayout(image_layout)

    def paint_line_edit(self, editObject, action=True):
        '''окрашивание формы ввода в зависимости от action'''
        if action:
            editObject.setStyleSheet('''
                QLineEdit{
                    background-color: rgb(49, 104, 244);
                    color: white}''')
        else:
            editObject.setStyleSheet('''
                QLineEdit{
                    background-color: 0}''')

    def paint_statusBar(self, statusBar, action=True):
        '''окрашивание меню бара в зависимости от action'''
        if action:
            statusBar.setStyleSheet('''
                QStatusBar{
                    background: rgb(49, 104, 244);
                    font-weight: bold;
                    color: white
                }''')
        else:
            statusBar.setStyleSheet('''
                QStatusBar{background: 0}''')

    def enter_chek(self):
        '''проверка введенного логина и пароля'''
        try:
            s_login = self.login_string.text()
            s_password = self.password_string.text()
            if s_login:
                query = '''
                    SELECT login, password FROM UserID
                '''
                correct = False
                # data_tuple = (login, password)
                with sqlite3.connect('librium2.db') as con:
                    variants = con.execute(query).fetchall()

                for log, password in variants:
                    if log == s_login and check_password_hash(password,
                                                              s_password):
                        correct = True
                        break
                if correct:
                    self.now_login = s_login
                    self.findChild(QAction).setEnabled(True)
                    self.main_window()
                else:
                    raise EnterError
            else:
                raise FailureLoginError

        except LoginError as ex:
            self.statusBar().showMessage(ex.message())
            self.paint_statusBar(self.statusBar())
            self.paint_line_edit(self.login_string)
            self.paint_line_edit(self.password_string, False)
        except EnterError as ex:
            self.statusBar().showMessage(ex.message())
            self.statusBar().showMessage(ex.message())
            self.paint_statusBar(self.statusBar())
            self.paint_line_edit(self.login_string, False)
            self.paint_line_edit(self.password_string, False)
        except PasswordError as ex:
            self.statusBar().showMessage(ex.message())
            self.statusBar().showMessage(ex.message())
            self.paint_statusBar(self.statusBar())
            self.paint_line_edit(self.login_string, False)
            self.paint_line_edit(self.password_string)

    def registration_window(self):
        self.statusBar().clearMessage()
        self.paint_statusBar(self.statusBar(), False)
        widget = QWidget()
        image_layout = QVBoxLayout()
        image_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout = QGridLayout()
        self.setCentralWidget(widget)

        image = QImage('system/registration.png').scaled(100, 100)
        label = QLabel(pixmap=QPixmap(image))
        image_layout.addWidget(label, alignment=Qt.AlignCenter)

        self.login_string = QLineEdit()
        self.password_string1 = QLineEdit()
        self.password_string2 = QLineEdit()

        layout.addWidget(QLabel('Введите логин:'), 0, 0)
        layout.addWidget(self.login_string, 0, 1, alignment=Qt.AlignCenter)
        layout.addWidget(QLabel('Введите пароль:'), 1, 0)
        layout.addWidget(self.password_string1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(QLabel('Повторите пароль:'), 2, 0)
        layout.addWidget(self.password_string2, 2, 1, alignment=Qt.AlignCenter)
        image_layout.addLayout(layout)
        image_layout.addWidget(QPushButton('Зарегистрироваться',
                                           clicked=self.registration_new))
        widget.setLayout(image_layout)

    def registration_new(self):
        '''создание и проверка новых аккаунтов'''
        seqs = [
            'qwe', 'wer', 'ert', 'rty', 'tyu', 'yui', 'uio', 'iop',
            'asd', 'sdf', 'dfg', 'fgh', 'ghj', 'hjk', 'jkl', 'zxc',
            'xcv', 'cvb', 'vbn', 'bnm', 'йцу', 'цук', 'уке', 'кен',
            'енг', 'нгш', 'гшщ', 'шщз', 'щзх', 'зхъ', 'фыв', 'ыва',
            'вап', 'апр', 'про', 'рол', 'олд', 'лдж', 'джэ', 'ячс',
            'чсм', 'сми', 'мит', 'ить', 'тьб', 'ьбю', 'жэё', '123',
            '456', '789'
        ]

        try:
            if self.login_string.text():
                query = '''
                    SELECT login FROM UserID
                '''
                with sqlite3.connect('librium2.db') as con:
                    all_logins = con.execute(query).fetchall()
                all_logins = [i[0] for i in all_logins]
                self.count = len(all_logins) + 1
                if self.login_string.text() in all_logins:
                    raise RepetitiveLoginError()
            else:
                raise FailureLoginError()

            if self.password_string1.text() == self.password_string2.text():
                password = self.password_string1.text()
                if len(password) < 8:
                    raise LenNewPasswordError()
                for s in seqs:
                    if s in password:
                        raise SimpleNewPasswordError()

                self.statusBar().showMessage(
                    'Регистрация прошла успешно!')
                self.paint_statusBar(self.statusBar(), False)
                self.paint_line_edit(self.login_string, False)
                self.paint_line_edit(self.password_string1, False)
                self.paint_line_edit(self.password_string2, False)

                query = '''
                    INSERT INTO UserID
                    VALUES (?, ?, ?)
                '''
                data_tuple = (self.count, self.login_string.text(),
                              generate_password_hash(password))
                with sqlite3.connect('librium2.db') as con:
                    con.execute(query, data_tuple)
                self.now_login = self.login_string.text()
                os.mkdir(f'Images/{self.now_login}')
                self.findChild(QAction).setEnabled(True)
                self.main_window()
            else:
                raise UnequalNewPassword()

        except LoginError as ex:
            self.statusBar().showMessage(ex.message())
            self.paint_statusBar(self.statusBar())
            self.paint_line_edit(self.login_string)
            self.paint_line_edit(self.password_string1, False)
            self.paint_line_edit(self.password_string2, False)

        except PasswordError as ex:
            self.statusBar().showMessage(ex.message())
            self.paint_statusBar(self.statusBar())
            self.paint_line_edit(self.login_string, False)
            self.paint_line_edit(self.password_string1)
            self.paint_line_edit(self.password_string2)


app = QApplication()
window = Window()
window.show()
app.exec()
