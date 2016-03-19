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
import atexit
import webbrowser
#import socket 

#from fonctions import translate
import xml_info
import Viewer
import Controller

class Principal(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

##################################################
        # create the menu bar
##################################################
        Menubar = self.menuBar()

##################################################
        #Corpus and Server
        Menu_Corpus = Menubar.addMenu(self.tr('&Corpus and Server'))
        Menu_distant = Menu_Corpus.addMenu(QtGui.QIcon('images/distant.png'),
                                                             self.tr('&Remote'))
        Menu_distant.setStatusTip(self.tr('Connect to prosperologie.org\
            servers'))

        get_remote_corpus = xml_info.myxml()
        if get_remote_corpus.get():
            if get_remote_corpus.parse():
                for corpus in get_remote_corpus.getDataCorpus(): 
#TODO not enabled if cannot reach port 60000
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
        menu_local_edit = QtGui.QAction("Edit project", self)
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

        menu_server_vars = QtGui.QAction("&Variables testing", self)
        menu_server_vars.setStatusTip("Directly interact with server variables")
        menu_server_vars.triggered.connect(self.display_server_vars)
        Menu_Corpus.addAction(menu_server_vars)

#TODO transform corpus p1<->p2
        menu_convert_corpus = QtGui.QAction("&Convert P1 and P2 corpus", self)
        Menu_Corpus.addAction(menu_convert_corpus)
        menu_convert_corpus.setEnabled(False) 

#TODO recup corpus, fusion, generer sous corpus
#TODO Constellations and corpus comparisons

##################################################
        #Concepts and lexics
        menu_concepts = Menubar.addMenu('&Concepts')
        menu_concepts_edition = QtGui.QAction("&Edition", self)
        menu_concepts.addAction(menu_concepts_edition)
        menu_concepts_edition.setEnabled(False)
        menu_sycorax =  QtGui.QAction("&Sycorax", self)
        menu_sycorax.setStatusTip("Advanced concepts edition")
        menu_concepts.addAction(menu_sycorax)
        menu_sycorax.setEnabled(False)
        
##################################################
        #Texts
        Menu_Texts = Menubar.addMenu('&Texts and Contexts')
        menu_contexts = QtGui.QAction('&Contexts', self)    
        Menu_Texts.addAction(menu_contexts)
        menu_contexts.setStatusTip("Work with contexts")
        menu_contexts.triggered.connect(self.display_contexts)
        Menu_AddTex = QtGui.QAction('&Add a new text', self)    
        Menu_Texts.addAction(Menu_AddTex)
        Menu_AddTex.setEnabled(False)
        Menu_ModTex = QtGui.QAction('&Action on selected texts', self)    
        Menu_Texts.addAction(Menu_ModTex)
        Menu_ModTex.setEnabled(False)

##################################################
        #Viz and computations
        menu_comput = Menubar.addMenu('&Computations')
        menu_pers =  QtGui.QAction("&Persons", self)
        menu_pers.setStatusTip("Detect people")
        menu_comput.addAction(menu_pers)
        menu_pers.triggered.connect(self.display_pers)
        menu_pers.setEnabled(False)
#TODO viz
#TODO author signatures, grappes, periodisations
#TODO corpus indicators and properties
#TODO list evolutions

##################################################
        #Marlowe
        Menu_Marlowe = Menubar.addMenu('&Marlowe')
        menu_marlowe_gen = QtGui.QAction("&Variant generation", self)
        menu_marlowe_gen.triggered.connect(self.add_gen_mrlw_tab)
        Menu_Marlowe.addAction(menu_marlowe_gen)
        Menu_Marlowe_remote = QtGui.QAction("&Remote", self)
        Menu_Marlowe_remote.triggered.connect(self.MarloweViewer)
        Menu_Marlowe.addAction(Menu_Marlowe_remote)

##################################################
        #Parameters&sHelp
        menu_param = Menubar.addMenu('&Parameters and help')
        menu_parameters = QtGui.QAction('&Parameters', self)
        menu_param.addAction(menu_parameters)
        menu_parameters.setEnabled(False)
#reduire le poids seulement si expr englobante de meme type
        menu_help = QtGui.QAction('&Manual', self)
        menu_param.addAction(menu_help)
        menu_param.triggered.connect(lambda: webbrowser.open('http://mypads.framapad.org/mypads/?/mypads/group/doxa-g71fm7ki/pad/view/interface-p2-manuel-de-l-utilisateur-hsa17wo'))


##################################################
##################################################
        # create the status bar
##################################################
        self.status = self.statusBar()
        self.status.showMessage(u"Ready")

##################################################
##################################################
        #create the progressebar
##################################################
        self.PrgBar = Viewer.PrgBar(self)
        self.status.addPermanentWidget(self.PrgBar.bar)
        
##################################################
##################################################
        # create the toolbar
##################################################
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
##################################################
#cadrans NO - NE - SO - SE
##################################################
##################################################

##################################################
    #cadran NO
##################################################
#TODO start with principal concepts. Lexicon and concepts access via menu

##################################################
##### Tab for actants                #############

        self.actantsTab = Viewer.actantsTab()

##################################################
##### Tab for authors                #############

        self.authorsTab = Viewer.authorsTab()

##################################################
##### Tab for concepts #############
        self.NOT2 = Viewer.ConceptTab()
        self.NOT2.select.currentIndexChanged.connect(self.select_concept)
        self.NOT2.sort_command.currentIndexChanged.connect(self.affiche_concepts_scores)
        self.NOT2.dep0.listw.currentItemChanged.connect(self.cdep0_changed)
        self.NOT2.depI.listw.currentItemChanged.connect(self.cdepI_changed)
        self.NOT2.depII.listw.currentItemChanged.connect(self.cdepII_changed)
        self.NOT2.depI.deselected.connect(lambda: self.NOT2.depII.listw.clear())
        self.NOT2.dep0.deselected.connect(lambda: [self.NOT2.depI.listw.clear(), 
            self.NOT2.depII.listw.clear()])
#TODO add those  below
        for i in range(6,12):
            self.NOT2.sort_command.model().item(i).setEnabled(False)

##################################################
##### Tab for syntax items (Lexicon) #############
        self.NOT1 = Viewer.LexiconTab()
        self.NOT1.select.currentIndexChanged.connect(self.select_liste)
        self.NOT1.sort_command.currentIndexChanged.connect(self.affiche_liste_scores)
        self.NOT1.dep0.listw.currentItemChanged.connect(self.ldep0_changed) 
        self.NOT1.depI.listw.currentItemChanged.connect(self.ldepI_changed)
        self.NOT1.depII.listw.currentItemChanged.connect(self.ldepII_changed)
        self.NOT1.depI.deselected.connect(lambda: self.NOT1.depII.listw.clear())
        self.NOT1.dep0.deselected.connect(lambda: [self.NOT1.depI.listw.clear(), self.NOT1.depII.listw.clear()])
#TODO add those below
        for i in range(6,12):
            self.NOT1.sort_command.model().item(i).setEnabled(False)

#TODO activate all context menus via the Controller
        #context menu activation

        self.NOT1.dep0.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(0)))
        self.NOT1.dep0.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(0)))
        self.NOT1.dep0.listw.addAction(QtGui.QAction('copy list', self,
            triggered=self.copy_to_cb))
        self.NOT1.depI.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(1)))
        self.NOT1.depI.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(1)))
        self.NOT1.depII.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(2)))
