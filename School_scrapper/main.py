import sys

from PyQt6 import QtGui
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton

from School_scrapper import give_me_my_hometasks


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Урочки')
        self.setWindowIcon(QIcon('img/monkey.png'))

        qbtn = QPushButton('Получить УРОЧКИ!', self)
        qbtn.clicked.connect(give_me_my_hometasks)
        qbtn.resize(150, 100)
        qbtn.move(75, 100)

        qbtn.setStyleSheet('''
            background-color: red;
            border-style: outset;
            border-width: 2px;
            border-radius: 10px;
            border-color: beige;
            font: bold 14px;
            color: white;
        ''')

        self.show()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        pixmap = QPixmap("img/dvoyki.jpg")
        painter.drawPixmap(self.rect(), pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec())
