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
import subprocess
import threading
import atexit
import webbrowser
import functools

import Viewer
import Controller

class Principal(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        # create the menu 
        ##################################################
        menu = Viewer.MyMenu()
        self.setMenuBar(menu)

        get_remote_corpus = Controller.myxml()
        if get_remote_corpus.get():
            if get_remote_corpus.parse():
                for corpus in get_remote_corpus.getDataCorpus(): 
                    t = QtGui.QAction(corpus[0], self)
                    t.triggered.connect(functools.partial(self.connect_server,
                                 "prosperologie.org", corpus[1], corpus[0]))
                    menu.distant.addAction(t)


        menu.local_connect.triggered.connect(self.connect_server_localhost)
        menu.local_edit.triggered.connect(self.add_edit_corpus_tab)
        menu.codex.triggered.connect(self.codex_window)
        menu.server_vars.triggered.connect(self.display_server_vars)
        menu.contexts.triggered.connect(self.display_contexts)
        menu.pers.triggered.connect(self.display_pers)
        menu.marlowe_gen.triggered.connect(self.add_gen_mrlw_tab)
        menu.Marlowe_remote.triggered.connect(self.MarloweViewer)
        menu.manual.triggered.connect(lambda: webbrowser.open('http://mypads.framapad.org/mypads/?/mypads/group/doxa-g71fm7ki/pad/view/interface-p2-manuel-de-l-utilisateur-hsa17wo'))

        # create the status bar
        ##################################################
        self.status = self.statusBar()
        self.status.showMessage(self.tr("Ready"))

        #create the progressebar
        ##################################################
        self.PrgBar = Viewer.PrgBar(self)
        self.status.addPermanentWidget(self.PrgBar.bar)
        
        # create the toolbar
        ##################################################
        self.toolbar = self.addToolBar("")    
        #self.toolbar.setIconSize(QtCore.QSize(16, 16))
        self.toolbar.setMovable(0)

        self.toolbar_descr_corpus = QtGui.QLabel()
        self.toolbar.addWidget(self.toolbar_descr_corpus)
        
        spacer2 = QtGui.QLabel()
        spacer2.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer2)

        self.toolbar_name_corpus = QtGui.QLabel()
        self.toolbar.addWidget(self.toolbar_name_corpus)

        ##################################################
        #cadrans NO - NE - SO - SE
        #
        #   ###########
        #   #    #    #
        #   # NO # NE #
        #   #    #    #
        #   ###########
        #   #    #    #
        #   # SO # SE #
        #   #    #    #
        #   ###########
        

        ##################################################
        #cadran NO
        ##################################################


        ##### Tab for actants                #############
        ##################################################

        self.actantsTab = Viewer.actantsTab()

        ##### Tab for authors                #############
        ##################################################

        self.authorsTab = Viewer.authorsTab()
        self.authorsTab.L.currentItemChanged.connect(self.authLchanged)
        self.authorsTab.S.currentIndexChanged.connect(self.authLchanged)

        ##### Tab for concepts #############
        ##################################################
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
        for i in range(7,12):
            self.NOT2.sort_command.model().item(i).setEnabled(False)

        ##### Tab for syntax items (Lexicon) #############
        ##################################################
        self.NOT1 = Viewer.LexiconTab()
        self.NOT1.select.currentIndexChanged.connect(self.select_liste)
        self.NOT1.sort_command.currentIndexChanged.connect(self.affiche_liste_scores)
        self.NOT1.dep0.listw.currentItemChanged.connect(self.ldep0_changed) 
        #TODO add those below
        for i in range(6,11):
            self.NOT1.sort_command.model().item(i).setEnabled(False)

        #context menus activation
        self.NOT1.dep0.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(0)))
        self.NOT1.dep0.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(0)))
        self.NOT1.dep0.listw.addAction(QtGui.QAction('copy list', self,
            triggered=lambda: self.copy_lw(self.NOT1.dep0.listw)))

        self.NOT2.dep0.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(0)))
        self.NOT2.dep0.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(0)))
        self.NOT2.dep0.listw.addAction(QtGui.QAction('copy list', self,
            triggered=lambda: self.copy_lw(self.NOT2.dep0.listw)))
        self.NOT2.depI.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(1)))
        self.NOT2.depI.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(1)))
        self.NOT2.depI.listw.addAction(QtGui.QAction('copy list', self,
            triggered=lambda: self.copy_lw(self.NOT2.depI.listw)))
        self.NOT2.depII.listw.addAction(QtGui.QAction('texts', self,
            triggered=lambda: self.show_texts_from_list(2)))
        self.NOT2.depII.listw.addAction(QtGui.QAction('network', self,
            triggered=lambda: self.show_network(2)))
        self.NOT2.depII.listw.addAction(QtGui.QAction('copy list', self,
            triggered=lambda: self.copy_lw(self.NOT2.depII.listw)))

        ##### Tab for persons                #############
        ##################################################
        self.show_persons = Viewer.personsTab()

        #Networks tab
        ##################################################
        self.tabNetworks = QtGui.QTabWidget()
        self.tabNetworks.setTabsClosable(True)
        self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

        #NO QTabWidget
        ################################################
        self.NOTs = QtGui.QTabWidget()
        self.NOTs.addTab(self.actantsTab, self.tr("Actants"))
        self.NOTs.addTab(self.authorsTab, self.tr("Authors"))
        self.NOTs.addTab(self.NOT2, self.tr("Concepts"))
        self.NOTs.addTab(self.NOT1, self.tr("Lexicon"))
        self.NOTs.currentChanged.connect(self.change_NOTab)
        self.NOTs.setTabsClosable(True)
        self.NOTs.tabCloseRequested.connect(self.NOTs.removeTab)
        Viewer.hide_close_buttons(self.NOTs,0)
        Viewer.hide_close_buttons(self.NOTs,1)
        Viewer.hide_close_buttons(self.NOTs,2)
        Viewer.hide_close_buttons(self.NOTs,3)

        ##################################################
        #cadran NE
        ##################################################

        # Journal
        ##################################################
        self.journal = Viewer.Journal(self)

        #Explorer Tab
        ################################################
        #TODO ajouter navigateur (concepts)
        self.explorer_widget =  Viewer.Explorer()
        self.explorer_widget.saisie.returnPressed.connect(self.explorer)
        self.explorer_widget.liste.listw.currentItemChanged.connect(self.explo_item_selected)
        self.explorer_widget.liste.listw.addAction(QtGui.QAction(self.tr('texts'),
            self, triggered=self.explo_show_text))

        ##### Tab for formulae                #############
        ##################################################

        formulaeTab = QtGui.QWidget()

        #Access by context CTX
        ################################################
        self.CTXs = Viewer.Contexts()
        self.CTXs.l.currentItemChanged.connect(self.contexts_contents) 

        #evaluer directement les variables du serveur
        ##################################################
        self.server_vars = Viewer.ServerVars()
        self.server_vars.champ.returnPressed.connect(self.server_vars_Evalue)
        self.server_vars.button_eval.clicked.connect(self.server_vars_Evalue)
        self.server_vars.button_getsem.clicked.connect(self.server_getsem_Evalue)
        self.server_vars.button_eval_index.clicked.connect(self.server_index_Evalue)

        #NE QTabWidget
        ##################################################
        self.NETs = QtGui.QTabWidget()
        self.NETs.setTabsClosable(True)
        self.NETs.tabCloseRequested.connect(self.NETs.removeTab)
        self.journal_index = self.NETs.addTab(self.journal.journal,
            self.tr("Journal"))
        Viewer.hide_close_buttons(self.NETs,0)
        self.NETs.addTab(self.explorer_widget, self.tr("Search"))
        Viewer.hide_close_buttons(self.NETs,1)
        self.NETs.addTab(formulaeTab, self.tr("Formulae"))
        Viewer.hide_close_buttons(self.NETs,2)
        self.NETs.setTabEnabled(2, False)

        ##################################################
        #cadran SO
        ##################################################

        #l'onglet des textes
        ##################################################
        self.SOT1 = QtGui.QTabWidget()
        self.SOT1.setTabsClosable(True)
        self.SOT1.tabCloseRequested.connect(self.SOT1.removeTab)

        #SO QTabWidget
        ##################################################

        #TODO les expression englobantes

        self.SOTs = QtGui.QTabWidget()
        self.SOTs.setTabsClosable(True)
        self.SOTs.tabCloseRequested.connect(self.SOTs.removeTab)
        self.SOTs.addTab(self.SOT1, self.tr("Texts"))
        Viewer.hide_close_buttons(self.SOTs,0)

        ##################################################
        #cadran SE
        ##################################################

        # onglet proprietes du texte
        ##################################################
        self.textProperties = QtGui.QTabWidget()

        # sous onglet proprietes saillantes
        self.saillantes = Viewer.SaillantesProperties()
        self.saillantes.Act.doubleClicked.connect(self.deploie_Actant)
        self.saillantes.Cat.doubleClicked.connect(self.deploie_Cat)
        self.saillantes.Col.doubleClicked.connect(self.deploie_Col)
        self.textProperties.addTab(self.saillantes, self.tr("Salient structures"))

        # sous onglet des éléments 
        self.text_elements = Viewer.TextElements()
        self.textProperties.addTab(self.text_elements.widget, 
            self.tr("Text elements"))
        self.text_elements.element_list.doubleClicked.connect(self.deploie_text_elements)
        #TODO add those below
        temp_apports = QtGui.QWidget()
        self.textProperties.addTab(temp_apports, self.tr("Contributions"))
        self.textProperties.setTabToolTip(2, self.tr("Apports et reprises"))
        self.textProperties.setTabEnabled(2, False)
        temp_proches = QtGui.QWidget()
        self.textProperties.addTab(temp_proches, self.tr("Analogous"))
        self.textProperties.setTabToolTip(3, self.tr("Textes proches"))
        self.textProperties.setTabEnabled(3, False)

        #CTX content
        ##################################################
        self.SET2 = Viewer.textCTX()
        self.SET2.T.cellChanged.connect(self.onChangeCTX)
        self.SET2.valid.clicked.connect(self.saveCTX)
        self.SET2.valid.setEnabled(False)
        self.SET2.reset.clicked.connect(self.resetCTX)
        self.SET2.reset.setEnabled(False)
    
        # onglet contenu du texte
        ##################################################
        self.textContent = QtGui.QTextEdit() 

        #sentences tab
        ##################################################
        self.tab_sentences = QtGui.QTabWidget()
        self.tab_sentences.setTabsClosable(True)
        self.tab_sentences.tabCloseRequested.connect(self.tab_sentences.removeTab)

        #SE QTabWidget
        ##################################################
        self.SETs = QtGui.QTabWidget()
        self.SETs.addTab(self.textProperties, self.tr("Properties"))
        self.SETs.addTab(self.SET2, self.tr("Context"))
        self.SETs.addTab(self.textContent, self.tr("Text"))
        self.SETs.addTab(self.tab_sentences, self.tr("Sentences"))

        self.SETs.currentChanged.connect(self.change_SETab)
        self.textProperties.currentChanged.connect(self.change_text_prop_tab)
        self.text_elements.selector.currentIndexChanged.connect(self.show_text_elements)

        ################################################
        ###Main Layout en grid
        ################################################
        #FIXME corriger resize des grids sur petits ecrans
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

        #TODO allow cadran to resize to the whole window 
        #grid.setRowMinimumHeight(0,1000))
        #testeur = QtGui.QPushButton('+')
        #self.NOTs.setCornerWidget(testeur)
        
        #grid.setContentsMargins(2,2,2,2)

        self.setWindowTitle(self.tr('P-II interface'))
        self.setWindowIcon(QtGui.QIcon("images/Prospero-II.png"))
        self.show() 

    ################################################
    #Fin de la methode principale d'affichage
    #début des fonctions
    ################################################

