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

class MyMenu(QtGui.QMenuBar):
    """the menu"""
    def __init__(self, parent=None): 
        QtGui.QMenuBar.__init__(self)

        ##################################################
        #Corpus and Server
        #TODO avec ou sans &?
        Menu_Corpus = self.addMenu(self.tr('Corpus and Server'))
        Menu_distant = Menu_Corpus.addMenu(QtGui.QIcon('images/distant.png'),
                                                             self.tr('Remote'))

        get_remote_corpus = Controller.myxml()
        if get_remote_corpus.get():
            if get_remote_corpus.parse():
                for corpus in get_remote_corpus.getDataCorpus(): 
                    #TODO not enabled if cannot reach port 60000
                    t = QtGui.QAction(corpus[0], self)
                    t.triggered.connect(functools.partial(self.connect_server,
                                 "prosperologie.org", corpus[1]))
                    Menu_distant.addAction(t)
        
        menu_local = Menu_Corpus.addMenu(QtGui.QIcon('images/home.png'),
             self.tr('Local')) 
        self.local_connect = QtGui.QAction(self.tr("Connect"), self)
        menu_local.addAction(self.local_connect)
        self.local_edit = QtGui.QAction(self.tr("Edit project"), self)
        menu_local.addAction(self.local_edit)
        #TODO edit local server parameters: path, port
        menu_local_param = QtGui.QAction(self.tr("Local server parameters"), self)
        menu_local.addAction(menu_local_param)
        menu_local_param.setEnabled(False)

        Menu_Corpus.addSeparator()

        self.codex = QtGui.QAction(self.tr("Codex"), self)
        Menu_Corpus.addAction(self.codex)

        self.server_vars = QtGui.QAction(self.tr("Variables testing"), self)
        Menu_Corpus.addAction(self.server_vars)

        #TODO transform corpus p1<->p2
        menu_convert_corpus = QtGui.QAction(self.tr("Convert P1 and P2 corpus"), self)
        Menu_Corpus.addAction(menu_convert_corpus)
        menu_convert_corpus.setEnabled(False) 

        #TODO recup corpus, fusion, generer sous corpus
        #TODO Constellations and corpus comparisons

        ##################################################
        #Concepts and lexics
        menu_concepts = self.addMenu(self.tr('Concepts'))
        menu_concepts_edition = QtGui.QAction(self.tr("Edition"), self)
        menu_concepts.addAction(menu_concepts_edition)
        menu_concepts_edition.setEnabled(False)
        menu_sycorax =  QtGui.QAction(self.tr("Sycorax"), self)
        menu_concepts.addAction(menu_sycorax)
        menu_sycorax.setEnabled(False)
        
        ##################################################
        #Texts
        Menu_Texts = self.addMenu(self.tr('Texts and Contexts'))
        self.contexts = QtGui.QAction(self.tr('Contexts'), self)
        Menu_Texts.addAction(self.contexts)
        Menu_AddTex = QtGui.QAction(self.tr('Add a new text'), self)
        Menu_Texts.addAction(Menu_AddTex)
        Menu_AddTex.setEnabled(False)
        Menu_ModTex = QtGui.QAction(self.tr('Action on selected texts'), self)
        Menu_Texts.addAction(Menu_ModTex)
        Menu_ModTex.setEnabled(False)

        ##################################################
        #Viz and computations
        menu_comput = self.addMenu(self.tr('Computations'))
        self.pers =  QtGui.QAction(self.tr("Persons"), self)
        menu_comput.addAction(self.pers)
        self.pers.setEnabled(False)
        #TODO viz
        #TODO author signatures, grappes, periodisations
        #TODO corpus indicators and properties
        #TODO list evolutions

        ##################################################
        #Marlowe
        Menu_Marlowe = self.addMenu(self.tr('Marlowe'))
        self.marlowe_gen = QtGui.QAction(self.tr("Variant generation"), self)
        Menu_Marlowe.addAction(self.marlowe_gen)
        self.Marlowe_remote = QtGui.QAction(self.tr("Remote"), self)
        Menu_Marlowe.addAction(self.Marlowe_remote)

        ##################################################
        #Parameters&sHelp
        menu_param = self.addMenu(self.tr('Parameters and help'))
        menu_parameters = QtGui.QAction(self.tr('Parameters'), self)
        menu_param.addAction(menu_parameters)
        menu_parameters.setEnabled(False)
        #ex reduire le poids seulement si expr englobante de meme type
        self.manual = QtGui.QAction(self.tr('Manual'), self)
        menu_param.addAction(self.manual)

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

