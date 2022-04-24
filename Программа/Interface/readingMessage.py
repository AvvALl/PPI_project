from datetime import datetime

from uiForms.readMessageDialog import Ui_readMessageDialog
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QIcon, QPixmap
import os
import textwrap
from zipfile import ZipFile

class readingMessage(QtWidgets.QDialog):
    """Класс для чтения сообщений
    Предназначен для просмотра сообщений
    Прдеставлен в виде диалогового окна
    В окне содержаться поля:
    От кого, кому, тема сообщения, а также поле в виде текстового редактора
    для чтения сообщений. Содержит таблицу для прилагаемых файлов и кнопоки для загрузки

    Attributes:
	dirForAttach: путь к папке для сохранения прилагаемых файлов
	subjectLabel: виджет для вывода темы
	fromLabel: виджет для вывода отправителя
	toLabel: виджет для вывода получателя
	messageTextBrow: виджет для вывода тела сообщения
	attachTable: виджет для вывода прилагаемых файлов
    """

    dirForAttach="A:/trash/CPISfiles/attachments/"
    def __init__(self, msg, client):
        super(readingMessage, self).__init__()
        self.ui = Ui_readMessageDialog()
        self.ui.setupUi(self)

        self.cl=client
        self.ui.subjectLabel.setText(msg.subject)
        self.ui.fromLabel.setText(self.ui.fromLabel.text()+msg.fromAddr)
        self.ui.toLabel.setText(self.ui.toLabel.text()+msg.toAddr)
        self.ui.messageTextBrow.setText(msg.body)

        self.attachments=msg.attachments
        self.showAttach()

        self.ui.attachTable.horizontalHeader().hide()
        self.ui.attachTable.verticalHeader().hide()
        self.ui.saveButton.clicked.connect(self.saveAllAttachments)
        self.ui.attachTable.clicked.connect(self.loadAttachment)
        #self.layout().setSizeConstraint(QLayout.SetFixedSize)


    def showAttach(self):
	"""Добавляет обозначения прилагаемых файлов в соответствующий виджет
	Таблица имеет кратность 7, те в строке содержится максимум 7 файлов
	Args:
	Returns:
	"""
        tableSize=7
        if len(self.attachments)!=0:
            self.ui.attachTable.setRowCount(len(self.attachments)//tableSize+1)
            self.ui.attachTable.setColumnCount(tableSize if len(self.attachments)>=tableSize else len(self.attachments))
            for i in range(0, len(self.attachments)):
                filename,format=os.path.splitext(self.attachments[i][0])
                self.ui.attachTable.setCellWidget(i//tableSize, i%tableSize, attachFile('\n'.join(textwrap.wrap(self.attachments[i][0], 13)), "A:/data/Icons/48px/" +format[1:] + ".png"))
                #self.ui.attachTable.resizeColumnsToContents()
                self.ui.attachTable.resizeRowsToContents()

            self.ui.infoLabel.setText("Всего файлов: "+str(len(self.attachments)))
            self.setFixedSize(1100, 800)
        else:
            self.ui.saveButton.hide()
            self.ui.infoLabel.hide()
            self.ui.attachTable.hide()
            self.setFixedSize(1100, 600)

    def saveAllAttachments(self):
        curTime=datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        zipName=self.dirForAttach+"Attachments-"+curTime+".zip"
        with ZipFile(zipName,"w") as zip_f:
            for file in self.attachments:
                zip_f.writestr(file[0], file[1])

    def loadAttachment(self, indx):
	"""Сохраняет выбранный файл в соответствующую папку
	Args:
	  indx: представляет собой экземляр ячейки таблицы для прилагаемых файлов.
		Содержит значения номера строки и столбца, по корым был совершен клик.
	Returns:
	"""
        indxAttach=indx.row()*self.ui.attachTable.columnCount()+indx.column()
        with open(self.dirForAttach+self.attachments[indxAttach][0],"wb") as f:
            f.write(self.attachments[indxAttach][1])
        """
        saving the file visually
        """
        print(self.ui.attachTable.cellWidget(indx.row(),indx.column())._text)

        pass


class attachFile(QWidget):
    def __init__(self, text, img, parent=None):
        QWidget.__init__(self, parent)

        self._text = text
        self._img = img
        self.setLayout(QVBoxLayout())
        self.lbPixmap = QLabel(self)
        self.lbText = QLabel(self)
        self.lbText.setAlignment(Qt.AlignCenter)
        self.lbPixmap.setAlignment(Qt.AlignCenter)

        self.layout().addWidget(self.lbPixmap)
        self.layout().addWidget(self.lbText)

        self.initUi()

    def initUi(self):
        self.lbPixmap.setPixmap(QPixmap(self._img).scaled(self.lbPixmap.size(), Qt.KeepAspectRatio))
        self.lbText.setText(self._text)

    @pyqtProperty(str)
    def img(self):
        return self._img

    @img.setter
    def total(self, value):
        if self._img == value:
            return
        self._img = value
        self.initUi()

    @pyqtProperty(str)
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:
            return
        self._text = value
        self.initUi()