#TODO send to texts list
        self.NOT1.depII.listw.addAction(QtGui.QAction('sentences', self,
            triggered=self.teste_wording))
        self.NOT1.depII.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(2)))

        self.NOT2.dep0.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(0)))
        self.NOT2.dep0.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(0)))
#TODO #self.NOT2.dep0.addAction(QtGui.QAction('copy list', self, triggered=self.copy_to_cb))
        self.NOT2.depI.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(1)))
        self.NOT2.depI.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(1)))
        self.NOT2.depII.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(2)))
#TODO send to texts list
        self.NOT2.depII.listw.addAction(QtGui.QAction('sentences', self,
            triggered=self.teste_wording))
        self.NOT2.depII.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(2)))

##################################################
##### Tab for persons                #############

        self.show_persons = QtGui.QWidget()
#TODO make it closable

################################################
#NO QTabWidget
        self.NOTs = QtGui.QTabWidget()
        self.NOTs.addTab(self.actantsTab, self.tr("Actants"))
        self.NOTs.addTab(self.authorsTab, self.tr("Authors"))
        self.NOTs.addTab(self.NOT2, "Concepts")
        self.NOTs.addTab(self.NOT1, self.tr("Lexicon"))
        self.NOTs.currentChanged.connect(self.change_NOTab)

##################################################
        #cadran NE
##################################################

##################################################
# Journal
        self.journal = Viewer.Journal()

################################################
#Explorer Tab
#TODO ajouter navigateur (concepts)
        self.explorer_widget =  Viewer.Explorer()
        self.explorer_widget.saisie.returnPressed.connect(self.explorer)
        self.explorer_widget.liste.listw.currentItemChanged.connect(self.explo_item_selected)
        self.explorer_widget.liste.listw.addAction(QtGui.QAction('texts', self,
            triggered=self.explo_show_text))
##################################################
##### Tab for formulae                #############

        formulaeTab = QtGui.QWidget()

################################################
#Access by context CTX
        self.CTXs = Viewer.Contexts()
        self.CTXs.l.currentItemChanged.connect(self.contexts_contents) 

##################################################
#evaluer directement les variables du serveur
        self.server_vars = Viewer.ServerVars()
        self.server_vars.champ.returnPressed.connect(self.server_vars_Evalue)
        self.server_vars.button_eval.clicked.connect(self.server_vars_Evalue)
        self.server_vars.button_getsem.clicked.connect(self.server_getsem_Evalue)
        self.server_vars.button_eval_index.clicked.connect(self.server_index_Evalue)

##################################################
#NE QTabWidget
        self.NETs = QtGui.QTabWidget()
        self.NETs.setTabsClosable(True)
        self.NETs.tabCloseRequested.connect(self.NETs.removeTab)
        self.journal_index = self.NETs.addTab(self.journal.journal, "Journal")
        Viewer.hide_close_buttons(self.NETs,0)
        self.NETs.addTab(self.explorer_widget, "Search")
        Viewer.hide_close_buttons(self.NETs,1)
        self.NETs.addTab(formulaeTab, "Formulae")
        Viewer.hide_close_buttons(self.NETs,2)

##################################################
        #cadran SO
##################################################

##################################################
#l'onglet des textes
        self.SOT1 = QtGui.QTabWidget()
        self.SOT1.setTabsClosable(True)
        self.SOT1.tabCloseRequested.connect(self.SOT1.removeTab)

##################################################
#l'onglet des réseaux
        self.tabNetworks = QtGui.QTabWidget()
        self.tabNetworks.setTabsClosable(True)
        self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

##################################################
#TODO les expression englobantes

##################################################
#SO QTabWidget
        self.SOTs = QtGui.QTabWidget()
        self.SOTs.setTabsClosable(True)
        self.SOTs.tabCloseRequested.connect(self.SOTs.removeTab)
        self.SOTs.addTab(self.SOT1, self.tr("Texts"))
        Viewer.hide_close_buttons(self.SOTs,0)

##################################################
#cadran SE
##################################################

##################################################
    # onglet proprietes du texte
        self.textProperties = QtGui.QTabWidget()

    # sous onglet proprietes saillantes
        self.saillantes = Viewer.SaillantesProperties()
        self.saillantes.Act.doubleClicked.connect(self.deploie_Actant)
        self.saillantes.Cat.doubleClicked.connect(self.deploie_Cat)
        self.saillantes.Col.doubleClicked.connect(self.deploie_Col)
        self.textProperties.addTab(self.saillantes, self.tr("Sailent structures"))

    # sous onglet des éléments 
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

##################################################
    #CTX content
        self.SET2 = Viewer.textCTX()
        self.SET2.T.cellChanged.connect(self.onChangeCTX)
        self.SET2.valid.clicked.connect(self.saveCTX)
        self.SET2.valid.setEnabled(False)
        self.SET2.reset.clicked.connect(self.resetCTX)
        self.SET2.reset.setEnabled(False)
    
