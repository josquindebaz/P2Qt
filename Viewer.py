#!/usr/bin/python
# -*- coding: utf-8 -*-
from PySide import QtCore 
from PySide import QtGui 
import re
import os
import datetime
#from Foundation import NSURL

import Controller
import generator_mrlw


class PrgBar(object):
    """a progress bar"""
    def __init__(self, parent=None): 
        self.bar = QtGui.QProgressBar()
        self.bar.setMaximumSize(199,19)
        self.val = 0
        self.disp()
        self.total = 0

    def setv(self, val):
        self.val = val 
        self.disp()

    def disp(self):
        self.bar.setValue(self.val)
        QtGui.QApplication.processEvents()

    def add(self, i):
        self.val += i
        self.disp()

    def perc(self, total):
        self.total = total
        self.inc = 0
        self.setv(0)

    def percAdd(self, i):
        self.inc += i
        self.setv(self.inc*100/self.total)
        if self.inc == self.total:
            self.inc = 0
            self.total = 0
            self.setv(0)

    def reset(self):
        self.bar.reset()


class TexteWidgetItem(object):
    def __init__(self, resume):
        self.Widget = QtGui.QListWidgetItem()
        txt_resume = formeResume(resume)
        self.WidgetLabel = QtGui.QLabel(txt_resume)
#TODO texte en blanc quand selectionné

def formeResume(resume):
    return u"%s <span style=\"font: bold\">%s</span> %s" % resume 


class Liste_texte(object):
    def __init__(self, element, liste_textes):
        self.tab_title = "%s (%d)" % (element, len(liste_textes))

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


class MyDelegate (QtGui.QStyledItemDelegate):
    
    closedSignal = QtCore.Signal()

    def __init__(self, parent=None): 
        super(MyDelegate, self).__init__(parent)
        self.closeEditor.connect(self.cSignal)

    def cSignal(self):
        self.closedSignal.emit()


class ListViewDrop(QtGui.QListWidget):

    fileDropped = QtCore.Signal(list)

    def __init__(self, type, parent=None):
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
#FIXME bug Qt et MAC ne donne pas path complet
            for url in event.mimeData().urls():
                #print str(NSURL.URLWithString_(str(url.toString())))
                #links.append(str(url.toLocalFile())) #pb encodage
                links.append(url.toLocalFile())
            self.fileDropped.emit(links)
        else:
            event.ignore()


