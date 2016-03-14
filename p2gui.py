#!/usr/bin/python
# -*- coding: utf-8 -*-

from PySide import QtCore 
from PySide import QtGui 
from PySide import QtWebKit
import sys
import re
import datetime
import os
import time
import functools
import subprocess
import threading
import socket 
import atexit

from fonctions import translate
import xml_info
import interface_prospero
import Viewer
import Controller


class client(object):
    def __init__(self, h, p):
        self.c = interface_prospero.ConnecteurPII() 
        #self.c.start()
        self.c.set(h, p)
        self.Etat = self.c.connect_x(5)
        #self.teste_connect()
        if not (self.Etat):
            msgBox = QtGui.QMessageBox()
            msgBox.setText("connection failed")
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()

    def teste_connect(self):
        teste = self.c.connect()
        if (teste):
            self.Etat = True
        else :
            self.Etat = False
            print "niet"

    def disconnect(self):
        self.c.disconnect()

    def recup_liste_concept(self, sem):
        var = "%s[0:]" % sem
        return re.split(", ", self.c.eval_variable(var))
    

    def eval_vector(self, type, type_calc):
        return self.c.eval_vect_values(type, type_calc)

    def eval_var(self, var):
        #self.eval_var_result = self.c.eval_variable(var)
        return self.c.eval_variable(var)
        
    def eval_var_ctx(self, props, ctx_range):
        return self.c.eval_ctx(props, ctx_range)

    def eval_get_sem(self, exp, sem):
        """jp : pour retrouver la sémantique d'un élément : 
        getsem 'nucléaire' $ent
        """
        #exp = exp.encode('utf-8')
        #return self.c.eval_fonc("getsem:%s:%s" % (exp, sem))
        return self.c.eval_fonct(u"getsem", exp, sem)

    def add_cache_var(self, cle, val):
        self.c.add_cache_var(cle, val)

    # pour anticiper les getsem /corpus/texte $txt
    def add_cache_fonct(self, cle, val):
        self.c.add_cache_fonc(cle, val)
    
    def creer_msg_search(self, fonc, element, pelement='', txt=False, 
                                    ptxt='', ph=False, pph='', val=False):
        return self.c.creer_msg_search(fonc, element, 
                        pelement, txt, ptxt, ph, pph, val)

    def eval (self, L):
        return self.c.eval(L)

    def eval_set_ctx(self, sem_txt, field, val):
        return self.c.eval_set_ctx(sem_txt, field, val)


class Principal(QtGui.QMainWindow):
    def __init__(self, parent=None):
        #super(Principal, self).__init__()
        QtGui.QMainWindow.__init__(self, parent)
        self.initUI()
        
    def pre_calcule(self):
        self.activity("pre-computing : texts")
        self.preCompute = Controller.preCompute(self)
        self.listeObjetsTextes = self.preCompute.listeObjetsTextes

        self.NOT5_list.clear()
        self.NOT5_list.addItems(self.preCompute.liste_champs_ctx)

        self.PrgBar.setv(50)

        # associated values
        self.activity("pre-computing : values")
        compteur = 0
        max_compteur = len(self.preCompute.type_var) * len(self.preCompute.type_calcul)
        for typ in self.preCompute.type_var :
            for calc in self.preCompute.type_calcul:
            #freq et nbaut ne marche pas ?
                self.preCompute.cacheAssocValue(typ, calc)
                compteur += 1
                self.PrgBar.setv(50 + (int(float(compteur) * 50 / max_compteur)))
        self.PrgBar.reset()
    
    def initUI(self):
        # create the menu bar
        Menubar = self.menuBar()

        Menu_Corpus = Menubar.addMenu('&Corpus')
        Menu_distant = Menu_Corpus.addMenu(QtGui.QIcon('images/distant.png'),
                                                                     '&Remote')
        Menu_distant.setStatusTip('Connect to prosperologie.org servers')

        get_remote_corpus = xml_info.myxml()
        if get_remote_corpus.get():
            if get_remote_corpus.parse():
                for corpus in get_remote_corpus.getDataCorpus(): 
                    t = QtGui.QAction(corpus[0], self)
                    t.triggered.connect(functools.partial(self.connect_server,
                                 "prosperologie.org", corpus[1]))
                    Menu_distant.addAction(t)
        
        menu_local = Menu_Corpus.addMenu(QtGui.QIcon('images/home.png'),
             '&Local') 
        menu_local.setStatusTip('Connect to a local server')
        menu_local_connect = QtGui.QAction("Connect", self)
        menu_local_connect.triggered.connect(self.connect_server_localhost)
        menu_local.addAction(menu_local_connect)
        menu_local_edit = QtGui.QAction("Edit corpus", self)
        menu_local_edit.triggered.connect(self.add_edit_corpus_tab)
        menu_local.addAction(menu_local_edit)
#TODO edit local server parameters: path, port
        menu_local_param = QtGui.QAction("Local server parameters", self)
        menu_local.addAction(menu_local_param)
        menu_local_param.setEnabled(False)

        Menu_codex = QtGui.QAction("&codex", self)
        Menu_codex.setStatusTip("Use and edit source repositories\
                                                 for ctx generation")
        Menu_codex.triggered.connect(self.codex_window)
        Menu_Corpus.addAction(Menu_codex)

        Menu_Texts = Menubar.addMenu('&Texts')
        Menu_AddTex = QtGui.QAction('&Add a new text', self)    
        Menu_Texts.addAction(Menu_AddTex)
        Menu_AddTex.setEnabled(False)
        Menu_ModTex = QtGui.QAction('&Action on selected texts', self)    
        Menu_Texts.addAction(Menu_ModTex)
        Menu_ModTex.setEnabled(False)

        Menu_Marlowe = Menubar.addMenu('&Marlowe')
        menu_marlowe_gen = QtGui.QAction("&Variant generation", self)
        menu_marlowe_gen.triggered.connect(self.add_gen_mrlw_tab)
        Menu_Marlowe.addAction(menu_marlowe_gen)
        Menu_Marlowe_remote = QtGui.QAction("&Remote", self)
        Menu_Marlowe_remote.triggered.connect(self.MarloweViewer)
        Menu_Marlowe.addAction(Menu_Marlowe_remote)

        # create the status bar
        self.status = self.statusBar()
        self.status.showMessage(u"Ready")

        #create the progressebar
        self.PrgBar = Viewer.PrgBar(self)
        self.status.addPermanentWidget(self.PrgBar.bar)
        
        # create the toolbar
        self.toolbar = self.addToolBar("toolbar")    
        self.toolbar.setIconSize(QtCore.QSize(16, 16))
        self.toolbar.setMovable(0)

#        spacer1 = QtGui.QLabel()
#        spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
#        self.toolbar.addWidget(spacer1)

        self.toolbar_descr_corpus = QtGui.QLabel()
        self.toolbar.addWidget(self.toolbar_descr_corpus)
        
        spacer2 = QtGui.QLabel()
        spacer2.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer2)

        self.toolbar_name_corpus = QtGui.QLabel()
        self.toolbar.addWidget(self.toolbar_name_corpus)

##################################################
        #quart SE
##################################################

    # onglet proprietes du texte
        self.textProperties = QtGui.QTabWidget()

    # sous onglet proprietes saillantes
        saillantes = QtGui.QWidget()
        self.textProperties.addTab(saillantes, self.tr("Sailent structures"))
    
    # une box horizontale pour contenir les 3 listes
        saillantesH = QtGui.QHBoxLayout()
        saillantes.setLayout(saillantesH)
        saillantesH.setContentsMargins(0,0,0,0) 
        saillantesH.setSpacing(0) 

    #Vbox des actants du texte
        saillantesVAct = QtGui.QVBoxLayout()
        saillantesActTitle = QtGui.QLabel()
        #saillantesActTitle.setText("Actants")
        saillantesActTitle.setText("Entities")
        saillantesVAct.addWidget(saillantesActTitle)
        self.saillantesAct = QtGui.QListWidget()
        saillantesVAct.addWidget(self.saillantesAct)
        saillantesH.addLayout(saillantesVAct)
        self.saillantesAct.doubleClicked.connect(self.deploie_Actant)

    #Vbox des categories du texte
        saillantesVCat = QtGui.QVBoxLayout()
        saillantesCatTitle = QtGui.QLabel()
        saillantesCatTitle.setText("Categories")
        saillantesVCat.addWidget(saillantesCatTitle)
        self.saillantesCat = QtGui.QListWidget()
        saillantesVCat.addWidget(self.saillantesCat)
        saillantesH.addLayout(saillantesVCat)
        self.saillantesCat.doubleClicked.connect(self.deploie_Cat)

    #Vbox des collections du texte
        saillantesVCol = QtGui.QVBoxLayout()
        saillantesColTitle = QtGui.QLabel()
        saillantesColTitle.setText("Collections")
        saillantesVCol.addWidget(saillantesColTitle)
        self.saillantesCol = QtGui.QListWidget()
        saillantesVCol.addWidget(self.saillantesCol)
        saillantesH.addLayout(saillantesVCol)
        self.saillantesCol.doubleClicked.connect(self.deploie_Col)

        self.text_elements = Viewer.TextElements()
        self.textProperties.addTab(self.text_elements.widget, u"Text elements")
        self.text_elements.element_list.doubleClicked.connect(self.deploie_text_elements)
#TODO add those below
        temp_apports = QtGui.QWidget()
        self.textProperties.addTab(temp_apports, u"Contributions")
        self.textProperties.setTabToolTip(2, u"Apports et reprises")
        self.textProperties.setTabEnabled(2, False)
        temp_proches = QtGui.QWidget()
        self.textProperties.addTab(temp_proches, u"Analogous")
        self.textProperties.setTabToolTip(3, u"Textes proches")
        self.textProperties.setTabEnabled(3, False)

    # onglet contenu du CTX
        self.textCTX = QtGui.QTableWidget()
        self.textCTX.verticalHeader().setVisible(False)
        self.textCTX.setColumnCount(2)
        self.textCTX.setHorizontalHeaderLabels([u'field', u'value'])
        self.textCTX.horizontalHeader().setStretchLastSection(True)     
        self.textCTX.cellChanged.connect(self.onChangeCTX)
    
        Vbox_textCTX = QtGui.QVBoxLayout()
        Vbox_textCTX.setContentsMargins(0,0,0,0) 
        Vbox_textCTX.setSpacing(0) 

        Vbox_textCTX.addWidget(self.textCTX)
        Vbox_textCTX_W = QtGui.QWidget()
        Vbox_textCTX_W.setLayout(Vbox_textCTX)
        
        self.Hbox_textCTX_commands = QtGui.QHBoxLayout()
        self.textCTX_valid = QtGui.QPushButton("save")
        self.textCTX_valid.clicked.connect(self.saveCTX)
        self.textCTX_valid.setEnabled(False)
        self.Hbox_textCTX_commands.addWidget(self.textCTX_valid)
        self.textCTX_reset = QtGui.QPushButton("reset")
        self.textCTX_reset.clicked.connect(self.resetCTX)
        self.Hbox_textCTX_commands.addWidget(self.textCTX_reset)
        self.textCTX_reset.setEnabled(False)
        Hbox_textCTX_commands_spacer = QtGui.QLabel()
        Hbox_textCTX_commands_spacer.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
#TOTO add, delete
        self.Hbox_textCTX_commands.addWidget(Hbox_textCTX_commands_spacer) 
        textCTX_commandsButton = QtGui.QPushButton(u"\u25cb")
        self.Hbox_textCTX_commands.addWidget(textCTX_commandsButton)
        textCTX_commandsButton.setEnabled(False)
        Vbox_textCTX.addLayout(self.Hbox_textCTX_commands)

        # onglet contenu du texte
        self.textContent = QtGui.QTextEdit() 

        #Tabs
        self.SubWdwSETabs = QtGui.QTabWidget()
        SETabV = QtGui.QVBoxLayout()
        SETabV.setContentsMargins(0,0,0,0) 
        SETabV.setSpacing(0) 
        SETabVH = QtGui.QHBoxLayout()
        SETabV.addLayout(SETabVH)
        SETabVH.addWidget(self.SubWdwSETabs)
        self.SubWdwSETabs.addTab(self.textProperties, "Properties")
        self.SubWdwSETabs.addTab(Vbox_textCTX_W, "Context")
        self.SubWdwSETabs.addTab(self.textContent, "Text")

        self.SubWdwSETabs.currentChanged.connect(self.change_SETab)
        self.textProperties.currentChanged.connect(self.change_text_prop_tab)
        self.text_elements.selector.currentIndexChanged.connect(self.show_text_elements)

##################################################
        #quart SO
