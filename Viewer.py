#!/usr/bin/python
# -*- coding: utf-8 -*-
from PySide import QtCore 
from PySide import QtGui 
import re


class TexteWidgetItem(object):
        def __init__(self,resume):
		self.Widget = QtGui.QListWidgetItem()
                txt_resume = u"%s <span style=\"font: bold\">%s</span> %s" % resume 
                self.WidgetLabel = QtGui.QLabel(txt_resume)
                #TODO texte en blanc quand selectionné

class Liste_texte(object):
        def __init__(self,element,liste_textes):
                self.tab_title = "%s (%d)" % (element,len(liste_textes))

                self.show_texts_widget = QtGui.QWidget()
                HBox_texts = QtGui.QHBoxLayout()
                HBox_texts.setContentsMargins(0,0,0,0) 
                HBox_texts.setSpacing(0) 
                self.show_texts_widget.setLayout(HBox_texts)
                self.show_texts_corpus = QtGui.QListWidget()
                self.show_texts_corpus.setAlternatingRowColors(True)
                HBox_texts.addWidget(self.show_texts_corpus)
                self.show_texts_anticorpus = QtGui.QListWidget()
                self.show_texts_anticorpus.setAlternatingRowColors(True)
                HBox_texts.addWidget(self.show_texts_anticorpus)



class MyDelegate (QtGui.QStyledItemDelegate ):
	
	closedSignal = QtCore.Signal()

	def __init__(self, parent=None): 
		super(MyDelegate, self).__init__(parent)
		self.closeEditor.connect(self.cSignal)

	def cSignal(self):
		self.closedSignal.emit()





class ListViewDrop(QtGui.QListWidget):

	fileDropped = QtCore.Signal(list)

	def __init__(self,type,parent=None):
		super(ListViewDrop, self).__init__(parent)
		self.setAcceptDrops(True)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			links = []
			for url in event.mimeData().urls():
				#links.append(str(url.toLocalFile())) #pb encodage
				links.append(url.toLocalFile())
			self.fileDropped.emit(links)
		else:
		    event.ignore()


class testwindow(QtGui.QWidget):
        def __init__(self, parent=None):
                super(testwindow, self).__init__(parent,QtCore.Qt.Window)
		