##################################################
    # onglet contenu du texte
        self.textContent = QtGui.QTextEdit() 

##################################################
#sentences tab
        self.tab_sentences = QtGui.QTabWidget()
        self.tab_sentences.setTabsClosable(True)
        self.tab_sentences.tabCloseRequested.connect(self.tab_sentences.removeTab)

##################################################
#SE QTabWidget
        self.SETs = QtGui.QTabWidget()
        self.SETs.addTab(self.textProperties, "Properties")
        self.SETs.addTab(self.SET2, "Context")
        self.SETs.addTab(self.textContent, "Text")

        self.SETs.currentChanged.connect(self.change_SETab)
        self.textProperties.currentChanged.connect(self.change_text_prop_tab)
        self.text_elements.selector.currentIndexChanged.connect(self.show_text_elements)

################################################
################################################
        ###Main Layout en grid
################################################
################################################
#FIXME corriger resize des grids sur petits ecrans
#TODO allow cadran to resize to the whole window 
        main = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        grid.addWidget(self.NOTs,0, 0)
        grid.addWidget(self.NETs, 0, 1)
        grid.addWidget(self.SOTs, 1, 0)
        grid.addWidget(self.SETs, 1, 1)
        grid.setContentsMargins(5,10,5,5)
        grid.setSpacing(10)
        main.setLayout(grid)
        self.setCentralWidget(main)

        #grid.setRowMinimumHeight(0,1000))
        #testeur = QtGui.QPushButton('+')
        #self.NOTs.setCornerWidget(testeur)
        
        #grid.setContentsMargins(2,2,2,2)

        self.setWindowTitle(u'P-II interface')
        self.setWindowIcon(QtGui.QIcon("images/Prospero-II.png"))
        self.show() 

################################################
################################################
#Fin de la methode principale d'affichage
#début des fonctions
################################################
################################################

    def pre_calcule(self):
        self.activity("pre-computing : texts")
        self.preCompute = Controller.preCompute(self)
        self.listeObjetsTextes = self.preCompute.listeObjetsTextes

        self.CTXs.l.clear()
        self.CTXs.l.addItems(self.preCompute.liste_champs_ctx)

        self.PrgBar.setv(50)

        # associated values
        self.activity("pre-computing : values")
        compteur = 0
        max_compteur = len(self.preCompute.type_var) * len(self.preCompute.type_calcul)
        for typ in self.preCompute.type_var :
            for calc in self.preCompute.type_calcul:
#FIXME freq et nbaut ne marche pas ?
                self.preCompute.cacheAssocValue(typ, calc)
                compteur += 1
                self.PrgBar.setv(50 + (int(float(compteur) * 50 / max_compteur)))
        self.PrgBar.reset()
#TODO get concepts for search engine

    def activity(self, message):
        """Add message to the journal"""
        self.status.showMessage(message)
        time = "%s" % datetime.datetime.now()
        self.journal.history.append("%s %s" % (time[:19], message))
        with open("P-II-gui.log",'a') as logfile:
            logfile.write("%s %s\n" % (time[:19], message.encode("utf-8")))

#REMOVEME>
#    def ord_liste_txt(self, liste_sem, order="chrono"):
#        liste = {}
#        if (order=="chrono"):
#            for e in liste_sem :
#                txt = self.listeObjetsTextes[e]
#                date = txt.getCTX("date")
#                date = re.split(" ", date) #sépare date et heure
#                if (len(date) > 1):
#                    date, heure = date
#                else:
#                    date = date[0]
#                liste[e] = "-".join(reversed(re.split("/", date)))
#            return sorted(liste.items(), key=lambda (k, v) : v) 
#<REMOVEME

    def destroy_texts_tabs(self):
        for i in reversed(range(self.SOT1.tabBar().count())):
            self.SOT1.tabBar().removeTab(i)

    def create_corpus_texts_tab(self):
        """create a tab for corpus texts"""
#FIXME reset if open a new corpus
        self.destroy_texts_tabs()
        n = len(self.preCompute.listeTextes)
        self.activity(u"Displaying text list (%d items)" % n)
        self.CorpusTexts = Viewer.ListTexts(False,
            self.preCompute.dicTxtSem.values(), self.listeObjetsTextes)
        self.CorpusTexts.corpus.itemSelectionChanged.connect(self.onSelectText)
        self.SOT1.addTab(self.CorpusTexts, "corpus (%d)"%n)
        Viewer.hide_close_buttons(self.SOT1,0) #corpus text tab permanent

    def onSelectText(self):
        """when a text is selected, select it in other lists and display text properties"""
        #get txt sem
        row = self.SOT1.focusWidget().currentRow()
        txt = self.SOT1.focusWidget().widget_list[row]
        self.semantique_txt_item = txt.sem
        self.activity("Displaying %s %s %s" %txt.getResume())

        #find txt in other tabs
        for t in range (self.SOT1.count()): 
            lw =  self.SOT1.widget(t).findChildren(QtGui.QListWidget) 
            for i, l in enumerate(lw):
                l.itemSelectionChanged.disconnect(self.onSelectText)
                tab_txts = l.widget_list
                if txt in tab_txts:
                    l.setCurrentRow(tab_txts.index(txt)) 
                else:
                    l.deselect_all()
                l.itemSelectionChanged.connect(self.onSelectText)

        #display properties in selected tab
        if (self.SETs.currentIndex() == 0):
            self.show_textProperties(self.semantique_txt_item)
        elif (self.SETs.currentIndex() == 1):
            self.show_textCTX(self.semantique_txt_item) 
        elif (self.SETs.currentIndex() == 2):
            self.show_textContent(self.semantique_txt_item)
                