##################################################

        self.SubWdwSO = QtGui.QTabWidget()
        self.SubWdwSO.setTabsClosable(True)
        self.SubWdwSO.tabCloseRequested.connect(self.SubWdwSO.removeTab)

        #l'onglet des textes
        self.SOT1 = QtGui.QTabWidget()
        self.SOT1.setTabsClosable(True)
        self.SOT1.tabCloseRequested.connect(self.SOT1.removeTab)

        #la liste des textes du corpus
        self.CorpusTexts = QtGui.QListWidget()
        self.CorpusTexts.setAlternatingRowColors(True)
        self.SOT1.addTab(self.CorpusTexts, "corpus")
        Viewer.hide_close_buttons(self.SOT1,0)
        self.CorpusTexts.itemSelectionChanged.connect(self.onSelectText)
        
#TODO les expression englobantes

        #mise en place des onglets
        self.SubWdwSO.addTab(self.SOT1, self.tr("Texts"))
        Viewer.hide_close_buttons(self.SubWdwSO,0)


##################################################
        #quart NE
##################################################


#l'historique des actions -> Journal
        self.journal = Viewer.Journal()
        
#evaluer directement les variables du serveur
        self.server_vars = Viewer.ServerVars()
        self.server_vars.champ.returnPressed.connect(self.server_vars_Evalue)
        self.server_vars.button_eval.clicked.connect(self.server_vars_Evalue)
        self.server_vars.button_getsem.clicked.connect(self.server_getsem_Evalue)

#mise en place des onglets
        self.SubWdwNE = QtGui.QTabWidget()
        self.SubWdwNE.setTabsClosable(True)
        self.SubWdwNE.tabCloseRequested.connect(self.SubWdwNE.removeTab)
        self.journal_index = self.SubWdwNE.addTab(self.journal.journal, "Journal")
        Viewer.hide_close_buttons(self.SubWdwNE,0)
        self.SubWdwNE.addTab(self.server_vars, "Server vars")
        Viewer.hide_close_buttons(self.SubWdwNE,1)
        self.SubWdwNE.setCurrentIndex(0)


##################################################
    #quart NO
##################################################

        self.SubWdwNO =  QtGui.QTabWidget()
        
##### Tab for syntax items (Lexicon) #############

        NOT1 = QtGui.QWidget()

    #une box verticale
        NOT1V = QtGui.QVBoxLayout()
        NOT1.setLayout(NOT1V)
        NOT1V.setContentsMargins(0,0,0,0) 
        NOT1V.setSpacing(0) 

    #une ligne horizontale qui contient les commandes au dessus-de la liste 
        NOT1VHC = QtGui.QHBoxLayout()
        NOT1V.addLayout(NOT1VHC)
        self.NOT1select = QtGui.QComboBox()
        self.NOT1select.addItems([u"entities", u"qualities", u"markers",
            u"verbs", "undefined", "persons", u"expressions",  u"numbers",
            u"function words", ])
#TODO add those
        for i in range(7,9):
            self.NOT1select.model().item(i).setEnabled(False)
        NOT1VHC.addWidget(self.NOT1select)
        self.NOT1select.currentIndexChanged.connect(self.select_liste)
        self.NOT1select.setEnabled(False) 

    # un spacer pour mettre les commandes sur la droite
        spacer3 = QtGui.QLabel()
        spacer3.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        NOT1VHC.addWidget(spacer3)

    #sorting command
        self.NOT1commands2 = QtGui.QComboBox()
        self.NOT1commands2.addItems([u"occurences", u"deployment",
            u"alphabetically", "number of texts", "first apparition", 
            "last apparition", "weigthed", "autors number", 
            "day present number", "relatif nb jours", 
            "representant number", "network element number"])
        NOT1VHC.addWidget(self.NOT1commands2)
        self.NOT1commands2.setEnabled(False) 
        self.NOT1commands2.currentIndexChanged.connect(self.affiche_liste_scores)

    #une box horizontale pour liste, score et deploiement
        NOT1VH = QtGui.QHBoxLayout()
        NOT1V.addLayout(NOT1VH) 
    #lexicon liste
        self.lexicon_depl_0 = Viewer.ConceptListWidget()
        self.lexicon_depl_0.currentItemChanged.connect(self.lexicon_depl_0_changed) 
        NOT1VH.addWidget(self.lexicon_depl_0)
    #I deployment
        self.lexicon_depl_I = Viewer.ConceptListWidget()
        NOT1VH.addWidget(self.lexicon_depl_I)
        self.lexicon_depl_I.currentItemChanged.connect(self.lexicon_depl_I_changed)
    #II deployment 
        self.lexicon_depl_II = Viewer.ConceptListWidget()
        NOT1VH.addWidget(self.lexicon_depl_II)

        self.lexicon_depl_II.currentItemChanged.connect(self.lexicon_depl_II_changed)
        self.lexicon_depl_I.deselected.connect(lambda: self.lexicon_depl_II.clear())
        self.lexicon_depl_0.deselected.connect(lambda: [self.lexicon_depl_I.clear(),
            self.lexicon_depl_II.clear()])

##### Tab for concepts #############
        NOT2 = QtGui.QWidget()
        NOT2V = QtGui.QVBoxLayout()
        NOT2.setLayout(NOT2V)
        NOT2V.setContentsMargins(0,0,0,0) 
        NOT2V.setSpacing(0) 

        NOT2VHC = QtGui.QHBoxLayout()
        NOT2V.addLayout(NOT2VHC)
        self.NOT2select = QtGui.QComboBox()
        self.NOT2select.addItems([u"collections", u'actants', u"fictions", 
            u"entity categories", u"verb categories", u"marker categories",
            u"quality categories" ])
        NOT2VHC.addWidget(self.NOT2select)
        self.connect(self.NOT2select, 
            QtCore.SIGNAL("currentIndexChanged(const QString)"), 
            self.select_concept)
        self.NOT2select.setEnabled(False) 
        NOT2_spacer = QtGui.QLabel()
        NOT2_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        NOT2VHC.addWidget(NOT2_spacer)

    #sorting command
        self.NOT2commands2 = QtGui.QComboBox()
        self.NOT2commands2.addItems([u"occurences", u"deployment",
            u"alphabetically", "number of texts", "first apparition", 
            "last apparition", "weigthed", "autors number", 
            "day present number", "relatif nb jours", 
            "representant number", "network element number"])
        NOT2VHC.addWidget(self.NOT2commands2)
        self.NOT2commands2.setEnabled(False) 
        self.NOT2commands2.currentIndexChanged.connect(self.affiche_concepts_scores)

        NOT2VH = QtGui.QHBoxLayout()
        NOT2V.addLayout(NOT2VH) 

    #concept list 
        self.concepts_depl_0 = Viewer.ConceptListWidget()
        self.concepts_depl_0.currentItemChanged.connect(self.concepts_depl_0_changed)
        NOT2VH.addWidget(self.concepts_depl_0)
    #I deployment
        self.concepts_depl_I = Viewer.ConceptListWidget()
        NOT2VH.addWidget(self.concepts_depl_I)
        self.concepts_depl_I.currentItemChanged.connect(self.concepts_depl_I_changed)
    #II deployment 
        self.concepts_depl_II = Viewer.ConceptListWidget()
        NOT2VH.addWidget(self.concepts_depl_II)

        self.concepts_depl_II.currentItemChanged.connect(self.concepts_depl_II_changed)
        self.concepts_depl_I.deselected.connect(lambda: self.concepts_depl_II.clear())
        self.concepts_depl_0.deselected.connect(lambda: [self.concepts_depl_I.clear(),
            self.concepts_depl_II.clear()])


################################################
#Explorer Tab
#TODO ajouter navigateur (concepts)
        self.explorer_widget =  Viewer.Explorer()
        self.explorer_widget.Explo_saisie.returnPressed.connect(self.explorer)
        self.explorer_widget.Explo_liste.currentItemChanged.connect(self.explo_item_selected)


################################################
#Acces par CTX
        NOT5 = QtGui.QWidget()

    #une box verticale
        NOT5V = QtGui.QVBoxLayout()
        NOT5.setLayout(NOT5V)
        # on prend toute la place
        NOT5V.setContentsMargins(0,0,0,0) 
        NOT5V.setSpacing(0) 

    #une ligne horizontale qui contient les commandes au dessus-de la liste 
        NOT5VHC = QtGui.QHBoxLayout()
        NOT5V.addLayout(NOT5VHC)

        spacer_CTX_1 = QtGui.QLabel()
        spacer_CTX_1.setSizePolicy(QtGui.QSizePolicy.Expanding, 
                                        QtGui.QSizePolicy.Minimum)
        NOT5VHC.addWidget(spacer_CTX_1)
    
        self.NOT5Commands1 = QtGui.QPushButton()
        self.NOT5Commands1.setIcon(QtGui.QIcon("images/gear.png"))
#desactivé au lancement, tant qu'on a pas de liste
        self.NOT5Commands1.setEnabled(False) 
        NOT5VHC.addWidget(self.NOT5Commands1)

    #une box horizontale pour liste et deploiement
        NOT5VH = QtGui.QHBoxLayout()
        NOT5V.addLayout(NOT5VH) 
        self.NOT5_list = QtGui.QListWidget()
        self.NOT5_list.setAlternatingRowColors(True)
        self.NOT5_list.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                     QtGui.QSizePolicy.Preferred)
        self.NOT5_list.currentItemChanged.connect(self.contexts_contents) 
        NOT5VH.addWidget(self.NOT5_list)
        self.NOT5_cont = QtGui.QListWidget()
        self.NOT5_cont.setAlternatingRowColors(True)
        NOT5VH.addWidget(self.NOT5_cont)
        self.NOT5_cont.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
#           self.NOT5_cont.currentItemChanged.connect() 


        self.SubWdwNO.addTab(NOT1, self.tr("Lexicon"))
        self.SubWdwNO.addTab(NOT2, "Concepts")
        self.SubWdwNO.addTab(self.explorer_widget, "Search")
        self.SubWdwNO.addTab(NOT5, "Contexts")

        self.SubWdwNO.currentChanged.connect(self.change_NOTab)
        #SubWdwNO.setCurrentIndex(0) #Focus sur l'onglet listes concepts

################################################
################################################
#FIXME corriger resize des grids sur petits ecrans
        ###Layout en grid
        main = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        grid.addWidget(self.SubWdwNO,0, 0)
        grid.addWidget(self.SubWdwNE, 0, 1)
        grid.addWidget(self.SubWdwSO, 1, 0)
        grid.addWidget(self.SubWdwSETabs, 1, 1)
        main.setLayout(grid)
        self.setCentralWidget(main)

        #grid.setRowMinimumHeight(0,1000))
        #testeur = QtGui.QPushButton('+')
        #self.SubWdwNO.setCornerWidget(testeur)
        
        #grid.setContentsMargins(2,2,2,2)

        self.setWindowTitle(u'P-II interface')
        self.show() 


