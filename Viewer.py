#!/usr/bin/python
# -*- coding: utf-8 -*-
from PySide import QtCore 
from PySide import QtGui 
import re,os
import Controller
import datetime

#from Foundation import NSURL

class PrgBar(object):
	"""a progress bar"""
	def __init__(self, parent=None): 
                self.bar = QtGui.QProgressBar()
                self.bar.setMaximumSize(199, 19)
		self.val = 0
		self.disp()
		self.total = 0

	def setv(self,val):
		self.val = val 
		self.disp()

	def disp(self):
		self.bar.setValue( self.val )
		QtGui.QApplication.processEvents()

	def add(self,i):
		self.val += i
		self.disp()

	def perc(self,total):
		self.total = total
		self.inc = 0
		self.setv(0)

	def percAdd(self,i):
		self.inc += i
		self.setv(self.inc*100/self.total)
		if self.inc == self.total:
			self.inc = 0
			self.total = 0
			self.setv(0)

	def reset(self):
		self.bar.reset()
		
def formeResume(resume):
	return u"%s <span style=\"font: bold\">%s</span> %s" % resume 


class TexteWidgetItem(object):
        def __init__(self,resume):
		self.Widget = QtGui.QListWidgetItem()
                txt_resume = formeResume(resume)
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
#FIXME bug Qt et Yosemite ne donne pas path complet
			for url in event.mimeData().urls():
                                #print str(NSURL.URLWithString_(str(url.toString())))
				#links.append(str(url.toLocalFile())) #pb encodage
				links.append(url.toLocalFile())
			self.fileDropped.emit(links)
		else:
		    event.ignore()