#REMOVEME>
#    def selectTxtCorpus(self, txt):
#        self.CorpusTexts.corpus.itemSelectionChanged.disconnect(self.onSelectText)
#        self.CorpusTexts.corpus.setCurrentRow(self.dic_widget_list_txt[0].index(txt))
#        self.CorpusTexts.corpus.itemSelectionChanged.connect(self.onSelectText)
#<REMOVEME

    def deselectText(self):
        """vide les listes pour eviter confusion et deselectionne les listwidget"""
        self.saillantes.Act.clear()
        self.saillantes.Cat.clear()
        self.saillantes.Col.clear()
        self.text_elements.element_list.clear()
        self.efface_textCTX()
        self.textContent.clear()

        if hasattr(self, "semantique_txt_item"):
            del self.semantique_txt_item

        for listwidget in self.SOT1.findChildren(QtGui.QListWidget) :
            listwidget.itemSelectionChanged.disconnect(self.onSelectText)
            listwidget.deselect_all()
            listwidget.itemSelectionChanged.connect(self.onSelectText)

    def change_NOTab(self):
        if (self.NOTs.currentIndex() == 1): # si l'onglet des Concepts est sélectionné
            if  hasattr(self, "client"): # si connecte
                if not hasattr(self, "sem_concept"): #si pas de concept selectionné
                    self.select_concept(self.NOT2.select.currentText())
        elif (self.NOTs.currentIndex() == 0): 
            if  hasattr(self, "client"): 
                if not hasattr(self, "sem_liste_concept"): #si pas de concept selectionné
                    self.select_liste(self.NOT1.select.currentText()) 

    def change_SETab(self):
        if  hasattr(self, "semantique_txt_item"):
            sem_txt = self.semantique_txt_item
            if (self.SETs.currentIndex () == 0):
                self.saillantes.Act.clear()
                self.saillantes.Cat.clear()
                self.saillantes.Col.clear()
                self.show_textProperties(sem_txt)
            elif (self.SETs.currentIndex () == 1):
                self.efface_textCTX()
                self.show_textCTX(sem_txt) 
            elif (self.SETs.currentIndex () == 2):
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
        r = self.SET2.T.currentRow()
        if (r != -1):
            self.SET2.T.currentItem().setBackground(QtGui.QColor(237,243,254)) # cyan
            self.SET2.valid.setEnabled(True)
            self.SET2.reset.setEnabled(True)

    def saveCTX(self):
        sem_txt = self.semantique_txt_item
        txt =  self.listeObjetsTextes[sem_txt]
#FIXME AttributeError: 'Texte' object has no attribute 'formeResume'
        txtResume = txt.formeResume()
        modif = []
        for r in range(self.SET2.T.rowCount()):
            field = self.SET2.T.item(r, 0).text()
            val =  self.SET2.T.item(r, 1).text()
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
                newResume = txt.formeResume()
                for listWidget in self.SOT1.findChildren(QtGui.QListWidget):
                    for label in  listWidget.findChildren(QtGui.QLabel):
                        if label.text() == txtResume:
                            label.setText(newResume)
            
#FIXME pb de cache quand remet a jour la liste des ctx
        self.maj_metadatas()

        self.SET2.valid.setEnabled(False)
        self.SET2.reset.setEnabled(False)
        self.resetCTX()

    def resetCTX(self):
        self.SET2.valid.setEnabled(False)
        self.SET2.reset.setEnabled(False)
        self.show_textCTX(self.semantique_txt_item)
 
    def select_concept(self, typ):
        """ quand un element de Concepts est selectionné """
        self.sem_concept = Controller.semantiques[self.NOT2.select.currentText()]
        if (self.sem_concept in ["$col"]):
            #deployment for collections
            self.NOT2.sort_command.setCurrentIndex(1)
        self.affiche_concepts_scores()
        self.detect_concepts = ["abracadabri"]

    def select_liste(self, typ):
        """ quand un element de Lexicon est selectionné """
        self.sem_liste_concept = Controller.semantiques[self.NOT1.select.currentText()]
        self.detect_lexicon = ["abracadabri"]
        self.affiche_liste_scores()

    def change_liste(self, content):
        self.NOT1.dep0.listw.clear()
        self.NOT1.depI.listw.clear()
        self.NOT1.depII.listw.clear()
        for r in range(len(content)):
            i = QtGui.QListWidgetItem(content[r])
            self.NOT1.dep0.listw.addItem(i)
            #i.setToolTip('rank:%d'%(r+1))
            
    def change_liste_concepts(self, content):
        self.NOT2.dep0.listw.clear()
        self.NOT2.depI.listw.clear()
        self.NOT2.depII.listw.clear()
        self.NOT2.dep0.listw.addItems(content)

    def affiche_concepts_scores(self):
        which_concepts = self.NOT2.sort_command.currentText()
        typ = self.NOT2.select.currentText()
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
        which = self.NOT1.sort_command.currentText()
        typ = self.NOT1.select.currentText()
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
                if (self.sem_liste_concept == "$ent" and which == "deployment"
                                                                    and val == 0):
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

    def ldep0_changed(self):
        """ suite au changement de sélection, mettre à jour les vues dépendantes """ 
        which = self.NOT1.sort_command.currentText()
        itemT = self.NOT1.dep0.listw.currentItem()
        if (not len(self.NOT1.dep0.listw.selectedItems())):
            self.NOT1.dep0.listw.setCurrentItem(itemT)
        if (itemT):
            value, item = re.split(" ",itemT.text(),1)
#TODO clarify the rules for exaequos in rank
            #row = self.NOT1.dep0.listw.currentRow() 
            #self.activity("%s selected, rank %d" % (item, row+1))
            self.activity("%s selected, value %s" % (item, value))
            self.NOT1.depI.listw.clear() # on efface la liste
            self.NOT1.depII.listw.clear()
            sem = self.sem_liste_concept
            if (sem  in ["$ent"])  :
                # recupere la designation semantique de l'element
                self.semantique_lexicon_item_0 = self.client.eval_get_sem(item, sem)
                #liste les representants
                result = re.split(", ", self.client.eval_var("%s.rep[0:]"%
                    self.semantique_lexicon_item_0))
                
                if (result != [u'']):
                    self.ldepI_unsorted = []
                    for r in range(len(result)):
                        if (which  == "occurences" or which == "alphabetically"):
                            ask = "%s.rep%d.val"% (self.semantique_lexicon_item_0, r)
                        elif (which  == "deployment"):
                            ask = "%s.rep%d.dep"% (self.semantique_lexicon_item_0, r)
                        elif (which  == "number of texts"):