################################################
################################################
#Fin de la methode principale d'affichage
#début des fonctions
################################################
################################################


    def activity(self, message):
        """Add message to the journal"""
        self.status.showMessage(message)
        time = "%s" % datetime.datetime.now()
        self.journal.history.append("%s %s" % (time[:19], message))
        with open("P-II-gui.log",'a') as logfile:
            logfile.write("%s %s\n" % (time[:19], message.encode("utf-8")))

    def ord_liste_txt(self, liste_sem, order="chrono"):
        liste = {}
        if (order=="chrono"):
            for e in liste_sem :
                txt = self.listeObjetsTextes[e]
                date = txt.getCTX("date")
                date = re.split(" ", date) #sépare date et heure
                if (len(date) > 1):
                    date, heure = date
                else:
                    date = date[0]
                liste[e] = "-".join(reversed(re.split("/", date)))
            liste =   sorted(liste.items(), key=lambda (k, v) : v) 
            return liste

    def display_liste_textes_corpus(self):
        """displays texts for the corpus"""
        n = len(self.preCompute.listeTextes)
        self.activity(u"Displaying text list (%d items)" % n)
        tab_title ="corpus (%d)"%n
        self.SOT1.tabBar().setTabText(0, tab_title)
        self.CorpusTexts.clear()

        if not hasattr(self, "dic_widget_list_txt"):
            self.dic_widget_list_txt = { 0 : []}
        else : 
            self.dic_widget_list_txt[0] =  []

        self.PrgBar.perc(len(self.listeObjetsTextes))

        for sem, tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
            txt =  self.listeObjetsTextes[sem]
            self.dic_widget_list_txt[0].append(txt)
            WI = Viewer.TexteWidgetItem(txt.getResume())
            self.CorpusTexts.addItem(WI.Widget)
            self.CorpusTexts.setItemWidget(WI.Widget, WI.WidgetLabel)

            self.PrgBar.percAdd(1)

    def onSelectText(self):
        """Update text properties windows when a text is selected """
        tab = self.SOT1.tabText(self.SOT1.currentIndex())
        row = self.SOT1.focusWidget().currentRow()

        if (self.SOT1.currentIndex() == 0) :
            txt = self.dic_widget_list_txt[0][row]
            self.semantique_txt_item =  txt.sem
        else :
            i = 0
            for listwidget in self.SOT1.currentWidget().findChildren(QtGui.QListWidget) :
                if listwidget == self.SOT1.focusWidget():
                    txt = self.dic_widget_list_txt[tab][i][row]
                    self.semantique_txt_item = txt.sem
                i = i+1

        #selectionne le texte dans l'onglet corpus s'il n'est pas actif
        if (self.SOT1.currentIndex() != 0): 
            self.selectTxtCorpus(txt)
        if (self.SOT1.count() > 1): #si plus d'une tab
            for t in range (1, self.SOT1.count()): #parcourt les tabs
                l =  self.SOT1.widget(t).findChildren(QtGui.QListWidget) #les listwidget de la tab
                l[0].itemSelectionChanged.disconnect(self.onSelectText)
                l[1].itemSelectionChanged.disconnect(self.onSelectText)
                #si l'objet txt est dans le dic de l'element
                if txt in  self.dic_widget_list_txt[self.SOT1.tabText(t)][0]:
                    l[0].setCurrentRow(self.dic_widget_list_txt[self.SOT1.tabText(t)][0].index(txt)) #selectionne le txt
                    l[1].clearSelection()
                else: #s'il est dans son anticorpus
                    l[1].setCurrentRow(self.dic_widget_list_txt[self.SOT1.tabText(t)][1].index(txt))
                    l[0].clearSelection()
                l[0].itemSelectionChanged.connect(self.onSelectText)
                l[1].itemSelectionChanged.connect(self.onSelectText)

         
        self.activity("Displaying %s" %Viewer.formeResume2(txt.getResume()))

        #pour accélérer l'affichage, on ne remplit que l'onglet sélectionné
        if (self.SubWdwSETabs.currentIndex() == 0):
            self.show_textProperties(self.semantique_txt_item)
        elif (self.SubWdwSETabs.currentIndex() == 1):
            self.show_textCTX(self.semantique_txt_item) 
        elif (self.SubWdwSETabs.currentIndex() == 2):
            self.show_textContent(self.semantique_txt_item)
                
    def selectTxtCorpus(self, txt):
        self.CorpusTexts.itemSelectionChanged.disconnect(self.onSelectText)
        self.CorpusTexts.setCurrentRow(self.dic_widget_list_txt[0].index(txt))
        self.CorpusTexts.itemSelectionChanged.connect(self.onSelectText)

    def deselectText(self):
        """vide les listes pour eviter confusion et deselectionne les listwidget"""
        self.saillantesAct.clear()
        self.saillantesCat.clear()
        self.saillantesCol.clear()
        self.text_elements.element_list.clear()
        self.efface_textCTX()
        self.textContent.clear()
        if hasattr(self, "semantique_txt_item"):
            del self.semantique_txt_item

        for listwidget in self.SOT1.findChildren(QtGui.QListWidget) :
            listwidget.itemSelectionChanged.disconnect(self.onSelectText)
            listwidget.clearSelection()
            listwidget.itemSelectionChanged.connect(self.onSelectText)

    def change_NOTab(self):
        if (self.SubWdwNO.currentIndex() == 1): # si l'onglet des Concepts est sélectionné
            if  hasattr(self, "client"): # si connecte
                if not hasattr(self, "sem_concept"): #si pas de concept selectionné
                    self.select_concept(self.NOT2select.currentText())
        elif (self.SubWdwNO.currentIndex() == 0): 
            if  hasattr(self, "client"): 
                if not hasattr(self, "sem_liste_concept"): #si pas de concept selectionné
                    self.select_liste(self.NOT1select.currentText()) 

    def change_SETab(self):
        if  hasattr(self, "semantique_txt_item"):
            sem_txt = self.semantique_txt_item
            if (self.SubWdwSETabs.currentIndex () == 0):
                self.saillantesAct.clear()
                self.saillantesCat.clear()
                self.saillantesCol.clear()
                self.show_textProperties(sem_txt)
            elif (self.SubWdwSETabs.currentIndex () == 1):
                self.efface_textCTX()
                self.show_textCTX(sem_txt) 
            elif (self.SubWdwSETabs.currentIndex () == 2):
                self.textContent.clear()
                self.show_textContent(sem_txt)
            self.resetCTX() 

    def change_text_prop_tab(self):
        if  hasattr(self, "semantique_txt_item"):
            sem_txt = self.semantique_txt_item
            if (self.textProperties.currentIndex () == 0):
                self.show_sailent(sem_txt)
            elif (self.textProperties.currentIndex() == 1):
                self.show_text_elements(sem_txt)

    def onChangeCTX(self):
        r = self.textCTX.currentRow()
        if (r != -1):
            self.textCTX.currentItem().setBackground(QtGui.QColor(237,243,254)) # cyan
            self.textCTX_valid.setEnabled(True)
            self.textCTX_reset.setEnabled(True)

    def saveCTX(self):
        sem_txt = self.semantique_txt_item
        txt =  self.listeObjetsTextes[sem_txt]
        txtResume = Viewer.formeResume(txt.getResume())
        modif = []
        for r in range(self.textCTX.rowCount()):
            field = self.textCTX.item(r, 0).text()
            val =  self.textCTX.item(r, 1).text()
            ask = u"%s.ctx.%s" % (sem_txt, field)
            result = self.client.eval_var(ask)
            result = re.sub(u"^\s*", "", result)
            if (result != val):
                #print [field, result, val]
                self.client.eval_set_ctx(sem_txt, field, val)
#FIXME NE MARCHE PAS A TOUS LES COUPS !!
                self.client.add_cache_var(sem_txt +".ctx."+field, val)
                self.listeObjetsTextes[sem_txt].setCTX(field, val)
                modif.append(field)
                
#FIXME a la creation d'un nouveau champ ?
        #self.client.eval_set_ctx(sem_txt, "testfield", val)


        # mettre à jour listes des textes si auteur, date, titre
        if len(set(modif) & set(["author", "date", "title"])):
            if "date" in modif:
                self.display_liste_textes_corpus()
                self.selectTxtCorpus(txt)
        #TODO faire de même pour les autres onglets
                for tab in range(1, self.SOT1.count())   :
                    self.SOT1.removeTab(tab)
            else :
                newResume = Viewer.formeResume(txt.getResume())
                for listWidget in self.SOT1.findChildren(QtGui.QListWidget):
                    for label in  listWidget.findChildren(QtGui.QLabel):
                        if label.text() == txtResume:
                            label.setText(newResume)
            

#FIXME pb de cache quand remet a jour la liste des ctx
        self.maj_metadatas()

        self.textCTX_valid.setEnabled(False)
        self.textCTX_reset.setEnabled(False)
        self.resetCTX()

    def resetCTX(self):
        self.textCTX_valid.setEnabled(False)
        self.textCTX_reset.setEnabled(False)
        self.show_textCTX(self.semantique_txt_item)
 
    def select_concept(self, typ):
        """ quand un element de Concepts est selectionné """
        self.sem_concept = Controller.semantiques[self.NOT2select.currentText()]
        if (self.sem_concept in ["$col"]):
            #deployment for collections
            self.NOT2commands2.setCurrentIndex(1)
        self.affiche_concepts_scores()
        self.detect_concepts = ["abracadabri"]

    def select_liste(self, typ):
        """ quand un element de Lexicon est selectionné """
        self.sem_liste_concept = Controller.semantiques[self.NOT1select.currentText()]
        self.detect_lexicon = ["abracadabri"]
        self.affiche_liste_scores()

    def change_liste(self, content):
        self.lexicon_depl_0.clear()
        self.lexicon_depl_I.clear()
        self.lexicon_depl_II.clear()
        for r in range(len(content)):
            i = QtGui.QListWidgetItem(content[r])
            self.lexicon_depl_0.addItem(i)
            i.setToolTip('rank:%d'%(r+1))
            
    def change_liste_concepts(self, content):
        self.concepts_depl_0.clear()
        self.concepts_depl_I.clear()
        self.concepts_depl_II.clear()
        self.concepts_depl_0.addItems(content)

    def affiche_concepts_scores(self):
        which_concepts = self.NOT2commands2.currentText()
        typ = self.NOT2select.currentText()
        self.sem_concept = Controller.semantiques[typ]
        content = self.client.recup_liste_concept(self.sem_concept)
        self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ, 
                len(content), which_concepts))
        liste_valued =[]

        self.PrgBar.perc(len(content))

        for row  in range(len(content)):
            if (which_concepts == "occurences" or which_concepts == "alphabetically"):
                order = "val"
                ask = "%s%d.%s"% (self.sem_concept, row, order)
            elif (which_concepts == "deployment"):
                order = "dep"
                ask = "%s%d.%s"% (self.sem_concept, row, order)
            elif (which_concepts == "number of texts"):
                order = "nbtxt"
                ask = "%s%d.%s"% (self.sem_concept, row, order)
            elif (which_concepts == "first apparition"):
                order = "fapp"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)
            elif (which_concepts == "last apparition"):
                order = "lapp"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)

            result  = self.client.eval_var(ask)

            try :
                if (which_concepts  in ["first apparition", 
                                             "last apparition"]):
                    val = re.sub(u"^\s*", "", result)
                else :
                    val = int(result)
            except:
                #en cas de non reponse
                print "pb", [ask]
                val = 0
            liste_valued.append([val, content[row]])

    
            self.PrgBar.percAdd(1)


        liste_final =[]
        self.content_liste_concept = []
        if (which_concepts == "alphabetically"):
            for i in sorted(liste_valued, key=lambda x : x[1], reverse = 0):
                item_resume = u"%s %s" % (i[0], i[1])
                liste_final.append(item_resume) 
                self.content_liste_concept.append(i[1])
        else :
            for i in sorted(liste_valued, key=lambda x : x[0], reverse = 1):
                item_resume = u"%s %s" % (i[0], i[1])
                liste_final.append(item_resume) 
                self.content_liste_concept.append(i[1])
        self.change_liste_concepts(liste_final)

    def affiche_liste_scores(self):
        which = self.NOT1commands2.currentText()
        typ = self.NOT1select.currentText()
        self.sem_liste_concept = Controller.semantiques[typ]
        content = self.client.recup_liste_concept(self.sem_liste_concept)
        if (self.sem_liste_concept not in ['ent']):
            self.lexicon_list_semantique = content
        self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,
            len(content), which))
        liste_valued =[]
        self.PrgBar.perc(len(content))
        for row  in range(len(content)):
            if (which == "occurences" or which == "alphabetically"):
                order = "val"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)
            elif (which == "deployment"):
                order = "dep"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)
            elif (which == "number of texts"):
                order = "nbtxt"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)
            elif (which == "first apparition"):
                order = "fapp"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)
            elif (which == "last apparition"):
                order = "lapp"
                ask = "%s%d.%s"% (self.sem_liste_concept, row, order)

            result = self.client.eval_var(ask)

            try :
                if which  in ["first apparition",  "last apparition"]:
                    val = re.sub(u"^\s*", "", result)
                else :
                    val = int(result)
                if (self.sem_liste_concept == "$ent" and which == "deployment" and val == 0):
                    val = 1
            except:
                #en cas de non reponse
                print "No answer from the server to: ", [ask]
                val = 0
            liste_valued.append([val, content[row]])
    
            self.PrgBar.percAdd(1)

        liste_final =[]
        self.content_liste_lexicon = []
        if (which == "alphabetically"):
            for i in sorted(liste_valued, key=lambda x : x[1], reverse = 0):
                item_resume = u"%s %s" % (i[0], i[1])
                liste_final.append(item_resume) 
                self.content_liste_lexicon.append(i[1])
        else :
            for i in sorted(liste_valued, key=lambda x : x[0], reverse = 1):
                item_resume = u"%s %s" % (i[0], i[1])
                liste_final.append(item_resume) 
                self.content_liste_lexicon.append(i[1])
        self.change_liste(liste_final)

    def lexicon_depl_0_changed(self):
        """ suite au changement de sélection, mettre à jour les vues dépendantes """ 
        which = self.NOT1commands2.currentText()
        itemT = self.lexicon_depl_0.currentItem()
        if (not len(self.lexicon_depl_0.selectedItems())):
            self.lexicon_depl_0.setCurrentItem(itemT)
        if (itemT):
            value, item = re.split(" ",itemT.text(),1)
            row = self.lexicon_depl_0.currentRow() 