#REMOVEME>
    #def pre_calcule(self):
        #self.activity(self.tr("Caching text values"))
        #self.preCompute = Controller.preCompute(self)
        #self.listeObjetsTextes = self.preCompute.listeObjetsTextes
        #self.CTXs.l.clear()
        #self.CTXs.l.addItems(self.preCompute.liste_champs_ctx)
        ## associated values
        #max_compteur = len(self.preCompute.type_var) * len(self.preCompute.type_calcul)
        #self.PrgBar.perc(max_compteur)
        #for typ in self.preCompute.type_var :
            #self.activity(self.tr("Caching values for %s") % typ)
            #for calc in self.preCompute.type_calcul:
                #self.preCompute.cacheAssocValue(typ, calc)
                #self.PrgBar.percAdd(1)
        #TODO get concepts for search engine
#REMOVEME>

    def activity(self, message):
        """Add message to the journal"""
        self.status.showMessage(message)
        time = "%s" % datetime.datetime.now()
        self.journal.history.append("%s %s" % (time[:19], message))
        with open("P-II-gui.log",'a') as logfile:
            logfile.write("%s %s\n" % (time[:19], message.encode("utf-8")))

    def destroy_texts_tabs(self):
        for i in reversed(range(self.SOT1.tabBar().count())):
            self.SOT1.tabBar().removeTab(i)

    def display_authors(self):
        #TODO sort by number of pages, get texts
        ask = u"$aut[0:]" 
        result = self.client.eval_var(ask)
        list_results = re.split(", ", result)
        self.activity(self.tr("Displaying %d authors")%len(list_results))
        self.authorsTab.L.clear()
        self.PrgBar.perc(len(list_results))

        for i, aut in enumerate(list_results):
            ask = u"$aut%d.txt[0:]" % i 
            result = self.client.eval_var(ask)
            txts = re.split(", ", result)
            n = len(txts)
            item = QtGui.QListWidgetItem()
            item.setText("%d %s" % (n, aut))
            ask = "$aut%d.nbpg" % i 
            nbpg = self.client.eval_var(ask)
            firstTxt = txts[0]
            firstTxt = self.listeObjetsTextes[self.dicTxtSem[firstTxt]]
            firstDate = firstTxt.getCTX("date")
            firstDate = firstDate[0:10]
            lastTxt = txts[-1]
            lastTxt = self.listeObjetsTextes[self.dicTxtSem[lastTxt]]
            lastDate = lastTxt.getCTX("date")
            lastDate = lastDate[0:10]
            item.setToolTip("<table><tr><th colspan=\"2\">%s</th></tr><tr><td>number of texts</td><td align=\"right\">%d</td><tr><td>number of pages</td><td align=\"right\">%s</td></tr><tr><td>first text date</td><td align=\"right\">%s</td></tr><tr><td>last text date</td><td align=\"right\">%s</td></tr></table>"%(aut, n, nbpg, firstDate, lastDate))
            self.authorsTab.L.addItem(item)
            self.PrgBar.percAdd(1)

        self.PrgBar.reset()

    def actsLchanged(self):
        if hasattr(self, "client"):
            self.actantsTab.L1.clear()
            self.actantsTab.L2.clear()
            row = self.actantsTab.L.currentRow()
            cur = self.actantsTab.L.currentItem().text()
            ask = "$act%s.res[0:]" % (row)
            result = self.client.eval_var(ask)
            network = re.split(", ", result)
            if len(network):
                for r in range(self.actantsTab.L.count()):
                    element = self.actantsTab.L.item(r).text()
                    if (element != cur):
                        val, el = Controller.sp_el(element)
                        if (el not in network):
                            #TODO incompatibilities : not actant in the same text
                            self.actantsTab.L2.addItem(element)
                        else:
                            #ask = "$act%s.res%d.val" % (row, r)
                            #result = self.client.eval_var(ask)
                            #FIXME give always the same result
                            #print "C4186", [ask, result]
                            self.actantsTab.L1.addItem(el)

    def authLchanged(self):
        #TODO score, deploiement, acces aux textes et aux enonces
        if hasattr(self, "client"):
            self.authorsTab.L2.clear()
            row = self.authorsTab.L.currentRow()
            if (row == -1): #if no author selected, take first
                self.authorsTab.L.setCurrentRow(0)
                row = 0
            which = Controller.semantiques[self.authorsTab.S.currentText()]
            ask = "$aut%s.%s[0:]" % (row, which)
            result1 = self.client.eval_var(ask)
            concepts = re.split(", ", result1)
            #FIXME pb no answer for pers & undef, different sizes for act
            if which in ['$pers', '$undef', '$act']:
                for i, el in enumerate(concepts):
                    ask = "$aut%s.%s%d.val" % (row, which, i)
                    val = self.client.eval_var(ask)
                    self.authorsTab.L2.addItem("%s %s"%(val, el))
            else:
                ask2 = "$aut%s.val_freq_%s[0:]" % (row, which[1:])
                result2 = self.client.eval_var(ask2)
                result2 = re.split(", ", result2)
                liste_valued = ["%s %s"%(int(val), concepts[row]) for row, 
                            val in enumerate(result2)]
                self.authorsTab.L2.addItems(liste_valued)

    def create_corpus_texts_tab(self):
        """create a tab for corpus texts"""
        #FIXME reset if open a new corpus
        self.destroy_texts_tabs()

        n = len(self.listeObjetsTextes)
        self.activity(self.tr("Displaying text list (%d items)") % n)
        self.CorpusTexts = Viewer.ListTexts(False,
            self.dicTxtSem.values(), self.listeObjetsTextes, self)
        self.CorpusTexts.corpus.itemSelectionChanged.connect(self.onSelectText)
        self.SOT1.addTab(self.CorpusTexts, self.tr("corpus (%d)")%n)
        Viewer.hide_close_buttons(self.SOT1,0) #corpus text tab permanent

    def onSelectText(self):
        """when a text is selected, select it in other lists and display text properties"""
        row = self.SOT1.focusWidget().currentRow()
        txt = self.SOT1.focusWidget().widget_list[row]
        self.semantique_txt_item = txt.sem
        self.activity(self.tr("Displaying %s %s %s") %txt.getResume())

        #find txt in other tabs
        for t in range(self.SOT1.count()): 
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
        if (self.NOTs.currentIndex() == 1): #Authors
            if  hasattr(self, "client"): # si connecte
                self.display_authors()
        elif (self.NOTs.currentIndex() == 2): #Concepts
            if  hasattr(self, "client"): # si connecte
                if not hasattr(self, "sem_concept"): 
                    self.select_concept(self.NOT2.select.currentText())
        elif (self.NOTs.currentIndex() == 3):#Lexicon
            if  hasattr(self, "client"): 
                if not hasattr(self, "sem_liste_concept"): 
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
        #if (self.sem_concept in ["$col"]):
            ##deployment for collections
            #self.NOT2.sort_command.setCurrentIndex(1)
        self.affiche_concepts_scores()

    def select_liste(self, typ):
        """ quand un element de Lexicon est selectionné """
        self.sem_liste_concept = Controller.semantiques[self.NOT1.select.currentText()]
        self.affiche_liste_scores()

    def change_liste(self, content):
        self.NOT1.dep0.listw.clear()
        #self.NOT1.depI.listw.clear()
        #self.NOT1.depII.listw.clear()
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
        which = self.NOT2.sort_command.currentText()
        typ = self.NOT2.select.currentText()
        if hasattr(self, "client"):
            sem = Controller.semantiques[typ]
            content = self.client.recup_liste_concept(sem)
            if (content == ['']):
                parent.activity(u"Nothing to Display for %s" % (typ))
            else:
                self.activity(self.tr("Displaying %s list (%d items) ordered by %s") % (typ, 
                    len(content), which))
                liste_valued =[]
                self.PrgBar.perc(len(content))

                sort = Controller.hash_sort[which]

                ask = "val_%s_%s[0:]" % (sort, sem[1:])
                result  = self.client.eval_var(ask)
                if (which  in ["first apparition", "last apparition"]):
                    liste_valued = [[val, content[row]] for row, 
                        val in enumerate(re.split(", ", result))]
                else:
                    liste_valued = [[int(val), content[row]] for row, 
                        val in enumerate(re.split(", ", result))]

                    #TODO the same for I et II

                liste_final = []
                if (which == "alphabetically"):
                    for i in sorted(liste_valued, key=lambda x: x[1], reverse = 0):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 
                elif (which in ["first apparition", "last apparition"]):
                    for i in sorted(liste_valued, 
                            key=lambda x: ''.join(sorted(x[0].split('/'), reverse=1)),
                             reverse = 0):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 
                else :
                    for i in sorted(liste_valued, key=lambda x: x[0], reverse=1):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 

                self.change_liste_concepts(liste_final)

    def affiche_liste_scores(self):
        which = self.NOT1.sort_command.currentText()
        typ = self.NOT1.select.currentText()
        if hasattr(self, "client"):
            sem = Controller.semantiques[typ]
            content = self.client.recup_liste_concept(self.sem_liste_concept)
            liste_final = []
            if (content == ['']):
                self.activity(u"Nothing to Display for %s" % (typ))
            else:
                self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ, 
                    len(content), which))
                liste_valued =[]
                self.PrgBar.perc(len(content))

                sort = Controller.hash_sort[which]

                #TODO correct for undef and mo
                if sem not in ['$mo' ]:
                    ask = "val_%s_%s[0:]" % (sort, sem[1:])
                    result  = re.split(', ', self.client.eval_var(ask))
                    if sem in ['$undef']:
                        print "C18389", len(result), len(content)
                        result = result[:len(content)]
                    if (which  in ["first apparition", "last apparition"]):
                        liste_valued = [[val, content[row]] for row, 
                            val in enumerate(result)]
                    else:
                        liste_valued = [[int(val), content[row]] for row, 
                            val in enumerate(result)]
                else:
                    #REMOVEME>
                    for row, concept in enumerate(content):
                        ask = "%s%d.%s" % (sem, row, sort)
                        result  = self.client.eval_var(ask)
                        if (which  in ["first apparition", 
                                                     "last apparition"]):
                            val = re.sub(u"^\s*", "", result)
                        else :
                            try:
                                val = int(result)
                            except:
                                print "C32607", result
                        if val == 1:
                            list_resume = map(lambda x: [1, x], content[row:])
                            liste_valued.extend(list_resume)
                            break
                        else: 
                            liste_valued.append([val, content[row]])
                            self.PrgBar.percAdd(1)
                    self.PrgBar.reset()
                    #<REMOVEME

                liste_final = []
                if (which == "alphabetically"):
                    for i in sorted(liste_valued, key=lambda x: x[1], reverse = 0):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 
                elif (which in ["first apparition", "last apparition"]):
                    for i in sorted(liste_valued, 
                            key=lambda x: ''.join(sorted(x[0].split('/'), reverse=1)),
                             reverse = 0):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 
                else :
                    for i in sorted(liste_valued, key=lambda x: x[0], reverse=1):
                        item_resume = u"%s %s" % (i[0], i[1])
                        liste_final.append(item_resume) 

                self.change_liste(liste_final)

    def ldep0_changed(self):
        itemT = self.NOT1.dep0.listw.currentItem()
        if (not len(self.NOT1.dep0.listw.selectedItems())):
            self.NOT1.dep0.listw.setCurrentItem(itemT)
        if (itemT):
            value, item = re.split(" ",itemT.text(),1)
            self.activity("%s selected" % (item))

            self.activity("%s selected, value %s" % (item, value))
            sem = Controller.semantiques[self.NOT1.select.currentText()]
            #FIXME $qual whereas elsewhere $qualite
            if (sem == '$qualite'):
                self.semantique_lexicon_item_0 = re.sub('$qual', '$qualite',
                    self.client.eval_get_sem(item, "$qual"))
            else :
                self.semantique_lexicon_item_0 = self.client.eval_get_sem(item, sem) 
            #print "C122743", item, sem, self.semantique_lexicon_item_0

    def cdep0_changed(self,level):
        """ suite au changement de sélection, mettre à jour les vues dépendantes """ 
        #FIXME et quand les valeurs du niveau 0 sont nulles, il n'affiche pas du tout le dico ?
        which_concepts = self.NOT2.sort_command.currentText()
        itemT = self.NOT2.dep0.listw.currentItem()

        if (not len(self.NOT2.dep0.listw.selectedItems())):
            self.NOT2.dep0.listw.setCurrentItem(itemT)

        if (itemT):
            value, item = re.split(" ",itemT.text(),1)
            self.activity(self.tr("%s selected, value %s") % (item, value))
            self.NOT2.depI.listw.clear()
            self.NOT2.depII.listw.clear()

            sem = self.sem_concept 
            self.semantique_concept_item = self.client.eval_get_sem(item, sem) 
            
            if self.semantique_concept_item == "":
                #FIXME pb avec certains éléments des catégories
                print "C990", [item, sem]

            ask = "%s.rep[0:]"% self.semantique_concept_item
            result = self.client.eval_var(ask)
            result = re.split(", ", result)
            
            if (result != [u'']):
                if (sem in ["$cat_ent", "$cat_epr", "$cat_mar", "$cat_qua"]):
                    #display directly on II list
                    liste_scoree = []
                    self.PrgBar.perc(len(result))

                    for r in range(len(result)):
                        if (which_concepts == "number of texts"):
                            #FIXME corriger, il donne la valeur de la categorie entiere
                            ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item, r)
                            print "C1976: %s" % ask
                        elif(which_concepts == "number of authors"):
                            #FIXME il ne renvoie rien
                            ask = "%s.rep%d.nbaut"% (self.semantique_concept_item, r)
                            print "C1977: %s" % ask
                        elif(which_concepts == "first apparition"):
                            #FIXME il ne renvoie rien
                            ask = "%s.rep%d.fapp"% (self.semantique_concept_item, r)
                            print "C1978: %s" % ask
                        elif(which_concepts == "last apparition"):
                            #FIXME il ne renvoie rien
                            ask = "%s.rep%d.lapp"% (self.semantique_concept_item, r)
                            print "C1979: %s" % ask
                        else :
                            ask = "%s.rep%d.val"% (self.semantique_concept_item, r)
                        val = int(self.client.eval_var(ask))

                        if val == 0:
                            liste_scoree.extend(map(lambda x: [x, 0],
                                result[r:]))
                            break

                        liste_scoree.append([result[r], val ])
                        self.PrgBar.percAdd(1)
                    if (which_concepts == "alphabetically"):
                        liste_scoree.sort()
                    self.NOT2.depII.listw.addItems(map(lambda x : "%d %s"% (x[1], x[0]), liste_scoree))   
                    self.PrgBar.reset()
                else:
                    self.cdepI_unsorted = []
                    for r in range(len(result)):
                        if (which_concepts  == "occurences" or which_concepts == "alphabetically"):
                            ask = "%s.rep%d.val"% (self.semantique_concept_item, r)
                        elif (which_concepts  == "deployment"):
                            ask = "%s.rep%d.dep"% (self.semantique_concept_item, r)
                        elif (which_concepts == "number of texts"):
                            #FIXME does not return anything
                            ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item, r)
                        elif (which_concepts == "first apparition"):
                            #FIXME does not return anything
                            ask = "%s.rep%d.fapp"% (self.semantique_concept_item, r)
                        elif (which_concepts == "last apparition"):
                            #FIXME does not return anything
                            ask = "%s.rep%d.lapp"% (self.semantique_concept_item, r)
                        elif (which_concepts == "number of authors"):
                            #FIXME does not return anything
                            ask = "%s.rep%d.nbaut"% (self.semantique_concept_item, r)
                        try:
                            val = int(self.client.eval_var(ask))
                        except:
                            print "C19584", ask, self.client.eval_var(ask)
                        
                        to_add = "%d %s"%(val, result[r])
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        if (val == 0):
                            self.cdepI_unsorted.extend(map(lambda x : "0 %s" %x, result[r:]))
                            break
                        self.cdepI_unsorted.append(to_add)
                        
                    if (which_concepts == "alphabetically"):
                        ldepI_sorted = sorted(self.cdepI_unsorted,
                            key=lambda x: re.split(" ", x)[1], reverse=0)
                    else :
                        ldepI_sorted = sorted(self.cdepI_unsorted,
                            key=lambda x: int(re.split(" ", x)[0]), reverse=1)
                    self.NOT2.depI.listw.addItems(ldepI_sorted)

                    # afficher directement II du premier item de I 
                    self.NOT2.depI.listw.setCurrentItem(self.NOT2.depI.listw.item(0))
                    #self.cdepI_changed()

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
            ask2 = "%s.rep%d.rep_present[0:]" % (self.semantique_concept_item, row)
            result2 = self.client.eval_var(ask2)
            presents = re.split(", ", result2)
            
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
                    self.NOT2.depII.listw.addItems(map(lambda x: "%d %s"% (x[1], x[0]), 
                        sorted(liste_scoree)))
                else :
                    ask2 = "%s.rep%d.rep_present[0:]" % (self.semantique_concept_item, row)
                    result2 = self.client.eval_var(ask2)
                    presents = re.split(", ", result2)
                    self.PrgBar.perc(len(result))
                    for r in range(len(result)):
                        ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item, row, r)
                        val = int(self.client.eval_var(ask))

                        if (val == 1 and result[r] in presents):
                        #quand on atteint 1, on arrête la boucle
                            self.NOT2.depII.listw.addItems(map(lambda x: "1 %s" %x,
                                presents[r:]))
                            absents = list(set(result[r:]) - set(presents[r:]))
                            self.NOT2.depII.listw.addItems(map(lambda x: "0 %s" %x, 
                                absents))
                            break
                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                        #if (val == 0):
                            #self.NOT2.depII.listw.addItems(map(lambda x: "0 %s" %x, result[r:]))
                            #break
                        self.NOT2.depII.listw.addItem("%d %s"%(val, result[r])) 
                        self.PrgBar.percAdd(1)
        self.PrgBar.reset()

    def cdepII_changed(self):
        itemT = self.NOT2.depII.listw.currentItem()
        if (itemT):
            val, item = Controller.sp_el(itemT.text())
            row = self.NOT2.depII.listw.currentRow() 
            self.activity(self.tr("%s selected") % item)
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
        self.activity(self.tr("Starting local server"))
        self.thread = threading.Thread(target = self.server_thread)
        self.thread.start()
        self.Param_Server_R_button.setText(self.tr('Stop server'))
        self.Param_Server_R_button.clicked.disconnect(self.lance_server)
        self.Param_Server_R_button.clicked.connect(self.stop_server)
        #TODO la connection locale lancera le serveur local
            
    def server_thread(self):    
        server_path = self.Param_Server_path_P2.text()
        port = self.Param_Server_val_port.text()
        PRC  = self.Param_Server_path_PRC.text()
        #TODO protéger l'adresse du prc
        commande = "%s -e -p %s -f %s" % (server_path, port, PRC)
        self.activity(self.tr("Loading %s") % PRC)
        self.local_server = subprocess.Popen(commande, shell=True)
        
    def stop_server(self):
        self.activity(self.tr("Stopping local server"))
        self.local_server.terminate()   
        self.thread.stop()
        self.Param_Server_R_button.setText(self.tr('Start server'))
        self.Param_Server_R_button.clicked.disconnect(self.stop_server)
        self.Param_Server_R_button.clicked.connect(self.lance_server)
    
    def connect_server_localhost(self):
        self.connect_server('localhost')
        #self.connect_server(h='192.168.1.99', p='60000')

    def connect_server(self, h = 'prosperologie.org', p = '60000', name=""):
        self.activity(self.tr("Connecting to server"))
        self.client=Controller.client(h, p)
        
        if (self.client.etat):
            # donne le focus a l'onglet journal
            self.NETs.setCurrentIndex(self.journal_index)

            #show actants
            self.display_actants()

            #recup CTX and TXT
            recupTXT = Controller.recupTXT_CTX(self) 
            self.listeObjetsTextes = recupTXT.listeObjetsTextes
            self.dicTxtSem = recupTXT.dicTxtSem

            #Show corpus texts list on its own tab
            self.create_corpus_texts_tab()

            #provide contexts
            self.CTXs.l.clear()
            self.CTXs.l.addItems(recupTXT.liste_champs_ctx)

            #display info in the toolbar
            #TODO display volume
            nbpg = self.client.eval_var("$nbpg")
            nbtxt = self.client.eval_var("$nbtxt")
            if name != "":
                message = "<b>%s</b> %s texts %s pages ? volume" % (name, nbtxt, nbpg)
            else:
                message = "%s texts %s pages ? volume" % (nbtxt, nbpg)
            self.toolbar_descr_corpus.setText(message)
        
    def disconnect_server(self):
        """Disconnect"""
        self.activity(self.tr("Disconnecting"))
        self.client.disconnect()
        self.Param_Server_B.setText(self.tr('Connect to server'))
        self.Param_Server_B.clicked.connect(self.connect_server)

    def add_edit_corpus_tab(self):
        self.param_corpus = Viewer.Corpus_tab(self)
        QtCore.QObject.connect(self.param_corpus.send_codex_ViewListeTextes,
                 QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)
        self.param_corpus.launchPRC_button.clicked.connect(self.launchPRC)
        self.param_corpus_tab_index = self.NETs.addTab(self.param_corpus,
            self.tr("Corpus"))
        self.NETs.setCurrentIndex(self.param_corpus_tab_index)

    def display_contexts(self):
        i = self.NETs.addTab(self.CTXs, self.tr("Contexts"))
        self.NETs.setCurrentIndex(i)

    def display_server_vars(self):
        i = self.NETs.addTab(self.server_vars, self.tr("Server vars"))
        self.NETs.setCurrentIndex(i)

    def display_pers(self):
        addTab = True
        for t in range(3, self.NOTs.count()):
            if (self.NOTs.tabText(t) == self.tr("Persons")):
                addTab = False
                
        if (addTab):
            self.persons_tab_index = self.NOTs.addTab(self.show_persons, self.tr("Persons"))
            self.NOTs.setCurrentIndex(self.persons_tab_index)

        self.show_persons.L.clear()

        ask = "$pers[0:]" 
        result = self.client.eval_var(ask)
        list_results = re.split(", ", result)
        self.activity(self.tr("Displaying %d persons")%len(list_results))

        self.PrgBar.perc(len(list_results))

        for i, p in enumerate(list_results):
            ask = u"$pers%d.freq" % i 
            r = self.client.eval_var(ask)
            self.show_persons.L.addItem("%s %s"%(p, r))

    def display_actants(self):
        ask = u"$act[0:]" 
        result = self.client.eval_var(ask)
        list_results = re.split(", ", result)
        self.activity(self.tr("Displaying %d actants")%len(list_results))
        self.NOTs.setCurrentIndex(0)
        self.actantsTab.L.clear()

        if len(list_results) > 0:
            #ask2 = u"val_freq_act[0:]" 
            #TODO order values
            ask2 = u"val_nbtxt_act[0:]" 
            result2 = self.client.eval_var(ask2)
            list_val = re.split(", ", result2)
            liste_valued = ["%d %s"%(int(val), list_results[row]) 
                for row, val in enumerate(list_val)]
            self.actantsTab.L.addItems(liste_valued)
        
            self.actantsTab.L.currentItemChanged.connect(self.actsLchanged)

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
        tabindex = self.NETs.addTab(MarloweView, self.tr("Marlowe"))
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
        self.SET2.T.setHorizontalHeaderLabels([self.tr('field'),
            self.tr('value')]) #on remet les headers apres le clear

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
                #FIXME for pers and undef too
                if sem_concept not in ['$pers', '$undef']:
                    ask = "%s.val_freq_%s[0:]" % (self.semantique_txt_item,
                        sem_concept[1:])
                    list_val = re.split(', ', self.client.eval_var(ask))
                    #FIXME should be same size
                    if len(list_val) > len(self.list_element_items):
                        print "C15323 different list size", len(list_val) , len(self.list_element_items)
                        list_val = list_val[:len(self.list_element_items)]
                    liste_valued = ["%s %s"% (int(val),
                        self.list_element_items[row]) for row, val in enumerate(list_val)]
                    self.text_elements.element_list.addItems(liste_valued)
                    self.list_elements_valued = { self.list_element_items[row]: int(val) 
                        for row, val in enumerate(list_val) }
                else:
                    self.list_elements_valued = {}
                    val = False 
                    for i, item in enumerate(self.list_element_items):
                        ask = u"%s.%s%d.val"%(self.semantique_txt_item, sem_concept, i)
                        val = int(self.client.eval_var(ask))
                        if (val == 1):
                            list_resume = map(lambda x: "1 %s"%x, self.list_element_items[i:])
                            self.text_elements.element_list.addItems(list_resume)
                            break
                        else:
                            self.list_elements_valued[self.list_element_items[i]] = val
                            self.text_elements.element_list.addItem("%d %s"%(val, item))

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
        self.list_act = result.split(',')

        if len(self.list_act) > 0:
            ask = "%s.val_freq_act[0:]"%(sem_txt)
            result = self.client.eval_var(ask)
            list_val = re.split(', ',result) 
            liste_valued = ["%d %s"%(int(val), self.list_act[row])
                for row, val in enumerate(list_val)]
            self.saillantes.Act.addItems(liste_valued)
            self.liste_act_valued = { self.list_act[i]: [int(val), 0] 
                for i, val in enumerate(list_val) }

        #les catégories

        self.saillantes.Cat.clear()
        self.saillantesCat_deployes = []
        liste_cats = []
        self.list_cat_txt = {} 

        for typ in [u"cat_qua", u"cat_mar", u"cat_epr", u"cat_ent"]:
            list_cat_sem = "%s.%s[0:]" % (sem_txt, typ)
            list_cat  = re.split(', ', self.client.eval_var(list_cat_sem))

            if (list_cat != [u'']):
                for r, c in enumerate(list_cat):
                    self.list_cat_txt[c] =  [typ, r] 
                ask = "%s.val_freq_%s[0:]"%(sem_txt, typ)
                result = self.client.eval_var(ask)
                list_val = re.split(', ',result) 
                #FIXME should have same size
                if len(list_val) > len(list_cat):
                    print "C31278 different list size"
                    list_val = list_val[:len(list_cat)]
                try:
                    liste_valued = [ [int(val), list_cat[row]] for row, val in enumerate(list_val) ]
                except:
                    print "C9338", list_cat, list_val
                liste_cats.extend(liste_valued)

        #if less tan 4 cat, show them all
        #show until reached .5 of cumulated frequencies (show exaequo)
        liste_cats.sort(reverse=True)
        if len(liste_cats) <=4 : 
            self.list_cat_aff = ["%d %s"%(val, el) for val, el in liste_cats] 
        else:
            self.list_cat_aff = []
            somme = sum(map(lambda x: x[0], liste_cats))
            cum = 0
            old_val = False 
            for val, el in liste_cats:
                cum += val 
                if (float(cum)/somme < 0.5) or (val == old_val):
                    self.list_cat_aff.append("%d %s"%(val, el))
                    old_val = val
                else:
                    break 
        self.saillantes.Cat.addItems(self.list_cat_aff)

        # les collections
        # on met toutes les collections parce que leur émergence est donnée par leur déploiement
        #TODO saillantes
        self.saillantes.Col.clear()
        self.saillantesCol_deployees = []
        list_col_sem = "%s.col[0:]" % sem_txt
        result = self.client.eval_var(list_col_sem)
        
        if (result != u""):
            self.list_col = re.split(", ", result)   
            self.list_col_valued = {}
            vals = re.split(', ', self.client.eval_var("%s.val_dep_col[0:]"%(sem_txt)))
            if len(vals) > len(self.list_col):
                print "C31277 different list size"
                vals = vals[:len(self.list_col)]
            liste_valued = ["%d %s"%(int(val), self.list_col[row]) for row, val in enumerate(vals)]
            self.list_col_valued = {self.list_col[row]: int(val) for row, val in enumerate(vals)}
            self.saillantes.Col.addItems(liste_valued)

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
        for resume in self.list_cat_aff:
            self.saillantes.Cat.addItem(resume)
            cat = re.sub("^\s*\d* ", "", resume)

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
                        ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item, 
                            sem[0], sem[1], sub_n)
                        res = self.client.eval_var(ask)
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(res, result[sub_n]))
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
                ask = "%s.act%d.rep_present[0:]"%(self.semantique_txt_item, 
                    self.list_act.index(r))
                result = self.client.eval_var(ask)
                if (result != u''):
                    result = re.split(", ", result)
                    for sub_n in range(len(result)) :
                        if (result[sub_n] not in self.liste_act_valued.keys()):
                            ask = "%s.act%d.rep_present%d.val"%(self.semantique_txt_item, 
                                self.list_act.index(r), sub_n)
                            res = self.client.eval_var(ask)
                            
                            self.liste_act_valued[result[sub_n]] = [res, 2]
                        i = QtGui.QListWidgetItem()
                        i.setText(u"  %s %s"%(self.liste_act_valued[result[sub_n]][0], 
                            result[sub_n]))
                        #i.setBackground(QtGui.QColor(245,245,245))
                        i.setBackground(QtGui.QColor(237, 243, 254)) # cyan
                        self.saillantes.Act.addItem(i)
                    
    def recup_element_lexicon(self):
        """get semantic and name of item pointed in lexicon list"""
        element = self.NOT1.dep0.listw.currentItem().text() 
        val, element = Controller.sp_el(element)
        return (self.semantique_lexicon_item_0, element)
         
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
        else:
            element = self.NOT2.dep0.listw.currentItem().text() 
            val, element = Controller.sp_el(element)
            return  (self.semantique_concept_item, element)

    def add_networks_tab(self):
        """display tab network in the NE cadran"""
        self.networks_tab_index = self.NOTs.addTab(self.tabNetworks, self.tr("Networks"))

    def show_network(self, lvl):
        """Show the network of a selected item"""
        #create the networks tab if not exists
        if (not hasattr(self, "networks_tab_index")):
            self.add_networks_tab()
        #TODO supprimer tab generale quand derniere sous-tab supprimee

        if (self.lexicon_or_concepts() == "lexicon"):
            sem, element = self.recup_element_lexicon()
        elif (self.lexicon_or_concepts() == "concepts"):
            sem, element = self.recup_element_concepts(lvl)

        for i in range(0, self.tabNetworks.count()):
            if (self.tabNetworks.tabText(i) == element):
                self.tabNetworks.removeTab(i)
        
        res_semantique = "%s.res[0:]" % (sem)

        result_network =   re.split(", ", self.client.eval_var(res_semantique))
        
        self.activity(self.tr("Displaying network for %s (%d items)")% (element,
                 len(result_network)))

        if (len(result_network)):
            valued = []
            ask2 = "%s.res[0:].val"%sem
            print ask2
            result = self.client.eval_var(ask2)
            print result
            #REMOVEME
            #self.PrgBar.perc(len(result_network))
            #for i, el in enumerate(result_network):
                ##TODO vérifier les scores
                #ask = "%s.res%d.val"%(sem, i)
                #val = self.client.eval_var(ask)
                #valued.append("%s %s"%(val, el))
                #self.PrgBar.percAdd(1)
            network_view = Viewer.NetworksViewer(valued)
            network_view.elements.setValue(len(result_network))

        index = self.tabNetworks.addTab(network_view.show_network_widget, element)
        self.tabNetworks.setTabToolTip(index, element)
        self.tabNetworks.setCurrentIndex(index)
        self.NOTs.setCurrentIndex(self.networks_tab_index)

    def explo_item_selected(self):
        self.explorer_widget.explo_lexi.clear()
        if self.explorer_widget.liste.listw.currentItem():
            motif = self.explorer_widget.liste.listw.currentItem().text()
            val, motif = Controller.sp_el(motif)
            result = self.client.eval_index(motif)
            if (len(result[0][1])):
                for r in result[0][1]:
                    if Controller.explo_lexic.has_key(r):
                        self.explorer_widget.explo_lexi.addItem(Controller.explo_lexic[r])
                    else:
                        print "C17249 %s" % r
            else :
                result = self.client.eval_get_sem(motif, '$undef')
                if result != ['']:
                    self.explorer_widget.explo_lexi.addItem('undefined')
                    
                
            #TODO check concept

    def explo_show_text(self):
        """Show texts containing a pattern"""
        motif = self.motif #recup from self.explorer
        row =  self.explorer_widget.liste.listw.currentRow()
        element = self.explorer_widget.liste.listw.currentItem().text()
        val, element = Controller.sp_el(element)
        
        select_search = self.explorer_widget.select_fix.currentIndex()
        types = [u"$search.pre", u"$search.suf", u"$search.rac"]
        type_search = types[select_search]
        
        #ask = self.client.creer_msg_search(type_search, motif, pelement="%d"%row, txt=True, ptxt="[0:]", val=True)
        ask = self.client.creer_msg_search(type_search, motif, pelement="%d"%row, txt=True )
        result = self.client.eval(ask)
        print "C17307", ask, result
        liste_textes = re.split(", ", result)
        lt_valued = {}
        list_sems = map(lambda k: self.dicTxtSem[k], liste_textes)
        for i in list_sems:
        #TODO scorer/trier
            lt_valued[i] = 1
        self.show_texts(element, lt_valued)

    def show_texts_from_list(self, lvl):
        if hasattr(self, "client"):
            if (self.lexicon_or_concepts() == "lexicon"):
                sem, element = self.recup_element_lexicon()
            elif (self.lexicon_or_concepts() == "concepts"):
                sem, element = self.recup_element_concepts(lvl)

            ask = "%s.txt[0:]" % (sem)
            result = self.client.eval_var(ask)
            if  (result == ""):
                self.activity(self.tr("No text to display for %s") % (element))
            else:
                liste_textes = re.split(", ", result) 
                self.activity(self.tr("Displaying %d texts for %s") % (len(liste_textes), element))
                #transform txt filename to sem
                list_sems = map(lambda k: self.dicTxtSem[k], liste_textes)
                #get element occurences in texts
                ask = "%s.txt[0:].val"%(sem)
                r = self.client.eval_var(ask)
                result = re.split(', ', r)
                lt_valued = { list_sems[i]: int(val) for i, val in enumerate(result)}
                self.show_texts(element, lt_valued)

    def lexicon_or_concepts(self):
        i = self.NOTs.currentIndex()
        if (i == 3):
            return "lexicon"
        elif (i == 2):
            return "concepts"
        else:
            return False

    def show_texts(self, element, lvalued):
        """Show texts containing a selected item"""
        #TODO remove deselect and select the text in the new tab
        self.deselectText()
        
        #display
        texts_widget = Viewer.ListTexts(element, lvalued, 
            self.listeObjetsTextes, self)
        #TODO sorting by date/score, filter
        for sem, tri in texts_widget.sort():
            txt =  self.listeObjetsTextes[sem]
            texts_widget.add(sem, txt.getResume())

        texts_widget.corpus.itemSelectionChanged.connect(self.onSelectText) 
        QtCore.QObject.connect(texts_widget.corpus.action_sentences, 
            QtCore.SIGNAL("triggered()"), self.teste_wording)
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
        #FIXME info must come from text list
        if (self.lexicon_or_concepts() == "lexicon"):
            sem, item = self.recup_element_lexicon()
        elif (self.lexicon_or_concepts() == "concepts"):
            sem, item = self.recup_element_concepts(lvl)

        print "C1690", sem, item
        score, item = Controller.sp_el(item)
        #score, item = re.search("^(\d*) (.*)", item).group(1, 2)
        #self.activity("%s double click" % (item))
        print "C1691", score, item

        if (int(score)):
            ask = "$ph.+%s"%(item)
            result = self.client.eval_var(ask)
            
            if (not hasattr(self, "tab_sentences_index")):
            #FIXME make it closable, only the sentences of the text selected
                self.tab_sentences_index = self.SETs.addTab(self.tab_sentences,
                    self.tr("Sentences"))
            
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
        self.motif = self.explorer_widget.saisie.text()
        if (self.motif != ""):
            types = [u"$search.pre", u"$search.suf", u"$search.rac"]
            type_search = types[self.explorer_widget.select_fix.currentIndex()]
            if (self.explorer_widget.sensitivity.isChecked()):
                type_search = re.sub("search", "searchcs", type_search)
            if (self.motif == "abracadabri"): self.easter1()
            if (self.motif != "" and hasattr(self, "client")):
                ask = self.client.creer_msg_search(type_search, self.motif, "[0:]") 
                result = self.client.eval(ask)
                print "C25712", ask, result
                if (result != ''):
                    liste_result = re.split(", ", result)
                    self.activity(self.tr("Searching for {%s}: %d results")%(self.motif,
                        len(liste_result)))
                    self.PrgBar.perc(len(liste_result))
                    for i in range(len(liste_result)):
                        ask = self.client.creer_msg_search(type_search, 
                            self.motif, "%d"%i, val=True) 
                        r = self.client.eval(ask)
                        print "C25713", ask, r 
                        self.PrgBar.percAdd(1)
                        self.explorer_widget.liste.listw.addItem("%s %s"% (r,
                            liste_result[i]))
                else :
                    self.activity(self.tr("Searching for {%s}: no result") % (self.motif)) 

    def contexts_contents(self):
        self.CTXs.cont.clear()
        if (self.CTXs.l.currentItem()):
            champ = self.CTXs.l.currentItem().text()
            result = self.client.eval_var(u"$ctx.%s[0:]" % champ)
            result = re.split("(?<!\\\), ", result)#negative lookbehind assertion
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
    
    def to_clipboard(self, l):
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText("\n".join(l))
        self.activity(u"%d elements copied to clipboard" % (len(l)))

    def copy_lw(self, listw):
        n  = listw.count()
        liste = []
        if (n):
            for row in range(n):
                element = re.sub("^(\d{1,}) (.*)$", "\\2\t\\1",
                    listw.item(row).text(), 1) #on inverse pour excel
                liste.append(element)
        self.to_clipboard(liste)

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
        self.h22Label = QtGui.QLabel(self.tr("Text file list: drag and drop"))
        h22Buttons.addWidget(self.h22Label)
        h22_spacer = QtGui.QLabel()
        h22_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                     QtGui.QSizePolicy.Minimum)
        h22Buttons.addWidget(h22_spacer)
        h22gen = QtGui.QPushButton()
        h22gen.setIcon(QtGui.QIcon("images/gear.png"))
        h22gen.setToolTip(self.tr("test file names"))
        h22Buttons.addWidget(h22gen)
        QtCore.QObject.connect(h22gen, 
            QtCore.SIGNAL("clicked()"), self.generate)

        self.h22liste = Viewer.ListViewDrop(self)
        self.h22liste.fileDropped.connect(self.FilesDropped)
        h22.addWidget(self.h22liste)
        self.h22liste.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.h22liste.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_h22listeItem = QtGui.QAction(self.tr('delete item'), self)
        self.h22liste.addAction(efface_h22listeItem)
        QtCore.QObject.connect(efface_h22listeItem, QtCore.SIGNAL("triggered()"), self.efface_h22listeItem)
        efface_h22liste = QtGui.QAction(self.tr('clear list'), self)
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

        self.h23BT = QtGui.QCheckBox(self.tr("get titles"))
        h23Buttons.addWidget(self.h23BT)
        #self.h23BT.setChecked(True)
        self.h23BT.stateChanged.connect(self.generate)
        self.h23BR = QtGui.QCheckBox(self.tr("replace"))
        h23Buttons.addWidget(self.h23BR)
        h23BS = QtGui.QPushButton(self.tr("save CTX"))
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
        h12BS = QtGui.QPushButton(self.tr("save codex"))
        h12BS.clicked.connect(self.codex_dic.save_codex)
        h12buttons.addWidget(h12BS)

        self.listRad = QtGui.QListWidget()
        h12.addWidget(self.listRad)
        self.listRad.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.listRad.doubleClicked.connect(self.mod_listRadItem)
        self.listRad.currentItemChanged.connect(self.changeRad)
        self.listRad.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_listRadItem = QtGui.QAction(self.tr('delete item'), self)
        self.listRad.addAction(efface_listRadItem)
        QtCore.QObject.connect(efface_listRadItem, QtCore.SIGNAL("triggered()"), self.efface_listRadItem)
        add_listRadItem = QtGui.QAction(self.tr('add item'), self)
        self.listRad.addAction(add_listRadItem)
        QtCore.QObject.connect(add_listRadItem, QtCore.SIGNAL("triggered()"), self.add_listRadItem)
        self.listRad.setItemDelegate(Viewer.MyDelegate(self))
        self.listRad.itemDelegate().closedSignal.connect(self.mod_listRadItem_done)

        self.initiate()

        h13 = QtGui.QVBoxLayout()
        H1.addLayout(h13)
        self.h13List = QtGui.QTableWidget()
        self.h13List.setColumnCount(2)
        self.h13List.setHorizontalHeaderLabels([self.tr('field'),
            self.tr('value')])
        self.h13List.horizontalHeader().setStretchLastSection(True)     
        self.h13List.verticalHeader().setVisible(False)
        h13.addWidget(self.h13List)

        self.h13List.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        efface_listRadValueItem = QtGui.QAction('delete line', self)
        self.h13List.addAction(efface_listRadValueItem)
        QtCore.QObject.connect(efface_listRadValueItem, QtCore.SIGNAL("triggered()"), self.efface_listRadValueItem)
        add_listRadValueItem = QtGui.QAction(self.tr('add line'), self)
        self.h13List.addAction(add_listRadValueItem)
        QtCore.QObject.connect(add_listRadValueItem, QtCore.SIGNAL("triggered()"), self.add_listRadValueItem)
        copy_h13listLine = QtGui.QAction(self.tr('copy line'), self)
        self.h13List.addAction(copy_h13listLine)
        QtCore.QObject.connect(copy_h13listLine, QtCore.SIGNAL("triggered()"), self.copy_h13listLine)
        paste_h13listLine = QtGui.QAction(self.tr('paste line'), self)
        self.h13List.addAction(paste_h13listLine)
        QtCore.QObject.connect(paste_h13listLine, QtCore.SIGNAL("triggered()"), self.paste_h13listLine)

        self.h13List.cellChanged.connect(self.onChangeh13List)

        h14 = QtGui.QVBoxLayout()
        H1.addLayout(h14)
        h14buttons = QtGui.QHBoxLayout()
        h14.addLayout(h14buttons)
        h14BM = QtGui.QPushButton(self.tr("merge"))
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
            self.h12LabelNum.setText(self.tr("%d entries")%len(self.codex_dic.dico))
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
        self.h22Label.setText(self.tr("Text file list: drag and drop"))
        self.generate()

    def efface_h22listeItem(self):
        if self.h22liste.selectedItems():
            self.h22liste.takeItem(self.h22liste.currentRow())
            #self.generate()
            self.h22Label.setText(self.tr("%s texts")% self.h22liste.count())

    def changeRad(self):
        self.h13List.clear()    
        self.h13List.setHorizontalHeaderLabels([self.tr('field'),
            self.tr('value')])
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
                self.h22Label.setText(self.tr("%s texts")% self.h22liste.count())
                print "a"
                QtGui.QApplication.processEvents()
        self.h22liste.sortItems()
        #if os.path.exists(url):
        #    if os.path.splitext(url)[1] in ['.txt', '.TXT']:
        #        item = QtGui.QListWidgetItem(url, self.h22liste)
        #        item.setStatusTip(url)
        #        self.h22Label.setText(u"%s texts"% self.h22liste.count())
        #        QtGui.QApplication.processEvents()
        #self.h22liste.sortItems()
        #self.generate()

    def appendItems(self, liste):
        self.h22liste.clear()
        self.h22liste.addItems(liste)
        self.h22Label.setText(self.tr("%s texts")% self.h22liste.count())
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
            self.h23liste.setHorizontalHeaderLabels([self.tr('path'),
                self.tr('key,  date and title')])
        else :
            self.h23liste.setHorizontalHeaderLabels([self.tr('path'),
                self.tr('key and date')])
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
            self.h23Label.setText(self.tr("%d matches, %d fails") % (m, f))
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
        item_value = QtGui.QTableWidgetItem(self.tr("\u00A0 no match"))
        item_value.setForeground(QtGui.QColor("red"))
        self.h23liste.setItem(r, 1, item_value)
        item_path.setToolTip(self.tr("no match"))
        item_value.setToolTip(self.tr("no match"))

    def merge_codex(self):
        fname, filt = QtGui.QFileDialog.getOpenFileName(self, 
            self.tr('Open file'), '.', '*.cfg;*.publi;*.xml')
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
                self.h14MergeList.addItem("%s: %s"%(k, str(v)))
            self.h14LabelNum.setText(self.tr("%d fails") % len(fails))

    def saveCTX(self):
        if hasattr(self, "CTX_to_be_saved"):
            for path, v in self.CTX_to_be_saved.iteritems():
                if  not (os.path.isfile(path) and not self.h23BR.checkState())   :
                    CTX = Controller.parseCTX()
                    CTX.path = path
                    CTX.dico = v    
                    CTX.savefile()
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    translator = QtCore.QTranslator()
    translator.load('i18n/'+ QtCore.QLocale.system().name())
    app.installTranslator(translator)
    #Translation: pyside-lupdate -verbose -noobsolete i18n/P2.pro ; lrelease i18n/P2.pro 

    window  = Principal()
    #window.show()
    sys.exit(app.exec_())