#FIXME corriger : il donne la valeur de l'EF entier
                            ask = "%s.rep%d.nbtxt"% (self.semantique_lexicon_item_0, r)
                            print "C26624: %s" %ask

                        val = int(self.client.eval_var(ask))
                        
                        to_add = "%d %s"%(val, result[r])
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.ldepI_unsorted.extend(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.ldepI_unsorted.append(to_add)
                            
                    if (which == "alphabetically"):
                        ldepI_sorted = sorted(self.ldepI_unsorted, key = lambda x : re.split(" ", x)[1], reverse =  0)
                    else :
                        ldepI_sorted = sorted(self.ldepI_unsorted, key = lambda x : int(re.split(" ", x)[0]), reverse =  1)
                    self.NOT1.depI.listw.addItems(ldepI_sorted)
                    # afficher directement E du premier element de D 
                    self.NOT1.depI.listw.setCurrentItem(self.NOT1.depI.listw.item(0))
                    self.ldepI_changed()
            else :
                self.semantique_lexicon_item_0 =  sem 

    def ldepI_changed(self):
        """quand un item de D est sélectionné, afficher représentants dans E"""
        which = self.NOT1.sort_command.currentText()
        itemT = self.NOT1.depI.listw.currentItem()
        if (itemT):
            row = self.ldepI_unsorted.index(itemT.text())
            self.NOT1.depII.listw.clear() # on efface la liste
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

                    self.NOT1.depII.listw.addItems(map(lambda x : "%d %s"% (x[1], x[0]), sorted(liste_scoree)))
                else :
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_lexicon_item_0, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.NOT1.depII.listw.addItems(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.NOT1.depII.listw.addItem("%d %s"%(val, result[r])) 
                        self.PrgBar.percAdd(1)
        self.PrgBar.reset()

    def ldepII_changed(self):
        itemT = self.NOT1.depII.listw.currentItem()
        if (itemT):
            item = re.sub("^\d* ", "", itemT.text())
            #item = itemT.text() # l'element selectionné
            row = self.NOT1.depII.listw.currentRow() 
            self.activity("%s selected" % item)
            sem = self.sem_liste_concept
            self.semantique_lexicon_item_II = u"%s.rep%d" %\
                (self.semantique_lexicon_item_I,  row)

    def cdep0_changed(self,level):
        """ suite au changement de sélection, mettre à jour les vues dépendantes """ 
        which_concepts = self.NOT2.sort_command.currentText()
        itemT = self.NOT2.dep0.listw.currentItem()
        if (not len(self.NOT2.dep0.listw.selectedItems())):
            self.NOT2.dep0.listw.setCurrentItem(itemT)
        if (itemT):
            value, item = re.split(" ",itemT.text(),1)
            #item = re.sub("^\d* ", "", itemT.text())
            #row = self.NOT2.dep0.listw.currentRow() 
            self.activity("%s selected, value %s" % (item, value))
            self.NOT2.depI.listw.clear() # on efface la liste
            self.NOT2.depII.listw.clear()
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
                        print "C1976: %s" % ask
                        val = int(self.client.eval_var(ask))
                        
                        liste_scoree.append([ result[r], val ])
                        self.PrgBar.percAdd(1)
                    if (which_concepts == "alphabetically"):
                        liste_scoree.sort()
                    self.NOT2.depII.listw.addItems(map(lambda x : "%d %s"% (x[1], x[0]), liste_scoree))   

                else:
                    self.cdepI_unsorted = []
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
                            self.cdepI_unsorted.extend(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.cdepI_unsorted.append(to_add)
                        
                    if (sem not in ["$cat_ent", "$cat_epr", "$cat_mar", "$cat_qua"]):
                        if (which_concepts == "alphabetically"):
                            ldepI_sorted = sorted(self.cdepI_unsorted, key = lambda x : re.split(" ", x)[1], reverse =  0)
                        else :
                            ldepI_sorted = sorted(self.cdepI_unsorted, key = lambda x : int(re.split(" ", x)[0]), reverse =  1)
                    self.NOT2.depI.listw.addItems(ldepI_sorted)

                    # afficher directement II du premier item de I 
                    self.NOT2.depI.listw.setCurrentItem(self.NOT2.depI.listw.item(0))
                    self.cdepI_changed()

    def cdepI_changed(self):
        """quand un item de D est sélectionné, afficher représentants dans E"""
        which_concepts = self.NOT2.sort_command.currentText()
        itemT = self.NOT2.depI.listw.currentItem()
        if (itemT):
            row = self.cdepI_unsorted.index(itemT.text())
            self.NOT2.depII.listw.clear() # on efface la liste
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
                    self.NOT2.depII.listw.addItems(map(lambda x : "%d %s"% (x[1], x[0]), sorted(liste_scoree)))
                else :
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item, row, r)
                        val = int(self.client.eval_var(ask))
                        
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.NOT2.depII.listw.addItems(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.NOT2.depII.listw.addItem("%d %s"%(val, result[r])) 
                        self.PrgBar.percAdd(1)
        self.PrgBar.reset()

    def cdepII_changed(self):
        itemT = self.NOT2.depII.listw.currentItem()
        if (itemT):
            val, item = Controller.sp_el(itemT.text())
            row = self.NOT2.depII.listw.currentRow() 
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

    def server_index_Evalue(self):
        var = self.server_vars.champ.text()
        self.server_vars.champ.clear()
        result = self.client.eval_index(var)
        result = " ".join(result[0][1])
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
        self.client=Controller.client(h, p)
        
        if (self.client.etat):
            # donne le focus a l'onglet journal
            self.NETs.setCurrentIndex(self.journal_index)
            # calcule en avance
            self.pre_calcule()
            #display info in the toolbar
            self.toolbar_descr_corpus.setText("Corpus name? %s texts %s pages\
... volume" % (self.preCompute.nbtxt, self.preCompute.nbpg))
#TODO display corpus name, volume

            #display list for the current selected tab
#            if (self.lexicon_or_concepts() == "lexicon"):
#                self.select_liste(self.NOT1.select.currentText())
#            elif (self.lexicon_or_concepts() == "concepts"):
#                self.select_concept(self.NOT2.select.currentText())


#FIXME first
            self.activity("calculating actants")
            ask = u"$act[0:]" 
            result = self.client.eval_var(ask)
            list_results = re.split(", ", result)
            self.actantsTab.L.clear()
            for i, act in enumerate(list_results):
                ask = u"$act%d.txt[0:]" % i 
                result = self.client.eval_var(ask)
                n = len(re.split(", ", result))
                self.actantsTab.L.addItem("%d %s" % (n, act))

            self.activity("calculating authors")
            ask = u"$aut[0:]" 
            result = self.client.eval_var(ask)
            list_results = re.split(", ", result)
            self.authorsTab.L.clear()
            for i, aut in enumerate(list_results):
                ask = u"$aut%d.txt[0:]" % i 
                result = self.client.eval_var(ask)
                n = len(re.split(", ", result))
                self.authorsTab.L.addItem("%d %s" % (n, aut))




            #Show corpus texts list on its own tab
            self.create_corpus_texts_tab()

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
        self.param_corpus_tab_index = self.NETs.addTab(self.param_corpus, "Corpus")
        self.NETs.setCurrentIndex(self.param_corpus_tab_index)

    def display_contexts(self):
        i = self.NETs.addTab(self.CTXs, "Contexts")
        self.NETs.setCurrentIndex(i)

    def display_server_vars(self):
        i = self.NETs.addTab(self.server_vars, "Server vars")
        self.NETs.setCurrentIndex(i)

    def display_pers(self):
        i = self.NOTs.addTab(self.show_persons, "Persons")
        self.NOTs.setCurrentIndex(i)

    def codex_window(self):
        codex_w = codex_window(self)
        codex_w.show()

    def add_gen_mrlw_tab(self):
        self.gen_mrlw = Viewer.MrlwVarGenerator()
        self.gen_mrlw_tab_index = self.NETs.addTab(self.gen_mrlw.gen_mrlw, 
                                                    self.tr("Variant generation"))
        self.NETs.setCurrentIndex(self.gen_mrlw_tab_index)

    def MarloweViewer(self):
        MarloweView = QtWebKit.QWebView()
        tabindex = self.NETs.addTab(MarloweView, "Marlowe")
        self.NETs.setCurrentIndex(tabindex)
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
        self.SET2.T.clear()
        self.SET2.T.setRowCount(0)
        self.SET2.T.setHorizontalHeaderLabels([u'field', u'value']) #on remet les headers apres le clear

    def show_textCTX(self, sem):
        """Show text metadata"""
        self.efface_textCTX()
        ctx = self.listeObjetsTextes[sem].getCTXall()
        self.SET2.T.setRowCount(len(ctx))
        for r, (field, value) in enumerate(ctx.iteritems()):
            itemCTXwidget_field = QtGui.QTableWidgetItem(field)
            self.SET2.T.setItem(r, 0, itemCTXwidget_field)
            itemCTXwidget_val = QtGui.QTableWidgetItem(value)
            self.SET2.T.setItem(r, 1, itemCTXwidget_val)
        self.SET2.T.resizeRowsToContents()

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
                for i, item in enumerate(self.list_element_items):
                    ask = u"%s.%s%d.val"%(self.semantique_txt_item, sem_concept, i)
                    val = int(self.client.eval_var(ask))
                    self.list_elements_valued[self.list_element_items[i]] = val
                    self.text_elements.element_list.addItem("%d %s"%(val, item))

    def deploie_text_elements(self):
#TODO add indef
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
                result = self.client.eval_var(ask)
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.list_elements_valued.keys()):
                            ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item,
                             sem_concept, self.list_element_items.index(r), sub_n)
                            res = self.client.eval_var(ask)
                            self.list_elements_valued[result[sub_n]] = res
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.list_elements_valued[result[sub_n]],
                             result[sub_n]))
                        i.setBackground(QtGui.QColor(237,243,254)) # cyan
                        self.text_elements.element_list.addItem(i)
       
    def show_sailent(self, sem_txt): 