#TODO clarify the rules for exaequos in rank
            #self.activity("%s selected, rank %d" % (item, row+1))
            self.activity("%s selected, rank %d, value %s" % (item, row+1, value))
            self.lexicon_depl_I.clear() # on efface la liste
            self.lexicon_depl_II.clear()
            sem = self.sem_liste_concept
            if (sem  in ["$ent"])  :
                # recupere la designation semantique de l'element
                self.semantique_lexicon_item_0 = self.client.eval_get_sem(item, sem)
                #liste les representants
                result = re.split(", ", self.client.eval_var("%s.rep[0:]"%
                    self.semantique_lexicon_item_0))
                
                
                if (result != [u'']):

                    self.lexicon_depl_I_unsorted = []
                    for r in range(len(result)):
                        if (which  == "occurences" or which == "alphabetically"):
                            ask = "%s.rep%d.val"% (self.semantique_lexicon_item_0, r)
                        elif (which  == "deployment"):
                            ask = "%s.rep%d.dep"% (self.semantique_lexicon_item_0, r)
                        elif (which  == "number of texts"):
#FIXME corriger : il donne la valeur de l'EF entier
                            ask = "%s.rep%d.nbtxt"% (self.semantique_lexicon_item_0, r)
                            print ask
                        val = int(self.client.eval_var(ask))
                        
                        to_add = "%d %s"%(val, result[r])
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.lexicon_depl_I_unsorted.extend(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.lexicon_depl_I_unsorted.append(to_add)
                            
                    if (which == "alphabetically"):
                        lexicon_depl_I_sorted = sorted(self.lexicon_depl_I_unsorted, key = lambda x : re.split(" ", x)[1], reverse =  0)
                    else :
                        lexicon_depl_I_sorted = sorted(self.lexicon_depl_I_unsorted, key = lambda x : int(re.split(" ", x)[0]), reverse =  1)
                    self.lexicon_depl_I.addItems(lexicon_depl_I_sorted)
                    # afficher directement E du premier element de D 
                    self.lexicon_depl_I.setCurrentItem(self.lexicon_depl_I.item(0))
                    self.lexicon_depl_I_changed()
            else :
                self.semantique_lexicon_item_0 =  sem 



    def lexicon_depl_I_changed(self):
        """quand un item de D est sélectionné, afficher représentants dans E"""
        which = self.NOT1commands2.currentText()
        itemT = self.lexicon_depl_I.currentItem()
        if (itemT):
            row = self.lexicon_depl_I_unsorted.index(itemT.text())
            self.lexicon_depl_II.clear() # on efface la liste
            ask = "%s.rep%d.rep[0:]" % (self.semantique_lexicon_item_0, row)
            self.semantique_lexicon_item_I = u"%s.rep%d" %\
                (self.semantique_lexicon_item_0,  row)
            result =self.client.eval_var(ask)
             
            if (result != "") :
                result = re.split(", ", result)
                if (which == "alphabetically"):
                    liste_scoree = []

                    self.PrgBar.perc(len(result))

                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_lexicon_item_0, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        liste_scoree.append([result[r], val])
                        self.PrgBar.percAdd(1)

                    self.lexicon_depl_II.addItems(map(lambda x : "%d %s"% (x[1], x[0]), sorted(liste_scoree)))
                else :
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_lexicon_item_0, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.lexicon_depl_II.addItems(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.lexicon_depl_II.addItem("%d %s"%(val, result[r])) 
                        self.PrgBar.percAdd(1)
        self.PrgBar.reset()

    def lexicon_depl_II_changed(self):
        itemT = self.lexicon_depl_II.currentItem()
        if (itemT):
            item = re.sub("^\d* ", "", itemT.text())
            #item = itemT.text() # l'element selectionné
            row = self.lexicon_depl_II.currentRow() 
            self.activity("%s selected" % item)
            sem = self.sem_liste_concept
            self.semantique_lexicon_item_II = u"%s.rep%d" %\
                (self.semantique_lexicon_item_I,  row)

    def concepts_depl_0_changed(self,level):
        """ suite au changement de sélection, mettre à jour les vues dépendantes """ 
        which_concepts = self.NOT2commands2.currentText()
        itemT = self.concepts_depl_0.currentItem()
        if (not len(self.concepts_depl_0.selectedItems())):
            self.concepts_depl_0.setCurrentItem(itemT)
        if (itemT):
            item = re.sub("^\d* ", "", itemT.text())
            row = self.concepts_depl_0.currentRow() 
            self.activity("%s selected, rank %d" % (item, row+1))
            self.concepts_depl_I.clear() # on efface la liste
            self.concepts_depl_II.clear()
            sem = self.sem_concept # recupere la designation semantique de l'element
            self.semantique_concept_item = self.client.eval_get_sem(item, sem) #liste les representants
            result = re.split(", ", self.client.eval_var("%s.rep[0:]"% self.semantique_concept_item))
            
            if (result != [u'']):
                if (sem in ["$cat_ent", "$cat_epr", "$cat_mar", "$cat_qua"]):
                #display directly on II list
                    liste_scoree = []
                    prgbar_val = 0
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        if (which_concepts == "number of texts"):
#FIXME corriger, il donne la valeur de la categorie entiere
                            ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item, r)
                        else :
                            ask = "%s.rep%d.val"% (self.semantique_concept_item, r)
                        val = int(self.client.eval_var(ask))
                        
                        liste_scoree.append([ result[r], val ])
                        self.PrgBar.percAdd(1)
                    if (which_concepts == "alphabetically"):
                        liste_scoree.sort()
                    self.concepts_depl_II.addItems(map(lambda x : "%d %s"% (x[1], x[0]), liste_scoree))   

                else:
                    self.concepts_depl_I_unsorted = []
                    for r in range(len(result)):
                        if (which_concepts  == "occurences" or which_concepts == "alphabetically"):
                            ask = "%s.rep%d.val"% (self.semantique_concept_item, r)
                        elif (which_concepts  == "deployment"):
                            ask = "%s.rep%d.dep"% (self.semantique_concept_item, r)
                        elif (which_concepts == "number of texts"):
                            ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item, r)
                        val = int(self.client.eval_var(ask))
                        
                        to_add = "%d %s"%(val, result[r])
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.concepts_depl_I_unsorted.extend(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.concepts_depl_I_unsorted.append(to_add)
                        
                    if (sem not in ["$cat_ent", "$cat_epr", "$cat_mar", "$cat_qua"]):
                        if (which_concepts == "alphabetically"):
                            lexicon_depl_I_sorted = sorted(self.concepts_depl_I_unsorted, key = lambda x : re.split(" ", x)[1], reverse =  0)
                        else :
                            lexicon_depl_I_sorted = sorted(self.concepts_depl_I_unsorted, key = lambda x : int(re.split(" ", x)[0]), reverse =  1)
                    self.concepts_depl_I.addItems(lexicon_depl_I_sorted)

                    # afficher directement II du premier item de I 
                    self.concepts_depl_I.setCurrentItem(self.concepts_depl_I.item(0))
                    self.concepts_depl_I_changed()


    def concepts_depl_I_changed(self):
        """quand un item de D est sélectionné, afficher représentants dans E"""
        which_concepts = self.NOT2commands2.currentText()
        itemT = self.concepts_depl_I.currentItem()
        if (itemT):
            row = self.concepts_depl_I_unsorted.index(itemT.text())
            self.concepts_depl_II.clear() # on efface la liste
            ask = "%s.rep%d.rep[0:]" % (self.semantique_concept_item, row)
            self.semantique_concept_item_I = u"%s.rep%d" %\
                (self.semantique_concept_item,  row)
            result = self.client.eval_var(ask)
            
            if (result != "") :
                result = re.split(", ", result)
                if (which_concepts == "alphabetically"):
                    liste_scoree = []
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        liste_scoree.append([result[r], val])
                        self.PrgBar.percAdd(1)
                    self.concepts_depl_II.addItems(map(lambda x : "%d %s"% (x[1], x[0]), sorted(liste_scoree)))
                else :
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.concepts_depl_II.addItems(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.concepts_depl_II.addItem("%d %s"%(val, result[r])) 
                        self.PrgBar.percAdd(1)
        self.PrgBar.reset()

    def concepts_depl_II_changed(self):
        itemT = self.concepts_depl_II.currentItem()
        if (itemT):
            val, item = Controller.sp_el(itemT.text())
            row = self.concepts_depl_II.currentRow() 
            self.activity("%s selected" % item)
            sem = self.sem_concept
            if (sem in ["$cat_ent", "$cat_epr", "$cat_mar", "$cat_qua"]):
                self.semantique_concept_item_II = u"%s.rep%d" %\
                             (self.semantique_concept_item,  row)
            else :
                self.semantique_concept_item_II = u"%s.rep%d" %\
                            (self.semantique_concept_item_I,  row)
            
    def server_vars_Evalue(self):
        var = self.server_vars.champ.text()
        self.server_vars.champ.clear()
        result = self.client.eval_var(var)
        self.server_vars.result.setTextColor("red")
        self.server_vars.result.append("%s" % var)
        self.server_vars.result.setTextColor("black")
        self.server_vars.result.append(result)

    def server_getsem_Evalue(self):
        var = self.server_vars.champ.text()
        self.server_vars.champ.clear()
        items = re.split("\s*", var)
        self.server_vars.result.setTextColor("red")
        self.server_vars.result.append("%s" % var)
        if (len(items) == 2):
            self.server_vars.result.setTextColor("black")
            el, sem = items
            self.server_vars.result.append(self.client.eval_get_sem(el, sem))
            
    def lance_server(self):
        self.activity("Starting local server")
        self.thread = threading.Thread(target = self.server_thread)
        self.thread.start()
        self.Param_Server_R_button.setText('Stop server')
        self.Param_Server_R_button.clicked.disconnect(self.lance_server)
        self.Param_Server_R_button.clicked.connect(self.stop_server)
#a terme la connection locale lancera le serveur local
            
    def server_thread(self):    
        server_path = self.Param_Server_path_P2.text()
        port = self.Param_Server_val_port.text()
        PRC  = self.Param_Server_path_PRC.text()
        #TODO protéger l'adresse du prc
        commande = "%s -e -p %s -f %s" % (server_path, port, PRC)
        self.activity("Loading %s" % PRC)
        self.local_server = subprocess.Popen(commande, shell=True)
        
    def stop_server(self):
        self.activity("Stopping local server")
        self.local_server.terminate()   
        self.thread.stop()
        self.Param_Server_R_button.setText('Start server')
        self.Param_Server_R_button.clicked.disconnect(self.stop_server)
        self.Param_Server_R_button.clicked.connect(self.lance_server)
    
    def connect_server_localhost(self):
        self.connect_server('localhost')
        #self.connect_server(h='192.168.1.99', p='60000')

    def connect_server(self, h = 'prosperologie.org', p = '60000'):
        self.activity("Connecting to server")
        #self.client=client(self.Param_Server_val_host.text(), self.Param_Server_val_port.text())

        #self.client=client("prosperologie.org", "60000")
        #self.client=client("192.168.1.99", "4000")

        self.client=client(h, p)
        #self.client=client("prosperologie.org", "60000")
        #self.client=client("localhost", "60000")

        #self.client.teste_connect()
        
        if (self.client.Etat):
            # donne le focus a l'onglet journal
            self.SubWdwNE.setCurrentIndex(self.journal_index)

            # calcule en avance
            self.pre_calcule()


            #display info in the toolbar
            self.toolbar_descr_corpus.setText("%s pages %s texts" %\
                (self.preCompute.nbpg, self.preCompute.nbtxt))
#TODO recup corpus name, volume

            #display list for the current selected tab
            if (self.lexicon_or_concepts() == "lexicon"):
                self.select_liste(self.NOT1select.currentText())
            elif (self.lexicon_or_concepts() == "concepts"):
                self.select_concept(self.NOT2select.currentText())

            self.NOT1commands2.setEnabled(True) 
#TODO add those below
            for i in range(6,12):
                self.NOT1commands2.model().item(i).setEnabled(False)

            self.NOT1select.setEnabled(True) 

            self.NOT2commands2.setEnabled(True) 
#TODO add those  below
            for i in range(6,12):
                self.NOT2commands2.model().item(i).setEnabled(False)

            self.NOT2select.setEnabled(True) 


#TODO activate all context menus via the Controller
            #context menu activation

            self.lexicon_depl_0.addAction(QtGui.QAction('texts', self, triggered=lambda:
                self.show_texts(0)))
#TODO #self.lexicon_depl_0.addAction(QtGui.QAction('sentences', self, triggered=self.teste_wording))
            self.lexicon_depl_0.addAction(QtGui.QAction('network', self,
triggered=lambda: self.show_network(0)))
            self.lexicon_depl_0.addAction(QtGui.QAction('copy list', self,
                triggered=self.copy_to_cb))
            self.lexicon_depl_I.addAction(QtGui.QAction('texts', self,
                triggered=lambda: self.show_texts(1)))
            self.lexicon_depl_I.addAction(QtGui.QAction('network', self,
                triggered=lambda: self.show_network(1)))
            self.lexicon_depl_II.addAction(QtGui.QAction('texts', self,
                triggered=lambda: self.show_texts(2)))
            self.lexicon_depl_II.addAction(QtGui.QAction('sentences', self,
                triggered=self.teste_wording))
            self.lexicon_depl_II.addAction(QtGui.QAction('network', self,
                triggered=lambda: self.show_network(2)))


            self.concepts_depl_0.addAction(QtGui.QAction('texts', self, triggered=lambda:
                self.show_texts(0)))
#TODO #self.concepts_depl_0.addAction(QtGui.QAction('sentences', self, triggered=self.teste_wording))
            self.concepts_depl_0.addAction(QtGui.QAction('network', self,
triggered=lambda: self.show_network(0)))
#TODO #self.concepts_depl_0.addAction(QtGui.QAction('copy list', self, triggered=self.copy_to_cb))
            self.concepts_depl_I.addAction(QtGui.QAction('texts', self,
                triggered=lambda: self.show_texts(1)))
            self.concepts_depl_I.addAction(QtGui.QAction('network', self,
                triggered=lambda: self.show_network(1)))
            self.concepts_depl_II.addAction(QtGui.QAction('texts', self,
                triggered=lambda: self.show_texts(2)))
            self.concepts_depl_II.addAction(QtGui.QAction('sentences', self,
                triggered=self.teste_wording))
            self.concepts_depl_II.addAction(QtGui.QAction('network', self,
                triggered=lambda: self.show_network(2)))

            # affiche textes au demarrage
            self.display_liste_textes_corpus()

            #self.Explo_action.setEnabled(True) 
        
    def disconnect_server(self):
        """Disconnect"""
        self.activity("Disconnecting")
        self.client.disconnect()
        self.Param_Server_B.setText('Connect to server')
        self.Param_Server_B.clicked.connect(self.connect_server)

    def add_edit_corpus_tab(self):
        self.param_corpus = Viewer.Corpus_tab(self)
        QtCore.QObject.connect(self.param_corpus.send_codex_ViewListeTextes,
                 QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)
        self.param_corpus.launchPRC_button.clicked.connect(self.launchPRC)
        self.param_corpus_tab_index = self.SubWdwNE.addTab(self.param_corpus, "Corpus")
        self.SubWdwNE.setCurrentIndex(self.param_corpus_tab_index)

    def codex_window(self):
        codex_w = codex_window(self)
        codex_w.show()

    def add_gen_mrlw_tab(self):
        self.gen_mrlw = Viewer.MrlwVarGenerator()
        self.gen_mrlw_tab_index = self.SubWdwNE.addTab(self.gen_mrlw.gen_mrlw, 
                                                    self.tr("Variant generation"))
        self.SubWdwNE.setCurrentIndex(self.gen_mrlw_tab_index)

    def MarloweViewer(self):
        MarloweView = QtWebKit.QWebView()
        tabindex = self.SubWdwNE.addTab(MarloweView, "Marlowe")
        self.SubWdwNE.setCurrentIndex(tabindex)
        url = "http://tiresias.xyz:8080/accueil"
        MarloweView.load(QtCore.QUrl(url))
    

    def show_textContent(self,  sem_txt):
        """Insert text content in the dedicated window"""
        #contentText_semantique = "%s.ph[0:]" % sem_txt
        #txt_content = self.client.eval_var(contentText_semantique)
#FIXME this is the worst way to do it
        i = 0
        b = True
        txt_content = ""
        while (b):
            sem = "%s.ph%d" % (sem_txt, i)
            res = self.client.eval_var(sem)
            if (res != ""):
                txt_content += "%s\n" % res 
            else :
                b = False
            i += 1
        
        self.textContent.clear()
        self.textContent.append(txt_content)
        #move cursor to the beginning of the text
        self.textContent.moveCursor(QtGui.QTextCursor.Start)
        
    def efface_textCTX(self):
        self.textCTX.clear()
        self.textCTX.setRowCount(0)
        self.textCTX.setHorizontalHeaderLabels([u'field', u'value']) #on remet les headers apres le clear

    def show_textCTX(self, sem):
        """Show text metadata"""
        self.efface_textCTX()
        ctx = self.listeObjetsTextes[sem].getCTXall()
        self.textCTX.setRowCount(len(ctx))
        r = 0
        for field, value in ctx.iteritems() :
            itemCTXwidget_field = QtGui.QTableWidgetItem(field)
            self.textCTX.setItem(r, 0, itemCTXwidget_field)
            itemCTXwidget_val = QtGui.QTableWidgetItem(value)
            self.textCTX.setItem(r, 1, itemCTXwidget_val)
            r += 1
        self.textCTX.resizeRowsToContents()

    def show_textProperties(self,  sem_txt):
        """Show text properties according to selected tab"""
        if (self.textProperties.currentIndex() == 0):
            self.show_sailent(sem_txt)
        elif (self.textProperties.currentIndex() == 1):
            self.show_text_elements(sem_txt)

    def show_text_elements(self, sem_txt):
        if  hasattr(self, "semantique_txt_item"):
            self.text_elements.element_list.clear()
            sem_concept = Controller.semantiques[self.text_elements.selector.currentText()]
            list_element_sem = "%s.%s[0:]" % (self.semantique_txt_item, sem_concept)
            list_element  = self.client.eval_var(list_element_sem)
            self.text_element_depl = []
            if (list_element != u''):
                self.list_element_items = re.split(", ", list_element)
                self.list_elements_valued = {}
                i = 0
                for item in self.list_element_items:
                    ask = u"%s.%s%d.val"%(self.semantique_txt_item, sem_concept, i)
                    print ask
#FIXME not the correct value for $ent, $expr
                    val = int(self.client.eval_var(ask))
                    self.list_elements_valued[self.list_element_items[i]] = val
                    self.text_elements.element_list.addItem("%d %s"%(val, item))
                    i += 1

    def deploie_text_elements(self):
        item = self.text_elements.element_list.currentItem().text()
        val, item = Controller.sp_el(item)
        self.text_elements.element_list.clear()
        sem_concept = Controller.semantiques[self.text_elements.selector.currentText()]
        for r in self.list_element_items:
            self.text_elements.element_list.addItem(u"%d %s" %\
                (self.list_elements_valued[r], r))

            if ((r == item) and (item in self.text_element_depl)):
                self.text_element_depl.remove(item)
            elif (r == item) :
                self.text_element_depl.append(item)

            if (r in self.text_element_depl):             
                ask = "%s.%s%d.rep_present[0:]"%(self.semantique_txt_item,
                    sem_concept, self.list_element_items.index(r))
                print ask
#FIXME not the correct deployment
                result = self.client.eval_var(ask)
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.list_elements_valued.keys()):
                            ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item,
                             sem_concept, self.list_element_items.index(r), sub_n)