class Corpus_tab(QtGui.QListWidget):
    def __init__(self, type, parent=None):
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
        spacer_1.setSizePolicy(QtGui.QSizePolicy.Expanding, 
                                    QtGui.QSizePolicy.Minimum)
        H2LV1B.addWidget(spacer_1)
        self.checkTexts = QtGui.QCheckBox("file existence")
        H2LV1B.addWidget(self.checkTexts)
        self.checkTexts.stateChanged.connect(self.checkFileExistence)
    
        self.TextFilesDates = {}

        self.ViewListeTextes = ListViewDrop(self)
        self.ViewListeTextes.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.ViewListeTextes.fileDropped.connect(self.TxtFilesDropped)
        H2LV1.addWidget(self.ViewListeTextes)

        self.ViewListeTextes.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        addItem_ViewListeTextes = QtGui.QAction('add text', self)
        self.ViewListeTextes.addAction(addItem_ViewListeTextes)
        QtCore.QObject.connect(addItem_ViewListeTextes, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeTextes)
        efface_ViewListeTextesItem = QtGui.QAction('delete item', self)
        self.ViewListeTextes.addAction(efface_ViewListeTextesItem)
        QtCore.QObject.connect(efface_ViewListeTextesItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextesItem)
        efface_ViewListeTextes = QtGui.QAction('clear list', self)
        self.ViewListeTextes.addAction(efface_ViewListeTextes)
        QtCore.QObject.connect(efface_ViewListeTextes, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextes)
        self.send_codex_ViewListeTextes = QtGui.QAction('send to codex', self)
        self.ViewListeTextes.addAction(self.send_codex_ViewListeTextes)
        #QtCore.QObject.connect(send_codex_ViewListeTextes, 
        #   QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)

        H22Tab = QtGui.QTabWidget()
        H2.addWidget(H22Tab)
        H22TabDic = QtGui.QWidget()
        H22Tab.addTab(H22TabDic, "Dictionaries")
        H2L = QtGui.QVBoxLayout()
        H22TabDic.setLayout(H2L)
        H2L.setContentsMargins(0,0,0,0) 
        H2L.setSpacing(0) 

        self.ViewListeConcepts = ListViewDrop(self)
        H2L.addWidget(self.ViewListeConcepts)
        self.ViewListeConcepts.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.ViewListeConcepts.fileDropped.connect(self.ccfFilesDropped)
        self.ViewListeConcepts.setContextMenuPolicy(
                            QtCore.Qt.ActionsContextMenu)

        self.ViewListeConcepts.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        addItem_ViewListeConcepts = QtGui.QAction('add concept file', self)
        self.ViewListeConcepts.addAction(addItem_ViewListeConcepts)
        QtCore.QObject.connect(addItem_ViewListeConcepts, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeConcepts)

        efface_ViewListeConceptsItem = QtGui.QAction('delete item', self)
        self.ViewListeConcepts.addAction(efface_ViewListeConceptsItem)
        QtCore.QObject.connect(efface_ViewListeConceptsItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeConceptsItem)
        efface_ViewListeConcepts = QtGui.QAction('clear list', self)
        self.ViewListeConcepts.addAction(efface_ViewListeConcepts)
        QtCore.QObject.connect(efface_ViewListeConcepts, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeConcepts)

        self.ViewListeLexicons = ListViewDrop(self)
        H2L.addWidget(self.ViewListeLexicons)
        self.ViewListeLexicons.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.ViewListeLexicons.fileDropped.connect(self.dicFilesDropped)
        self.ViewListeLexicons.setContextMenuPolicy(
                        QtCore.Qt.ActionsContextMenu)

        addItem_ViewListeLexicons = QtGui.QAction('add lexicon file', self)
        self.ViewListeLexicons.addAction(addItem_ViewListeLexicons)
        QtCore.QObject.connect(addItem_ViewListeLexicons, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeLexicons)

        efface_ViewListeLexiconsItem = QtGui.QAction('delete item', self)
        self.ViewListeLexicons.addAction(efface_ViewListeLexiconsItem)
        QtCore.QObject.connect(efface_ViewListeLexiconsItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexiconsItem)
        efface_ViewListeLexicons = QtGui.QAction('clear list', self)
        self.ViewListeLexicons.addAction(efface_ViewListeLexicons)
        QtCore.QObject.connect(efface_ViewListeLexicons, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexicons)

        H22TabPar = QtGui.QWidget()
        H22Tab.addTab(H22TabPar, "Parameters")
          
    def TxtFilesDropped(self, l):
        existing = [] 
        for r in range(self.ViewListeTextes.count()):
            existing.append(self.ViewListeTextes.item(r).text())
        for url in list(set(l) - set(existing)):
            if os.path.exists(url):
                if os.path.splitext(url)[1] in ['.txt', '.TXT']:
                    item = QtGui.QListWidgetItem(url, self.ViewListeTextes)
                    item.setStatusTip(url)
                    self.TextFilesDates[url] = u"%s" %\
                        datetime.datetime.now().strftime("%Y-%m-%d")
                    item.setToolTip("insertion\
                         date %s" % self.TextFilesDates[url])
        self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())

    def efface_ViewListeTextes(self):
        self.ViewListeTextes.clear()
        self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
        self.TextFilesDates = {}

    def addItem_ViewListeTextes(self):
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self, 'Add file',
                                                         '.', '*.txt;*.TXT')
        if (fnames):
            self.TxtFilesDropped(fnames)

    def efface_ViewListeTextesItem(self):
        Items = self.ViewListeTextes.selectedItems()
        if (Items):
            for item in Items:
                del(self.TextFilesDates[item.text()])
                self.ViewListeTextes.takeItem(self.ViewListeTextes.row(item))
        self.numTexts.setText(u"%d texts"%self.ViewListeTextes.count())
    
    def efface_ViewListeConcepts(self):
        self.ViewListeConcepts.clear()

    def addItem_ViewListeConcepts(self):
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self, 'Add file',
                                                         '.', '*.fic;*.cat;*.col')
        if (fnames):
            self.ccfFilesDropped(fnames)

    def efface_ViewListeConceptsItem(self):
        Items = self.ViewListeConcepts.selectedItems()
        if (Items):
            for item in Items:
                self.ViewListeConcepts.takeItem(
                    self.ViewListeConcepts.row(item))

    def ccfFilesDropped(self, l):
        existing = [] 
        for r in range(self.ViewListeConcepts.count()):
            existing.append(self.ViewListeConcepts.item(r).text())
        for url in list(set(l) - set(existing)):
            if os.path.exists(url):
                if os.path.splitext(url)[1] in ['.cat', '.fic', '.col']:
                    item = QtGui.QListWidgetItem(url, self.ViewListeConcepts)
                    item.setStatusTip(url)
        self.ViewListeConcepts.sortItems()
        
    def efface_ViewListeLexicons(self):
        self.ViewListeLexicons.clear()

    def addItem_ViewListeLexicons(self):
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self, 'Add file',
                                                         '.', '*.dic')
        if (fnames):
            self.dicFilesDropped(fnames)

    def efface_ViewListeLexiconsItem(self):
        Items = self.ViewListeLexicons.selectedItems()
        if (Items):
            for item in Items:
                self.ViewListeLexicons.takeItem(
                    self.ViewListeLexicons.row(item))

    def dicFilesDropped(self, l):
        existing = [] 
        for r in range(self.ViewListeLexicons.count()):
            existing.append(self.ViewListeLexicons.item(r).text())
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
        fname, filt = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                    rep, 'Corpus (*.prc *.PRC)')
        return fname
      
    def openPRC(self):
        fname = self.getFile()
        if (fname) :
            corpus = Controller.parseCorpus()
            corpus.open(fname)

            self.nameCorpus.clear()
            self.nameCorpus.setText(fname)

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
            if self.checkTexts.checkState():
                if os.path.isfile(F):
                    self.ViewListeTextes.item(row).setForeground(
                                            QtGui.QColor("green"))
                else:
                    self.ViewListeTextes.item(row).setForeground(
                                                QtGui.QColor("red"))
            else:
                self.ViewListeTextes.item(row).setForeground(
                                        QtGui.QColor("black"))

    def mergePRC(self):
        fname = self.getFile()
        if (fname) :
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
        fileName, ext = QtGui.QFileDialog.getSaveFileName(self,
                                    "Save prc file", '', '*.prc') 
        corpusS = Controller.parseCorpus()    
        concepts = []
        for r in range(self.ViewListeConcepts.count()):
            concepts.append(self.ViewListeConcepts.item(r).text())
        ressources = []
        for r in  range(self.ViewListeLexicons.count()):
            ressources.append(self.ViewListeLexicons.item(r).text())
        corpusS.savefile(fileName, langue=u"français",
            ressource_list=ressources, concept_list=concepts, 
                                    text_dic=self.TextFilesDates)
        self.launchPRC_button.setEnabled(True)
        self.nameCorpus.setText(fileName)