#TODO signaler indéfinis importants
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



        self.saillantes.Act.clear()
        self.saillantesAct_deployes = []
        list_act_sem = "%s.act[0:]" % sem_txt
        result = self.client.eval_var(list_act_sem)
        list_act = result.split(',')
        list_act_sem_val = list_act_sem + ".val"
        result = self.client.eval_var(list_act_sem_val)
        list_act_val = result.split(',')
        for pos, act in enumerate(list_act):
            self.client.add_cache_var("%s.act%s"%(sem_txt, pos), act)
            self.client.add_cache_var("%s.act%s.val"%(sem_txt, pos), list_act_val[pos])
        if (list_act):
            #self.list_act = re.split(", ", list_act)
            self.list_act = list_act
            self.liste_act_valued = {}
            self.PrgBar.perc(len(self.list_act))
            for i in range(len(self.list_act)) :
                val = int(self.client.eval_var(u"%s.act%d.val"%(sem_txt, i)))
                
                self.liste_act_valued [self.list_act[i]] = [ val, 0 ] 
                self.saillantes.Act.addItem(u"%d %s" % (val, self.list_act[i]))
                self.PrgBar.percAdd (1)

        #les catégories
        #le serveur renvoie toutes les éléments de la catégorie
        #si len(cat_ent[0:]) > 2, deux algos a tester pour économiser les interactions avec le serveur :
        # si cat_ent0.val < len(cat_ent[0:]) on approxime le cumul des frequences de valeur par celui du rapport du nb d'element analysés sur le nb d'element total qu'on multiplie par cat_ent0.val, on arrête quand on atteint 0,5 ou on affiche les cat tant qu'elles ont le même score
        # si cat_ent0.val > len(cat_ent[0:]) on fait le rapport des valeurs cumulees sur la somme totale si les valeurs suivantes avaient le même score que le dernier obtenu : Val_cumul / ((len(cat_ent[0:]) - i) * cat_ent[i].val + Val_cumul) on s'arrete en atteignant 0,25 ou etc

        self.list_cat_valued = {}
        self.list_cat_txt = {} 
        self.saillantes.Cat.clear()
        self.saillantesCat_deployes = []
        #for typ in [u"cat_qua", u"cat_mar", u"cat_epr", u"cat_ent"]:
        for typ in [u"cat_ent"]: #uniquement les cat_ent
            list_cat_sem = "%s.%s[0:]" % (sem_txt, typ)
            list_cat  = self.client.eval_var(list_cat_sem)

            if (list_cat != u''):
                list_cat_items = re.split(", ", list_cat)
                for r, c in enumerate(list_cat_items):
                    self.list_cat_txt[c] = [typ, r]
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
            self.saillantes.Cat.addItem(resume)
            

        # les collections
        # on met toutes les collections parce que leur émergence est donnée par leur déploiement