class Corpus_tab(QtGui.QListWidget):
	def __init__(self,type,parent=None):
		super(Corpus_tab, self).__init__(parent)
                L = QtGui.QVBoxLayout()
                self.setLayout(L)
                L.setContentsMargins(0,0,0,0) 
                L.setSpacing(0) 

                H1 = QtGui.QHBoxLayout()
                H1.setContentsMargins(0,0,0,0) 
                H1.setSpacing(0) 
                L.addLayout(H1)
                self.nameCorpus = QtGui.QLineEdit()
		self.nameCorpus.setAcceptDrops(True)
                H1.addWidget(self.nameCorpus)
                openPRC_button = QtGui.QPushButton("Open")
                openPRC_button.setToolTip("Open a .prc file")
                openPRC_button.clicked.connect(self.openPRC)
                H1.addWidget(openPRC_button)
                mergePRC_button= QtGui.QPushButton("Merge")
                mergePRC_button.setToolTip("Merge text list with a .prc file")
                H1.addWidget(mergePRC_button)
                mergePRC_button.clicked.connect(self.mergePRC)
                savePRC_button= QtGui.QPushButton("Save")
                H1.addWidget(savePRC_button)
                savePRC_button.clicked.connect(self.savePRC)
                self.launchPRC_button= QtGui.QPushButton("Read")
                H1.addWidget(self.launchPRC_button)
                self.launchPRC_button.setEnabled(False)

                H2 = QtGui.QHBoxLayout()
                L.addLayout(H2)
                H2LV1 = QtGui.QVBoxLayout()
                H2.addLayout(H2LV1)
                H2LV1B = QtGui.QHBoxLayout()
                H2LV1.addLayout(H2LV1B)
                self.numTexts = QtGui.QLabel()
                H2LV1B.addWidget(self.numTexts)
                spacer_1 = QtGui.QLabel()
                spacer_1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum )
                H2LV1B.addWidget(spacer_1)
                self.checkTexts = QtGui.QCheckBox("file existence")
                H2LV1B.addWidget(self.checkTexts)
                self.checkTexts.stateChanged.connect( self.checkFileExistence )
        
                self.TextFilesDates = {}

                self.ViewListeTextes = ListViewDrop(self)
                self.ViewListeTextes.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
                self.ViewListeTextes.fileDropped.connect(self.TxtFilesDropped)
                H2LV1.addWidget(self.ViewListeTextes)


                self.ViewListeTextes.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_ViewListeTextesItem = QtGui.QAction('delete item',self)
                self.ViewListeTextes.addAction(efface_ViewListeTextesItem)
                QtCore.QObject.connect(efface_ViewListeTextesItem, QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextesItem)
                efface_ViewListeTextes = QtGui.QAction('clear list',self)
                self.ViewListeTextes.addAction(efface_ViewListeTextes)
                QtCore.QObject.connect(efface_ViewListeTextes, QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextes)
                self.send_codex_ViewListeTextes = QtGui.QAction('send to codex',self)
                self.ViewListeTextes.addAction(self.send_codex_ViewListeTextes)
                #QtCore.QObject.connect(send_codex_ViewListeTextes, QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)

                H22Tab = QtGui.QTabWidget()
                H2.addWidget(H22Tab)
                H22TabDic = QtGui.QWidget()
                H22Tab.addTab(H22TabDic,"Dictionaries")
                H2L = QtGui.QVBoxLayout()
                H22TabDic.setLayout(H2L)
                H2L.setContentsMargins(0,0,0,0) 
                H2L.setSpacing(0) 

                self.ViewListeConcepts = ListViewDrop(self)
                H2L.addWidget(self.ViewListeConcepts)
                self.ViewListeConcepts.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
                self.ViewListeConcepts.fileDropped.connect(self.ccfFilesDropped)
                self.ViewListeConcepts.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_ViewListeConceptsItem = QtGui.QAction('delete item',self)
                self.ViewListeConcepts.addAction(efface_ViewListeConceptsItem)
                QtCore.QObject.connect(efface_ViewListeConceptsItem, QtCore.SIGNAL("triggered()"), self.efface_ViewListeConceptsItem)
                efface_ViewListeConcepts = QtGui.QAction('clear list',self)
                self.ViewListeConcepts.addAction(efface_ViewListeConcepts)
                QtCore.QObject.connect(efface_ViewListeConcepts, QtCore.SIGNAL("triggered()"), self.efface_ViewListeConcepts)

                self.ViewListeLexicons = ListViewDrop(self)
                H2L.addWidget(self.ViewListeLexicons)
                self.ViewListeLexicons.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
                self.ViewListeLexicons.fileDropped.connect(self.dicFilesDropped)
                self.ViewListeLexicons.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_ViewListeLexiconsItem = QtGui.QAction('delete item',self)
                self.ViewListeLexicons.addAction(efface_ViewListeLexiconsItem)
                QtCore.QObject.connect(efface_ViewListeLexiconsItem, QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexiconsItem)
                efface_ViewListeLexicons = QtGui.QAction('clear list',self)
                self.ViewListeLexicons.addAction(efface_ViewListeLexicons)
                QtCore.QObject.connect(efface_ViewListeLexicons, QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexicons)

                H22TabPar = QtGui.QWidget()
                H22Tab.addTab(H22TabPar,"Parameters")
	  


        def TxtFilesDropped(self, l):
                existing = [] 
                for r in range( self.ViewListeTextes.count()):
                        existing.append( self.ViewListeTextes.item(r).text())
                for url in list(set(l) - set(existing)):
                        if os.path.exists(url):
                                if os.path.splitext(url)[1] in ['.txt','.TXT']:
                                        item = QtGui.QListWidgetItem(url, self.ViewListeTextes)
                                        item.setStatusTip(url)
                                        self.TextFilesDates[url] = u"%s"%datetime.datetime.now().strftime("%Y-%m-%d")
                                        item.setToolTip("insertion date %s" % self.TextFilesDates[url])
                self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())

        def efface_ViewListeTextes(self):
                self.ViewListeTextes.clear()
                self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
                self.TextFilesDates = {}


        def efface_ViewListeTextesItem(self):
                Items = self.ViewListeTextes.selectedItems()
                if (Items):
                        for item in Items:
                                del(self.TextFilesDates[item.text()])
                                self.ViewListeTextes.takeItem(self.ViewListeTextes.row(item))
                self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
        
        def efface_ViewListeConcepts(self):
                self.ViewListeConcepts.clear()

        def efface_ViewListeConceptsItem(self):
                Items = self.ViewListeConcepts.selectedItems()
                if (Items):
                        for item in Items:
                                self.ViewListeConcepts.takeItem(self.ViewListeConcepts.row(item))
                                

        def ccfFilesDropped(self, l):
                existing = [] 
                for r in range( self.ViewListeConcepts.count()):
                        existing.append( self.ViewListeConcepts.item(r).text())
                for url in list(set(l) - set(existing)):
                        if os.path.exists(url):
                                if os.path.splitext(url)[1] in ['.cat','.fic','.col']:
                                        item = QtGui.QListWidgetItem(url, self.ViewListeConcepts)
                                        item.setStatusTip(url)
                self.ViewListeConcepts.sortItems()
        
        def efface_ViewListeLexicons(self):
                self.ViewListeLexicons.clear()

        def efface_ViewListeLexiconsItem(self):
                Items = self.ViewListeLexicons.selectedItems()
                if (Items):
                        for item in Items:
                                self.ViewListeLexicons.takeItem(self.ViewListeLexicons.row(item))



        def dicFilesDropped(self, l):
                existing = [] 
                for r in range( self.ViewListeLexicons.count()):
                        existing.append( self.ViewListeLexicons.item(r).text())
                for url in list(set(l) - set(existing)):
                        if os.path.exists(url):
                                if os.path.splitext(url)[1] in ['.dic']:
                                        item = QtGui.QListWidgetItem(url, self.ViewListeLexicons)
                                        item.setStatusTip(url)
                self.ViewListeLexicons.sortItems()


                
        def getFile(self):
		if os.path.isdir("/Users/gspr/corpus"):
			rep = "/Users/gspr/corpus"
		else:
			rep = "."
                fname, filt = QtGui.QFileDialog.getOpenFileName(self, 'Open file', rep, 'Corpus (*.prc *.PRC)')
                return fname
      
        def openPRC(self):
                fname = self.getFile()
                if ( fname) :
                        corpus = Controller.parseCorpus()
                        corpus.open(fname)

                        self.nameCorpus.clear()
                        self.nameCorpus.setText( fname )

                        self.ViewListeTextes.clear()
                        for f in corpus.textFileList(): 
                                item = QtGui.QListWidgetItem(f[0])
                                item.setToolTip("insertion date %s" % f[1])
                                self.ViewListeTextes.addItem(item)
                                self.TextFilesDates[f[0]] = f[1]
                        self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
                        self.ViewListeTextes.sortItems()
                        if self.checkTexts.checkState() :
                                self.checkFileExistence()

                        self.ViewListeConcepts.clear()
                        self.ViewListeConcepts.addItems(corpus.conceptFileList())
                        self.ViewListeConcepts.sortItems()

                        self.ViewListeLexicons.clear()
                        self.ViewListeLexicons.addItems(corpus.dicFileList())
                        self.ViewListeLexicons.sortItems()

			self.launchPRC_button.setEnabled(True)

        def checkFileExistence(self):
                for row in range(self.ViewListeTextes.count()):
                        F = self.ViewListeTextes.item(row).text()
                        if self.checkTexts.checkState() :
                                if os.path.isfile(F):
                                        self.ViewListeTextes.item(row).setForeground(QtGui.QColor("green" ))
                                else:
                                        self.ViewListeTextes.item(row).setForeground(QtGui.QColor("red" ))
                        else:
                                self.ViewListeTextes.item(row).setForeground(QtGui.QColor("black" ))

                
        def mergePRC(self):
                fname = self.getFile()
                if ( fname) :
                        corpusM = Controller.parseCorpus()
                        corpusM.open(fname)
                        for f in corpusM.textFileList(): 
                                if f[0] not in self.TextFilesDates.keys():
                                        self.TextFilesDates[f[0]] = f[1]
                                        item = QtGui.QListWidgetItem(f[0])
                                        item.setToolTip("insertion date %s" % f[1])
                                        self.ViewListeTextes.addItem(item)
                        self.ViewListeTextes.sortItems()
                        self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
                        if self.checkTexts.checkState() :
                                self.checkFileExistence()

        def savePRC(self):
                fileName,ext = QtGui.QFileDialog.getSaveFileName(self,"Save prc file", '', '*.prc') 
                corpusS = Controller.parseCorpus()    
		concepts = []
		for r in range(self.ViewListeConcepts.count()):
			concepts.append(self.ViewListeConcepts.item(r).text())
		ressources = []
		for r in  range(self.ViewListeLexicons.count()):
			ressources.append(self.ViewListeLexicons.item(r).text())
                corpusS.savefile(fileName,langue=u"français",ressource_list=ressources,concept_list=concepts,text_dic=self.TextFilesDates)
		self.launchPRC_button.setEnabled(True)
		self.nameCorpus.setText( fileName )