class MrlwVarGenerator(object):
    """le 'generateur' Marlowe"""
    def __init__(self, parent=None):
        self.gen_mrlw = QtGui.QWidget()
        gen_mrlw_Hbox =  QtGui.QHBoxLayout() 
        self.gen_mrlw.setLayout(gen_mrlw_Hbox)
        gen_mrlw_Hbox.setContentsMargins(0,0,0,0) 
        gen_mrlw_Hbox.setSpacing(0) 

        gen_mrlw_Vbox_left = QtGui.QVBoxLayout()
        gen_mrlw_Hbox.addLayout(gen_mrlw_Vbox_left)
        self.gen_mrlw_phrase = QtGui.QTextEdit() 
        self.gen_mrlw_phrase.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.gen_mrlw_phrase.setFixedHeight(70) 
        gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_phrase)
        gen_mrlw_Button_varifie = QtGui.QPushButton("Identify")
        width = gen_mrlw_Button_varifie.fontMetrics().boundingRect(
                        gen_mrlw_Button_varifie.text()).width() + 30
        gen_mrlw_Button_varifie.setMaximumWidth(width)
        gen_mrlw_Button_varifie.clicked.connect(self.genere_identify)
        gen_mrlw_Vbox_left.addWidget(gen_mrlw_Button_varifie)
        gen_mrlw_Button_varifie_spacer = QtGui.QLabel()
        
        self.gen_mrlw_vars = QtGui.QTextEdit()
        self.gen_mrlw_vars.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.gen_mrlw_vars.setFixedHeight(70)
        gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_vars)
        gen_mrlw_genere_Hbox =   QtGui.QHBoxLayout() 
        gen_mrlw_Vbox_left.addLayout(gen_mrlw_genere_Hbox)
        gen_mrlw_Button_genere = QtGui.QPushButton("Generate")
        width = gen_mrlw_Button_genere.fontMetrics().boundingRect(
                        gen_mrlw_Button_genere.text()).width() + 30
        gen_mrlw_Button_genere.setMaximumWidth(width)
        gen_mrlw_genere_Hbox.addWidget(gen_mrlw_Button_genere)
        gen_mrlw_Button_genere.clicked.connect(self.genere_generate)
        gen_mrlw_genere_spacer = QtGui.QLabel()
        gen_mrlw_genere_spacer.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        gen_mrlw_genere_Hbox.addWidget(gen_mrlw_genere_spacer)

        self.gen_genere_spinbox = QtGui.QSpinBox()
        gen_mrlw_genere_Hbox.addWidget(self.gen_genere_spinbox)
        self.gen_genere_spinbox.setValue(1)
        self.gen_mrlw_result = QtGui.QTextEdit() 
        self.gen_mrlw_result.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.gen_mrlw_result.setFixedHeight(100)
        gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_result)

        gen_mrlw_Vbox_right = QtGui.QVBoxLayout()
        gen_mrlw_Hbox.addLayout(gen_mrlw_Vbox_right)
        self.gen_mrlw_test = QtGui.QLineEdit()
        self.gen_mrlw_test.returnPressed.connect(self.genere_test)
        self.gen_mrlw_test.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gen_mrlw_test.setFixedWidth(256)
        gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_test)
        self.gen_mrlw_test_result = QtGui.QListWidget()
        self.gen_mrlw_test_result.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_test_result)
        self.gen_mrlw_test_result.doubleClicked.connect(
                                self.genere_test_result_dc)
        self.gen_mrlw_files = QtGui.QListWidget()
        self.gen_mrlw_files.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.gen_mrlw_files.setFixedHeight(50)
        gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_files)

        self.genere_mrlw = generator_mrlw.mrlw_variables()
        for F in self.genere_mrlw.files:
            self.gen_mrlw_files.addItem(F)

    
    def genere_identify(self):
        phrase = self.gen_mrlw_phrase.toPlainText()
        if  (phrase != u''):
            self.gen_mrlw_vars.clear()
            phrase = re.sub('[\r\n]', ' ', phrase)
            self.gen_mrlw_vars.append(self.genere_mrlw.get_vars_sentence(phrase))

    def genere_test(self):
        mot = self.gen_mrlw_test.text()
        self.gen_mrlw_test_result.clear()       
        recup = []
        if (mot != u""):
            if re.search("^\s*/Var\S{1,}", mot):
                mot = re.sub("^\s*", "", mot)
                mot = re.sub("\s{1,}$", "", mot)
                if mot[1:] in self.genere_mrlw.mrlw_vars.keys():
                    recup = self.genere_mrlw.mrlw_vars[mot[1:]]
                    self.gen_mrlw_test_result.addItems(recup)
            else :
                mot = re.sub("^\s*","", mot)
                mot = re.sub("\s{1,}$", "", mot)
                recup = self.genere_mrlw.repere_vars2(mot)
                for i in recup:
                    self.gen_mrlw_test_result.addItem("/%s"%i[1])
                

    def genere_generate(self):
        phrase = self.gen_mrlw_vars.toPlainText()
        if  (phrase != u''):
            for i in range(self.gen_genere_spinbox.value()):
                self.gen_mrlw_result.append(self.genere_mrlw.genere_phrase(phrase))
        
    
    def genere_test_result_dc(self):
        self.gen_mrlw_test.clear()
        self.gen_mrlw_test.setText(self.gen_mrlw_test_result.currentItem().text())
        self.genere_test()