#TODO ordonner, saillantes
        self.saillantes.Col.clear()
        self.saillantesCol_deployees = []
        list_col_sem = "%s.col[0:]" % sem_txt
        result = self.client.eval_var(list_col_sem)
        
        if (result != u""):
            self.list_col = re.split(", ", result)   
            self.list_col_valued = {}
            self.PrgBar.perc(len(self.list_col))
            for i in range(len(self.list_col)) :
                val = int(self.client.eval_var(u"%s.col%d.dep"%(sem_txt, i)))
                #FIXME list index out of range
                self.saillantes.Col.addItem(u"%d %s" % (val, self.list_col[i]))
                self.list_col_valued[self.list_col[i]] = val
                self.PrgBar.percAdd (1)

    def deploie_Col(self):
        item = self.saillantes.Col.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)

        self.saillantes.Col.clear()
        
        for r in self.list_col:
            self.saillantes.Col.addItem(u"%d %s" % (self.list_col_valued[r], r))

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
                            res = self.client.eval_var(ask)
                            
                            self.list_col_valued[result[sub_n]] = res
                        i = QtGui.QListWidgetItem()
                        i.setText(u"\u00B7 %s %s"%(self.list_col_valued[result[sub_n]],
                            result[sub_n]))
                        i.setBackground(QtGui.QColor(237,243,254))
                        self.saillantes.Col.addItem(i)
                
    def deploie_Cat(self):
        item = self.saillantes.Cat.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)
        self.saillantes.Cat.clear()
        for cat in self.list_cat_valued_ord:
            resume = u"%d %s" % (self.list_cat_valued[cat], cat)
            self.saillantes.Cat.addItem(resume)

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
                        self.saillantes.Cat.addItem(i)
                        
    def deploie_Actant(self):
        item = self.saillantes.Act.currentItem().text()
        item = re.sub("^\s*\d* ", "", item)
        self.saillantes.Act.clear()
        for r in self.list_act:
            self.saillantes.Act.addItem(u"%d %s" % (self.liste_act_valued[r][0], r))
            
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
                        self.saillantes.Act.addItem(i)
                    
    def recup_element_lexicon(self, lvl):
        """get semantic and name of item pointed in lexicon list"""
        if (self.sem_liste_concept in ['$ent']):
            if (lvl == 2):
                element = self.NOT1.depII.listw.currentItem().text() 
                val, element = Controller.sp_el(element)
                return  (self.semantique_lexicon_item_II, element)
            elif (lvl == 1):
                element0 = self.NOT1.dep0.listw.currentItem().text() 
                val, element0 = Controller.sp_el(element0)
                elementI = self.NOT1.depI.listw.currentItem().text() 
                val, elementI = Controller.sp_el(elementI)
                element = u"%s:%s" % (element0, elementI)
                return (self.semantique_lexicon_item_I, element)
            else :
                element = self.NOT1.dep0.listw.currentItem().text() 
                val, element = Controller.sp_el(element)
                return  (self.semantique_lexicon_item_0, element)
        else :
            element = self.NOT1.dep0.listw.currentItem().text() 
            val, element = Controller.sp_el(element)
            return (u"%s%d" % (self.semantique_lexicon_item_0,
                self.lexicon_list_semantique.index(element)), element)
        
    def recup_element_concepts(self, lvl):
        """get semantic and name of concept pointed in concept list"""
        if (lvl == 2):
            element = self.NOT2.depII.listw.currentItem().text() 
            val, element = Controller.sp_el(element)
            return  (self.semantique_concept_item_II, element)
        elif (lvl == 1):
            element0 = self.NOT2.dep0.listw.currentItem().text() 
            val, element0 = Controller.sp_el(element0)
            elementI = self.NOT2.depI.listw.currentItem().text() 
            val, elementI = Controller.sp_el(elementI)
            element = u"%s:%s" % (element0, elementI)
            return (self.semantique_concept_item_I, element)
        else :
            element = self.NOT2.dep0.listw.currentItem().text() 
            val, element = Controller.sp_el(element)
            return  (self.semantique_concept_item, element)

    def add_networks_tab(self):
        """display tab network in the SO cadran"""
        self.networks_tab_index = self.SOTs.addTab(self.tabNetworks, self.tr("Networks"))

    def show_network(self, lvl):
        """Show the network of a selected item"""
#TODO scorer
#TODO supprimer tab generale quand derniere sous-tab supprimee
        #create the networks tab if not exists
        if (not hasattr(self, "networks_tab_index")):
            self.add_networks_tab()

        if (self.lexicon_or_concepts() == "lexicon"):
            sem, element = self.recup_element_lexicon(lvl)
        elif (self.lexicon_or_concepts() == "concepts"):
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
        self.SOTs.setCurrentIndex(self.networks_tab_index)

    def explo_item_selected(self):
        self.explorer_widget.explo_lexi.clear()
        if self.explorer_widget.liste.listw.currentItem():
            motif = self.explorer_widget.liste.listw.currentItem().text()
            val, motif = Controller.sp_el(motif)
            result = self.client.eval_index(motif)
            for r in result[0][1]:
                if Controller.explo_lexic.has_key(r):
                    self.explorer_widget.explo_lexi.addItem(Controller.explo_lexic[r])
                else:
                    print "C17249 %s" % r
#TODO check concept


    def explo_show_text(self):
        """Show texts containing a pattern"""
        motif = self.explorer_widget.saisie.text()
        row =  self.explorer_widget.liste.listw.currentRow()
        element = self.explorer_widget.liste.listw.currentItem().text()
        val, element = Controller.sp_el(element)
        
        select_search = self.explorer_widget.select_fix.currentIndex()
        types = [u"$search.pre", u"$search.suf", u"$search.rac"]
        type_search = types[select_search]
        
        ask = self.client.creer_msg_search(type_search, motif,
            pelement="%d"%row, txt=True, ptxt="[0:]", val=True)
        result = self.client.eval(ask)
        liste_textes = re.split(", ", result)
        lt_valued = {}
        list_sems = map(lambda k: self.preCompute.dicTxtSem[k], liste_textes)
        for i in list_sems:
