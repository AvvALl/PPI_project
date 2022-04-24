import ntpath
import re
import textwrap
import os
import sys
import uuid
import time
from Crypto.PublicKey import RSA
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
from PyQt5 import Qt
from uiForms.sendForm import Ui_sendingForm
from inteface.readingMessage import attachFile
from client.utils import showMessage
from client.messages import Message
import copy

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
COLOR_NAME=["#000000", "#a0a0a4", "#0000ff", "#ffff00", "#ff0000", "#00ff00","#800080", "#a52a2a", "#ffffff"]
IMAGE_EXTENSIONS = ['.jpg','.png','.bmp']
HTML_EXTENSIONS = ['.htm', '.html']

def hexuuid():
    return uuid.uuid4().hex

def splitext(p):
    return os.path.splitext(p)[1].lower()


class sendingMessage(QtWidgets.QDialog):
    """Класс для отправки сообщений
    Представляет собой обработчик диалгового окна, который содержит виджеты для заполнения
    темы сообщения, а также определения получателя. Содержит виджет для написания тела сообщения
    и виджеты, для его редактирования. Содержит таблицу для прикрепленных файлов и кнопки для выбора прилагаемых файлов.
    
    Attributes:
	toEdit: виджет для получения имени получателя
	attachTable: виджет для отображения прикрепленных файлов
	textEdit: виджет для написания тела сообщения
	sendBtn: кнопка для отправки написанного сообщения
    """
    def __init__(self, client, msg=None, folder=None):
        super(sendingMessage, self).__init__()
        self.ui = Ui_sendingForm()
        self.ui.setupUi(self)

        self.toolBar=QToolBar()
        self.toolBar.setIconSize(QSize(16, 16))
        self.ui.textEditWidget.layout().addWidget(self.toolBar)

        self.textEdit=QTextEdit()
        self.textEdit.setFontPointSize(12)
        self.ui.textEditWidget.layout().addWidget(self.textEdit)

        self.textEdit.selectionChanged.connect(self.update_format)


        #Add font combobox to list widget (font menu)
        self.fonts=QFontComboBox()
        self.fonts.lineEdit().setReadOnly(True)
        self.fonts.currentFontChanged.connect(self.textEdit.setCurrentFont)
        self.toolBar.addWidget(self.fonts)

        self.fontSize=QComboBox()
        self.fontSize.addItems([str(s) for s in FONT_SIZES])
        self.fontSize.currentIndexChanged[str].connect(lambda s: self.textEdit.setFontPointSize(float(s)))
        self.fontSize.setCurrentIndex(5)
        self.toolBar.addWidget(self.fontSize)

        self.fontColor=QComboBox()
        self.colorPicker(self.fontColor)
        self.fontColor.currentIndexChanged[int].connect(lambda i: self.textEdit.setTextColor(QColor(COLOR_NAME[i])))
        self.toolBar.addWidget(self.fontColor)


        self.bold_action = QAction(QIcon(os.path.join('images', 'edit-bold.png')), "Bold", self)
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(lambda x: self.textEdit.setFontWeight(QFont.Bold if x else QFont.Normal))
        self.toolBar.addAction(self.bold_action)
        #self.ui.fontEditorList.addAction(self.bold_action)

        self.italic_action = QAction(QIcon(os.path.join('images', 'edit-italic.png')), "Italic", self)
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.textEdit.setFontItalic)
        self.toolBar.addAction(self.italic_action)

        self.underline_action = QAction(QIcon(os.path.join('images', 'edit-underline.png')), "Underline", self)
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.textEdit.setFontUnderline)
        self.toolBar.addAction(self.underline_action)

        self.toolBar.addSeparator()
        self.alignl_action = QAction(QIcon(os.path.join('images', 'edit-alignment.png')), "Align left", self)
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(lambda: self.textEdit.setAlignment(QtCore.Qt.AlignLeft))
        self.toolBar.addAction(self.alignl_action)

        self.alignc_action = QAction(QIcon(os.path.join('images', 'edit-alignment-center.png')), "Align center", self)
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(lambda: self.textEdit.setAlignment(QtCore.Qt.AlignCenter))
        self.toolBar.addAction(self.alignc_action)

        self.alignr_action = QAction(QIcon(os.path.join('images', 'edit-alignment-right.png')), "Align right", self)
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(lambda: self.textEdit.setAlignment(QtCore.Qt.AlignRight))
        self.toolBar.addAction(self.alignr_action)

        self._format_actions = [
            self.fonts,
            self.fontSize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            # We don't need to disable signals for alignment, as they are paragraph-wide.
        ]
        self.cl=client

        self.draftMsg, self.forceClose, self.draftFolder=None, True, folder
        if msg is not None:
            self.draftMsg, self.draftFolder=msg, folder
            self.setDraft(msg)

        self.ui.attachTable.horizontalHeader().hide()
        self.ui.attachTable.verticalHeader().hide()
        self.attachments=[]
        self.ui.attachBtn.clicked.connect(self.attachFileToMessage)
        self.ui.sendBtn.clicked.connect(self.sendMessage)
        self.ui.disableAllBtn.clicked.connect(self.disableAllFiles)
        self.ui.attachTable.clicked.connect(self.disableFile)
    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is neccessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.textEdit.currentFont())
        # Nasty, but we get the font-size as a float but want it was an int
        self.fontSize.setCurrentText(str(int(self.textEdit.fontPointSize())))
        self.fontColor.setCurrentIndex(COLOR_NAME.index(self.textEdit.textColor().name()))

        #self.italic_action.setChecked(self.ui.textEdit.fontItalic())
        #self.underline_action.setChecked(self.ui.textEdit.fontUnderline())
        self.bold_action.setChecked(self.textEdit.fontWeight() == QFont.Bold)
        self.alignl_action.setChecked(self.textEdit.alignment() == QtCore.Qt.AlignLeft)
        self.alignc_action.setChecked(self.textEdit.alignment() == QtCore.Qt.AlignCenter)
        self.alignr_action.setChecked(self.textEdit.alignment() == QtCore.Qt.AlignRight)
        self.block_signals(self._format_actions, False)

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def colorPicker(self, combo):
        pix=QPixmap(22,22)
        pix.fill(QColor("black"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("grey"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("blue"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("yellow"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("red"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("green"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("purple"))
        combo.addItem(QIcon(pix), "")
        pix.fill(QColor("brown"))
        combo.addItem(QIcon(pix), "")

    def path_leaf(self, path):
	"""Парсит путь к файлу
	Args: 
	  path: путь к сообщения в виде строки
	Returns:
	  После парсинга возрващается только имя файла и его разрешение в виде строки
	"""
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def attachFileToMessage(self):
        tableSize = 7
        fileName = QFileDialog.getOpenFileName(self, 'Выбор файла', "",  'All Files (*.*)')[0]
        #add filename add data of file to list
        if os.path.exists(fileName):
            data=None
            with open(fileName, 'rb') as f:
                data = f.read()
            base_name=self.path_leaf(fileName)

            self.attachments.append((base_name,data))

            #show icon of attachments file
            if len(self.attachments) != 0:
                self.ui.attachTable.setRowCount(len(self.attachments) // tableSize + 1)
                self.ui.attachTable.setColumnCount(
                    tableSize if len(self.attachments) >= tableSize else len(self.attachments))
                filename, format = os.path.splitext(self.attachments[-1][0])
                self.ui.attachTable.setCellWidget((len(self.attachments)-1) // tableSize, (len(self.attachments)-1) % tableSize,
                                                  attachFile('\n'.join(textwrap.wrap(self.attachments[-1][0], 13)),
                                                             "A:/data/Icons/48px/" + format[1:] + ".png"))
                # self.ui.attachTable.resizeColumnsToContents()
                self.ui.attachTable.resizeRowsToContents()

    def disableAllFiles(self):
        self.attachments=[]
        self.ui.attachTable.clear()
        self.ui.attachTable.setRowCount(0)
        self.ui.attachTable.setColumnCount(0)

    def disableFile(self, indx):
        indxAttach = indx.row() * self.ui.attachTable.columnCount() + indx.column()
        self.ui.attachTable.removeCellWidget(indx.row(), indx.column())
        self.attachments.pop(indxAttach)
        pass

    def checkAdress(self, str):
        pattern = "^[a-zA-Z0-9]*@([a-z]+.)+[a-z]{2,4}$"
        str=str.split(',')
        for address in str:
            if bool(re.match(pattern, address)):
                self.ui.toEdit.setText(address)
                self.ui.toEdit.setStyleSheet("QLineEdit{border: 2px solid black;}")
            else:
                self.ui.toEdit.setStyleSheet("QLineEdit{border:2px solid rgb(255,0,0);}")

    def setDraft(self, msg):
        self.ui.subjectEdit.setText(msg.subject)
        self.ui.toEdit.setText(msg.toAddr)
        self.textEdit.setText(msg.body)
        self.attachments=msg.attachments

        tableSize=7
        if len(self.attachments) != 0:
            for i in range(len(self.attachments)):
                self.ui.attachTable.setRowCount(len(self.attachments) // tableSize + 1)
                self.ui.attachTable.setColumnCount(
                    tableSize if len(self.attachments) >= tableSize else len(self.attachments))
                filename, format = os.path.splitext(self.attachments[i][0])
                self.ui.attachTable.setCellWidget(i // tableSize,
                                                  i % tableSize,
                                                  attachFile('\n'.join(textwrap.wrap(self.attachments[i][0], 13)),
                                                             "A:/data/Icons/48px/" + format[1:] + ".png"))
            # self.ui.attachTable.resizeColumnsToContents()
            self.ui.attachTable.resizeRowsToContents()


    def sendMessage(self):

        pattern = "^[a-zA-Z0-9]*@([a-z]+.)+[a-z]{2,4}$"
        try:
            #check subject
            subject = self.ui.subjectEdit.text()
            if subject!="":
                #check addresses
                toAddr = self.ui.toEdit.text()
                toAddr=toAddr.split(',')
                mailing= True if len(toAddr)>1 else False
                correctAddresses=[ bool(re.match(pattern,addr)) for addr in toAddr]
                if all(correctAddresses):
                    type_message = True
                    #key exchange
                    if not mailing and self.cl.encrypted:
                        if toAddr[0] != self.cl.full_login:
                            self.hide()
                            status=self.keyExchange(toAddr[0])
                            if status:
                                #encryption body and attachments
                                pubKey=self.cl.ndb.getPublicKeyRSA(toAddr[0])
                                if pubKey is not None:
                                    ebody=self.cl.encryptBodyText(self.textEdit.toHtml(), RSA.import_key(pubKey[1]), (pubKey[0], self.cl.crypto.id_keySign))
                                    if len(self.attachments)!=0:
                                        attachments=[(attach[0],self.cl.encryptAttachments(attach[1], RSA.import_key(pubKey[1]), (pubKey[0], self.cl.crypto.id_keySign))) for attach in self.attachments]
                                        self.attachments=attachments
                                else:
                                    type_message = False
                                    ebody = self.textEdit.toHtml()
                            else:
                                type_message = False
                                ebody = self.textEdit.toHtml()
                        else:
                            ebody=self.cl.encryptBodyText(self.textEdit.toHtml(), self.cl.crypto.keyRSA.public_key(), (self.cl.crypto.id_keyRSA, self.cl.crypto.id_keySign))
                            if len(self.attachments) != 0:
                                attachments = [(attach[0],self.cl.encryptAttachments(attach[1], self.cl.crypto.keyRSA.public_key(), (self.cl.crypto.id_keyRSA, self.cl.crypto.id_keySign)))
                                                    for attach in self.attachments]
                                self.attachments=attachments
                    else:
                        type_message=False
                        ebody=self.textEdit.toHtml()
                    newMessage=Message().buildMessage(self.cl.full_login,toAddr,subject, ebody,self.attachments, mailing=mailing,type_message=type_message)
                    self.cl.server_smtp.sendMessage(newMessage)
                    if self.draftMsg is not None:
                        self.cl.server_imap.deleteMessages(self.draftMsg.uid.decode(), self.draftFolder)
                    self.forceClose=False
                    self.close()
                else:
                    showMessage(False, "Неверно задан адрес получателя")
            else:
                showMessage(False, "Тема не задана")
        except Exception as e:
            print(e.args)
            showMessage(False, "Сообщение не было отправлено")
            self.close()

    def closeEvent(self, event):
        if self.forceClose and self.draftMsg is None:
            toAddr = self.ui.toEdit.text()
            toAddr = toAddr.split(',')
            mailing = True if len(toAddr) > 1 else False
            newMessage = Message().buildMessage(self.cl.full_login, toAddr, self.ui.subjectEdit.text(), self.textEdit.toHtml(), self.attachments,
                                                mailing=mailing,type_message=False).as_bytes()
            self.cl.server_imap.appendMessage(self.draftFolder, newMessage)

    def keyExchange(self, toAddr):
        if not self.cl.ndb.checkPublicKeys(toAddr):
            self.cl.sendKeys(toAddr, True)
            start=time.time()
            while 1:
                if start+35<time.time():
                    return False
                elif self.cl.ndb.checkPublicKeys(toAddr):
                    return True
            return True
        else:
            return True