#FIXME not the correct value 
                            print ask
                            res = self.client.eval_var(ask)
                            self.list_elements_valued[result[sub_n]] = res
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.list_elements_valued[result[sub_n]],
                             result[sub_n]))
                        i.setBackground(QtGui.QColor(237,243,254)) # cyan
                        self.text_elements.element_list.addItem(i)
       
    def show_sailent(self, sem_txt): 
        #les actants
        #les actants en tête sont calculés par le serveur
#    ex entre 0 et 4 pages :  le poids mini d'un actant est de 2 , le nbre d'actants ideal est 5
#    ex entre 5 et 9 pages :  le poids mini d'un actant est de 3 , le nbre d'actants ideal est 7
#    ...
#
#    ex entre 50 et 99 pages :  le poids mini d'un actant est de 7 , le nbre d'actants ideal est 25
#
#    une page == 2000 caractères
#TexteParametrageDesActants TableDuParametrageDuNombreDActants[]=
#{
#    { 0 , 5 , 2 , 5 },
#    { 5 , 10, 3 , 7 },
#    {10 , 20, 4 ,10},
#    {20 , 50, 5 ,15 },
#    {50, 100, 6 ,20},
#    {100,-1,  7 ,25},  // PS le -1 sert de fin de table .... in for
#};
#TexteParametrage_ConceptsEmergents TableDuParametrageDesConceptsEmergents[]=
#{
#    { 0 , 5 , 2 , 2 },
#    { 5 , 10, 3 , 3 },
#    {10 , 20, 4 , 4},
#    {20 , 50, 7 , 5 },
#    {50, 100, 10, 7},
#    {100,-1,  12 ,10},
#};



        self.saillantesAct.clear()
        self.saillantesAct_deployes = []
        list_act_sem = "%s.act[0:]" % sem_txt
        result = self.client.eval_var(list_act_sem)
        pos = 0
        list_act = result.split(',')
        list_act_sem_val = list_act_sem + ".val"
        result = self.client.eval_var(list_act_sem_val)
        list_act_val = result.split(',')
        for act in list_act :
            self.client.add_cache_var("%s.act%s"%(sem_txt, pos), act)
            self.client.add_cache_var("%s.act%s.val"%(sem_txt, pos), list_act_val[pos])
            pos +=1
        if (list_act):
            #self.list_act = re.split(", ", list_act)
            self.list_act = list_act
            self.liste_act_valued = {}
            self.PrgBar.perc(len(self.list_act))
            for i in range(len(self.list_act)) :
                val = int(self.client.eval_var(u"%s.act%d.val"%(sem_txt, i)))
                
                self.liste_act_valued [self.list_act[i]] = [ val, 0 ] 
                self.saillantesAct.addItem(u"%d %s" % (val, self.list_act[i]))
                self.PrgBar.percAdd (1)

        #les catégories
        #le serveur renvoie toutes les éléments de la catégorie
        #si len(cat_ent[0:]) > 2, deux algos a tester pour économiser les interactions avec le serveur :
        # si cat_ent0.val < len(cat_ent[0:]) on approxime le cumul des frequences de valeur par celui du rapport du nb d'element analysés sur le nb d'element total qu'on multiplie par cat_ent0.val, on arrête quand on atteint 0,5 ou on affiche les cat tant qu'elles ont le même score
        # si cat_ent0.val > len(cat_ent[0:]) on fait le rapport des valeurs cumulees sur la somme totale si les valeurs suivantes avaient le même score que le dernier obtenu : Val_cumul / ((len(cat_ent[0:]) - i) * cat_ent[i].val + Val_cumul) on s'arrete en atteignant 0,25 ou etc

        self.list_cat_valued = {}
        self.list_cat_txt = {} 
        self.saillantesCat.clear()
        self.saillantesCat_deployes = []
        #for typ in [u"cat_qua", u"cat_mar", u"cat_epr", u"cat_ent"]:
        for typ in [u"cat_ent"]: #uniquement les cat_ent
            list_cat_sem = "%s.%s[0:]" % (sem_txt, typ)
            list_cat  = self.client.eval_var(list_cat_sem)

            if (list_cat != u''):
                list_cat_items = re.split(", ", list_cat)
                r = 0
                for c in list_cat_items:
                    self.list_cat_txt[c] = [typ, r]
                    r += 1
                cum = 0
                old_val = 0
                #old_val2 = 0
                self.PrgBar.perc(len(list_cat_items))
                for i in range(len(list_cat_items)):
                    ask = u"%s.%s%d.val"%(sem_txt, typ, i)
                    val = int(self.client.eval_var(ask))
                    
                    if (val < old_val):
                        break
                    cum += val
                    C = float(cum) / (cum + ((len(list_cat_items) - i) * val))
                    #C2 = float(i) / len(list_cat_items) * val
                    #if (C2 > 0.50 and old_val2 == 0) :
                    #       old_val2 = val  
                    if (C > 0.25 and old_val == 0) :
                        old_val = val   
                    self.list_cat_valued[list_cat_items[i]] = val
                    self.PrgBar.percAdd (1)

        self.list_cat_valued_ord = []
        for cat in sorted(self.list_cat_valued.items(), key = lambda(k, v) : v, reverse=1):
            self.list_cat_valued_ord.append(cat[0])
            resume = u"%d %s" % (int(cat[1]), cat[0])
            #if int(cat[1]) < old_val:
            #       resume = "D" + resume
            #if int(cat[1]) < old_val2:
            #       resume = "E" + resume
            self.saillantesCat.addItem(resume)
            

        # les collections
        # on met toutes les collections parce que leur émergence est donnée par leur déploiement