#TODO scorer/trier
            lt_valued[i] = 1
        self.show_texts(element, lt_valued)

    def show_texts_from_list(self, lvl):
        if (self.lexicon_or_concepts() == "lexicon"):
            sem, element = self.recup_element_lexicon(lvl)
        elif (self.lexicon_or_concepts() == "concepts"):
            sem, element = self.recup_element_concepts(lvl)

        result = self.client.eval_var("%s.txt[0:]" % (sem))
        if  (result == ""):
            self.activity(u"No text to display for %s" % (element))
        else:
            liste_textes = re.split(", ", result) 
            #transform txt filename to sem
            list_sems = map(lambda k: self.preCompute.dicTxtSem[k], liste_textes)
            #get element occurences in texts
            lt_valued = {}
            for i, t in enumerate(list_sems):
                ask = "%s.txt%s.val"%(sem, i)
                lt_valued[t] = int(self.client.eval_var(ask))
            #send to display
            self.show_texts(element, lt_valued)

    def lexicon_or_concepts(self):
#FIXME pas par index
        i = self.NOTs.currentIndex()
        if (i == 1):
            return "lexicon"
        elif (i == 0):
            return "concepts"
        else:
            return False

    def show_texts(self, element, lvalued):
        """Show texts containing a selected item"""
#TODO remove deselect and select the text in the new tab
        self.deselectText()
        self.activity(u"Displaying %d texts for %s" % (len(lvalued), element))
        
        #display
        texts_widget = Viewer.ListTexts(element, lvalued, 
            self.listeObjetsTextes)
#TODO sorting by date/score, filter
        for sem, tri in texts_widget.sort():
            txt =  self.listeObjetsTextes[sem]
            texts_widget.add(sem, txt.getResume())

        texts_widget.corpus.itemSelectionChanged.connect(self.onSelectText) 
        texts_widget.anticorpus.itemSelectionChanged.connect(self.onSelectText)  

        #insert tab and give focus
        self.del_tab_text_doubl(element)
        index = self.SOT1.addTab(texts_widget, texts_widget.title)
        self.SOT1.setCurrentIndex(index)
        self.SOTs.setCurrentIndex(0)
        self.SOT1.tabBar().setTabToolTip(index, texts_widget.title)

    def del_tab_text_doubl(self, element):
        """delete text tab if exists"""
        for i in range(1, self.SOT1.count()):
            tab_element = re.sub(" \(\d*\)$", "", self.SOT1.tabText(i))
            if (tab_element == element):
                self.SOT1.removeTab(i)

    def teste_wording(self):
        if (self.NOTs.currentIndex() == 0) : # si l'onglet lexicon
            item = self.NOT1.depII.listw.currentItem().text()
        if (self.NOTs.currentIndex() == 1) : # si l'onglet concepts
            item = self.NOT2.depII.listw.currentItem().text()

        score, item = re.search("^(\d*) (.*)", item).group(1, 2)
        self.activity(u"%s double click" % (item))
        if (int(score)):
            ask = "$ph.+%s"%(item)
            result = self.client.eval_var(ask)
            
            if (not hasattr(self, "tab_sentences_index")):
#FIXME make it closable, only the sentences of the text selected
                self.tab_sentences_index = self.SETs.addTab(self.tab_sentences, "Sentences")
            
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
            self.SOTs.setCurrentIndex(self.tab_sentences_index)

    def easter1(self):
        self.explorer_widget.explo_easter.setPixmap(QtGui.QPixmap("images/Prospero-II.png"))

    def explorer(self):
        self.explorer_widget.liste.listw.clear()
        motif = self.explorer_widget.saisie.text()
        if (motif != ""):
            types = [u"$search.pre", u"$search.suf", u"$search.rac"]
            type_search = types[self.explorer_widget.select_fix.currentIndex()]
            if (self.explorer_widget.sensitivity.isChecked()):
                type_search = re.sub("search", "searchcs", type_search)
            if (motif == "abracadabri"): self.easter1()
            if (motif != "" and hasattr(self, "client")):
                ask = self.client.creer_msg_search(type_search, motif, "[0:]") 
                result = self.client.eval(ask)
                if (result != u''):
                    liste_result = re.split(", ", result)
                    self.activity("searching for {%s}: %d results"%(motif,
                        len(liste_result)))
                    self.PrgBar.perc(len(liste_result))
                    for i in range(len(liste_result)):
                        ask = self.client.creer_msg_search(type_search, motif,
                                            "%d"%i, val=True) #match value
#TODO sentences
                        r = self.client.eval(ask)
                        self.PrgBar.percAdd(1)
                        self.explorer_widget.liste.listw.addItem("%s %s"% (r,
                            liste_result[i]))
                else :
                    self.activity("searching for {%s}: 0 result" % (motif) )
    
    def contexts_contents(self):
        self.CTXs.cont.clear()
        if (self.CTXs.l.currentItem()):
            champ = self.CTXs.l.currentItem().text()
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
                self.CTXs.cont.addItem(u"%d %s"%(el[1], re.sub("\\\,", ",", el[0])))

    def maj_metadatas(self):
        string_ctx =    self.client.eval_var("$ctx")
        #self.client.add_cache_var(sem_txt +".ctx."+field, val)
        current  =  self.CTXs.l.currentItem() 
        self.CTXs.cont.clear()
        if (current):
            self.CTXs.l.setCurrentItem(current)
            self.contexts_contents()
    
    def copy_to_cb(self):
        debut  =  self.NOT1.dep0.listw.currentRow()
        fin  = self.NOT1.dep0.listw.count()
        liste = []
        if (fin):
            for row in range(0, fin):
                element = re.sub("^(\d{1,}) (.*)$", "\\2\t\\1", self.NOT1.dep0.listw.item(row).text(), 1) #on inverse pour excel
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
#TODO enumerate
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
#TODO enumerate
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