class Journal(object):
    """Le journal d'enquête"""
    def __init__(self, parent=None): 
        self.journal = QtGui.QWidget()
        journal_vbox =  QtGui.QVBoxLayout() 
        self.journal.setLayout(journal_vbox)
        journal_vbox.setContentsMargins(0,0,0,0) 
        journal_vbox.setSpacing(0)

        self.history =  QtGui.QTextEdit()
        journal_vbox.addWidget(self.history)

        journal_hobx = QtGui.QHBoxLayout()

        spacer1 = QtGui.QLabel()
        spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                         QtGui.QSizePolicy.Minimum)
        journal_hobx.addWidget(spacer1)

        journal_button_save = QtGui.QPushButton('Save journal')
        width = journal_button_save.fontMetrics().boundingRect(
                        journal_button_save.text()).width() + 30
        journal_button_save.setMaximumWidth(width)
        journal_button_save.clicked.connect(self.journal_save)
        journal_hobx.addWidget(journal_button_save)
        journal_vbox.addLayout(journal_hobx)

    def journal_save(self):
	dte = str(datetime.date.today())
	fname, filt = QtGui.QFileDialog.getSaveFileName(self.journal,
                             'Save file','journal_%s.txt'%dte,'*.txt')
	if (fname):
		with open(fname, 'w') as journal_file:
			journal_file.write(self.history.toPlainText().encode('utf-8'))