class actantsTab(QtGui.QWidget):
    """Widget actants lists"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        H = QtGui.QHBoxLayout()
        self.setLayout(H)
        H.setContentsMargins(0,0,0,0) 
        self.L = QtGui.QListWidget()
        H.addWidget(self.L)
        #self.T = QtGui.QTreeWidget()
        #H.addWidget(self.T)
        V1 = QtGui.QVBoxLayout()
        H.addLayout(V1)
        H1 = QtGui.QLabel('emerging configurations')
        V1.addWidget(H1)
        L1 = QtGui.QListWidget()
        V1.addWidget(L1)
        V2 = QtGui.QVBoxLayout()
        H.addLayout(V2)
        H2 = QtGui.QLabel("incompatibilities")
        V2.addWidget(H2)
        L2 = QtGui.QListWidget()
        V2.addWidget(L2)
        
class authorsTab(QtGui.QWidget):
    """Widget authors lists"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        H = QtGui.QHBoxLayout()
        self.setLayout(H)
        H.setContentsMargins(0,0,0,0) 
        self.L = QtGui.QListWidget()
        H.addWidget(self.L)
        #FIXME ecrase cadrans 
        V1 = QtGui.QVBoxLayout()
        H.addLayout(V1)
        H0 = QtGui.QLabel('first\nlast\nnbpg\nnbtxt')
        V1.addWidget(H0)
        S = QtGui.QComboBox()
        V1.addWidget(S)
        L2 = QtGui.QListWidget()
        H.addWidget(L2)
        V2 = QtGui.QVBoxLayout()
        H.addLayout(V2)
        H1 = QtGui.QLabel('specific')
        V2.addWidget(H1)
        L3 = QtGui.QListWidget()
        V2.addWidget(L3)
        V3 = QtGui.QVBoxLayout()
        H.addLayout(V3)
        H2 = QtGui.QLabel('absent')
        V3.addWidget(H2)
        L4 = QtGui.QListWidget()
        V3.addWidget(L4)
        
class LexiconTab(QtGui.QWidget):
    """Widget displaying lexicon lists"""
    #TODO abandonner 3 colonnes
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        V = QtGui.QVBoxLayout()
        self.setLayout(V)
        V.setContentsMargins(0,0,0,0) 
        V.setSpacing(0) 
        VHC = QtGui.QHBoxLayout()
        V.addLayout(VHC)
        self.select = QtGui.QComboBox()
        #send persons to a dedicated tab
        self.select.addItems([ 
            u'entities',
            u"qualities",
            u"markers", 
            u"verbs", 
            "undefined", 
            "persons", 
            u"expressions",  
            u"numbers",
            u"function words"
        ])
        #TODO add a special tab for indef in NE tab
        #TODO add those
        for i in range(7,9):
            self.select.model().item(i).setEnabled(False)
        VHC.addWidget(self.select)

        # un spacer pour mettre les commandes sur la droite
        spacer3 = QtGui.QLabel()
        spacer3.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        VHC.addWidget(spacer3)

        #sorting command
        self.sort_command = QtGui.QComboBox()
        self.sort_command.addItems(sorting_command_list)
        VHC.addWidget(self.sort_command)

        #une box horizontale pour liste, score et deploiement
        VH = QtGui.QHBoxLayout()
        V.addLayout(VH) 
        #lexicon liste
        self.dep0 = MyListWidget()
        VH.addWidget(self.dep0)
        #I deployment
        self.depI = MyListWidget()
        VH.addWidget(self.depI)
        #II deployment 
        self.depII = MyListWidget()
        VH.addWidget(self.depII)