#TODO ordonner, saillantes
        self.saillantesCol.clear()
        self.saillantesCol_deployees = []
        list_col_sem = "%s.col[0:]" % sem_txt
        result = self.client.eval_var(list_col_sem)
        
        if (result != u""):
            self.list_col = re.split(", ", result)   
            self.list_col_valued = {}
            self.PrgBar.perc(len(self.list_col))
            for i in range(len(self.list_col)) :
                val = int(self.client.eval_var(u"%s.col%d.dep"%(sem_txt, i)))
                
                self.saillantesCol.addItem(u"%d %s" % (val, self.list_col[i]))
                self.list_col_valued[self.list_col[i]] = val
                self.PrgBar.percAdd (1)

    def deploie_Col(self):
        item = self.saillantesCol.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)

        self.saillantesCol.clear()
        
        for r in self.list_col:
            self.saillantesCol.addItem(u"%d %s" % (self.list_col_valued[r], r))

            if ((r == item) and (item in self.saillantesCol_deployees)):
                self.saillantesCol_deployees.remove(item)
            elif (r == item) :
                self.saillantesCol_deployees.append(item)

            if (r in self.saillantesCol_deployees):             
                ask = "%s.col%d.rep_present[0:]"%(self.semantique_txt_item, self.list_col.index(r))
                result = self.client.eval_var(ask)
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.list_col_valued.keys()):
                            ask = "%s.col%d.rep_present%d.val"%(self.semantique_txt_item, self.list_col.index(r), sub_n)
                            print ask
#FIXME pas la bonne valeur
                            res = self.client.eval_var(ask)
                            
                            self.list_col_valued[result[sub_n]] = res
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.list_col_valued[result[sub_n]], result[sub_n]))
#TODO trouver couleur par defaut du alternate
                        #i.setBackground(QtGui.QColor(245,245,245)) # gris clair
                        i.setBackground(QtGui.QColor(237,243,254)) # cyan
                        self.saillantesCol.addItem(i)
                
    def deploie_Cat(self):
        item = self.saillantesCat.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)
        self.saillantesCat.clear()
        for cat in self.list_cat_valued_ord:
            resume = u"%d %s" % (self.list_cat_valued[cat], cat)
            self.saillantesCat.addItem(resume)

            if ((cat == item) and (item in self.saillantesCat_deployes)):
                self.saillantesCat_deployes.remove(item)
            elif (cat == item) :
                self.saillantesCat_deployes.append(item)
      
            if (cat in self.saillantesCat_deployes):             
                sem = self.list_cat_txt[cat]
                ask = "%s.%s%d.rep_present[0:]"%(self.semantique_txt_item, sem[0], sem[1])
                result = self.client.eval_var(ask)
                
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.list_cat_valued.keys()):
                            ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item, sem[0], sem[1], sub_n)
                            res = self.client.eval_var(ask)
                            self.list_cat_valued[result[sub_n]] = res
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.list_cat_valued[result[sub_n]][0], result[sub_n]))
                        #i.setBackground(QtGui.QColor(245,245,245))
                        i.setBackground(QtGui.QColor(237,243,254)) # cyan
                        self.saillantesCat.addItem(i)
                        
              

    def deploie_Actant(self):
        item = self.saillantesAct.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)
        self.saillantesAct.clear()
        for r in self.list_act:
            self.saillantesAct.addItem(u"%d %s" % (self.liste_act_valued[r][0], r))
            
            if ((r == item) and (item in self.saillantesAct_deployes)):
                self.saillantesAct_deployes.remove(item)
            elif (r == item) :
                self.saillantesAct_deployes.append(item)
                
            if (r in self.saillantesAct_deployes):             
                ask = "%s.act%d.rep_present[0:]"%(self.semantique_txt_item, self.list_act.index(r))
                result = self.client.eval_var(ask)
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.liste_act_valued.keys()):
                            ask = "%s.act%d.rep_present%d.val"%(self.semantique_txt_item, self.list_act.index(r), sub_n)
                            res = self.client.eval_var(ask)
                            
                            self.liste_act_valued[result[sub_n]] = [res, 2]
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.liste_act_valued[result[sub_n]][0], result[sub_n]))
                        #i.setBackground(QtGui.QColor(245,245,245))
                        i.setBackground(QtGui.QColor(237, 243, 254)) # cyan
                        self.saillantesAct.addItem(i)
                    
                
    def recup_element_lexicon(self, lvl):
        """get semantic and name of item pointed in lexicon list"""
        if (self.sem_liste_concept in ['$ent']):
            if (lvl == 2):
                element = self.lexicon_depl_II.currentItem().text() 
                val, element = Controller.sp_el(element)
                return  (self.semantique_lexicon_item_II, element)
            elif (lvl == 1):
                element0 = self.lexicon_depl_0.currentItem().text() 
                val, element0 = Controller.sp_el(element0)
                elementI = self.lexicon_depl_I.currentItem().text() 
                val, elementI = Controller.sp_el(elementI)
                element = u"%s:%s" % (element0, elementI)
                return (self.semantique_lexicon_item_I, element)
            else :
                element = self.lexicon_depl_0.currentItem().text() 
                val, element = Controller.sp_el(element)
                return  (self.semantique_lexicon_item_0, element)
        else :
            element = self.lexicon_depl_0.currentItem().text() 
            val, element = Controller.sp_el(element)
            return (u"%s%d" % (self.semantique_lexicon_item_0,
                self.lexicon_list_semantique.index(element)), element)
        
    def recup_element_concepts(self, lvl):
        """get semantic and name of concept pointed in concept list"""
        if (lvl == 2):
            element = self.concepts_depl_II.currentItem().text() 
            val, element = Controller.sp_el(element)
            return  (self.semantique_concept_item_II, element)
        elif (lvl == 1):
            element0 = self.concepts_depl_0.currentItem().text() 
            val, element0 = Controller.sp_el(element0)
            elementI = self.concepts_depl_I.currentItem().text() 
            val, elementI = Controller.sp_el(elementI)
            element = u"%s:%s" % (element0, elementI)
            return (self.semantique_concept_item_I, element)
        else :
            element = self.concepts_depl_0.currentItem().text() 
            val, element = Controller.sp_el(element)
            return  (self.semantique_concept_item, element)

    def add_networks_tab(self):
        #l'onglet des réseaux
        self.tabNetworks = QtGui.QTabWidget()
        self.tabNetworks.setTabsClosable(True)
        self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)
        self.networks_tab_index = self.SubWdwSO.addTab(self.tabNetworks, self.tr("Networks"))

    def show_network(self, lvl):
        """Show the network of a selected item"""