class NetworksViewer(object):
    """Display co-occurence network"""
    def __init__(self, items, parent=None):
        self.show_network_widget = QtGui.QWidget()
        show_network_box = QtGui.QVBoxLayout()
        # on prend toute la place
        show_network_box.setContentsMargins(0,0,0,0) 
        show_network_box.setSpacing(0) 
        self.show_network_widget.setLayout(show_network_box)

        #selecteur de concept
        net_sel_concept = QtGui.QComboBox()
        net_sel_concept.addItems([u"Entities"])
        show_network_box.addWidget(net_sel_concept)

        Network_list =  QtGui.QListWidget()
        Network_list.addItems(items)
        show_network_box.addWidget(Network_list)

class TextElements(object):
    """Display text elements"""
    def __init__(self,  parent=None):
        self.widget = QtGui.QWidget()
        box = QtGui.QVBoxLayout()
        box.setContentsMargins(0,0,0,0) 
        box.setSpacing(0) 
        self.widget.setLayout(box)

        selector = QtGui.QComboBox()
        selector.addItems([u"Entity categories"])
        box.addWidget(selector)

        self.element_list =  QtGui.QListWidget()
        box.addWidget(self.element_list)


def hide_close_buttons(tabs_widget,index):
        """hide close button on tab no 'index', on the left side for Mac"""
        if tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide):
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide).resize(0,0)
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide).hide()
        elif tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide):
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide).resize(0,0)
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide).hide()