class ConceptTab(QtGui.QWidget):
    #TODO systématiser 3 colonnes ou passer à deux ?
    """Widget displaying concept lists"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        V = QtGui.QVBoxLayout()
        self.setLayout(V)
        V.setContentsMargins(0,0,0,0) 
        V.setSpacing(0) 

        VHC = QtGui.QHBoxLayout()
        V.addLayout(VHC)
        self.select = QtGui.QComboBox()
        self.select.addItems([
            u"entities&fictions",  
            u"entity categories",
            u"quality categories", 
            u"marker categories", 
            u"verb categories",
            u"collections",
            u"fictions"
            ])
        VHC.addWidget(self.select)

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        VHC.addWidget(spacer)

        #sorting command
        self.sort_command = QtGui.QComboBox()
        self.sort_command.addItems(sorting_command_list)
        VHC.addWidget(self.sort_command)

        VH = QtGui.QHBoxLayout()
        V.addLayout(VH) 

        #concept list 
        self.dep0 = MyListWidget()
        VH.addWidget(self.dep0)
        #I deployment
        self.depI = MyListWidget()
        VH.addWidget(self.depI)
        #II deployment 
        self.depII = MyListWidget()
        VH.addWidget(self.depII)

class Contexts(QtGui.QWidget):
    """Widget displaying corpus text contexts"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        V = QtGui.QVBoxLayout()
        self.setLayout(V)
        V.setContentsMargins(0,0,0,0) 
        V.setSpacing(0) 
        VHC = QtGui.QHBoxLayout()
        V.addLayout(VHC)

        #TODO add CTX commands
        #spacer_CTX_1 = QtGui.QLabel()
        #spacer_CTX_1.setSizePolicy(QtGui.QSizePolicy.Expanding, 
                                        #QtGui.QSizePolicy.Minimum)
        #VHC.addWidget(spacer_CTX_1)
    
        #self.NOT5Commands1 = QtGui.QPushButton()
        #self.NOT5Commands1.setIcon(QtGui.QIcon("images/gear.png"))
        ##desactivé au lancement, tant qu'on a pas de liste
        #self.NOT5Commands1.setEnabled(False) 
        #VHC.addWidget(self.NOT5Commands1)

        #une box horizontale pour liste et deploiement
        VH = QtGui.QHBoxLayout()
        V.addLayout(VH) 
        self.l = QtGui.QListWidget()
        self.l.setAlternatingRowColors(True)
        self.l.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                     QtGui.QSizePolicy.Preferred)
        VH.addWidget(self.l)
        self.cont = QtGui.QListWidget()
        self.cont.setAlternatingRowColors(True)
        VH.addWidget(self.cont)
        self.cont.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)