#TODO scorer
#TODO supprimer tab generale quand derniere sous-tab supprimee
        #create the networks tab if not exists
        if (not hasattr(self, "networks_tab_index")):
            self.add_networks_tab()
        if (self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
            sem, element = self.recup_element_lexicon(lvl)
        if (self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
            sem, element = self.recup_element_concepts(lvl)
        for i in range(0, self.tabNetworks.count()):
            if (self.tabNetworks.tabText(i) == element):
                self.tabNetworks.removeTab(i)
        
        res_semantique = "%s.res[0:]" % (sem)
        result_network =   re.split(", ", self.client.eval_var(res_semantique))
        network_view = Viewer.NetworksViewer(result_network)

        self.activity(u"Displaying network for %s (%d items)" % (element,
                                                             len(result_network)))
        index = self.tabNetworks.addTab(network_view.show_network_widget, element)
        self.tabNetworks.setTabToolTip(index, element)
        # give focus
        self.tabNetworks.setCurrentIndex(index)
        self.SubWdwSO.setCurrentIndex(self.networks_tab_index)

    def explo_item_selected(self):
        self.Explo_commands.setEnabled(True) 
###        motif = re.sub("^\d* ", "", self.Explo_liste.currentItem().text())
###        self.client.eval_var("$ef[0:]")
###        liste_ef =re.split(", ", self.client.eval_var_result) 
###        for efN in  range(len(liste_ef)):
###            self.client.eval_var("$ef%d.rep_present[0:]"%efN)
###            result = re.split(", ", self.client.eval_var_result) 
###            if motif in  result:
###                 self.Explo_concepts.setText(liste_ef[efN])


    def explo_show_text(self):
        """Show texts containing a pattern"""
#TODO scorer/trier
        self.deselectText()

        motif = self.Explo_saisie.text()
        row =  self.Explo_liste.currentRow()
        ask = self.client.creer_msg_search("$search.rac", motif, "%d"%row, txt=True, ptxt="[0:]")
        result = self.client.eval(ask)
        liste_textes = re.split(", ", result)
        self.activity(u"Displaying %d texts for %s" % (len(liste_textes), motif))

        liste_textes = map(lambda k : self.preCompute.dicTxtSem[k], liste_textes)

        texts_widget = Viewer.Liste_texte(motif, liste_textes)

        self.dic_widget_list_txt[ texts_widget.tab_title ] =  [ [], [] ]
        for sem, tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
            txt =  self.listeObjetsTextes[sem]
            if sem in liste_textes: 
                WI = Viewer.TexteWidgetItem(txt.getResume())
                texts_widget.show_texts_corpus.addItem(WI.Widget)
                texts_widget.show_texts_corpus.setItemWidget(WI.Widget, WI.WidgetLabel)
                self.dic_widget_list_txt[texts_widget.tab_title][0].append(txt)
            else :
                WI = Viewer.TexteWidgetItem(txt.getResume())
                texts_widget.show_texts_anticorpus.addItem(WI.Widget)
                texts_widget.show_texts_anticorpus.setItemWidget(WI.Widget, WI.WidgetLabel)
                self.dic_widget_list_txt[texts_widget.tab_title][1].append(txt)
    
        texts_widget.show_texts_corpus.itemSelectionChanged.connect(self.onSelectText) 
        texts_widget.show_texts_anticorpus.itemSelectionChanged.connect(self.onSelectText)  

        #si la tab de l'element existe déjà, on efface l'ancienne
        for i in range(0, self.SOT1.count()):
            if (re.search("^{%s} (\d*)"%motif, self.SOT1.tabText(i))):
                self.SOT1.removeTab(i)
            
        index = self.SOT1.addTab(texts_widget.show_texts_widget, texts_widget.tab_title)
        self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
        self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
        self.SOT1.tabBar().setTabToolTip(index, texts_widget.tab_title)

    def show_texts(self, lvl):
        """Show texts containing a selected item"""
#TODO sorting by date/score, filter

        self.deselectText()

        if (self.lexicon_or_concepts() == "lexicon"):
            sem, element = self.recup_element_lexicon(lvl)
        elif (self.lexicon_or_concepts() == "concepts"):
            sem, element = self.recup_element_concepts(lvl)

        txts_semantique = "%s.txt[0:]" % (sem)
        result = self.client.eval_var(txts_semantique)

        if  (result == ""):
            self.activity(u"No text to displaying for %s" % (element))
        else:
            liste_textes = re.split(", ", result) 
            self.activity(u"Displaying %d texts for %s" % (len(liste_textes), element))
            
            liste_textes = map(lambda k: self.preCompute.dicTxtSem[k], liste_textes)
            liste_textes_valued = {}
            #get element occurences in texts
            for i in range(len(liste_textes)):
                ask = "%s.txt%s.val"%(sem, i)
                liste_textes_valued[liste_textes[i]] = self.client.eval_var(ask)

            texts_widget = Viewer.Liste_texte(element, liste_textes)
            self.dic_widget_list_txt[ texts_widget.tab_title ] =  [ [], [] ]
            for sem, tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
                txt =  self.listeObjetsTextes[sem]
                if sem in liste_textes: 
                    new_resume = ("%s (%s)"%(txt.getResume()[0],liste_textes_valued[sem]) , txt.getResume()[1], txt.getResume()[2])
                    WI = Viewer.TexteWidgetItem(new_resume)
                    texts_widget.show_texts_corpus.addItem(WI.Widget)
                    texts_widget.show_texts_corpus.setItemWidget(WI.Widget,
                                                                     WI.WidgetLabel)
                    self.dic_widget_list_txt[texts_widget.tab_title][0].append(txt)
                else :
                    WI = Viewer.TexteWidgetItem(txt.getResume())
                    texts_widget.show_texts_anticorpus.addItem(WI.Widget)
                    texts_widget.show_texts_anticorpus.setItemWidget(WI.Widget, WI.WidgetLabel)
                    self.dic_widget_list_txt[texts_widget.tab_title][1].append(txt)

        
            texts_widget.show_texts_corpus.itemSelectionChanged.connect(self.onSelectText) 
            texts_widget.show_texts_anticorpus.itemSelectionChanged.connect(self.onSelectText)  

            #si la tab de l'element existe déjà, on efface l'ancienne
            for i in range(1, self.SOT1.count()):
                tab_element = re.sub(" \(\d*\)$", "", self.SOT1.tabText(i))
                if (tab_element == element):
                    self.SOT1.removeTab(i)
                
            index = self.SOT1.addTab(texts_widget.show_texts_widget, texts_widget.tab_title)
            self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
            self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
            self.SOT1.tabBar().setTabToolTip(index, texts_widget.tab_title)

    def lexicon_or_concepts(self):
        i = self.SubWdwNO.currentIndex()
        if (i == 0):
            return "lexicon"
        elif (i == 1):
            return "concepts"
        else:
            return False
            
    def teste_wording(self):
        if (self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
            item = self.lexicon_depl_II.currentItem().text()
        if (self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
            item = self.concepts_depl_II.currentItem().text()

        score, item = re.search("^(\d*) (.*)", item).group(1, 2)
        self.activity(u"%s double click" % (item))
        if (int(score)):
            ask = "$ph.+%s"%(item)
            result = self.client.eval_var(ask)
            
            if (not hasattr(self, "tab_sentences_index")):
                self.tab_sentences = QtGui.QTabWidget()
                self.tab_sentences.setTabsClosable(True)
                self.tab_sentences.tabCloseRequested.connect(self.tab_sentences.removeTab)
                self.tab_sentences_index = self.SubWdwSO.addTab(self.tab_sentences, "Sentences")
            
            for i in range(0, self.tab_sentences.count()):
                if (self.tab_sentences.tabText(i) == item):
                    self.tab_sentences.removeTab(i)
             
            show_sentences_widget = QtGui.QWidget()
            show_sentences_box = QtGui.QVBoxLayout()
            # on prend toute la place
            show_sentences_box.setContentsMargins(0,0,0,0) 
            show_sentences_box.setSpacing(0) 
            show_sentences_widget.setLayout(show_sentences_box)
            index = self.tab_sentences.addTab(show_sentences_widget, item)
            self.tab_sentences.setTabToolTip(index, item)

            sentence_text = QtGui.QTextEdit() 
            show_sentences_box.addWidget(sentence_text)
            sentence_text.append(result)

            #give focus
            self.tab_sentences.setCurrentIndex(index)
            self.SubWdwSO.setCurrentIndex(self.tab_sentences_index)

    def easter1(self):
        tempImage = QtGui.QPixmap("images/Prospero-II.png")
        self.explorer_widget.Explo_concepts.setPixmap(tempImage)

    def explorer(self):
        self.explorer_widget.Explo_liste.clear()
        motif = self.explorer_widget.Explo_saisie.text()
        if (motif != ""):
            types = [u"$search.pre", u"$search.suf", u"$search.rac"]
            type_search = types[self.explorer_widget.select_fix.currentIndex()]

            if (motif == "abracadabri"):
                self.easter1()

            #la liste des match
            ask = self.client.creer_msg_search(type_search, motif, "[0:]") 
            result = self.client.eval(ask)
            if (result != u''):
                liste_result = re.split(", ", result)
                self.activity("searching for {%s} %d results"%(motif, len(liste_result)))
                self.PrgBar.perc(len(liste_result))
                for i in range(len(liste_result)):
                    ask = self.client.creer_msg_search(type_search, motif,
                                        "%d"%i, val=True) #la valeur du match
#TODO get_sem, liste textes, énoncés
#TODO select all
                    r = self.client.eval(ask)
                    self.PrgBar.percAdd(1)
                    self.explorer_widget.Explo_liste.addItem("%s %s"% (r, liste_result[i]))
            else :
                result = re.split(", ", self.activity("searching for {%s} : 0\
                    result" % motif))
    
    def contexts_contents(self):
        self.NOT5_cont.clear()
        if (self.NOT5_list.currentItem()):
            champ = self.NOT5_list.currentItem().text()
            #print [champ]
            result = self.client.eval_var(u"$ctx.%s[0:]" % champ)
            result = re.split("(?<!\\\), ", result)#negative lookbehind assertion
            #print [result]
            dic_CTX = {}
            for r in result:
                if r in dic_CTX.keys():
                    dic_CTX[r] = dic_CTX[r] + 1
                else:
                    dic_CTX[r] = 1
            for el in sorted(dic_CTX.items(), key= lambda (k, v) : (-v, k)):
                self.NOT5_cont.addItem(u"%d %s"%(el[1], re.sub("\\\,", ",", el[0])))


        
                
    def maj_metadatas(self):
        string_ctx =    self.client.eval_var("$ctx")
        #self.client.add_cache_var(sem_txt +".ctx."+field, val)
        current  =  self.NOT5_list.currentItem() 
        self.NOT5_cont.clear()
        if (current):
            self.NOT5_list.setCurrentItem(current)
            self.contexts_contents()
    
    def copy_to_cb(self):
        debut  =  self.lexicon_depl_0.currentRow()
        fin  = self.lexicon_depl_0.count()
        liste = []
        if (fin):
            for row in range(0, fin):
                element = re.sub("^(\d{1,}) (.*)$", "\\2\t\\1", self.lexicon_depl_0.item(row).text(), 1) #on inverse pour excel
                liste.append(element)
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText("\n".join(liste))
            self.activity(u"%d elements copied to clipboard" % (len(liste)))

    def send_codex_ViewListeTextes(self):
        Items = self.param_corpus.ViewListeTextes.selectedItems()
        if (Items):
            codex_w = codex_window(self)
            codex_w.show()
            l = []
            for item in Items:
                l.append(item.text())   
            codex_w.appendItems(l)

    def launchPRC(self):
        PRC = self.param_corpus.nameCorpus.text()
        if (os.name == 'nt'):
            server_path = "prospero-II-serveur.exe"
        else:
            server_path = "./prospero-server"
        port = 60000
        commande = "%s -e -d 1 -p %s -f %s" % (server_path, port, PRC)
        print commande
        local_server = subprocess.Popen(commande, shell=True)
        time.sleep(5)
        self.connect_server("localhost", port)
#kill the server when the gui is closed
        atexit.register(local_server.terminate) 
            

class codex_window(QtGui.QWidget):
    def __init__(self, parent=None):
        super(codex_window, self).__init__(parent, QtCore.Qt.Window)
        self.codex_dic = Controller.edit_codex()
        if self.codex_dic.cherche_codex():
            self.codex_dic.parse_codex_xml("codex.xml")

        L = QtGui.QVBoxLayout()
        self.setLayout(L)

        H2 = QtGui.QHBoxLayout()
        L.addLayout(H2)
        h22 = QtGui.QVBoxLayout()
        H2.addLayout(h22)

        h22Buttons = QtGui.QHBoxLayout()
        h22.addLayout(h22Buttons)
        self.h22Label = QtGui.QLabel("Text file list: drag and drop")
        h22Buttons.addWidget(self.h22Label)
        h22_spacer = QtGui.QLabel()
        h22_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                     QtGui.QSizePolicy.Minimum)
        h22Buttons.addWidget(h22_spacer)
        h22gen = QtGui.QPushButton()
        h22gen.setIcon(QtGui.QIcon("images/gear.png"))
        h22gen.setToolTip(u"test file names")
        h22Buttons.addWidget(h22gen)
        QtCore.QObject.connect(h22gen, 
            QtCore.SIGNAL("clicked()"), self.generate)

        self.h22liste = Viewer.ListViewDrop(self)
        self.h22liste.fileDropped.connect(self.FilesDropped)
        h22.addWidget(self.h22liste)
        self.h22liste.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.h22liste.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_h22listeItem = QtGui.QAction('delete item', self)
        self.h22liste.addAction(efface_h22listeItem)
        QtCore.QObject.connect(efface_h22listeItem, QtCore.SIGNAL("triggered()"), self.efface_h22listeItem)
        efface_h22liste = QtGui.QAction('clear list', self)
        self.h22liste.addAction(efface_h22liste)
        QtCore.QObject.connect(efface_h22liste, QtCore.SIGNAL("triggered()"), self.efface_h22liste)


        h23 = QtGui.QVBoxLayout()

        h23Buttons = QtGui.QHBoxLayout()
        h23.addLayout(h23Buttons)
        self.h23Label = QtGui.QLabel()
        h23Buttons.addWidget(self.h23Label)
        h23spacer = QtGui.QLabel()
        h23spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        h23Buttons.addWidget(h23spacer)

        self.h23BT = QtGui.QCheckBox("get titles")
        h23Buttons.addWidget(self.h23BT)
        #self.h23BT.setChecked(True)
        self.h23BT.stateChanged.connect(self.generate)
        self.h23BR = QtGui.QCheckBox("replace")
        h23Buttons.addWidget(self.h23BR)
        h23BS = QtGui.QPushButton("save CTX")
        h23Buttons.addWidget(h23BS)
        h23BS.clicked.connect(self.saveCTX)


        self.h23liste = QtGui.QTableWidget()
        self.h23liste.verticalHeader().setVisible(False)
        #TODO rendre la liste non editable
        h23.addWidget(self.h23liste)

        
        H2.addLayout(h23)

        H1 = QtGui.QHBoxLayout()

        h11 = QtGui.QVBoxLayout()
        H1.addLayout(h11)
        
        self.select_champ = QtGui.QComboBox()
        h11.addWidget(self.select_champ)
        
        self.search_line = QtGui.QLineEdit()
        h11.addWidget(self.search_line)
        self.search_line.returnPressed.connect(self.eval_search_line)
        self.search_result = QtGui.QListWidget()
        h11.addWidget(self.search_result)
        self.search_result.currentItemChanged.connect(self.eval_search_C)

        self.search_line.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.search_result.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        h12 = QtGui.QVBoxLayout()
        H1.addLayout(h12)


        h12buttons = QtGui.QHBoxLayout()
        h12.addLayout(h12buttons)
        self.h12LabelNum = QtGui.QLabel()
        h12buttons.addWidget(self.h12LabelNum)
        h12buttonsSpacer = QtGui.QLabel()
        h12buttons.addWidget(h12buttonsSpacer)
        h12buttonsSpacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        h12BS = QtGui.QPushButton("save codex")
        h12BS.clicked.connect(self.codex_dic.save_codex)
        h12buttons.addWidget(h12BS)

        self.listRad = QtGui.QListWidget()
        h12.addWidget(self.listRad)
        self.listRad.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.listRad.doubleClicked.connect(self.mod_listRadItem)
        self.listRad.currentItemChanged.connect(self.changeRad)
        self.listRad.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_listRadItem = QtGui.QAction('delete item', self)
        self.listRad.addAction(efface_listRadItem)
        QtCore.QObject.connect(efface_listRadItem, QtCore.SIGNAL("triggered()"), self.efface_listRadItem)
        add_listRadItem = QtGui.QAction('add item', self)
        self.listRad.addAction(add_listRadItem)
        QtCore.QObject.connect(add_listRadItem, QtCore.SIGNAL("triggered()"), self.add_listRadItem)
        self.listRad.setItemDelegate(Viewer.MyDelegate(self))
        self.listRad.itemDelegate().closedSignal.connect(self.mod_listRadItem_done)


        self.initiate()


        h13 = QtGui.QVBoxLayout()
        H1.addLayout(h13)
        self.h13List = QtGui.QTableWidget()
        self.h13List.setColumnCount(2)
        self.h13List.setHorizontalHeaderLabels([u'field', u'value'])
        self.h13List.horizontalHeader().setStretchLastSection(True)     
        self.h13List.verticalHeader().setVisible(False)
        h13.addWidget(self.h13List)

        self.h13List.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_listRadValueItem = QtGui.QAction('delete line', self)
        self.h13List.addAction(efface_listRadValueItem)
        QtCore.QObject.connect(efface_listRadValueItem, QtCore.SIGNAL("triggered()"), self.efface_listRadValueItem)
        add_listRadValueItem = QtGui.QAction('add line', self)
        self.h13List.addAction(add_listRadValueItem)
        QtCore.QObject.connect(add_listRadValueItem, QtCore.SIGNAL("triggered()"), self.add_listRadValueItem)
        copy_h13listLine = QtGui.QAction('copy line', self)
        self.h13List.addAction(copy_h13listLine)
        QtCore.QObject.connect(copy_h13listLine, QtCore.SIGNAL("triggered()"), self.copy_h13listLine)
        paste_h13listLine = QtGui.QAction('paste line', self)
        self.h13List.addAction(paste_h13listLine)
        QtCore.QObject.connect(paste_h13listLine, QtCore.SIGNAL("triggered()"), self.paste_h13listLine)

        self.h13List.cellChanged.connect(self.onChangeh13List)

        h14 = QtGui.QVBoxLayout()
        H1.addLayout(h14)
        h14buttons = QtGui.QHBoxLayout()
        h14.addLayout(h14buttons)
        h14BM = QtGui.QPushButton("merge")
        h14buttons.addWidget(h14BM)
        h14BM.clicked.connect(self.merge_codex)
        self.h14LabelNum = QtGui.QLabel()
        h14buttons.addWidget(self.h14LabelNum)
        h14buttonsSpacer = QtGui.QLabel()
        h14buttons.addWidget(h14buttonsSpacer)
        h14buttonsSpacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        self.h14MergeList = QtGui.QListWidget()
        h14.addWidget(self.h14MergeList)

        L.addLayout(H1)

    
    def initiate(self):
        self.listRad.currentItemChanged.disconnect(self.changeRad)
        self.listRad.doubleClicked.disconnect(self.mod_listRadItem)
        if len(self.codex_dic.dico):
            self.listRad.clear()    
            self.listRad.addItems(self.codex_dic.dico.keys())
            self.listRad.sortItems()
            self.h12LabelNum.setText("%d entries"%len(self.codex_dic.dico))
        self.reset_select_champ()
        self.listRad.doubleClicked.connect(self.mod_listRadItem)
        self.listRad.currentItemChanged.connect(self.changeRad)

    def reset_select_champ(self):
        self.select_champ.clear()
        self.select_champ.addItem(u"")
        if len(self.codex_dic.dico):
            self.select_champ.addItems(self.codex_dic.champs())
        self.search_line.clear()
        self.search_result.clear()

    def efface_listRadItem(self):
        item = self.listRad.currentItem().text()
        del(self.codex_dic.dico[item])
        row = self.listRad.currentRow()
        self.listRad.takeItem(row)

    def add_listRadItem(self):
        item = QtGui.QListWidgetItem("")
        self.listRad.insertItem(self.listRad.count(), item)
        self.listRad.setCurrentItem(item)
        self.mod_listRadItem()

    def mod_listRadItem(self):
        item = self.listRad.currentItem()
            
        item.setFlags(self.listRad.currentItem().flags() | QtCore.Qt.ItemIsEditable)
        #item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
        self.listRadItemText = item.text()
        if (self.listRad.state() !=  self.listRad.EditingState):
            self.listRad.editItem(item)

    def mod_listRadItem_done(self):
        item = self.listRad.currentItem()

        old = self.listRadItemText
        new = item.text()
        if (old != new) :
            if (new in self.codex_dic.dico.keys()):
                item.setText(old)
            else : 
                if (old == ""):
                    self.codex_dic.dico[new] =  { u"author" : "", u"medium"  :
                        "", u"media-type" : "", u"authorship" : "",
                        u"localisation" : "", u"observations" : "" } 
                    self.changeRad()
                else :
                    self.codex_dic.dico[new] =  self.codex_dic.dico[old]
                    del(self.codex_dic.dico[old])
                self.listRad.sortItems()
                self.listRad.scrollToItem(item)

    def efface_listRadValueItem(self):
        if self.h13List.selectedItems() :
            row = self.h13List.currentRow()
            k = self.listRad.currentItem().text()
            f = self.h13List.item(row, 0).text()
            del(self.codex_dic.dico[k][f])
            self.h13List.removeRow(row)

    def add_listRadValueItem(self):
        self.h13List.insertRow(0)
    
    def copy_h13listLine(self):
        r = self.h13List.currentRow()
        if  self.h13List.currentItem():
            self.copy_h13listLineContent = [self.h13List.item(r, 0).text(), self.h13List.item(r, 1).text()]

    def paste_h13listLine(self):
        if hasattr(self, "copy_h13listLineContent"):
            self.h13List.cellChanged.disconnect(self.onChangeh13List)
            field, value = self.copy_h13listLineContent
            k = self.listRad.currentItem().text()
            row = -1
            for r in range(self.h13List.rowCount()):
                if (self.h13List.item(r, 0)):
                    if field == self.h13List.item(r, 0).text() :
                        row = r
            if (row > -1):
                self.h13List.item(row, 1).setText(value)
            else :
                self.h13List.insertRow(r+1)
                self.h13List.setItem(r+1, 0, QtGui.QTableWidgetItem(field))
                self.h13List.setItem(r+1, 1, QtGui.QTableWidgetItem(value))
            self.codex_dic.dico[k][field] = value
            self.h13List.cellChanged.connect(self.onChangeh13List)

    def efface_h22liste(self):
        self.h22liste.clear()
        self.h22Label.setText("Text file list: drag and drop")
        self.generate()

    def efface_h22listeItem(self):
        if self.h22liste.selectedItems():
            self.h22liste.takeItem(self.h22liste.currentRow())
            #self.generate()
            self.h22Label.setText(u"%s texts"% self.h22liste.count())

    def changeRad(self):
        self.h13List.clear()    
        self.h13List.setHorizontalHeaderLabels([u'field', u'value'])
        RAD = self.listRad.currentItem().text() 
        if (RAD == ""):
            fields = {}
        elif RAD in self.codex_dic.dico.keys():
            fields = self.codex_dic.dico[RAD].keys()
        self.h13List.setRowCount(len(fields))
        r = 0
        for field in fields:
            i_field = QtGui.QTableWidgetItem(field)
            self.h13List.setItem(r, 0, i_field)
            v_field = QtGui.QTableWidgetItem(self.codex_dic.dico[RAD][field])
            self.h13List.setItem(r, 1, v_field)
            r += 1
        self.h13List.resizeColumnToContents (0)

    def onChangeh13List(self):
        r = self.h13List.currentRow()
        c = self.h13List.currentColumn()
        if ((r != -1) and (c != -1)):
            k = self.listRad.currentItem().text()
            f = self.h13List.item(r, 0).text()
            if (not re.match("^\s*$", f)) :
                if (c):
                    v = self.h13List.currentItem().text()
                    self.codex_dic.dico[k][f] = v
                else:
                    oldfields = self.codex_dic.champs()
                    oldfield =   self.oldfield(k)
                    if (oldfield in self.codex_dic.dico[k].keys()):
                        self.codex_dic.dico[k][f] = self.codex_dic.dico[k][oldfield] 
                        del (self.codex_dic.dico[k][oldfield])
                    else :
                        self.codex_dic.dico[k][f] = ""
                self.reset_select_champ()
            else:
                oldfield =   self.oldfield(k)
                if (oldfield):
                    self.h13List.item(r, 0).setText (oldfield)
            self.h13List.resizeColumnToContents (0)
                
    def oldfield(self, k):           
        listefield = []
        for row in range(self.h13List.rowCount()):
            listefield.append(self.h13List.item(row, 0).text())
        L = list(set(self.codex_dic.dico[k].keys()) - set(listefield))
        if len(L):
            return L[0]
        else :
            return False

    def FilesDropped(self, l):
        existing = [] 
        for r in range(self.h22liste.count()):
            existing.append(self.h22liste.item(r).text())
        for url in list(set(l) - set(existing)):
            if os.path.splitext(url)[1] in ['.txt', '.TXT']:
                item = QtGui.QListWidgetItem(url, self.h22liste)
                item.setStatusTip(url)
                self.h22Label.setText(u"%s texts"% self.h22liste.count())
                print "a"
                QtGui.QApplication.processEvents()
        self.h22liste.sortItems()
###            if os.path.exists(url):
###                if os.path.splitext(url)[1] in ['.txt', '.TXT']:
###                    item = QtGui.QListWidgetItem(url, self.h22liste)
###                    item.setStatusTip(url)
###                    self.h22Label.setText(u"%s texts"% self.h22liste.count())
###                    QtGui.QApplication.processEvents()
###            self.h22liste.sortItems()
###        self.generate()

    def appendItems(self, liste):
        self.h22liste.clear()
        self.h22liste.addItems(liste)
        self.h22Label.setText(u"%s texts"% self.h22liste.count())
        self.h22liste.sortItems()
    
    def eval_search_line(self):
        self.search_result.clear()
        pattern = self.search_line.text()
        field = self.select_champ.currentText()
        result = self.codex_dic.chercheValue(field, pattern)
        for r in result:
            self.search_result.addItem(" : ".join(r))
        self.search_result.sortItems()
        
    def eval_search_C(self):
        item = self.search_result.currentItem()
        if (item):
            i = item.text()
            i = re.split(" : ", i, 1)[0]
            item = self.listRad.findItems(i, QtCore.Qt.MatchFlags(QtCore.Qt.MatchExactly))
            self.listRad.setCurrentItem(item[0])

    def generate(self):
        self.CTX_to_be_saved = {}
        self.h23liste.clear()
        self.h23liste.setRowCount(0)
        self.h23liste.setColumnCount(2)
        if self.h23BT.checkState():
            self.h23liste.setHorizontalHeaderLabels([u'path', u'key,  date and title'])
        else :
            self.h23liste.setHorizontalHeaderLabels([u'path', u'key and date'])
        self.h23liste.horizontalHeader().setStretchLastSection(True)    
        m = 0
        f = 0
        for r in range(self.h22liste.count()):
            path = self.h22liste.item(r).text()
            test = self.codex_dic.eval_file(path)
            if (test):
                self.match_add(path, test)
                m += 1
            else :
                self.failed_add(path)
                f += 1
            self.h23Label.setText("%d matches, %d fails" % (m, f))
            QtGui.QApplication.processEvents()
        self.h23liste.resizeColumnToContents (0)
        self.h23liste.sortItems(1)

    def match_add(self, path, result):
        r = self.h23liste.rowCount()
        self.h23liste.insertRow(r)
        item_path = QtGui.QTableWidgetItem(path)        
        self.h23liste.setItem(r, 0, item_path)

        CTXpath = path[:-3] + "ctx"
        self.CTX_to_be_saved[CTXpath] = self.codex_dic.dico[result[0]].copy()
        self.CTX_to_be_saved[CTXpath]["date"] = result[1] + " 00:00:00"

        if self.h23BT.checkState():
            if (os.path.isfile(path)): 
                title = self.get_title(path)
            else :
                title = ""
            item_value_txt = u" ".join(result) + u" %s"% title
            self.CTX_to_be_saved[CTXpath][u"title"] = title
        else :
            item_value_txt = u" ".join(result) 
        item_value = QtGui.QTableWidgetItem(item_value_txt)
        self.h23liste.setItem(r, 1, item_value)
        data = ""
        for k, v in self.codex_dic.dico[result[0]].iteritems():
            data += "%s:%s\n"%(k, v)
        item_path.setToolTip(data[:-1])
        item_value.setToolTip(data[:-1])

    def get_title(self, path):
        """the first line of the .txt is taken for ctx title"""
        with open(path, "rU") as buf:
            B = buf.readlines()
        title = B[0][:-1]
        try :
            return title.decode('latin-1')
        except :
            return title.decode('utf-8')

    def failed_add(self, path):
        r = self.h23liste.rowCount()
        self.h23liste.insertRow(r)
        item_path = QtGui.QTableWidgetItem(path)        
        item_path.setForeground(QtGui.QColor("red"))
        self.h23liste.setItem(r, 0, item_path)
        item_value = QtGui.QTableWidgetItem(u"\u00A0 no match")
        item_value.setForeground(QtGui.QColor("red"))
        self.h23liste.setItem(r, 1, item_value)
        item_path.setToolTip("no match")
        item_value.setToolTip("no match")

    def merge_codex(self):
        fname, filt = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.', '*.cfg;*.publi;*.xml')
        if (fname) :
            m_codex = Controller.edit_codex()
            if os.path.splitext(fname)[1]  == ".publi":
                m_codex.parse_supports_publi(fname)
            elif os.path.splitext(fname)[1]  == ".cfg": 
                m_codex.parse_codex_cfg(fname)
            elif os.path.splitext(fname)[1]  == ".xml": 
                m_codex.parse_codex_xml(fname)
            self.codex_dic.dico, fails = m_codex.fusionne(self.codex_dic.dico, m_codex.dico)
            self.initiate() 
            self.h14MergeList.clear()
            for k, v in fails.iteritems():
                self.h14MergeList.addItem("%s : %s"%(k, str(v)))
            self.h14LabelNum.setText("%d fails" % len(fails))

    def saveCTX(self):
        if hasattr(self, "CTX_to_be_saved"):
            for path, v in self.CTX_to_be_saved.iteritems():
                if  not (os.path.isfile(path) and not self.h23BR.checkState())   :
                    CTX = Controller.parseCTX()
                    CTX.path = path
                    CTX.dico = v    
                    CTX.savefile()
    

def main():
    app = QtGui.QApplication(sys.argv)

    translator = QtCore.QTranslator()
#FIXME translation
    #self.translator.load('translations/en_GB') 
    #translator.load('translations/fr_FR') 
    translator.load('i18n/'+ QtCore.QLocale.system().name())
    app.installTranslator(translator)

    ex  = Principal()
    #ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
