import sys
import sqlite3

from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

from sympy import symbols, Eq, nsolve

class SputnikNameError(Exception):
    pass


class SputnikCordError(Exception):
    pass


class DotNameError(Exception):
    pass


class DotCordError(Exception):
    pass


class LenChoisedSputniksError(Exception):
    pass


class map_object():
    def __init__(self, name, x, y, z):
        self.name = name
        self.x = x
        self.y = y
        self.z = z


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Ручной GPS')
        uic.loadUi('sputnik.ui', self)
        self.con = sqlite3.connect("main.sqlite")
        self.sputniks = list()
        self.dm = False
        self.DB = self.con.cursor()
        # создание БД
        if len(self.DB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sputniks'").fetchall()) == 0:
            self.DB.execute('''CREATE TABLE sputniks(name, x, y, z);''')
            self.DB.execute('''CREATE TABLE dots(name, x, y, z);''')

        self.save_sputnik_button.clicked.connect(self.save_sputnik)
        self.calc_cord_button.clicked.connect(self.calc_cord)

        self.sputnik_table.cellClicked.connect(self.add_sputnik)
        self.change_fon_button.clicked.connect(self.change_fon)
        # обновление таблиц
        self.sinchronize_sputniks()
        self.sinchronize_dots()
    def test(self):
        self.dm = True
        self.update()
    # сменить фон (доделать)
    def change_fon(self):
        self.f = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                             'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]
        self.pixmap = QPixmap(self.f)
        #self.pixmap.size(self.map.size())
        self.map.setPixmap(self.pixmap)
        # вставить фон в laybel и рисовать поверх него с помощью указание в begin
    def paintEvent(self, event):
        if self.dm:
            painter = QPainter(self.map)
            self.map.setPixmap(self.pixmap)
            painter.end()
        self.dm = False
    # тест рисования(удалить)
    def draw_map(self):
        self.dm = True
        self.update()
    def draw_flag(self, qp):
        qp.setBrush(QColor(255, 0, 0))
        qp.drawRect(0, 0, 120, 30)
        qp.setBrush(QColor(0, 255, 0))
        qp.drawRect(30, 60, 120, 30)
        qp.setBrush(QColor(0, 0, 255))
        qp.drawRect(30, 90, 120, 30)
        print(1)
    #очистить выбраные спутники
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.AltModifier:
            if (event.key() == Qt.Key.Key_C):
                self.sputniks = []
                self.choised_sputniks.setText('*')
    # синхронизировать таблицу спутников
    def sinchronize_sputniks(self):
        data = self.DB.execute('SELECT * FROM sputniks').fetchall()
        self.sputnik_table.setRowCount(len(data))
        for i in range(len(data)):
            for j in range(len(data[i])):
                self.sputnik_table.setItem(i, j, QtWidgets.QTableWidgetItem(str(data[i][j])))
                self.sputnik_table.resizeColumnsToContents()
    # синхронизировать таблицу точек
    def sinchronize_dots(self):
        data = self.DB.execute('SELECT * FROM dots').fetchall()
        self.dots_table.setRowCount(len(data))
        for i in range(len(data)):
            for j in range(len(data[i])):
                self.dots_table.setItem(i, j, QtWidgets.QTableWidgetItem(str(data[i][j])))
                self.dots_table.resizeColumnsToContents()
    # выбрать спутник для вычеслений
    def add_sputnik(self, row, col):
        if col == 0:
            self.sputniks.insert(0, self.sputnik_table.item(row, col).text())
            if len(set(self.sputniks)) == 4:
                self.sputniks.pop(-1)
            self.sputniks = list(set(self.sputniks))
            self.choised_sputniks.setText(', '.join(set(self.sputniks)))

    # добавить спутник в БД
    def save_sputnik(self):
        try:
            sp = map_object(self.edit_sputnik_name.text(),
                    self.edit_sputnik_x.text(),
                    self.edit_sputnik_y.text(),
                    self.edit_sputnik_z.text())
            if sp.name == '':
                raise SputnikNameError
            elif not(sp.x.isdigit()) or not(sp.y.isdigit()) or not(sp.z.isdigit()):
                raise SputnikCordError
            self.DB.execute(f"""INSERT INTO sputniks (name, x, y, z)
                                    SELECT '{sp.name}','{sp.x}', '{sp.y}', '{sp.z}'
                                WHERE NOT EXISTS (
                                    SELECT 1
                                    FROM sputniks
                                    WHERE name = '{sp.name}'
                                    );""")
            self.con.commit()
            self.sinchronize_sputniks()

        except SputnikCordError:
            QMessageBox.warning(self, 'Непраильный ввод!', 'Координаты спутника должны быть числами!')
            pass
        except SputnikNameError:
            QMessageBox.warning(self, 'Непраильный ввод!', 'Введите имя спутника!')
    # вычисление коардинат точки
    def calc_cord(self):
        try:
            #корректность ввода
            if any([not(i.isdigit()) for i in [self.edit_dot_r1.text(),
                                               self.edit_dot_r2.text(),
                                               self.edit_dot_r3.text()]]):
                raise DotCordError
            elif self.edit_dot_name.text() == '':
                raise DotNameError
            elif len(self.sputniks) != 3:
                raise LenChoisedSputniksError
            # получить коврдинаты
            s_cord = self.DB.execute(f"""SELECT * FROM sputniks
                                        WHERE name IN ('{self.sputniks[0]}',
                                                       '{self.sputniks[1]}',
                                                       '{self.sputniks[2]}')""").fetchall()
            s1_x, s1_y, s1_z = float(s_cord[0][1]), float(s_cord[0][2]), float(s_cord[0][3])
            s2_x, s2_y, s2_z = float(s_cord[1][1]), float(s_cord[1][2]), float(s_cord[1][3])
            s3_x, s3_y, s3_z = float(s_cord[2][1]), float(s_cord[2][2]), float(s_cord[2][3])
            r1 = float(self.edit_dot_r1.text())
            r2 = float(self.edit_dot_r2.text())
            r3 = float(self.edit_dot_r3.text())
            # Определение переменных
            x, y, z = symbols('x y z')
            # Определение системы уравнений
            equations = [
                Eq((x - s1_x) ** 2 + (y - s1_y) ** 2 + (z - s1_z) ** 2, r1),
                Eq((x - s2_x) ** 2 + (y - s2_y) ** 2 + (z - s2_z) ** 2, r2),
                Eq((x - s3_x) ** 2 + (y - s3_y) ** 2 + (z - s3_z) ** 2, r3),
            ]
            initial_guess = [0, 0, 0]
            # Нахождение численного решения
            numerical_solution = nsolve(equations, symbols('x y z'), initial_guess)
            x = numerical_solution[0]
            y = numerical_solution[1]
            z = numerical_solution[2]
            dot = map_object(self.edit_dot_name.text(), x, y, z)
            # добавить точку в базу данных
            self.DB.execute(f"""INSERT INTO dots (name, x, y, z)
                                    SELECT '{dot.name}','{dot.x}', '{dot.y}', '{dot.z}'
                                WHERE NOT EXISTS (
                                    SELECT 1
                                    FROM dots
                                    WHERE name = '{dot.name}'
                                    );""")
            self.DB.execute(f"""UPDATE dots
                                    SET x = '{dot.x}', y = '{dot.y}', z = '{dot.z}'
                                    WHERE
                                        name = '{dot.name}'""")
            self.con.commit()
            # вывести коардинаты
            self.me_cord_output.setText(f'cord: {x} {y} {z}')
            # обновить внутреннюю таблицу точек
            self.sinchronize_dots()

        except DotNameError:
            self.me_cord_output.setText('введите имя точки')
        except DotCordError:
            self.me_cord_output.setText('радиусы должны быть числами')
        except LenChoisedSputniksError:
            self.me_cord_output.setText('выберете 3 спутника, кликнув на их названии в таблице')
        except ValueError: # обязательно, ведь по другому невозмо узнать есть ли такая точка (если не менять библеотеку)
            self.me_cord_output.setText('Такой точки нет')
        # отобразить на рисунке
        #self.draw_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())