class SaillantesProperties(QtGui.QWidget):
    """Widget displaying text saillant properties"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        #TODO use QTreeView and model

        #Vbox des actants du texte
        VAct = QtGui.QVBoxLayout()
        saillantesActTitle = QtGui.QLabel()
        saillantesActTitle.setText(self.tr("Actants"))
        VAct.addWidget(saillantesActTitle)
        self.Act = QtGui.QListWidget()
        VAct.addWidget(self.Act)

        #Vbox des categories du texte
        VCat = QtGui.QVBoxLayout()
        saillantesCatTitle = QtGui.QLabel()
        saillantesCatTitle.setText(self.tr("Categories"))
        VCat.addWidget(saillantesCatTitle)
        self.Cat = QtGui.QListWidget()
        VCat.addWidget(self.Cat)

        #Vbox des collections du texte
        VCol = QtGui.QVBoxLayout()
        saillantesColTitle = QtGui.QLabel()
        saillantesColTitle.setText(self.tr("Collections"))
        VCol.addWidget(saillantesColTitle)
        self.Col = QtGui.QListWidget()
        VCol.addWidget(self.Col)

        H = QtGui.QHBoxLayout()
        H.setContentsMargins(0,0,0,0) 
        H.setSpacing(0) 
        self.setLayout(H)
        H.addLayout(VAct)
        H.addLayout(VCat)
        H.addLayout(VCol)

class textCTX(QtGui.QWidget):
    """Widget displaying context for a text"""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        V = QtGui.QVBoxLayout()
        V.setContentsMargins(0,0,0,0) 
        V.setSpacing(0) 
        self.setLayout(V)

        self.T = QtGui.QTableWidget()
        self.T.verticalHeader().setVisible(False)
        self.T.setColumnCount(2)
        self.T.setHorizontalHeaderLabels([self.tr('field'), self.tr('value')])
        self.T.horizontalHeader().setStretchLastSection(True)     
        V.addWidget(self.T)
    
        commands = QtGui.QHBoxLayout()
        self.valid = QtGui.QPushButton(self.tr("save"))
        commands.addWidget(self.valid)
        self.reset = QtGui.QPushButton(self.tr("reset"))
        commands.addWidget(self.reset)
        spacer = QtGui.QLabel()
        spacer.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        commands.addWidget(spacer) 
        #TOTO add, delete
        B = QtGui.QPushButton(u"\u25cb")
        commands.addWidget(B)
        B.setEnabled(False)
        V.addLayout(commands)

class MyListWidgetTexts(QtGui.QListWidget):
    """a specific widget for textslists""" 
    def __init__(self, parent=None):
        QtGui.QListWidget.__init__(self)
        self.setAlternatingRowColors(True)
        self.itemSelectionChanged.connect(self.changeColor)
        #TODO directly ask children without list
        self.widget_list = []
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    def changeColor(self):
        currentRow = self.currentRow()
        for r in range(self.count()):
            if (r == currentRow):
                self.item(r).label.setStyleSheet("color: white;")  
            else:
                 self.item(r).label.setStyleSheet("color: black;")

    def deselect_all(self):
        self.clearSelection()
        for r in range(self.count()):
             self.item(r).label.setStyleSheet("color: black;")

class TexteWidgetItem(QtGui.QListWidgetItem):
    def __init__(self, text, parent=None):
        QtGui.QListWidgetItem.__init__(self)
        #self.setText(text)
        self.resume = text
        txt_resume = self.formeResume()
        self.label = QtGui.QLabel(txt_resume)
        self.setToolTip(txt_resume)
        #self.setData(QtCore.Qt.UserRole, text)

    def formeResume(self):
        return u"%s <span style=\"font: bold\">%s</span> %s" % self.resume 

class ListTexts(QtGui.QWidget):
    """Display texts corpus and anticorpus for an element"""
    def __init__(self, element, lsems, ltxts):
        QtGui.QWidget.__init__(self)

        self.lsems = lsems
        #print "C31471", lsems
        self.ltxts = ltxts
        HBox = QtGui.QHBoxLayout()
        HBox.setContentsMargins(0,0,0,0) 
        HBox.setSpacing(5) 
        self.setLayout(HBox)

        #TODO sorting
        #self.orderdt = QtGui.QAction("order by date", self, triggered=lambda: self.sortby("dt")) 
        #self.orderoc = QtGui.QAction("order by occurence", self, triggered=lambda: self.sortby("oc")) 

        if (element):
            self.title = "%s (%d)" % (element, len(self.lsems))
            self.corpus = MyListWidgetTexts()
            HBox.addWidget(self.corpus)
            self.anticorpus = MyListWidgetTexts()
            HBox.addWidget(self.anticorpus)
            #self.corpus.addAction(self.orderoc)
        else:
            self.corpus = MyListWidgetTexts()
            HBox.addWidget(self.corpus)
            for sem, tri in self.sort():
                txt = self.ltxts[sem]
                WI = TexteWidgetItem(txt.getResume())
                self.corpus.addItem(WI)
                self.corpus.setItemWidget(WI, WI.label)
                self.corpus.widget_list.append(txt) 

    def add(self, sem, resume):
        if sem in self.lsems.keys(): 
        #add to corpus list
            resume = ("%s [%s]"%(resume[0], self.lsems[sem]) , resume[1], resume[2])
            WI = TexteWidgetItem(resume)
            self.corpus.addItem(WI)
            self.corpus.setItemWidget(WI, WI.label)
            self.corpus.widget_list.append(self.ltxts[sem])
        else:
        #add to anticorpus list
            WI = TexteWidgetItem(resume)
            self.anticorpus.addItem(WI)
            self.anticorpus.setItemWidget(WI, WI.label)
            self.anticorpus.widget_list.append(self.ltxts[sem]) 

    def sort(self):
        l = self.ltxts.keys()
        liste = {}
        for e in l:
            liste[e] = self.get_date(self.ltxts[e])
        return sorted(liste.items(), key=lambda (k, v): v) 

    def get_date(self, txt):
        date = txt.getCTX("date")
        date = re.split(" ", date) #split date and time
        if (len(date) > 1):
            date, heure = date
        else:
            date = date[0]
        return "-".join(reversed(re.split("/", date)))

class MyDelegate(QtGui.QStyledItemDelegate):
    
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
        openPRC_button = QtGui.QPushButton(self.tr("Open"))
        openPRC_button.setToolTip(self.tr("Open a .prc file"))
        openPRC_button.clicked.connect(self.openPRC)
        H1.addWidget(openPRC_button)
        mergePRC_button= QtGui.QPushButton(self.tr("Merge"))
        mergePRC_button.setToolTip(self.tr("Merge text list with a .prc file"))
        H1.addWidget(mergePRC_button)
        mergePRC_button.clicked.connect(self.mergePRC)
        savePRC_button= QtGui.QPushButton(self.tr("Save"))
        H1.addWidget(savePRC_button)
        savePRC_button.clicked.connect(self.savePRC)
        self.launchPRC_button= QtGui.QPushButton(self.tr("Read"))
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
        self.checkTexts = QtGui.QCheckBox(self.tr("file existence"))
        H2LV1B.addWidget(self.checkTexts)
        self.checkTexts.stateChanged.connect(self.checkFileExistence)
    
        self.TextFilesDates = {}

        self.ViewListeTextes = ListViewDrop(self)
        self.ViewListeTextes.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.ViewListeTextes.fileDropped.connect(self.TxtFilesDropped)
        H2LV1.addWidget(self.ViewListeTextes)

        self.ViewListeTextes.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        addItem_ViewListeTextes = QtGui.QAction(self.tr('add text'), self)
        self.ViewListeTextes.addAction(addItem_ViewListeTextes)
        QtCore.QObject.connect(addItem_ViewListeTextes, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeTextes)
        efface_ViewListeTextesItem = QtGui.QAction(self.tr('delete item'), self)
        self.ViewListeTextes.addAction(efface_ViewListeTextesItem)
        QtCore.QObject.connect(efface_ViewListeTextesItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextesItem)
        efface_ViewListeTextes = QtGui.QAction(self.tr('clear list'), self)
        self.ViewListeTextes.addAction(efface_ViewListeTextes)
        QtCore.QObject.connect(efface_ViewListeTextes, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeTextes)
        self.send_codex_ViewListeTextes = QtGui.QAction(self.tr('send to codex'), self)
        self.ViewListeTextes.addAction(self.send_codex_ViewListeTextes)
        #QtCore.QObject.connect(send_codex_ViewListeTextes, 
        #   QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)

        H22Tab = QtGui.QTabWidget()
        H2.addWidget(H22Tab)
        H22TabDic = QtGui.QWidget()
        H22Tab.addTab(H22TabDic, self.tr("Dictionaries"))
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
        addItem_ViewListeConcepts = QtGui.QAction(self.tr('add concept file'), self)
        self.ViewListeConcepts.addAction(addItem_ViewListeConcepts)
        QtCore.QObject.connect(addItem_ViewListeConcepts, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeConcepts)

        efface_ViewListeConceptsItem = QtGui.QAction(self.tr('delete item'), self)
        self.ViewListeConcepts.addAction(efface_ViewListeConceptsItem)
        QtCore.QObject.connect(efface_ViewListeConceptsItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeConceptsItem)
        efface_ViewListeConcepts = QtGui.QAction(self.tr('clear list'), self)
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

        addItem_ViewListeLexicons = QtGui.QAction(self.tr('add lexicon file'), self)
        self.ViewListeLexicons.addAction(addItem_ViewListeLexicons)
        QtCore.QObject.connect(addItem_ViewListeLexicons, 
            QtCore.SIGNAL("triggered()"), self.addItem_ViewListeLexicons)

        efface_ViewListeLexiconsItem = QtGui.QAction(self.tr('delete item'), self)
        self.ViewListeLexicons.addAction(efface_ViewListeLexiconsItem)
        QtCore.QObject.connect(efface_ViewListeLexiconsItem, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexiconsItem)
        efface_ViewListeLexicons = QtGui.QAction(self.tr('clear list'), self)
        self.ViewListeLexicons.addAction(efface_ViewListeLexicons)
        QtCore.QObject.connect(efface_ViewListeLexicons, 
            QtCore.SIGNAL("triggered()"), self.efface_ViewListeLexicons)

        H22TabPar = QtGui.QWidget()
        H22Tab.addTab(H22TabPar, self.tr("Parameters"))
          
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
                    item.setToolTip(self.tr("insertion date %s") % self.TextFilesDates[url])
        self.numTexts.setText(self.tr("%d texts")%self.ViewListeTextes.count())

    def efface_ViewListeTextes(self):
        self.ViewListeTextes.clear()
        self.numTexts.setText(self.tr("%d texts")%self.ViewListeTextes.count())
        self.TextFilesDates = {}

    def addItem_ViewListeTextes(self):
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self,
         self.tr('Add file'), '.', '*.txt;*.TXT')
        if (fnames):
            self.TxtFilesDropped(fnames)

    def efface_ViewListeTextesItem(self):
        Items = self.ViewListeTextes.selectedItems()
        if (Items):
            for item in Items:
                del(self.TextFilesDates[item.text()])
                self.ViewListeTextes.takeItem(self.ViewListeTextes.row(item))
        self.numTexts.setText(self.tr("%d texts")%self.ViewListeTextes.count())
    
    def efface_ViewListeConcepts(self):
        self.ViewListeConcepts.clear()

    def addItem_ViewListeConcepts(self):
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self,
            self.tr('Add file'), '.', '*.fic;*.cat;*.col')
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
        fnames, filt = QtGui.QFileDialog.getOpenFileNames(self, 
            self.tr('Add file'), '.', '*.dic')
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
        fname, filt = QtGui.QFileDialog.getOpenFileName(self, 
            self.tr('Open file'), rep, 'Corpus (*.prc *.PRC)')
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
                item.setToolTip(self.tr("insertion date %s") % f[1])
                self.ViewListeTextes.addItem(item)
                self.TextFilesDates[f[0]] = f[1]
            self.numTexts.setText(self.tr("%d texts")%self.ViewListeTextes.count())
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
                    item.setToolTip(self.tr("insertion date %s") % f[1])
                    self.ViewListeTextes.addItem(item)
            self.ViewListeTextes.sortItems()
            self.numTexts.setText(self.tr("%d texts")%self.ViewListeTextes.count())
            if self.checkTexts.checkState() :
                self.checkFileExistence()

    def savePRC(self):
        fileName, ext = QtGui.QFileDialog.getSaveFileName(self,
                                    self.tr("Save prc file"), '', '*.prc') 
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
        gen_mrlw_Button_varifie = QtGui.QPushButton(self.tr("Identify"))
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
        gen_mrlw_Button_genere = QtGui.QPushButton(self.tr("Generate"))
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

        #TODO remove this button, translate
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
                             self.tr('Save file'),'journal_%s.txt'%dte,'*.txt')
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

        self.selector = QtGui.QComboBox()
        self.selector.addItems([u'entities', 'collections', u"entity categories",
            'verb categories', 'marker categories', 'quality categories',
            'fictions', 'expressions', 'undefined'])
        box.addWidget(self.selector)
        self.selector.model().item(8).setEnabled(False)

        self.element_list =  QtGui.QListWidget()
        box.addWidget(self.element_list)

class MyListWidget(QtGui.QWidget):
    """a specific widget for concept/lexicon lists""" 
    deselected = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.listw = QtGui.QListWidget()
        self.listw.setAlternatingRowColors(True)
        self.listw.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.previousItem = False
        self.listw.itemClicked.connect(self.deselect)
        self.listw.installEventFilter(self)

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)
        vbox.setContentsMargins(0, 0, 0, 0)
        #vbox.setSpacing(0)
        self.label = QtGui.QLabel()
        self.label.setVisible(False)
        self.label.setStyleSheet("* {border: 2px solid rgb(234, 240, 253);\
            background-color: white; padding: 2px; margin: 0px;\
            text-transform: lowercase;}")
        vbox.addWidget(self.label)
        vbox.addWidget(self.listw)

    def deselect(self, item):
        if (self.previousItem): 
            if ( str(self.previousItem) == str(item) ):
                self.listw.clearSelection()
                self.listw.setCurrentRow(-1)
                self.previousItem = False
                self.deselected.emit()
            else :
                self.previousItem = item
        else : 
            self.previousItem = item

    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.KeyPress and
                widget is self.listw):
            if (event.type()==QtCore.QEvent.KeyPress and (event.key() in
                        range(256) or event.key()==QtCore.Qt.Key_Space)):
                if hasattr(self, "motif"):
                    self.motif += chr(event.key())
                else:
                    self.motif = chr(event.key()) 
                self.searchmotif(self.motif, 0)
                return True
            elif (event.type()==QtCore.QEvent.KeyPress and
                        (event.key()==QtCore.Qt.Key_Escape)):
                self.motif = ""
                self.searchmotif('', 0)
                return True
            elif (event.type()==QtCore.QEvent.KeyPress and
                        (event.key()==QtCore.Qt.Key_Backspace)):
                if hasattr(self, "motif"):
                    self.motif = self.motif[:-1]
                    self.searchmotif(self.motif, 0)
                return True
            elif (event.type()==QtCore.QEvent.KeyPress and
                        (event.key()==QtCore.Qt.Key_Return)):
                if hasattr(self, "motif"):
                    if (self.motif != ""):
                        self.searchmotif(self.motif, 1)
                return True
        return QtGui.QWidget.eventFilter(self, widget, event)

    def searchmotif(self, motif, pos=0):
        if (self.motif != ""):
            if (pos == 0):
                self.pos = 0
            else:
                self.pos += 1
            matches = self.listw.findItems(self.motif, QtCore.Qt.MatchContains)
            if (matches):
                if (self.pos >= len(matches)):
                    self.pos = 0
                self.listw.setCurrentItem(matches[self.pos])
            else:
                self.listw.clearSelection()
                self.deselected.emit()
            self.label.setText(self.motif)
            self.label.setVisible(True)
        else:
            self.pos = 0
            self.listw.clearSelection()
            self.deselected.emit()
            self.label.setVisible(False)
            
class Explorer(QtGui.QWidget):
    """Searches"""
    def __init__(self, parent=None): 
        QtGui.QWidget.__init__(self)
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)
        vbox.setContentsMargins(0,0,0,0) 
        vbox.setSpacing(0) 

        self.saisie = QtGui.QLineEdit()
        vbox.addWidget(self.saisie)
        #self.saisie.setEnabled(False)

        hbox1 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox1)
        self.select_fix = QtGui.QComboBox()
        self.select_fix.addItems(["prefix", "suffix", "infix"])
        hbox1.addWidget(self.select_fix)

        Explo_spacer1 = QtGui.QLabel()
        Explo_spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                         QtGui.QSizePolicy.Minimum)
        hbox1.addWidget(Explo_spacer1)

        self.sensitivity = QtGui.QCheckBox(self.tr("case sensitivity"))
        hbox1.addWidget(self.sensitivity)

        hbox2 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox2)
        self.liste = MyListWidget()
        hbox2.addWidget(self.liste)

        #TODO display item presence in concepts
        vbox2 = QtGui.QVBoxLayout()
        hbox2.addLayout(vbox2)
        #TODO clic -> to the list, typer-retyper
        self.explo_lexi = QtGui.QListWidget()
        vbox2.addWidget(self.explo_lexi)
        self.explo_easter = QtGui.QLabel()
        vbox2.addWidget(self.explo_easter)
        #self.explo_concepts = QtGui.QListWidget()
        #vbox2.addWidget(self.explo_concepts)

class ServerVars(QtGui.QListWidget):
    """Asking directly the server vars"""
    def __init__(self, parent=None): 
        QtGui.QListWidget.__init__(self)
        Vbox =  QtGui.QVBoxLayout() 
        self.setLayout(Vbox)
        Vbox.setContentsMargins(0,0,0,0) 
        Vbox.setSpacing(0) 
        Hbox = QtGui.QHBoxLayout()
        server_vars_champL = QtGui.QFormLayout()
        self.champ = QtGui.QLineEdit()
        Hbox.addWidget(self.champ)
        self.button_eval = QtGui.QPushButton('eval')
        Hbox.addWidget(self.button_eval)
        self.button_getsem = QtGui.QPushButton('get sem')
        Hbox.addWidget(self.button_getsem)
        self.button_eval_index = QtGui.QPushButton('index')
        Hbox.addWidget(self.button_eval_index)

        self.button_clear = QtGui.QPushButton('clear')
        Hbox.addWidget(self.button_clear)

        Vbox.addLayout(Hbox)
        #self.result = QtGui.QTextEdit(readOnly = True) 
        self.result = QtGui.QTextEdit(readOnly = False) 
        Vbox.addWidget(self.result)
        self.button_clear.clicked.connect(self.result.clear)

def hide_close_buttons(tabs_widget,index):
        """hide close button on tab no 'index', on the left side for Mac"""
        if tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide):
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide).resize(0,0)
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.RightSide).hide()
        elif tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide):
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide).resize(0,0)
            tabs_widget.tabBar().tabButton(index, QtGui.QTabBar.LeftSide).hide()

sorting_command_list = [
    u"occurences",
    u"deployment",
    u"alphabetically",
    "number of texts",
    "first apparition",
    "last apparition",
    "number of authors",
    "weigthed",
    "day present number",
    "relatif nb jours",
    "representant number",
    "network element number"
    ]

