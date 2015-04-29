#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
from PySide import QtCore 
from PySide import QtGui 

from fonctions import translate

import re
import datetime
import subprocess, threading, socket, atexit
import os
import time

import interface_prospero
import generator_mrlw
import Viewer
import Model




class client(object):

        def __init__(self,h,p):

                self.c = interface_prospero.ConnecteurPII() 
                #self.c.start()
                self.c.set(h,p)
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

        def recup_liste_concept(self,sem):
                var = "%s[0:]" % sem
                return re.split(", ",self.c.eval_variable(var))
        

        def eval_vector(self,type, type_calc):
                return self.c.eval_vect_values(type, type_calc)

        def eval_var(self,var):
                #self.eval_var_result = self.c.eval_variable(var)
                return self.c.eval_variable(var)
                
        def eval_var_ctx(self,props,ctx_range):
                return self.c.eval_ctx(props,ctx_range)

        def eval_get_sem(self,exp,sem):
                # jp : pour retrouver la sémantique d'un élément : (getsem 'nucléaire' $ent )
                #exp = exp.encode('utf-8')
                #return self.c.eval_fonc("getsem:%s:%s" % (  exp , sem) )
                return self.c.eval_fonct(u"getsem" , exp , sem )

        def add_cache_var(self,cle,val):
                self.c.add_cache_var(cle,val)

        # pour anticiper les getsem /corpus/texte $txt
        def add_cache_fonct(self,cle,val):
                self.c.add_cache_fonc(cle,val)
        
        def creer_msg_search(self,fonc ,element, pelement='',txt=False,ptxt='',ph=False,pph='',val=False):
                return self.c.creer_msg_search(fonc ,element, pelement,txt,ptxt,ph,pph,val)

        def eval (self, L):
                return self.c.eval(L)

        def eval_set_ctx(self, sem_txt, field, val):
                return self.c.eval_set_ctx(sem_txt, field, val)



class Principal(QtGui.QMainWindow):
        def __init__(self,parent=None):
                #super(Principal, self).__init__()
                QtGui.QMainWindow.__init__(self, parent)
                self.initUI()
                
                
        def pre_calcule(self):
                '''
                        généralisation de l'accès aux props des ctx
                        
                        avec eval_var("$ctx") on récupère la liste des noms des champs ctx
                        qq ajustements sont à faire pour mettre en cache 
                                $txtX.titre_txt   à partir de title
                                $txtX.date_txt   à partir de date
                                
                '''
                

                self.activity("pre-computing : texts")
                self.listeTextes = self.recup_texts()
                self.listeObjetsTextes = {}
                self.dicTxtSem = {}
                for t in range(len(self.listeTextes)):
                        sem_texte = "$txt%d"%(t)
                        self.listeObjetsTextes[sem_texte] =  Model.Texte(sem_texte,self.listeTextes[t])
                        self.dicTxtSem[self.listeTextes[t]] = sem_texte

                # récupération des champs ctx
                string_ctx =    self.client.eval_var("$ctx")
                
                # les virgules contenues dans les titres ont été remplacées par \,
                # la manip suivante permet de remplacer dans un premier temps les \,par un TAG
                # ensuite de créer la liste, puis de remettre les virgules à la place des \,
                TAG="AZETYT"    # on peut mettre presque n'importe quoi ...
                string_ctx = string_ctx.replace ('\,', TAG )
                liste_ctx = string_ctx.split(',')
                liste_champs_ctx = []
                for champ_ctx in liste_ctx:
                        champ_ctx = champ_ctx.strip()
                        if champ_ctx.find (TAG) != -1 :
                                champ_ctx = champ_ctx.replace(TAG,',')
                        liste_champs_ctx.append ( champ_ctx)            
                
                liste_champs_ajuste = []

                for champ in liste_champs_ctx :
                         #title[0\]  date[0:]  etc on ne met pas le $ctx  ici...

                        string_ctx =self.client.eval_var("$ctx.%s%s"%(champ,"[0:]")) 
                        string_ctx = string_ctx.replace ('\,', TAG )
                        #liste_data_ctx = string_ctx.split(',') 
                        liste_data_ctx = string_ctx.split(', ') 
                        liste_data_ok_ctx =[]   

                        for data in liste_data_ctx :
                                if data.find(TAG) != -1:
                                        data = data.replace(TAG,',')
                                liste_data_ok_ctx.append ( data)

                        if len (liste_data_ok_ctx) != len (self.listeTextes):
                                print "problemo qq part les listes doivent avoir le même nbre d'éléments"
                                
                        # pb non résolu
                        # entre l'attribut de $txt -> titre_txt date_txt auteur_txt
                        # proatique pour accéder à ces propriétés
                        # et d'autres part les noms des champs ...
                        
                        '''     
                        if champ == "title" :
                                champ = u"titre_txt"
                        if champ == "date" :
                                champ = u"date_txt"
                        if champ == "author" :
                                champ = u"auteur_txt"
                        '''
                                
                                #ne pas traduire pour les calculs, uniquement pour la visualisation
                        #champ = translate(champ)

                        liste_champs_ajuste.append (champ)

                        for indice in range (len(self.listeTextes)):
                                sem_texte = "$txt%d"%(indice)
                                txt = self.listeObjetsTextes[sem_texte]
                                data = liste_data_ok_ctx[indice]
                                # sématique avec les noms des champs anglais
                                if data != "":
                                        self.client.add_cache_var( txt.sem + ".ctx.%s"%champ, data)
                                        txt.setCTX(champ,data)


                self.NOT5_list.clear()
                self.NOT5_list.addItems(liste_champs_ajuste)

		self.PrgBar.setv(  50 )
                
                # précalcule de valeurs associées 
                for type_var in [ "$ent" , "$ef" , "$col", "$qualite"] :
                        self.activity("pre-computing : %s " % (type_var))

#freq et nbaut ne marche pas ?
                        for type_calcul in ["freq","dep", "nbaut", "nbtxt","lapp","fapp"]:
                                L = self.client.eval_vector(type_var, type_calcul)
                                L = L.split(',')         
                                if (type_calcul == "freq"):
                                        t_calc = "val"
                                else:
                                        t_calc = type_calcul
                                indice = 0
                                for val in L :
                                        self.client.add_cache_var ("%s%s.%s"%(type_var,str(indice),t_calc),val)
                                        indice+=1
                                
                                self.PrgBar.add(  3 )
			self.PrgBar.add(  -2 )

                self.PrgBar.reset()

        
        def initUI(self):


                # create the menu bar
                Menubar = self.menuBar()

                Menu_Corpus = Menubar.addMenu('&Corpus')
                #Menu_Corpus.setShortcut('Ctrl+C')
		#Menu_project = QtGui.QAction('&corpus',self)
		#Menu_project.triggered.connect(self.edit_corpus)
		#Menu_Corpus.addAction(Menu_project)
                Menu_codex = QtGui.QAction("&codex",self)
                Menu_codex.setStatusTip("Use and edit source repositories for ctx generation")
                Menu_codex.triggered.connect(self.codex_window)
                Menu_Corpus.addAction(Menu_codex)
                Menu_distant = QtGui.QAction(QtGui.QIcon('images/distant.png'), '&prosperologie.org', self)        
                Menu_distant.setStatusTip('Connect to prosperologie.org server')
                Menu_distant.triggered.connect(self.connect_server)
                Menu_Corpus.addAction(Menu_distant)
                Menu_local = QtGui.QAction(QtGui.QIcon('images/home.png'), '&local', self)        
                Menu_local.setStatusTip('Launch a local server')
                Menu_local.triggered.connect(self.connect_server_localhost)
                Menu_Corpus.addAction(Menu_local)
                
                Menu_Texts = Menubar.addMenu('&Texts')
                Menu_AddTex = QtGui.QAction('&Add a new text', self)        
                Menu_Texts.addAction(Menu_AddTex)
                Menu_AddTex.setEnabled(False)
                Menu_ModTex = QtGui.QAction('&Action on selected texts', self)        
                Menu_Texts.addAction(Menu_ModTex)
                Menu_ModTex.setEnabled(False)
        



# parametrage du Gui : langue etc
                #ParamMenu = Menubar.addMenu(self.tr('&Parameters'))
                #LangInterface = ParamMenu.addMenu(self.tr("&Interface language"))
                #LangInterface.addAction("en_GB",self.lang_en_GB)
                #LangInterface.addAction("fr_FR",self.lang_fr_FR)
#               ConstelMenu = menubar.addMenu('&Constellation')
#               HelpMenu = menubar.addMenu('&Help')

                # create the status bar
                self.status = self.statusBar()
                self.status.showMessage(u"Ready")

                #create the progressebar
                self.PrgBar = Viewer.PrgBar(self)
                self.status.addPermanentWidget(self.PrgBar.bar)

                

        
		"""
                # create the toolbar
                toolbar = self.addToolBar("toolbar")    
                toolbar.setIconSize(QtCore.QSize(16, 16))
                toolbar.setMovable( 0 )

                

                #Saction = QtGui.QAction(QtGui.QIcon('images/Prospero-II.png'), 'Server', self)
                #toolbar.addAction(Saction)

                list1 = QtGui.QComboBox()
                #list1.addItem(u"Reference corpus")
#               list1.addItem(u"auteur : AFP")
                #toolbar.addWidget(list1)

                spacer1 = QtGui.QLabel()
                spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
                toolbar.addWidget(spacer1)
                
                etat1 = QtGui.QLabel()
#               etat1.setText("234 textes 5,44 pages volume 234")
                toolbar.addWidget(etat1)
                
                spacer2 = QtGui.QLabel()
                spacer2.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
                toolbar.addWidget(spacer2)

                etat2 = QtGui.QLabel()
#               etat2.setText("/Users/gspr/corpus/Alarm and Controversies/AaC.prc")
                toolbar.addWidget(etat2)
		"""

##################################################
                #quart SE
##################################################


        # onglet proprietes du texte
                self.textProperties = QtGui.QTabWidget()

        # sous onglet proprietes saillantes
                saillantes = QtGui.QWidget()
                self.textProperties.addTab(saillantes,self.tr("Sailent structures"))
        
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


#               SET1.addTab(SET12,u"Apports et reprises")
#               SET1.addTab(SET13,u"Eléments du texte")
#               SET1.addTab(SET14,u"Textes proches")
#               SET1.addTab(SET15,u"Textes identiques")

        # onglet contenu du CTX
                self.textCTX = QtGui.QTableWidget()
                self.textCTX.verticalHeader().setVisible(False)
                self.textCTX.setColumnCount(2)
                self.textCTX.setHorizontalHeaderLabels([u'field',u'value'])
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
                Hbox_textCTX_commands_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
#TOTO add, delete
                self.Hbox_textCTX_commands.addWidget(Hbox_textCTX_commands_spacer) 
                textCTX_commandsButton = QtGui.QPushButton(u"\u25cb")
                self.Hbox_textCTX_commands.addWidget(textCTX_commandsButton)
                textCTX_commandsButton.setEnabled(False)
                Vbox_textCTX.addLayout(self.Hbox_textCTX_commands)


        # onglet contenu du texte
                self.textContent = QtGui.QTextEdit() 

                self.SubWdwSETabs = QtGui.QTabWidget()

                #SubWdwSE = QtGui.QWidget()

                SETabV = QtGui.QVBoxLayout()
                SETabV.setContentsMargins(0,0,0,0) 
                SETabV.setSpacing(0) 
                SETabVH = QtGui.QHBoxLayout()
                SETabV.addLayout(SETabVH)

                #self.SETabTextDescr = QtGui.QLabel()
                #SETabVH.addWidget(self.SETabTextDescr)
                #self.SETabTextDescr.setStyleSheet("color: white")

                SETabVH.addWidget(self.SubWdwSETabs)

                #SubWdwSE.setLayout(SETabV)
                #SETabV.addWidget(self.SubWdwSETabs)

                self.SubWdwSETabs.addTab(self.textProperties,"Properties")
                self.SubWdwSETabs.addTab(Vbox_textCTX_W,"Metadata")
                self.SubWdwSETabs.addTab(self.textContent,"Text")

                self.SubWdwSETabs.currentChanged.connect(self.change_SETab)


##################################################
                #quart SO
##################################################
                self.SubWdwSO = QtGui.QTabWidget()

                #l'onglet des textes
                self.SOT1 = QtGui.QTabWidget()
                self.SOT1.setTabsClosable(True)
                self.SOT1.tabCloseRequested.connect(self.SOT1.removeTab)
                #la liste des textes du corpus
                self.CorpusTexts = QtGui.QListWidget()
                self.CorpusTexts.setAlternatingRowColors(True)
                self.SOT1.addTab(self.CorpusTexts,"corpus")
                # on fait disparaître le bouton close de la tab CorpusTexts, a gauche pour les mac
                if self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide):
                        self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide).resize(0,0)
                        self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide).hide()
                elif self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide):
                        self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).resize(0,0)
                        self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).hide()

                self.CorpusTexts.itemSelectionChanged.connect(self.onSelectText)
                
                
                #l'onglet des réseaux
                self.tabNetworks = QtGui.QTabWidget()
                self.tabNetworks.setTabsClosable(True)
                self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

#TODO les expression englobantes

                #mise en place des onglets

                self.SubWdwSO.addTab(self.SOT1,self.tr("Texts"))
                self.SubWdwSO.addTab(self.tabNetworks,self.tr("Networks"))


##################################################
                #quart NE
##################################################

##################################################
#Corpus
#

		self.param_corpus = Viewer.Corpus_tab(self)
                QtCore.QObject.connect(self.param_corpus.send_codex_ViewListeTextes, QtCore.SIGNAL("triggered()"), self.send_codex_ViewListeTextes)
                self.param_corpus.launchPRC_button.clicked.connect(self.launchPRC)

##################################################
#TODO logs
#parametrer le serveur
                Param_Server = QtGui.QWidget()
                Param_Server_V = QtGui.QVBoxLayout()
                Param_Server.setLayout(Param_Server_V)
#lance le serveur local avec le PRC ciblé
                Param_Server_R = QtGui.QFormLayout()
                Param_Server_R.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
                Param_Server_V.addLayout(Param_Server_R)

                self.Param_Server_path_P2 = QtGui.QLineEdit()
                #Param_Server_R.addRow("Local server path",self.Param_Server_path_P2)
                Param_Server_R.addRow(self.Param_Server_path_P2)
                #self.Param_Server_path_P2.setText("/Users/gspr/Documents/Prospero-II-serveur/prospero-II.app/Contents/MacOS/prospero-II")
                #self.Param_Server_path_P2.setText("/Users/gspr/Documents/Prospero-II-serveur/prospero-cocoa.app/Contents/MacOS/prospero-cocoa")

                Param_Server_path_P2_button = QtGui.QPushButton("select local server path")
                Param_Server_R.addWidget(Param_Server_path_P2_button)
                Param_Server_path_P2_button.clicked.connect(self.select_P2_path)

                self.Param_Server_path_PRC = QtGui.QLineEdit()
                #Param_Server_R.addRow("Corpus path",self.Param_Server_path_PRC)
                Param_Server_R.addRow(self.Param_Server_path_PRC)
                #self.Param_Server_path_PRC.setText("/Users/gspr/corpus/telephonie/0-projets/TELasso.prc")

                Param_Server_path_PRC_button = QtGui.QPushButton("select corpus path")
                Param_Server_R.addWidget(Param_Server_path_PRC_button)
                Param_Server_path_PRC_button.clicked.connect(self.select_PRC_path)
                self.Param_Server_R_button = QtGui.QPushButton('Start server')
                self.Param_Server_R_button.clicked.connect(self.lance_server)
                Param_Server_R.addWidget(self.Param_Server_R_button)


                #Param_Server_I = QtGui.QLabel()
                #Param_Server_I.setPixmap(QtGui.QPixmap('images/Prospero-II.png'))
                #Param_Server_V.addWidget(Param_Server_I)

#configurer les parametres de connexion au serveur distant
                self.Param_Server_val_host = QtGui.QLineEdit()
                Param_Server_R.addRow("&host",self.Param_Server_val_host)

                self.Param_Server_val_host.setText('prosperologie.org')#prosperologie.org
                #self.Param_Server_val_host.setText('localhost')

                self.Param_Server_val_port = QtGui.QLineEdit()
                Param_Server_R.addRow("&port",self.Param_Server_val_port)
                self.Param_Server_val_port.setText('4000')
                self.Param_Server_B = QtGui.QPushButton('Connect to server')
                self.Param_Server_B.setStyleSheet(" background-color : green; color : white; ") # bouton vert pour attirer le regard
                self.Param_Server_B.clicked.connect(self.connect_server)
                Param_Server_R.addWidget(self.Param_Server_B)

##################################################
#onglet de gestion du PRC a ajouter
                NET1 = QtGui.QTextEdit()



##################################################
#l'historique des actions
                self.History =  QtGui.QTextEdit()

##################################################
                T4 =  QtGui.QLabel()
#               viewImage = QtGui.QPixmap("viewer.png")
#               T4.setPixmap(viewImage)



#evaluer directement les variables du serveur
                server_vars = QtGui.QWidget()
                server_vars_Vbox =  QtGui.QVBoxLayout() 
                server_vars.setLayout(server_vars_Vbox)
                server_vars_Vbox.setContentsMargins(0,0,0,0) 
                server_vars_Vbox.setSpacing(0) 

                server_vars_Hbox = QtGui.QHBoxLayout()
                server_vars_champL = QtGui.QFormLayout()
                self.server_vars_champ = QtGui.QLineEdit()
                self.server_vars_champ.returnPressed.connect(self.server_vars_Evalue)
                server_vars_champL.addRow("&var",self.server_vars_champ)
                server_vars_Hbox.addLayout(server_vars_champL)
                server_vars_button_eval = QtGui.QPushButton('Eval')
                server_vars_Hbox.addWidget(server_vars_button_eval)
                server_vars_button_eval.clicked.connect(self.server_vars_Evalue)
                server_vars_button_getsem = QtGui.QPushButton('Get sem')
                server_vars_Hbox.addWidget(server_vars_button_getsem)
                server_vars_button_getsem.clicked.connect(self.server_getsem_Evalue)
                server_vars_button_clear = QtGui.QPushButton('Clear')
                server_vars_Hbox.addWidget(server_vars_button_clear)
                server_vars_button_clear.clicked.connect(self.server_vars_Clear)
                server_vars_Vbox.addLayout(server_vars_Hbox)

                self.server_vars_result = QtGui.QTextEdit(readOnly = True) 
                server_vars_Vbox.addWidget(self.server_vars_result)



##################################################
#le "generateur" Marlowe
                gen_mrlw = QtGui.QWidget()
                gen_mrlw_Hbox =  QtGui.QHBoxLayout() 
                gen_mrlw.setLayout(gen_mrlw_Hbox)
                gen_mrlw_Hbox.setContentsMargins(0,0,0,0) 
                gen_mrlw_Hbox.setSpacing(0) 

                gen_mrlw_Vbox_left = QtGui.QVBoxLayout()
                gen_mrlw_Hbox.addLayout(gen_mrlw_Vbox_left)
                self.gen_mrlw_phrase = QtGui.QTextEdit() 
                self.gen_mrlw_phrase.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
                self.gen_mrlw_phrase.setFixedHeight(70) 
                gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_phrase)
                gen_mrlw_Button_varifie = QtGui.QPushButton(self.tr("Identify"))
                width = gen_mrlw_Button_varifie.fontMetrics().boundingRect(gen_mrlw_Button_varifie.text()).width() + 30
                gen_mrlw_Button_varifie.setMaximumWidth(width)
                gen_mrlw_Button_varifie.clicked.connect(self.genere_identify)
                gen_mrlw_Vbox_left.addWidget(gen_mrlw_Button_varifie)
                gen_mrlw_Button_varifie_spacer = QtGui.QLabel()
                
                self.gen_mrlw_vars = QtGui.QTextEdit()
                self.gen_mrlw_vars.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
                self.gen_mrlw_vars.setFixedHeight(70)
                gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_vars)
                gen_mrlw_genere_Hbox =   QtGui.QHBoxLayout() 
                gen_mrlw_Vbox_left.addLayout(gen_mrlw_genere_Hbox)
                gen_mrlw_Button_genere = QtGui.QPushButton(self.tr("Generate"))
                width = gen_mrlw_Button_genere.fontMetrics().boundingRect(gen_mrlw_Button_genere.text()).width() + 30
                gen_mrlw_Button_genere.setMaximumWidth(width)
                gen_mrlw_genere_Hbox.addWidget(gen_mrlw_Button_genere)
                gen_mrlw_Button_genere.clicked.connect(self.genere_generate)
                gen_mrlw_genere_spacer = QtGui.QLabel()
                gen_mrlw_genere_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
                gen_mrlw_genere_Hbox.addWidget(gen_mrlw_genere_spacer)

                self.gen_genere_spinbox = QtGui.QSpinBox()
                gen_mrlw_genere_Hbox.addWidget(self.gen_genere_spinbox)
                self.gen_genere_spinbox.setValue(1)
                self.gen_mrlw_result = QtGui.QTextEdit() 
                self.gen_mrlw_result.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
                self.gen_mrlw_result.setFixedHeight(100)
                gen_mrlw_Vbox_left.addWidget(self.gen_mrlw_result)

                gen_mrlw_Vbox_right = QtGui.QVBoxLayout()
                gen_mrlw_Hbox.addLayout(gen_mrlw_Vbox_right)
                self.gen_mrlw_test = QtGui.QLineEdit()
                self.gen_mrlw_test.returnPressed.connect(self.genere_test)
                self.gen_mrlw_test.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
                self.gen_mrlw_test.setFixedWidth(256)
                gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_test)
                self.gen_mrlw_test_result = QtGui.QListWidget()
                self.gen_mrlw_test_result.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
                gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_test_result)
                self.gen_mrlw_test_result.doubleClicked.connect(self.genere_test_result_dc)
                self.gen_mrlw_files = QtGui.QListWidget()
                self.gen_mrlw_files.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
                self.gen_mrlw_files.setFixedHeight(50)
                gen_mrlw_Vbox_right.addWidget(self.gen_mrlw_files)

                self.genere_mrlw = generator_mrlw.mrlw_variables()
                for F in self.genere_mrlw.files:
                        self.gen_mrlw_files.addItem(F)

##################################################
#mise en place des onglets
                self.SubWdwNE = QtGui.QTabWidget()
#               self.SubWdwNE.setTabsClosable(True)
#               self.SubWdwNE.tabCloseRequested.connect(self.SubWdwNE.removeTab)

#               SubWdwNE.addTab(T4,"Viewer")
#               SubWdwNE.addTab(NET1,"Marlowe")
                self.SubWdwNE.addTab(self.param_corpus,"Corpus")
                self.History_index = self.SubWdwNE.addTab(self.History,"History")
                self.SubWdwNE.addTab(server_vars,"Vars")
                #self.SubWdwNE.addTab(Param_Server,"Server")
                self.SubWdwNE.addTab(gen_mrlw,self.tr("Variant generation"))

                self.SubWdwNE.setCurrentIndex(0)
                #self.SubWdwNE.setCurrentIndex(2)





##################################################
        #quart NO
##################################################

                self.SubWdwNO =  QtGui.QTabWidget()
                

##### L'onglet des listes des briques syntaxiques (Lexicon)


                NOT1 = QtGui.QWidget()

        #une box verticale
                NOT1V = QtGui.QVBoxLayout()
                NOT1.setLayout(NOT1V)
                # on prend toute la place
                NOT1V.setContentsMargins(0,0,0,0) 
                NOT1V.setSpacing(0) 


        #une ligne horizontale qui contient les commandes au dessus-de la liste 
                NOT1VHC = QtGui.QHBoxLayout()
                NOT1V.addLayout(NOT1VHC)

        #une liste deroulante pour choisir le contenu de la liste
                self.NOT1select = QtGui.QComboBox()
                self.NOT1select.addItem(u"entities") 
                self.NOT1select.addItem(u"qualities") 
                #self.NOT1select.addItem(u"markers") 
                #self.NOT1select.addItem(u"events") 
                #self.NOT1select.addItem(u"numbers") 
                #self.NOT1select.addItem(u"function words") 
                #self.NOT1select.addItem(u"undefineds") 
                #self.NOT1select.addItem(u"persons") 
                NOT1VHC.addWidget(self.NOT1select)
                self.connect(self.NOT1select,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.select_liste)
                self.NOT1select.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 


        # un spacer pour mettre les commandes sur la droite
                spacer3 = QtGui.QLabel()
                spacer3.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
                NOT1VHC.addWidget(spacer3)

        #le champ de recherche
                self.list_research = QtGui.QLineEdit()
                self.list_research.returnPressed.connect(self.list_lexicon_search)
                NOT1VHC.addWidget(self.list_research)
                

        # les commandes
                self.NOT1Commands1 = QtGui.QPushButton()
                self.NOT1Commands1.setText(u"\u2195")
                self.NOT1Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
                self.NOT1Commands1Menu = QtGui.QMenu(self)
                #NOT1Commands1Menu.addAction('&search')
                #submenu_sort = QtGui.QMenu('&sort')
                #NOT1Commands1Menu.addMenu(submenu_sort)
                self.NOT1Commands1Menu.addAction('occurences',self.affiche_liste_scores_oc)
                self.NOT1C1_dep = self.NOT1Commands1Menu.addAction('deployement',self.affiche_liste_scores_dep)
                self.NOT1Commands1Menu.addAction('alphabetically',self.affiche_liste_scores_alpha)
                self.NOT1Commands1Menu.addAction('number of texts',self.affiche_liste_scores_texts)
                self.NOT1Commands1Menu.addAction('first apparition',self.affiche_liste_scores_fapp)
                self.NOT1Commands1Menu.addAction('last apparition',self.affiche_liste_scores_lapp)
#TODO ajouter pondere, nb textes, nb auteurs, nb jours presents, relatif nb jours, nb representants, nb elements reseau
                #NOT1Commands1Menu.addAction('&sort')
                #NOT1Commands1Menu.addAction('&filter')
                self.NOT1Commands1.setMenu(self.NOT1Commands1Menu)
                NOT1VHC.addWidget(self.NOT1Commands1)


                self.NOT1Commands2 = QtGui.QPushButton()
                self.NOT1Commands2.setIcon(QtGui.QIcon("images/gear.png"))
                self.NOT1Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
                NOT1Commands2Menu = QtGui.QMenu(self)
                #NOT1Commands2Menu.addAction('network' , self.show_network)
                #NOT1Commands2Menu.addAction('texts' , self.show_texts)
                self.NOT1Commands2.setMenu(NOT1Commands2Menu)
                #NOT1VHC.addWidget(self.NOT1Commands2)

#TODO ajouter un déselect
        #une box horizontale pour liste, score et deploiement
                NOT1VH = QtGui.QHBoxLayout()
                NOT1V.addLayout(NOT1VH) 
        #la liste
                self.NOT12 = QtGui.QListWidget()
                self.NOT12.setAlternatingRowColors(True)
                self.NOT12.currentItemChanged.connect(self.liste_item_changed) #changement d'un item
                NOT1VH.addWidget(self.NOT12)

                #menu contextuel
                self.NOT12.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                copy_to_clipboard = QtGui.QAction('copy list to clipboard',self)
                show_network = QtGui.QAction('network' , self)
                show_texts =QtGui.QAction('texts' , self)
                QtCore.QObject.connect(show_texts, QtCore.SIGNAL("triggered()"), self.show_texts)
                QtCore.QObject.connect(show_network, QtCore.SIGNAL("triggered()"), self.show_network)
                QtCore.QObject.connect(copy_to_clipboard, QtCore.SIGNAL("triggered()"), self.copy_to_cb)
                self.NOT12.addAction(show_texts)
                self.NOT12.addAction(show_network)
                self.NOT12.addAction(copy_to_clipboard)

        #le deploiement
                self.NOT12_D = QtGui.QListWidget()
                NOT1VH.addWidget(self.NOT12_D)
                self.NOT12_D.currentItemChanged.connect(self.liste_D_item_changed) #changement d'un item
                self.NOT12_D.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.NOT12_D.addAction(show_texts)
                self.NOT12_D.addAction(show_network)
                self.NOT12_D.addAction(copy_to_clipboard)
        #le deploiement II
                self.NOT12_E = QtGui.QListWidget()
                NOT1VH.addWidget(self.NOT12_E)
                self.NOT12_E.currentItemChanged.connect(self.liste_E_item_changed) #changement d'un item
                self.NOT12_E.doubleClicked.connect(self.teste_wording)
                self.NOT12_E.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.NOT12_E.addAction(show_texts)
                self.NOT12_E.addAction(show_network)
                self.NOT12_E.addAction(copy_to_clipboard)


##### L'onglet des listes de concepts
                NOT2 = QtGui.QWidget()
                NOT2V = QtGui.QVBoxLayout()
                NOT2.setLayout(NOT2V)
                NOT2V.setContentsMargins(0,0,0,0) 
                NOT2V.setSpacing(0) 
                NOT2VHC = QtGui.QHBoxLayout()
                NOT2V.addLayout(NOT2VHC)
                self.NOT2select = QtGui.QComboBox()
                self.NOT2select.addItem(u"collections")
                self.NOT2select.addItem(u"fictions")
                self.NOT2select.addItem(u"entitie's categories")
                NOT2VHC.addWidget(self.NOT2select)
                self.connect(self.NOT2select,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.select_concept)
                self.NOT2select.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
                NOT2_spacer = QtGui.QLabel()
                NOT2_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
                NOT2VHC.addWidget(NOT2_spacer)
                self.concept_research = QtGui.QLineEdit()
                self.concept_research.returnPressed.connect(self.list_concept_search)
                NOT2VHC.addWidget(self.concept_research)
                self.NOT2Commands1 = QtGui.QPushButton()
                self.NOT2Commands1.setText(u"\u2195")
                self.NOT2Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
                self.NOT2Commands1Menu = QtGui.QMenu(self)
                self.NOT2Commands1Menu.addAction('occurences',self.affiche_concepts_scores_oc)
                self.NOT2Commands1Menu.addAction('deployement',self.affiche_concepts_scores_dep) 
                self.NOT2Commands1Menu.addAction('alphabetically',self.affiche_concepts_scores_alpha)
                self.NOT2Commands1Menu.addAction('number of texts',self.affiche_concepts_scores_texts)
                self.NOT2Commands1Menu.addAction('first apparition',self.affiche_concepts_scores_fapp)
                self.NOT2Commands1Menu.addAction('last apparition',self.affiche_concepts_scores_lapp)
                self.NOT2Commands1.setMenu(self.NOT2Commands1Menu)
                NOT2VHC.addWidget(self.NOT2Commands1)
                self.NOT2Commands2 = QtGui.QPushButton()
                self.NOT2Commands2.setIcon(QtGui.QIcon("images/gear.png"))
                self.NOT2Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
                NOT2Commands2Menu = QtGui.QMenu(self)
                NOT2Commands2Menu.addAction('network' , self.show_network)
                NOT2Commands2Menu.addAction('texts' , self.show_texts)
                self.NOT2Commands2.setMenu(NOT2Commands2Menu)
                NOT2VHC.addWidget(self.NOT2Commands2)
        #une box horizontale pour liste, score et deploiement
                NOT2VH = QtGui.QHBoxLayout()
                NOT2V.addLayout(NOT2VH) 
        #la liste
                self.NOT22 = QtGui.QListWidget()
                self.NOT22.setAlternatingRowColors(True)
                self.NOT22.currentItemChanged.connect(self.liste_concept_changed) #changement d'un item
                NOT2VH.addWidget(self.NOT22)
        #le deploiement
                self.NOT22_D = QtGui.QListWidget()
                NOT2VH.addWidget(self.NOT22_D)
                self.NOT22_D.currentItemChanged.connect(self.liste_D_concept_changed) #changement d'un item
        #le deploiement II
                self.NOT22_E = QtGui.QListWidget()
                NOT2VH.addWidget(self.NOT22_E)
                self.NOT22_E.currentItemChanged.connect(self.liste_E_concept_changed) #changement d'un item
                self.NOT22_E.doubleClicked.connect(self.teste_wording)



################################################
#Explorer
                NOT3 =  QtGui.QWidget()
                NOT3V = QtGui.QVBoxLayout()
                NOT3.setLayout(NOT3V)
                # on prend toute la place
                NOT3V.setContentsMargins(0,0,0,0) 
                NOT3V.setSpacing(0) 

                self.Explo_saisie = QtGui.QLineEdit()
                NOT3V.addWidget(self.Explo_saisie)
                self.Explo_saisie.returnPressed.connect(self.Explorer)

                NOT3VH = QtGui.QHBoxLayout()
                NOT3V.addLayout(NOT3VH)


                Explo_check_prefix = QtGui.QRadioButton("prefix")       
                Explo_check_prefix.setChecked(True)
                Explo_check_suffix = QtGui.QRadioButton("suffix")       
                Explo_check_infix = QtGui.QRadioButton("infix") 

                NOT3VH.addWidget(Explo_check_prefix)
                NOT3VH.addWidget(Explo_check_suffix)
                NOT3VH.addWidget(Explo_check_infix)

                self.Explo_radioGroup = QtGui.QButtonGroup()
                self.Explo_radioGroup.addButton(Explo_check_prefix,0)
                self.Explo_radioGroup.addButton(Explo_check_suffix,1)
                self.Explo_radioGroup.addButton(Explo_check_infix,2)



                #self.Explo_action = QtGui.QPushButton("search")
                #self.Explo_action.setEnabled(False) #desactivé au lancement
                #self.Explo_action.clicked.connect(self.Explorer)
                #NOT3VH.addWidget(self.Explo_action)

                Explo_spacer1 = QtGui.QLabel()
                Explo_spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
                NOT3VH.addWidget(Explo_spacer1)


                self.Explo_commands = QtGui.QPushButton()
                self.Explo_commands.setIcon(QtGui.QIcon("images/gear.png"))
                self.Explo_commands.setEnabled(False) 
                NOT3VH.addWidget(self.Explo_commands)
                Explo_commands_texts= QtGui.QMenu(self)
                Explo_commands_texts.addAction('texts' , self.explo_show_text)
                self.Explo_commands.setMenu(Explo_commands_texts)


                NOT3VH2 = QtGui.QHBoxLayout()
                NOT3V.addLayout(NOT3VH2)
                self.Explo_liste = QtGui.QListWidget()
                self.Explo_liste.currentItemChanged.connect(self.explo_item_selected)
                NOT3VH2.addWidget(self.Explo_liste)
                self.Explo_concepts = QtGui.QLabel()
                tempImage = QtGui.QPixmap("images/Prospero-II.png")
                self.Explo_concepts.setPixmap(tempImage)
                NOT3VH2.addWidget(self.Explo_concepts)

                # on prend toute la place
                #NOT3VH2.setContentsMargins(0,0,0,0) 
                #NOT3VH2.setSpacing(0) 
                

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
                spacer_CTX_1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum )
                NOT5VHC.addWidget(spacer_CTX_1)
        
                self.NOT5Commands1 = QtGui.QPushButton()
                self.NOT5Commands1.setIcon(QtGui.QIcon("images/gear.png"))
                self.NOT5Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
                NOT5VHC.addWidget(self.NOT5Commands1)

        #une box horizontale pour liste et deploiement
                NOT5VH = QtGui.QHBoxLayout()
                NOT5V.addLayout(NOT5VH) 
                self.NOT5_list = QtGui.QListWidget()
                self.NOT5_list.setAlternatingRowColors(True)
                self.NOT5_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
                self.NOT5_list.currentItemChanged.connect(self.contexts_contents) 
                NOT5VH.addWidget(self.NOT5_list)
                self.NOT5_cont = QtGui.QListWidget()
                self.NOT5_cont.setAlternatingRowColors(True)
                NOT5VH.addWidget(self.NOT5_cont)
                self.NOT5_cont.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
#               self.NOT5_cont.currentItemChanged.connect() 


                self.SubWdwNO.addTab(NOT1,self.tr("Lexicon"))
                self.SubWdwNO.addTab(NOT2,"Concepts")
                self.SubWdwNO.addTab(NOT3,"Search")
                self.SubWdwNO.addTab(NOT5,"Metadatas")

                self.SubWdwNO.currentChanged.connect(self.change_NOTab)
                #SubWdwNO.setCurrentIndex(0) #Focus sur l'onglet listes concepts

################################################
################################################
#TODO corriger resize des grids sur petits ecrans
                ###Layout en grid
                main = QtGui.QWidget()
                grid = QtGui.QGridLayout()
                grid.addWidget(self.SubWdwNO,0,0)
                grid.addWidget(self.SubWdwNE,0,1)
                grid.addWidget(self.SubWdwSO,1,0)
                #grid.addWidget(SubWdwSE,1,1)
                grid.addWidget(self.SubWdwSETabs,1,1)
                main.setLayout(grid)
                self.setCentralWidget(main)

                self.setWindowTitle(u'Prospéro interface')
                self.show() 
                #codex_w = codex_window(self)
                #codex_w.show()


################################################
################################################
#Fin de la methode principale d'affichage
#début des fonctions
################################################
################################################

        def menu_ctx(self,pos):
                menu = QtGui.Qmenu
        def select_P2_path(self):
                path = QtGui.QFileDialog.getOpenFileName(self, 'Select server path')
                self.Param_Server_path_P2.setText(path[0])

        def select_PRC_path(self):
                #ajouter un filtre d'extensions
                path = QtGui.QFileDialog.getOpenFileName(self, 'Select corpus path')
                self.Param_Server_path_PRC.setText(path[0])

        def get_semantique_concepts(self):
                if (self.NOT2select.currentText()=="collections") : 
                        return '$col'
                elif ( self.NOT2select.currentText()=="fictions" ) : 
                        return '$ef'
                elif (self.NOT2select.currentText()=="entitie's categories") : 
                        return '$cat_ent'
                else : 
                        return False

        def get_semantique(self):
                if (self.NOT1select.currentText()=="entities") : 
                        return '$ent'
                elif (self.NOT1select.currentText()=="qualities") : 
                        return '$qualite'
                else : 
                        return False

        def activity(self,message):
                """Add message to the history window"""
                self.status.showMessage(message)
                time = u"%s" % datetime.datetime.now()
                self.History.append("%s %s" % (time[:19],message))

        def ord_liste_txt(self,liste_sem,order="chrono"):
                liste = {}
                if (order=="chrono"):
                        for e in liste_sem :
                                txt = self.listeObjetsTextes[e]
                                date = txt.getCTX("date")
                                date = re.split(" ",date) #sépare date et heure
                                if (len(date) > 1):
                                        date,heure = date
                                else:
                                        date = date[0]
                                liste[e] = "-".join(reversed(re.split("/",date)))
                        liste =   sorted(liste.items(),key=lambda (k,v) : v) 
                        return liste
                

        def display_liste_textes_corpus(self):
                """displays texts for the corpus"""
                self.activity(u"Displaying text list (%d items)" %len(self.listeTextes)  )
                tab_title ="corpus (%d)"%len(self.listeTextes) 
                self.SOT1.tabBar().setTabText(0,tab_title)
                self.CorpusTexts.clear()

                if not hasattr(self, "dic_widget_list_txt"):
                        self.dic_widget_list_txt = { 0 : []}
                else : 
                        self.dic_widget_list_txt[0] =  []

		self.PrgBar.perc(len(self.listeObjetsTextes))

                for sem,tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
                        txt =  self.listeObjetsTextes[sem]
                        self.dic_widget_list_txt[0].append(txt)
			WI = Viewer.TexteWidgetItem(txt.getResume())
                        self.CorpusTexts.addItem(WI.Widget)
                        self.CorpusTexts.setItemWidget(WI.Widget,WI.WidgetLabel)

                        self.PrgBar.percAdd(1)



        def onSelectText(self):
                """Update text properties windows when a text is selected """

                tab = self.SOT1.tabText(self.SOT1.currentIndex())
                row = self.SOT1.focusWidget().currentRow()

                if (self.SOT1.currentIndex() == 0 ) :
                        txt = self.dic_widget_list_txt[0][row]
                        self.semantique_txt_item =  txt.sem
                else :
                        i = 0
                        for listwidget in self.SOT1.currentWidget().findChildren(QtGui.QListWidget) :
                                if listwidget == self.SOT1.focusWidget():
                                        txt = self.dic_widget_list_txt[tab][i][row]
                                        self.semantique_txt_item = txt.sem
                                i = i+1

                #self.activity(u"%s (%s) selected " % (txt.path,self.semantique_txt_item)) 

                if (self.SOT1.currentIndex() != 0): #selectionne le texte dans l'onglet corpus s'il n'est pas actif
                        self.selectTxtCorpus(txt)
                if (self.SOT1.count() > 1): #si plus d'une tab
                        for t in range (1,self.SOT1.count()): #parcourt les tabs
                                l =  self.SOT1.widget(t).findChildren(QtGui.QListWidget) #les listwidget de la tab
                                l[0].itemSelectionChanged.disconnect(self.onSelectText)
                                l[1].itemSelectionChanged.disconnect(self.onSelectText)
                                if txt in  self.dic_widget_list_txt[self.SOT1.tabText(t)][0]:#si l'objet txt est dans le dic de l'element
                                        l[0].setCurrentRow( self.dic_widget_list_txt[self.SOT1.tabText(t)][0].index(txt)) #selectionne le txt
                                        l[1].clearSelection()
                                else: #s'il est dans son anticorpus
                                        l[1].setCurrentRow( self.dic_widget_list_txt[self.SOT1.tabText(t)][1].index(txt))
                                        l[0].clearSelection()
                                l[0].itemSelectionChanged.connect(self.onSelectText)
                                l[1].itemSelectionChanged.connect(self.onSelectText)


                #V =  self.liste_txt_corpus[item_txt]
                #txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
                #self.SETabTextDescr.setText(item_txt)

                #pour accélérer l'affichage, on ne remplit que l'onglet sélectionné
                if ( self.SubWdwSETabs.currentIndex () == 0 ):
                        self.show_textProperties( self.semantique_txt_item)
                elif ( self.SubWdwSETabs.currentIndex () == 1 ):
                        self.show_textCTX(self.semantique_txt_item) 
                elif ( self.SubWdwSETabs.currentIndex () == 2 ):
                        self.show_textContent( self.semantique_txt_item)

        def selectTxtCorpus(self,txt):
                self.CorpusTexts.itemSelectionChanged.disconnect(self.onSelectText)
                self.CorpusTexts.setCurrentRow( self.dic_widget_list_txt[0].index(txt))
                self.CorpusTexts.itemSelectionChanged.connect(self.onSelectText)


        def deselectText(self):
                """vide les listes pour eviter confusion et deselectionne les listwidget"""
                self.saillantesAct.clear()
                self.saillantesCat.clear()
                self.saillantesCol.clear()
                #self.SETabTextDescr.setText("")
                self.efface_textCTX()
                self.textContent.clear()
                if hasattr(self,"semantique_txt_item"):
                        del self.semantique_txt_item


                for listwidget in self.SOT1.findChildren(QtGui.QListWidget) :
                        listwidget.itemSelectionChanged.disconnect(self.onSelectText)
                        listwidget.clearSelection()
                        listwidget.itemSelectionChanged.connect(self.onSelectText)



        def change_NOTab(self):
                if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet des Concepts est sélectionné
                        if  hasattr(self,"client"): # si connecte
                                if not  hasattr(self,"sem_concept"): #si pas de concept selectionné
                                        self.select_concept(self.NOT2select.currentText())

        def change_SETab(self):
                if  hasattr(self,"semantique_txt_item" ):
                        sem_txt = self.semantique_txt_item
                        if ( self.SubWdwSETabs.currentIndex () == 0 ):
                                self.saillantesAct.clear()
                                self.saillantesCat.clear()
                                self.saillantesCol.clear()
                                self.show_textProperties( sem_txt)
                        elif ( self.SubWdwSETabs.currentIndex () == 1 ):
                                self.efface_textCTX()
                                self.show_textCTX(sem_txt) 
                        elif ( self.SubWdwSETabs.currentIndex () == 2 ):
                                self.textContent.clear()
                                self.show_textContent( sem_txt)
                        self.resetCTX() 


        def onChangeCTX(self):
                r = self.textCTX.currentRow()
                if (r != -1):
                        self.textCTX.currentItem().setBackground(QtGui.QColor( 237,243,254)) # cyan
                        self.textCTX_valid.setEnabled(True)
                        self.textCTX_reset.setEnabled(True)


        def saveCTX(self):
                sem_txt = self.semantique_txt_item
                txt =  self.listeObjetsTextes[sem_txt]
                txtResume = txt.getResume()
                modif = []
                for r in range( self.textCTX.rowCount()):
                        field = self.textCTX.item(r,0).text()
                        val =  self.textCTX.item(r,1).text()
                        ask = u"%s.ctx.%s" % ( sem_txt,field)
                        result = self.client.eval_var(ask)
                        result = re.sub(u"^\s*","",result)
                        if (result != val):
                                #print [field, result, val]
                                self.client.eval_set_ctx( sem_txt,field,val)
                                #PB NE MARCHE PAS A TOUS LES COUPS !!
                                self.client.add_cache_var(sem_txt +".ctx."+field,val)
                                self.listeObjetsTextes[sem_txt].setCTX(field,val)
                                modif.append(field)
                                
                #PB a la creation d'un nouveau champ ?
                #self.client.eval_set_ctx( sem_txt,"testfield",val)


                # mettre à jour listes si auteur, date, titre
                if len(set(modif) & set(  ["author","date","title"])):
                        if "date" in modif:
                                self.display_liste_textes_corpus()
                                self.selectTxtCorpus(txt)
                                #TODO faire de même pour les autres onglets
                                for tab in range(1,self.SOT1.count())   :
                                        self.SOT1.removeTab(tab)
                        else :
                                newResume = txt.getResume()
                                for listWidget in self.SOT1.findChildren(QtGui.QListWidget):
                                        for label in  listWidget.findChildren(QtGui.QLabel):
                                                if label.text() == txtResume:
                                                        label.setText(newResume)
                        

                #PB de cache quand remet a jour la liste des ctx
                self.maj_metadatas()

                self.textCTX_valid.setEnabled(False)
                self.textCTX_reset.setEnabled(False)
                self.resetCTX()

                

        def resetCTX(self):
                self.textCTX_valid.setEnabled(False)
                self.textCTX_reset.setEnabled(False)
                self.show_textCTX(self.semantique_txt_item)
                

        def getvalueFromSem(self,item_txt,type):        
                sem = self.client.eval_get_sem(item_txt, type )
                val = self.client.eval_var(sem)
                return val

        def select_concept(self,typ):
                """ quand un element de Concepts est selectionné """
                self.sem_concept = self.get_semantique_concepts()
                if (self.sem_concept in ["$col"]):
                        self.affiche_concepts_scores_dep()
                else :
                        self.affiche_concepts_scores_oc()
                self.detect_concepts = ["abracadabri"]

        def select_liste(self,typ):
                """ quand un element de Lexicon est selectionné """
                self.sem_liste_concept = self.get_semantique()
                self.detect_lexicon = ["abracadabri"]
                self.affiche_liste_scores_oc()

        def change_liste(self,content):
                self.NOT1Commands2.setEnabled(False)
                self.NOT12.clear()
                self.NOT12_D.clear()
                self.NOT12_E.clear()
		for r in range(len(content)):
			i = QtGui.QListWidgetItem(content[r])
			self.NOT12.addItem(i)
			i.setToolTip('rank:%d'%(r+1))
			


        def change_liste_concepts(self,content):
                self.NOT22.clear()
                self.NOT22_D.clear()
                self.NOT22_E.clear()
                self.NOT22.addItems(content)


        def choose_score_tick(self):
                """tick and disable the choosen order selected, untick and enable others"""
                for act in self.NOT1Commands1Menu.actions():
                        if (act.text() == self.which):
                                act.setIcon(QtGui.QIcon("images/Tick.gif"))
                                act.setEnabled(False)
                        else:
                                act.setEnabled(True)
                                act.setIcon(QtGui.QIcon())
                if (self.sem_liste_concept not in ['$ent']):
                        self.NOT1C1_dep.setEnabled(False)
                self.NOT1Commands1.setText(u"\u2195 %s"%self.which)
        
        def choose_score_concepts_tick(self):
                """tick and disable the choosen order selected, untick and enable others"""
                for act in self.NOT2Commands1Menu.actions():
                        if (act.text() == self.which_concepts):
                                act.setIcon(QtGui.QIcon("images/Tick.gif"))
                                act.setEnabled(False)
                        else :
                                act.setEnabled(True)
                                act.setIcon(QtGui.QIcon())
                self.NOT2Commands1.setText(u"\u2195 %s"%self.which_concepts)
                        

        def affiche_liste_scores_alpha(self):
                self.which = "alphabetically"
                self.choose_score_tick()
                self.affiche_liste_scores()


        def affiche_liste_scores_texts(self):
                self.which = "number of texts"
                self.choose_score_tick()
                self.affiche_liste_scores()

        def affiche_liste_scores_fapp(self):
                self.which = "first apparition"
                self.choose_score_tick()
                self.affiche_liste_scores()


        def affiche_liste_scores_lapp(self):
                self.which = "last apparition"
                self.choose_score_tick()
                self.affiche_liste_scores()

        def affiche_liste_scores_oc(self):
                self.which = "occurences"
                self.choose_score_tick()
                self.affiche_liste_scores()

        def affiche_liste_scores_dep(self):
                self.which = "deployement"
                self.choose_score_tick()
                self.affiche_liste_scores()


        def affiche_concepts_scores_alpha(self):
                self.which_concepts = "alphabetically"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()


        def affiche_concepts_scores_texts(self):
                self.which_concepts = "number of texts"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()

        def affiche_concepts_scores_fapp(self):
                self.which_concepts = "first apparition"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()


        def affiche_concepts_scores_lapp(self):
                self.which_concepts = "last apparition"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()


        def affiche_concepts_scores_oc(self):
                self.which_concepts = "occurences"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()

        def affiche_concepts_scores_dep(self):
                self.which_concepts = "deployement"
                self.choose_score_concepts_tick()
                self.affiche_concepts_scores()


        def affiche_concepts_scores(self):
                typ = self.NOT2select.currentText()
                self.sem_concept = self.get_semantique_concepts()
                content = self.client.recup_liste_concept(self.sem_concept)
                self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,len(content), self.which_concepts))
                liste_valued =[]

		self.PrgBar.perc(len(content))

                for row  in range(len(content)):
                        if (self.which_concepts == "occurences" or self.which_concepts == "alphabetically"):
                                order = "val"
                                ask = "%s%d.%s"% ( self.sem_concept, row, order)
                        elif (self.which_concepts == "deployement"):
                                order = "dep"
                                ask = "%s%d.%s"% ( self.sem_concept, row, order)
                        elif (self.which_concepts == "number of texts"):
                                order = "nbtxt"
                                ask = "%s%d.%s"% ( self.sem_concept, row, order)
                        elif (self.which_concepts == "first apparition"):
                                order = "fapp"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
                        elif (self.which_concepts == "last apparition"):
                                order = "lapp"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)

                        result  = self.client.eval_var( ask )

                        try :
                                if self.which_concepts  in ["first apparition",  "last apparition"]:
                                        val = re.sub(u"^\s*","",result)
                                else :
                                        val = int(result)
                        except:
                                #en cas de non reponse
                                print "pb",[ask]
                                val = 0
                        liste_valued.append([val,content[row]])

        
                        self.PrgBar.percAdd(1)


                liste_final =[]
                self.content_liste_concept = []
                if (self.which_concepts == "alphabetically" ):
                        for i in sorted(liste_valued,key=lambda x : x[1],reverse = 0):
                                item_resume = u"%s %s" % (i[0], i[1])
                                liste_final.append(item_resume) 
                                self.content_liste_concept.append(i[1])
                else :
                        for i in sorted(liste_valued,key=lambda x : x[0],reverse = 1):
                                item_resume = u"%s %s" % (i[0], i[1])
                                liste_final.append(item_resume) 
                                self.content_liste_concept.append(i[1])
                self.change_liste_concepts(liste_final)



        def affiche_liste_scores(self):
                typ = self.NOT1select.currentText()
                self.sem_liste_concept = self.get_semantique()
                content = self.client.recup_liste_concept(self.sem_liste_concept)
                if ( self.sem_liste_concept not in ['ent']):
                        self.lexicon_list_semantique = content
                self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,len(content), self.which))
                liste_valued =[]
		self.PrgBar.perc(len(content))
                for row  in range(len(content)):
                        if (self.which == "occurences" or self.which == "alphabetically"):
                                order = "val"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
                        elif (self.which == "deployement"):
                                order = "dep"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
                        elif (self.which == "number of texts"):
                                order = "nbtxt"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
                        elif (self.which == "first apparition"):
                                order = "fapp"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
                        elif (self.which == "last apparition"):
                                order = "lapp"
                                ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)

                        result = self.client.eval_var( ask )

                        try :
                                if self.which  in ["first apparition",  "last apparition"]:
                                        val = re.sub(u"^\s*","",result)
                                else :
                                        val = int(result)
                                if (self.sem_liste_concept == "$ent" and self.which == "deployement" and val == 0):
                                        val = 1
                        except:
                                #en cas de non reponse
                                print "pb2",[ask]
                                val = 0
                        liste_valued.append([val,content[row]])
        
                        self.PrgBar.percAdd(1)



                liste_final =[]
                self.content_liste_lexicon = []
                if (self.which == "alphabetically" ):
                        for i in sorted(liste_valued,key=lambda x : x[1],reverse = 0):
                                item_resume = u"%s %s" % (i[0], i[1])
                                liste_final.append(item_resume) 
                                self.content_liste_lexicon.append(i[1])
                else :
                        for i in sorted(liste_valued,key=lambda x : x[0],reverse = 1):
                                item_resume = u"%s %s" % (i[0], i[1])
                                liste_final.append(item_resume) 
                                self.content_liste_lexicon.append(i[1])
                self.change_liste(liste_final)




        def liste_item_changed(self):
                """ suite au changement de sélection , mettre à jour les vues dépendantes """ 

                itemT = self.NOT12.currentItem()
                if (itemT):
                        item = re.sub("^\d* ","",itemT.text())
                        row = self.NOT12.currentRow() 
                        self.activity("%s selected, rank %d" % (item,row+1))
                        self.NOT12_D.clear() # on efface la liste
                        self.NOT12_E.clear()
                        sem = self.sem_liste_concept
                        if ( sem  in ["$ent"])  :
                                # recupere la designation semantique de l'element
                                self.semantique_liste_item = self.client.eval_get_sem(item, sem )
                                #liste les representants
                                result = re.split(", ", self.client.eval_var("%s.rep[0:]"% self.semantique_liste_item))
                                
                                
                                if ( result != [u''] ):

                                        self.liste_D_unsorted = []
                                        for r in range(len(result)):
                                                if (self.which  == "occurences" or self.which == "alphabetically"):
                                                        ask = "%s.rep%d.val"% (self.semantique_liste_item,r)
                                                elif (self.which  == "deployement" ):
                                                        ask = "%s.rep%d.dep"% (self.semantique_liste_item,r)
                                                elif (self.which  == "number of texts" ):
#TODO corriger : il donne la valeur de l'EF entier
                                                        ask = "%s.rep%d.nbtxt"% (self.semantique_liste_item,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                to_add = "%d %s"%(val, result[r] )
                                                #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                                                if (val == 0):
                                                        self.liste_D_unsorted.extend( map(lambda x : "0 %s" %x ,result[r:]) )
                                                        break
                                                self.liste_D_unsorted.append(to_add)
                                                        
                                        if (self.which == "alphabetically"):
                                                liste_D_sorted = sorted(self.liste_D_unsorted,key = lambda x : re.split(" ",x)[1],reverse =  0)
                                        else :
                                                liste_D_sorted = sorted(self.liste_D_unsorted,key = lambda x : int(re.split(" ",x)[0]),reverse =  1)
                                        self.NOT12_D.addItems(liste_D_sorted)
                                        # afficher directement E du premier element de D 
                                        self.NOT12_D.setCurrentItem(self.NOT12_D.item(0))
                                        self.liste_D_item_changed()
                        else :
                                self.semantique_liste_item =  sem 


                        #activation des boutons de commande
                        self.NOT1Commands2.setEnabled(True) 




        def liste_D_item_changed(self):
                """quand un item de D est sélectionné, afficher représentants dans E"""
                itemT = self.NOT12_D.currentItem()
                if (itemT):
                        """
                        if (self.which in ["occurences","deployement"]):
                                item = re.sub("^\d* ","",itemT.text())
                        else :
                                item = itemT.text() # l'element selectionné
                        """
                        #row = self.NOT12_D.currentRow() 
                        row = self.liste_D_unsorted.index(itemT.text())
                        #self.activity("%s selected" % item)
                        self.NOT12_E.clear() # on efface la liste
                        ask = "%s.rep%d.rep[0:]" % (self.semantique_liste_item,row)
                        self.semantique_liste_item_D = u"%s.rep%d" % (self.semantique_liste_item,  row)
                        result =self.client.eval_var(ask)
                         
                        if (result != "") :
                                result = re.split(", ", result)
                                if (self.which == "alphabetically"):
                                        liste_scoree = []

					self.PrgBar.perc(len(result))

                                        for r in range(len(result)):
                                                ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                liste_scoree.append([result[r],val])
                                                self.PrgBar.percAdd(1)

                                        self.NOT12_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),sorted(liste_scoree)))
                                else :
					self.PrgBar.perc(len(result))
                                        for r in range(len(result)):
                                                ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                                                if (val == 0):
                                                        self.NOT12_E.addItems( map(lambda x : "0 %s" %x ,result[r:]) )
                                                        break
                                                self.NOT12_E.addItem("%d %s"%(val, result[r] )) 
                                                self.PrgBar.percAdd(  1 )
		self.PrgBar.reset()

        def liste_E_item_changed(self):
                itemT = self.NOT12_E.currentItem()
                if (itemT):
                        item = re.sub("^\d* ","",itemT.text())
                        #item = itemT.text() # l'element selectionné
                        row = self.NOT12_E.currentRow() 
                        self.activity("%s selected" % item)
                        sem = self.sem_liste_concept
                        self.semantique_liste_item_E = u"%s.rep%d" % (self.semantique_liste_item_D,  row)
                


        def liste_concept_changed(self):
                """ suite au changement de sélection , mettre à jour les vues dépendantes """ 

                itemT = self.NOT22.currentItem()
                if (itemT):
                        item = re.sub("^\d* ","",itemT.text())
                        row = self.NOT22.currentRow() 
                        self.activity("%s selected, rank %d" % (item,row+1))
                        self.NOT22_D.clear() # on efface la liste
                        self.NOT22_E.clear()
                        sem = self.sem_concept # recupere la designation semantique de l'element
                        self.semantique_concept_item = self.client.eval_get_sem(item, sem ) #liste les representants
                        result = re.split(", ", self.client.eval_var("%s.rep[0:]"% self.semantique_concept_item))
                        
                        if ( result != [u''] ):
                                if (sem in ["$cat_ent"]):#affiche directement sur la liste E
                                        liste_scoree = []
                                        prgbar_val = 0
					self.PrgBar.perc(len(result))
                                        for r in range(len(result)):
                                                if (self.which_concepts == "number of texts"):
#TODO corriger, il donne la valeur de la categorie entiere
                                                        ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item,r)
                                                else :
                                                        ask = "%s.rep%d.val"% (self.semantique_concept_item,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                liste_scoree.append( [ result[r] , val ])
                                                self.PrgBar.percAdd( 1  )
                                        if (self.which_concepts == "alphabetically"):
                                                liste_scoree.sort()
                                        self.NOT22_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),liste_scoree))   

                                else:
                                        self.liste_D_concepts_unsorted = []
                                        for r in range(len(result)):
                                                if (self.which_concepts  == "occurences" or self.which_concepts == "alphabetically"):
                                                        ask = "%s.rep%d.val"% (self.semantique_concept_item,r)
                                                elif (self.which_concepts  == "deployement" ):
                                                        ask = "%s.rep%d.dep"% (self.semantique_concept_item,r)
                                                elif (self.which_concepts == "number of texts"):
                                                        ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                to_add = "%d %s"%(val, result[r] )
                                                #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                                                if (val == 0):
                                                        self.liste_D_concepts_unsorted.extend( map(lambda x : "0 %s" %x ,result[r:]) )
                                                        break
                                                self.liste_D_concepts_unsorted.append(to_add)
                                                
                                        if (sem not in ["$cat_ent"]):
                                                if (self.which_concepts == "alphabetically"):
                                                        liste_D_sorted = sorted(self.liste_D_concepts_unsorted,key = lambda x : re.split(" ",x)[1],reverse =  0)
                                                else :
                                                        liste_D_sorted = sorted(self.liste_D_concepts_unsorted,key = lambda x : int(re.split(" ",x)[0]),reverse =  1)
                                        self.NOT22_D.addItems(liste_D_sorted)

                                        # afficher directement E du premier item de D
                                        self.NOT22_D.setCurrentItem(self.NOT22_D.item(0))
                                        self.liste_D_concept_changed()


                        #activation des boutons de commande
                        self.NOT2Commands2.setEnabled(True) 




        def liste_D_concept_changed(self):
                """quand un item de D est sélectionné, afficher représentants dans E"""
                itemT = self.NOT22_D.currentItem()
                if (itemT):
                        row = self.liste_D_concepts_unsorted.index(itemT.text())
                        self.NOT22_E.clear() # on efface la liste
                        ask = "%s.rep%d.rep[0:]" % (self.semantique_concept_item,row)
                        self.semantique_concept_item_D = u"%s.rep%d" % (self.semantique_concept_item,  row)
                        result = self.client.eval_var(ask)
                        
                        if (result != "") :
                                result = re.split(", ", result)
                                if (self.which_concepts == "alphabetically"):
                                        liste_scoree = []
					self.PrgBar.perc(len(result))
                                        for r in range(len(result)):
                                                ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item,row,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                liste_scoree.append([result[r],val])
                                                self.PrgBar.percAdd(1)
                                        self.NOT22_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),sorted(liste_scoree)))
                                else :
					self.PrgBar.perc(len(result))
                                        for r in range(len(result)):
                                                ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item,row,r)
                                                val = int(self.client.eval_var(ask))
                                                
                                                #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
                                                if (val == 0):
                                                        self.NOT22_E.addItems( map(lambda x : "0 %s" %x ,result[r:]) )
                                                        break
                                                self.NOT22_E.addItem("%d %s"%(val, result[r] )) 
                                                self.PrgBar.percAdd( 1  )
		self.PrgBar.reset()

        def liste_E_concept_changed(self):
                itemT = self.NOT22_E.currentItem()
                if (itemT):
                        item = re.sub("^\d* ","",itemT.text())
                        row = self.NOT22_E.currentRow() 
                        self.activity("%s selected" % item)
                        sem = self.sem_concept
                        if (sem in ["$cat_ent"]):
                                self.semantique_concept_item_E = u"%s.rep%d" % (self.semantique_concept_item,  row)
                        else :
                                self.semantique_concept_item_E = u"%s.rep%d" % (self.semantique_concept_item_D,  row)
                


                        
        def server_vars_Evalue(self):
                var = self.server_vars_champ.text()
                self.server_vars_champ.clear()
                result = self.client.eval_var(var)
                self.server_vars_result.setColor("red")
                self.server_vars_result.append("%s" % var)
                self.server_vars_result.setColor("black")
                self.server_vars_result.append(result)


        def server_getsem_Evalue(self):
                var = self.server_vars_champ.text()
                self.server_vars_champ.clear()
                items = re.split("\s*",var)
                self.server_vars_result.setColor("red")
                self.server_vars_result.append("%s" % var)
                if (len(items) == 2):
                        self.server_vars_result.setColor("black")
                        el, sem = items
                        self.server_vars_result.append(self.client.eval_get_sem(el, sem))
                        

        def server_vars_Clear(self):
                self.server_vars_result.clear()
        
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
                commande = "%s -e -p %s -f %s" % (server_path,port,PRC)
                self.activity("Loading %s" % PRC)
                self.local_server = subprocess.Popen(commande, shell=True)
                
        def stop_server(self):
                self.activity("Stopping local server" )
                self.local_server.terminate()   
                self.thread.stop()
                self.Param_Server_R_button.setText('Start server')
                self.Param_Server_R_button.clicked.disconnect(self.stop_server)
                self.Param_Server_R_button.clicked.connect(self.lance_server)
        
        def connect_server_localhost(self):
                self.connect_server('localhost')
                #self.connect_server(h='192.168.1.99',p='60000')

        def connect_server(self,h = 'prosperologie.org',p = '60000'):
                self.activity("Connecting to server")
                #self.client=client(self.Param_Server_val_host.text(),self.Param_Server_val_port.text())

                #self.client=client("prosperologie.org","60000")
                #self.client=client("192.168.1.99","4000")

                self.client=client(h,p)
                #self.client=client("prosperologie.org","60000")
                #self.client=client("localhost","60000")

                #self.client.teste_connect()
		
		if (self.client.Etat):
                        # donne le focus a l'onglet history
                        self.SubWdwNE.setCurrentIndex(self.History_index)

                        # calcule en avance
                        self.pre_calcule()

                        # affiche liste au demarrage
                        self.select_liste(self.NOT1select.currentText())

                        self.NOT1Commands1.setEnabled(True) 
                        self.NOT1select.setEnabled(True) 
                        self.NOT2Commands1.setEnabled(True) 
                        self.NOT2select.setEnabled(True) 

                        # affiche textes au demarrage
                        self.display_liste_textes_corpus()

                        #self.Param_Server_B.clicked.connect(self.disconnect_server)
                        #self.Param_Server_B.setText("Disconnect")
                        #self.Param_Server_B.setStyleSheet(None)  #supprime css bouton vert

                        #self.Explo_action.setEnabled(True) 
                
        def disconnect_server(self):
                """Disconnect"""
                self.activity("Disconnecting")
                self.client.disconnect()
                self.Param_Server_B.setText('Connect to server')
                self.Param_Server_B.clicked.connect(self.connect_server)


        def codex_window(self):
                codex_w = codex_window(self)
                codex_w.show()

        def show_textContent(self ,  sem_txt):
                """Insert text content in the dedicated window"""
                contentText_semantique = "%s.ph[0:]" % sem_txt
                txt_content = self.client.eval_var(contentText_semantique)
                
                self.textContent.clear()
                self.textContent.append(txt_content)
                #move cursor to the beginning of the text
                self.textContent.moveCursor(QtGui.QTextCursor.Start)
                
        def efface_textCTX(self):
                self.textCTX.clear()
                self.textCTX.setRowCount(0)
                self.textCTX.setHorizontalHeaderLabels([u'field',u'value']) #on remet les headers apres le clear

        def show_textCTX(self, sem):
                """Show text metadata"""
                self.efface_textCTX()
                ctx = self.listeObjetsTextes[sem].getCTXall()
                self.textCTX.setRowCount(len(ctx))
                r = 0
                for field,value in ctx.iteritems() :
                        itemCTXwidget_field = QtGui.QTableWidgetItem(field)
                        self.textCTX.setItem(r,0,itemCTXwidget_field)
                        itemCTXwidget_val = QtGui.QTableWidgetItem(value)
                        self.textCTX.setItem(r,1,itemCTXwidget_val)
                        r += 1
                self.textCTX.resizeRowsToContents()

        def show_textProperties(self ,  sem_txt):
                """Show text sailent properties"""
                #les actants
                #les actants en tête sont calculés par le serveur
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
                        self.client.add_cache_var("%s.act%s"%(sem_txt,pos), act)
                        self.client.add_cache_var("%s.act%s.val"%(sem_txt,pos), list_act_val[pos])
                        pos +=1
                if (list_act):
                        #self.list_act = re.split(", ",list_act)
                        self.list_act = list_act
                        self.liste_act_valued = {}
			self.PrgBar.perc(len(self.list_act))
                        for i in range(len(self.list_act)) :
                                val = int(self.client.eval_var(u"%s.act%d.val"%(sem_txt,i)))
                                
                                self.liste_act_valued [self.list_act[i]] = [ val, 0 ] 
                                self.saillantesAct.addItem(u"%d %s" % (val, self.list_act[i]))
                                self.PrgBar.percAdd ( 1 )
                        

                #les catégories
                #le serveur renvoie toutes les éléments de la catégorie
                #si len(cat_ent[0:]) > 2, deux algos a tester pour économiser les interactions avec le serveur :
                # si cat_ent0.val < len(cat_ent[0:]) on approxime le cumul des frequences de valeur par celui du rapport du nb d'element analysés sur le nb d'element total qu'on multiplie par cat_ent0.val, on arrête quand on atteint 0,5 ou on affiche les cat tant qu'elles ont le même score
                # si cat_ent0.val > len(cat_ent[0:]) on fait le rapport des valeurs cumulees sur la somme totale si les valeurs suivantes avaient le même score que le dernier obtenu : Val_cumul / ( (len(cat_ent[0:]) - i ) * cat_ent[i].val + Val_cumul ) on s'arrete en atteignant 0,25 ou etc

                self.list_cat_valued = {}
                self.list_cat_txt = {} 
                self.saillantesCat.clear()
                self.saillantesCat_deployes = []
                #for typ in [u"cat_qua",u"cat_mar",u"cat_epr",u"cat_ent"]:
                for typ in [u"cat_ent"]: #uniquement les cat_ent
                        list_cat_sem = "%s.%s[0:]" % (sem_txt,typ)
                        list_cat  = self.client.eval_var(list_cat_sem)
                        
                        if (list_cat != u''):
                                list_cat_items = re.split(", ",list_cat)
                                r = 0
                                for c in list_cat_items:
                                        self.list_cat_txt[c] = [typ,r]
                                        r += 1
                                cum = 0
                                old_val = 0
                                #old_val2 = 0
				self.PrgBar.perc(len(list_cat_items))
                                for i in range(len(list_cat_items)):
                                        ask = u"%s.%s%d.val"%(sem_txt,typ,i)
                                        val = int(self.client.eval_var(ask))
                                        
                                        if (val < old_val):
                                                break
                                        cum += val
                                        C = float(cum) / (cum + ( (len(list_cat_items) - i ) * val ) )
                                        #C2 = float(i) / len(list_cat_items) * val
                                        #if (C2 > 0.50 and old_val2 == 0) :
                                        #       old_val2 = val  
                                        if (C > 0.25 and old_val == 0) :
                                                old_val = val   
                                        self.list_cat_valued[list_cat_items[i]] = val
					self.PrgBar.percAdd ( 1 )

                self.list_cat_valued_ord = []
                for cat in sorted( self.list_cat_valued.items(), key = lambda(k,v) : v,reverse=1):
                        self.list_cat_valued_ord.append(cat[0])
                        resume = u"%d %s" % (int(cat[1]), cat[0])
                        #if int(cat[1]) < old_val:
                        #       resume = "D" + resume
                        #if int(cat[1]) < old_val2:
                        #       resume = "E" + resume
                        self.saillantesCat.addItem(resume)
                        

                # les collections
                # on met toutes les collections parce que leur émergence est donnée par leur déploiement
#TODO ordonner
                self.saillantesCol.clear()
                self.saillantesCol_deployees = []
                list_col_sem = "%s.col[0:]" % sem_txt
                result = self.client.eval_var(list_col_sem)
                
                if (result != u""):
                        self.list_col = re.split(", ",result)   
                        self.list_col_valued = {}
			self.PrgBar.perc(len(self.list_col))
                        for i in range(len(self.list_col)) :
                                val = int(self.client.eval_var(u"%s.col%d.dep"%(sem_txt,i)))
                                
                                self.saillantesCol.addItem(u"%d %s" % (val, self.list_col[i]))
                                self.list_col_valued[self.list_col[i]] = val
                                self.PrgBar.percAdd ( 1 )



        def deploie_Col(self):
                item = self.saillantesCol.currentItem().text()
                item = re.sub("^\s*\d* ","",item)

                self.saillantesCol.clear()
                
                for r in self.list_col:
                        self.saillantesCol.addItem(u"%d %s" % (self.list_col_valued[r],r))

                        if ( (r == item) and (item in self.saillantesCol_deployees) ):
                                self.saillantesCol_deployees.remove(item)
                        elif (r == item) :
                                self.saillantesCol_deployees.append(item)

                        if (r in self.saillantesCol_deployees):                     
                                ask = "%s.col%d.rep_present[0:]"%(self.semantique_txt_item,self.list_col.index(r))
                                result = self.client.eval_var(ask)
                                if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.list_col_valued.keys() ):
                                                        ask = "%s.col%d.rep_present%d.val"%(self.semantique_txt_item,self.list_col.index(r),sub_n)
                                                        res = self.client.eval_var(ask)
                                                        
                                                        self.list_col_valued[result[sub_n]] = res
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.list_col_valued[result[sub_n]],result[sub_n]))
#TODO trouver couleur par defaut du alternate
                                                #i.setBackground(QtGui.QColor( 245,245,245)) # gris clair
                                                i.setBackground(QtGui.QColor( 237,243,254)) # cyan
                                                self.saillantesCol.addItem(i)
                                
        def deploie_Cat(self):
                item = self.saillantesCat.currentItem().text()
                item = re.sub("^\s*\d* ","",item)
                self.saillantesCat.clear()
                for cat in self.list_cat_valued_ord:
                        resume = u"%d %s" % (self.list_cat_valued[cat], cat)
                        self.saillantesCat.addItem(resume)

                        if ( (cat == item) and (item in self.saillantesCat_deployes) ):
                                self.saillantesCat_deployes.remove(item)
                        elif (cat == item) :
                                self.saillantesCat_deployes.append(item)
      
                        if (cat in self.saillantesCat_deployes):                     
                                sem = self.list_cat_txt[cat]
                                ask = "%s.%s%d.rep_present[0:]"%(self.semantique_txt_item,sem[0],sem[1])
                                result = self.client.eval_var(ask)
                                
                                if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.list_cat_valued.keys() ):
                                                        ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item,sem[0],sem[1],sub_n)
                                                        res = self.client.eval_var(ask)
                                                        self.list_cat_valued[result[sub_n]] = res
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.list_cat_valued[result[sub_n]][0],result[sub_n]))
                                                #i.setBackground(QtGui.QColor( 245,245,245))
                                                i.setBackground(QtGui.QColor( 237,243,254)) # cyan
                                                self.saillantesCat.addItem(i)
                                                
                          

        def deploie_Actant(self):
                item = self.saillantesAct.currentItem().text()
                item = re.sub("^\s*\d* ","",item)
                self.saillantesAct.clear()
                for r in self.list_act:
                        self.saillantesAct.addItem(u"%d %s" % (self.liste_act_valued[r][0], r))
                        
                        if ( (r == item) and (item in self.saillantesAct_deployes) ):
                                self.saillantesAct_deployes.remove(item)
                        elif (r == item) :
                                self.saillantesAct_deployes.append(item)
                                
                        if (r in self.saillantesAct_deployes):                     
                                ask = "%s.act%d.rep_present[0:]"%(self.semantique_txt_item,self.list_act.index(r))
                                result = self.client.eval_var(ask)
                                if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.liste_act_valued.keys() ):
                                                        ask = "%s.act%d.rep_present%d.val"%(self.semantique_txt_item,self.list_act.index(r),sub_n)
                                                        res = self.client.eval_var(ask)
                                                        
                                                        self.liste_act_valued[result[sub_n]] = [res,2]
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.liste_act_valued[result[sub_n]][0],result[sub_n]))
                                                #i.setBackground(QtGui.QColor( 245,245,245))
                                                i.setBackground(QtGui.QColor( 237,243,254)) # cyan
                                                self.saillantesAct.addItem(i)
                                        
                                
        def recup_element_lexicon(self):
                if ( self.sem_liste_concept in ['$ent']):
                        if  self.NOT12_E.currentItem() :
                                element = self.NOT12_E.currentItem().text() 
                                element = re.sub("^\d* ","",element)
                                return  (self.semantique_liste_item_E,element)
                        elif self.NOT12_D.currentItem():
                                element1 = self.NOT12.currentItem().text() 
                                element1 = re.sub("^\d* ","",element1)
                                element2 = self.NOT12_D.currentItem().text() 
                                element2 = re.sub("^\d* ","",element2)
                                element = u"%s:%s" % (element1,element2 )
                                return (self.semantique_liste_item_D  ,element)
                        else :
                                element = self.NOT12.currentItem().text() 
                                element = re.sub("^\d* ","",element)
                                return  (self.semantique_liste_item  ,element)
                else :
                        element = self.NOT12.currentItem().text() 
                        element = re.sub("^\d* ","",element)
                        return ("%s%d" % ( self.semantique_liste_item, self.lexicon_list_semantique.index(element)  ), element)
                
         
        def recup_element_concepts(self):
                if  self.NOT22_E.currentItem() :
                        element = self.NOT22_E.currentItem().text() 
                        element = re.sub("^\d* ","",element)
                        return  (self.semantique_concept_item_E,element)
                elif self.NOT22_D.currentItem():
                        element1 = self.NOT22.currentItem().text() 
                        element1 = re.sub("^\d* ","",element1)
                        element2 = self.NOT22_D.currentItem().text() 
                        element2 = re.sub("^\d* ","",element2)
                        element = u"%s:%s" % (element1,element2 )
                        return (self.semantique_concept_item_D  ,element)
                else :
                        element = self.NOT22.currentItem().text() 
                        element = re.sub("^\d* ","",element)
                        return  (self.semantique_concept_item  ,element)
                        


        def show_network(self):
#TODO scorer
                """Show the network of a selected item"""

                if ( self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
                        sem,element = self.recup_element_lexicon()
                if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
                        sem,element = self.recup_element_concepts()
                res_semantique = "%s.res[0:]" % (sem)

                #si la tab de l'element existe déjà, on efface l'ancienne
                for i in range(0, self.tabNetworks.count() ):
                        if (self.tabNetworks.tabText(i) == element):
                                self.tabNetworks.removeTab(i)
                                
                show_network_widget = QtGui.QWidget()
                show_network_box = QtGui.QVBoxLayout()
                # on prend toute la place
                show_network_box.setContentsMargins(0,0,0,0) 
                show_network_box.setSpacing(0) 
                show_network_widget.setLayout(show_network_box)
                index = self.tabNetworks.addTab(show_network_widget,"%s" % element)

                #selecteur de concept
                net_sel_concept = QtGui.QComboBox()
                net_sel_concept.addItems([u"entities"])
                show_network_box.addWidget(net_sel_concept)

                Network_list =  QtGui.QListWidget()
                show_network_box.addWidget(Network_list)
                result_network =   re.split(", ", self.client.eval_var(res_semantique))
                
                self.activity(u"Displaying network for %s (%d items)" % (element,len(result_network))  )
                Network_list.addItems(result_network)
                self.tabNetworks.setCurrentIndex(index)# donne le focus a l'onglet créé
                self.SubWdwSO.setCurrentIndex(1)# donne le focus a l'onglet Networks

        def explo_item_selected(self):
                self.Explo_commands.setEnabled(True) 
                """
                motif = re.sub("^\d* ","",self.Explo_liste.currentItem().text())
                self.client.eval_var("$ef[0:]")
                liste_ef =re.split(", ",self.client.eval_var_result) 
                for efN in  range(len(liste_ef)):
                        self.client.eval_var("$ef%d.rep_present[0:]"%efN)
                        result = re.split(", ",self.client.eval_var_result) 
                        if motif in  result:
                                 self.Explo_concepts.setText(liste_ef[efN])
                """     


        def explo_show_text(self):
                """Show texts containing a pattern"""
#TODO scorer/trier
                self.deselectText()

                motif = self.Explo_saisie.text()
                row =  self.Explo_liste.currentRow()
                ask = self.client.creer_msg_search("$search.rac",motif,"%d"%row,txt=True,ptxt="[0:]")
                result = self.client.eval( ask )
                liste_textes = re.split(", ",result)
                self.activity(u"Displaying %d texts for %s" % (len(liste_textes),motif))

                liste_textes = map(lambda k : self.dicTxtSem[k],liste_textes)

                texts_widget = Viewer.Liste_texte(motif,liste_textes)

                self.dic_widget_list_txt[ texts_widget.tab_title ] =  [ [],[] ]
                for sem,tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
                        txt =  self.listeObjetsTextes[sem]
                        if sem in liste_textes: 
				WI = Viewer.TexteWidgetItem(txt.getResume())
                                texts_widget.show_texts_corpus.addItem(WI.Widget)
                                texts_widget.show_texts_corpus.setItemWidget(WI.Widget,WI.WidgetLabel)
                                self.dic_widget_list_txt[texts_widget.tab_title][0].append(txt)
                        else :
				WI = Viewer.TexteWidgetItem(txt.getResume())
                                texts_widget.show_texts_anticorpus.addItem(WI.Widget)
                                texts_widget.show_texts_anticorpus.setItemWidget(WI.Widget,WI.WidgetLabel)
                                self.dic_widget_list_txt[texts_widget.tab_title][1].append(txt)
        
                texts_widget.show_texts_corpus.itemSelectionChanged.connect(self.onSelectText) 
                texts_widget.show_texts_anticorpus.itemSelectionChanged.connect(self.onSelectText)  

                #si la tab de l'element existe déjà, on efface l'ancienne
                for i in range(0, self.SOT1.count() ):
                        if (re.search("^{%s} (\d*)"%motif,self.SOT1.tabText(i) ) ):
                                self.SOT1.removeTab(i)
                        
                index = self.SOT1.addTab(texts_widget.show_texts_widget,texts_widget.tab_title)
                self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
                self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
                self.SOT1.tabBar().setTabToolTip(index,texts_widget.tab_title)


        def show_texts(self):
                """Show texts containing a selected item"""
#TODO scorer/trier
                self.deselectText()

                if ( self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
                        sem,element = self.recup_element_lexicon()
                if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
                        sem,element = self.recup_element_concepts()

                txts_semantique = "%s.txt[0:]" % (sem)
                result = self.client.eval_var(txts_semantique)

                if  (result == ""):
                        self.activity(u"No text to displaying for %s" % (element) )
                else:
                        liste_textes = re.split(", ",result) 
                        self.activity(u"Displaying %d texts for %s" % (len(liste_textes),element) )

                        liste_textes = map(lambda k : self.dicTxtSem[k],liste_textes)

                        texts_widget = Viewer.Liste_texte(element,liste_textes)
                        self.dic_widget_list_txt[ texts_widget.tab_title ] =  [ [],[] ]
                        for sem,tri in self.ord_liste_txt(self.listeObjetsTextes.keys()):
                                txt =  self.listeObjetsTextes[sem]
                                if sem in liste_textes: 
					WI = Viewer.TexteWidgetItem(txt.getResume())
                                        texts_widget.show_texts_corpus.addItem(WI.Widget)
                                        texts_widget.show_texts_corpus.setItemWidget(WI.Widget,WI.WidgetLabel)
                                        self.dic_widget_list_txt[texts_widget.tab_title][0].append(txt)
                                else :
					WI = Viewer.TexteWidgetItem(txt.getResume())
                                        texts_widget.show_texts_anticorpus.addItem(WI.Widget)
                                        texts_widget.show_texts_anticorpus.setItemWidget(WI.Widget,WI.WidgetLabel)
                                        self.dic_widget_list_txt[texts_widget.tab_title][1].append(txt)

                
                        texts_widget.show_texts_corpus.itemSelectionChanged.connect(self.onSelectText) 
                        texts_widget.show_texts_anticorpus.itemSelectionChanged.connect(self.onSelectText)  

                        #si la tab de l'element existe déjà, on efface l'ancienne
                        for i in range(0, self.SOT1.count() ):
                                if (re.search("^%s (\d*)"%element,self.SOT1.tabText(i) ) ):
                                        self.SOT1.removeTab(i)
                                
                        index = self.SOT1.addTab(texts_widget.show_texts_widget,texts_widget.tab_title)
                        self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
                        self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
                        self.SOT1.tabBar().setTabToolTip(index,texts_widget.tab_title)

                        
        def teste_wording(self):
                if ( self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
                        item = self.NOT12_E.currentItem().text()
                if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
                        item = self.NOT22_E.currentItem().text()

                score,item = re.search("^(\d*) (.*)",item).group(1,2)
                self.activity(u"%s double click" % (item))
                if (int(score)):
                        ask = "$ph.+%s"%(item)
                        result = self.client.eval_var(ask)
                        
                        
                        tab_utterance = 0
                        for i in range(self.SubWdwNE.count()):
                                if (self.SubWdwNE.tabText(i) == "Utterances"):
                                        tab_utterance = 1
                                        pass

                        if (tab_utterance == 0):
                                self.tabUtterances = QtGui.QTabWidget()
                                self.tabUtterances.setTabsClosable(True)
                                self.tabUtterances.tabCloseRequested.connect(self.tabUtterances.removeTab)
                                self.SubWdwNE.addTab(self.tabUtterances,"Utterances")
                        
                        for i in range(0, self.tabUtterances.count() ):
                                if (self.tabUtterances.tabText(i) == item):
                                        self.tabUtterances.removeTab(i)
                         
                        show_Utterances_widget = QtGui.QWidget()
                        show_Utterances_box = QtGui.QVBoxLayout()
                        # on prend toute la place
                        show_Utterances_box.setContentsMargins(0,0,0,0) 
                        show_Utterances_box.setSpacing(0) 
                        show_Utterances_widget.setLayout(show_Utterances_box)
                        index = self.tabUtterances.addTab(show_Utterances_widget,"%s" % item)

                        Utterance_Text = QtGui.QTextEdit() 
                        show_Utterances_box.addWidget(Utterance_Text)
                        Utterance_Text.append(result)


                        self.tabUtterances.setCurrentIndex(index)# donne le focus a l'onglet créé
                        self.SubWdwNE.setCurrentIndex(2)



        def list_lexicon_search(self):
                """recherche un motif dans la liste gauche du type de lexicon selectionné"""
                motif = self.list_research.text()
                if (motif != ""):
                        if (self.detect_lexicon[0] != motif or len(self.detect_lexicon) == 1):
                                self.activity(u"searching for %s" % (motif))
                                self.detect_lexicon = filter(lambda m : re.search(motif,m),self.content_liste_lexicon)
                                self.detect_lexicon.insert(0, motif)
                        if len(self.detect_lexicon) > 1:
                                elt  = self.detect_lexicon.pop(1)
                                row =  self.content_liste_lexicon.index(elt)
                                self.NOT12.setCurrentRow(row)

        def list_concept_search(self):
                """recherche un motif dans la liste gauche du type de concept selectionné"""
                motif = self.concept_research.text()
                if (motif != ""):
                        if (self.detect_concepts[0] != motif or len(self.detect_concepts) == 1):
                                self.activity(u"searching for %s" % (motif))
                                self.detect_concepts = filter(lambda m : re.search(motif,m),self.content_liste_concept)
                                self.detect_concepts.insert(0, motif)
                        if len(self.detect_concepts) > 1:
                                elt  = self.detect_concepts.pop(1)
                                row =  self.content_liste_concept.index(elt)
                                self.NOT22.setCurrentRow(row)

        def Explorer(self):
                self.Explo_liste.clear()
                motif = self.Explo_saisie.text()
                if (motif != ""):
                        if (self.Explo_radioGroup.checkedId() == 0):
                                type_search = u"$search.pre"
                        elif (self.Explo_radioGroup.checkedId() == 1):
                                type_search = u"$search.suf"
                        elif (self.Explo_radioGroup.checkedId() == 2):
                                type_search = u"$search.rac"

                        ask = self.client.creer_msg_search(type_search,motif,"[0:]") #la liste des match
                        result = self.client.eval( ask )
                        if (result != u''):
                                liste_result = re.split(", ", result)
                                self.activity("searching for {%s} %d results"%(motif,len(liste_result)))
				self.PrgBar.perc(len(liste_result))
                                for i in range(len(liste_result)):
                                        ask = self.client.creer_msg_search(type_search,motif,"%d"%i,val=True) #la valeur du match
#TODO get_sem, liste textes, énoncés
#TODO select all
                                        r = self.client.eval( ask )
                                        self.PrgBar.percAdd(1)
                                        self.Explo_liste.addItem("%s %s"% (r,liste_result[i]))
                        else :
                                result = re.split(", ", self.activity("searching for {%s} : 0 result" % motif))
                                

        
        def contexts_contents(self):
                self.NOT5_cont.clear()
                if (self.NOT5_list.currentItem()):
                        champ = self.NOT5_list.currentItem().text()
                        #print [champ]
                        result = self.client.eval_var(u"$ctx.%s[0:]" % champ)
                        result = re.split("(?<!\\\), ",result )#negative lookbehind assertion
                        #print [result]
                        dic_CTX = {}
                        for r in result:
                                if r in dic_CTX.keys():
                                        dic_CTX[r] = dic_CTX[r] + 1
                                else:
                                        dic_CTX[r] = 1
                        for el in sorted(dic_CTX.items(), key= lambda (k,v) : (-v,k)):
                                self.NOT5_cont.addItem(u"%d %s"%(el[1],re.sub("\\\,",",",el[0])))


        def recup_texts(self):
                txts = self.client.eval_var("$txt[0:]")
                return re.split(", ",txts)

        
        def genere_identify(self):
                phrase = self.gen_mrlw_phrase.toPlainText()
                if  (phrase != u''):
                        self.gen_mrlw_vars.clear()
                        phrase = re.sub('[\r\n]',' ',phrase)
                        self.gen_mrlw_vars.append(self.genere_mrlw.get_vars_sentence(phrase))

        def genere_test(self):
                mot = self.gen_mrlw_test.text()
                self.gen_mrlw_test_result.clear()       
                recup = []
                if (mot != u""):
                        if re.search("^\s*/Var\S{1,}", mot):
                                mot = re.sub("^\s*","",mot)
                                mot = re.sub("\s{1,}$","",mot)
                                if mot[1:] in self.genere_mrlw.mrlw_vars.keys():
                                        recup = self.genere_mrlw.mrlw_vars[mot[1:]]
                                        self.gen_mrlw_test_result.addItems(recup)
                        else :
                                mot = re.sub("^\s*","",mot)
                                mot = re.sub("\s{1,}$","",mot)
                                recup = self.genere_mrlw.repere_vars2(mot)
                                for i in recup:
                                        self.gen_mrlw_test_result.addItem("/%s"%i[1])
                                

        def genere_generate(self):
                phrase = self.gen_mrlw_vars.toPlainText()
                if  (phrase != u''):
                        for i in range( self.gen_genere_spinbox.value()):
                                self.gen_mrlw_result.append(self.genere_mrlw.genere_phrase(phrase))
                
        
        def genere_test_result_dc(self):
                self.gen_mrlw_test.clear()
                self.gen_mrlw_test.setText(  self.gen_mrlw_test_result.currentItem().text() )
                self.genere_test()
                
                                
        def maj_metadatas(self):
                string_ctx =    self.client.eval_var("$ctx")
                #self.client.add_cache_var(sem_txt +".ctx."+field,val)
                current  =  self.NOT5_list.currentItem() 
                self.NOT5_cont.clear()
                if (current):
                        self.NOT5_list.setCurrentItem(current)
                        self.contexts_contents()
        
        def copy_to_cb(self):
                debut  =  self.NOT12.currentRow()
                fin  = self.NOT12.count()
                liste = []
                if (fin):
                        for row in range( 0, fin):
                                element = re.sub("^(\d{1,}) (.*)$", "\\2\t\\1", self.NOT12.item(row).text() , 1) #on inverse pour excel
                                liste.append(element )
                        clipboard = QtGui.QApplication.clipboard()
                        clipboard.setText("\n".join(liste))
                        self.activity(u"%d elements copied to clipboard" % (len(liste) ) )



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
		server_path = "./prospero-server"
		port = 60000
                commande = "%s -e -p %s -f %s" % (server_path,port,PRC)
		print commande
                local_server = subprocess.Popen(commande, shell=True)
		time.sleep(5)
		self.connect_server("localhost",port)
		atexit.register(local_server.terminate) #kill the server when the gui is closed
			

class codex_window(QtGui.QWidget):
        def __init__(self, parent=None):
                super(codex_window, self).__init__(parent,QtCore.Qt.Window)
                self.codex_dic = Model.edit_codex()
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
                h22_spacer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
                h22Buttons.addWidget(h22_spacer)
                h22gen = QtGui.QPushButton()
              	h22gen.setIcon(QtGui.QIcon("images/gear.png"))
		h22gen.setToolTip(u"test file names")
                h22Buttons.addWidget(h22gen)
                QtCore.QObject.connect(h22gen, QtCore.SIGNAL("clicked()"), self.generate)

                self.h22liste = Viewer.ListViewDrop(self)
                self.h22liste.fileDropped.connect(self.FilesDropped)
                h22.addWidget(self.h22liste)
                self.h22liste.setSizePolicy( QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

                self.h22liste.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_h22listeItem = QtGui.QAction('delete item',self)
                self.h22liste.addAction(efface_h22listeItem)
                QtCore.QObject.connect(efface_h22listeItem, QtCore.SIGNAL("triggered()"), self.efface_h22listeItem)
                efface_h22liste = QtGui.QAction('clear list',self)
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
                self.h23BT.stateChanged.connect( self.generate )
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

                self.search_line.setSizePolicy( QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
                self.search_result.setSizePolicy( QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

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
                self.listRad.setSizePolicy( QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
                self.listRad.doubleClicked.connect(self.mod_listRadItem)
                self.listRad.currentItemChanged.connect(self.changeRad)
                self.listRad.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_listRadItem = QtGui.QAction('delete item',self)
                self.listRad.addAction(efface_listRadItem)
                QtCore.QObject.connect(efface_listRadItem, QtCore.SIGNAL("triggered()"), self.efface_listRadItem)
                add_listRadItem = QtGui.QAction('add item',self)
                self.listRad.addAction(add_listRadItem)
                QtCore.QObject.connect(add_listRadItem, QtCore.SIGNAL("triggered()"), self.add_listRadItem)
                self.listRad.setItemDelegate(Viewer.MyDelegate(self))
                self.listRad.itemDelegate().closedSignal.connect(self.mod_listRadItem_done)


                self.initiate()


                h13 = QtGui.QVBoxLayout()
                H1.addLayout(h13)
                self.h13List = QtGui.QTableWidget()
                self.h13List.setColumnCount(2)
                self.h13List.setHorizontalHeaderLabels([u'field',u'value'])
                self.h13List.horizontalHeader().setStretchLastSection(True)     
                self.h13List.verticalHeader().setVisible(False)
                h13.addWidget(self.h13List)

                self.h13List.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                efface_listRadValueItem = QtGui.QAction('delete line',self)
                self.h13List.addAction(efface_listRadValueItem)
                QtCore.QObject.connect(efface_listRadValueItem, QtCore.SIGNAL("triggered()"), self.efface_listRadValueItem)
                add_listRadValueItem = QtGui.QAction('add line',self)
                self.h13List.addAction(add_listRadValueItem)
                QtCore.QObject.connect(add_listRadValueItem, QtCore.SIGNAL("triggered()"), self.add_listRadValueItem)
                copy_h13listLine = QtGui.QAction('copy line',self)
                self.h13List.addAction(copy_h13listLine)
                QtCore.QObject.connect(copy_h13listLine, QtCore.SIGNAL("triggered()"), self.copy_h13listLine)
                paste_h13listLine = QtGui.QAction('paste line',self)
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
                        self.select_champ.addItems( self.codex_dic.champs() )
                self.search_line.clear()
                self.search_result.clear()
                

        def efface_listRadItem(self):
                item = self.listRad.currentItem().text()
                del(self.codex_dic.dico[item])
                row = self.listRad.currentRow()
                self.listRad.takeItem(row)

        def add_listRadItem(self):
                item = QtGui.QListWidgetItem("")
                self.listRad.insertItem(self.listRad.count(),item)
                self.listRad.setCurrentItem(item)
                self.mod_listRadItem()

        def mod_listRadItem(self):
                item = self.listRad.currentItem()
                        
                item.setFlags(self.listRad.currentItem().flags() | QtCore.Qt.ItemIsEditable)
                #item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
                self.listRadItemText = item.text()
                if (self.listRad.state() !=  self.listRad.EditingState ):
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
                                        self.codex_dic.dico[new] =  { u"author" : "", u"medium"  : "", u"media-type" : "" , u"authorship" : "", u"localisation" : "", u"observations" : "" } 
                                        self.changeRad()
                                else :
                                        self.codex_dic.dico[new] =  self.codex_dic.dico[old]
                                        del( self.codex_dic.dico[old])
                                self.listRad.sortItems()
                                self.listRad.scrollToItem(item)


        def efface_listRadValueItem(self):
                if self.h13List.selectedItems() :
                        row = self.h13List.currentRow()
                        k = self.listRad.currentItem().text()
                        f = self.h13List.item(row,0).text()
                        del(self.codex_dic.dico[k][f])
                        self.h13List.removeRow(row)

        def add_listRadValueItem(self):
                self.h13List.insertRow(0)
        
        def copy_h13listLine(self):
                r = self.h13List.currentRow()
                if  self.h13List.currentItem():
                        self.copy_h13listLineContent = [self.h13List.item(r,0).text(),self.h13List.item(r,1).text()]

        def paste_h13listLine(self):
                if hasattr(self,"copy_h13listLineContent"):
                        self.h13List.cellChanged.disconnect(self.onChangeh13List)
                        field,value = self.copy_h13listLineContent
                        k = self.listRad.currentItem().text()
                        row = -1
                        for r in range(self.h13List.rowCount()):
                                if (self.h13List.item(r,0)):
                                        if field == self.h13List.item(r,0).text() :
                                                row = r
                        if (row > -1):
                                self.h13List.item(row,1).setText(value)
                        else :
                                self.h13List.insertRow(r+1)
                                self.h13List.setItem(r+1,0, QtGui.QTableWidgetItem(field))
                                self.h13List.setItem(r+1,1, QtGui.QTableWidgetItem(value))
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
                self.h13List.setHorizontalHeaderLabels([u'field',u'value'])
                RAD = self.listRad.currentItem().text() 
                if (RAD == ""):
                        fields = {}
                elif RAD in self.codex_dic.dico.keys():
                        fields = self.codex_dic.dico[RAD].keys()
                self.h13List.setRowCount(len(fields))
                r = 0
                for field in fields:
                        i_field = QtGui.QTableWidgetItem(field)
                        self.h13List.setItem(r,0,i_field)
                        v_field = QtGui.QTableWidgetItem(self.codex_dic.dico[RAD][field])
                        self.h13List.setItem(r,1,v_field)
                        r += 1
                self.h13List.resizeColumnToContents (0)

        def onChangeh13List(self):
                r = self.h13List.currentRow()
                c = self.h13List.currentColumn()
                if ( (r != -1) and (c != -1 )):
                        k = self.listRad.currentItem().text()
                        f = self.h13List.item(r,0).text()
                        if (not re.match("^\s*$",f)) :
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
                                        self.h13List.item(r,0).setText (oldfield)
                        self.h13List.resizeColumnToContents (0)
                                
        def oldfield(self,k):                   
                listefield = []
                for row in range(self.h13List.rowCount()):
                        listefield.append(self.h13List.item(row,0).text())
                L = list(set(self.codex_dic.dico[k].keys()) - set(listefield))
                if len(L):
                        return L[0]
                else :
                        return False
                

        def FilesDropped(self, l):
                existing = [] 
                for r in range( self.h22liste.count()):
                        existing.append( self.h22liste.item(r).text())
                for url in list(set(l) - set(existing)):
			if os.path.splitext(url)[1] in ['.txt','.TXT']:
				item = QtGui.QListWidgetItem(url, self.h22liste)
				item.setStatusTip(url)
				self.h22Label.setText(u"%s texts"% self.h22liste.count())
				QtGui.QApplication.processEvents()
		self.h22liste.sortItems()
		"""
                        if os.path.exists(url):
                                if os.path.splitext(url)[1] in ['.txt','.TXT']:
                                        item = QtGui.QListWidgetItem(url, self.h22liste)
                                        item.setStatusTip(url)
					self.h22Label.setText(u"%s texts"% self.h22liste.count())
					QtGui.QApplication.processEvents()
                        self.h22liste.sortItems()
                self.generate()
		"""

	def appendItems(self,liste):
		self.h22liste.clear()
		self.h22liste.addItems(liste)
		self.h22Label.setText(u"%s texts"% self.h22liste.count())
		self.h22liste.sortItems()
		
	
        def eval_search_line(self):
                self.search_result.clear()
                pattern = self.search_line.text()
                field = self.select_champ.currentText()
                result = self.codex_dic.chercheValue(field,pattern)
                for r in result:
                        self.search_result.addItem( " : ".join(r))
                self.search_result.sortItems()
                
        def eval_search_C(self):
                item = self.search_result.currentItem()
                if (item):
                        i = item.text()
                        i = re.split(" : ",i,1)[0]
                        item = self.listRad.findItems(i,QtCore.Qt.MatchFlags(QtCore.Qt.MatchExactly))
                        self.listRad.setCurrentItem(item[0])

        def generate(self):
                self.CTX_to_be_saved = {}
                self.h23liste.clear()
                self.h23liste.setRowCount(0)
                self.h23liste.setColumnCount(2)
                if self.h23BT.checkState():
                        self.h23liste.setHorizontalHeaderLabels([u'path',u'key,  date and title'])
                else :
                        self.h23liste.setHorizontalHeaderLabels([u'path',u'key and date'])
                self.h23liste.horizontalHeader().setStretchLastSection(True)    
                m = 0
                f = 0
                for r in range(self.h22liste.count()):
                        path = self.h22liste.item(r).text()
                        test = self.codex_dic.eval_file( path  )
                        if (test):
                                self.match_add(path,test)
                                m += 1
                        else :
                                self.failed_add(path)
                                f += 1
			self.h23Label.setText("%d matches, %d fails" % (m,f))
			QtGui.QApplication.processEvents()
                self.h23liste.resizeColumnToContents (0)
                self.h23liste.sortItems(1)
        
        def match_add(self,path,result):
                r = self.h23liste.rowCount()
                self.h23liste.insertRow(r)
                item_path = QtGui.QTableWidgetItem(path)                
                self.h23liste.setItem(r,0,item_path)

                CTXpath = path[:-3] + "ctx"
                self.CTX_to_be_saved[CTXpath] = self.codex_dic.dico[result[0]].copy()
                self.CTX_to_be_saved[CTXpath]["date"] = result[1] + " 00:00:00"

                if self.h23BT.checkState():
                        title = self.get_title(path)
                        item_value_txt = u" ".join(result) + u" %s"% title
                        self.CTX_to_be_saved[CTXpath][u"title"] = title
                else :
                        item_value_txt = u" ".join(result) 
                item_value = QtGui.QTableWidgetItem(item_value_txt)
                self.h23liste.setItem(r,1,item_value)
                data = ""
                for k,v in self.codex_dic.dico[result[0]].iteritems():
                        data += "%s:%s\n"%(k,v)
                item_path.setToolTip(data[:-1])
                item_value.setToolTip(data[:-1])

        def get_title(self,path):
                B = open(path,"rU").readlines()
                title = B[0][:-1]
                try :
                        return title.decode('latin-1')
                except :
                        return title.decode('utf-8')

        def failed_add(self,path):
                r = self.h23liste.rowCount()
                self.h23liste.insertRow(r)
                item_path = QtGui.QTableWidgetItem(path)                
                item_path.setForeground(QtGui.QColor("red" ))
                self.h23liste.setItem(r,0,item_path)
                item_value = QtGui.QTableWidgetItem(u"\u00A0 no match")
                item_value.setForeground(QtGui.QColor("red" ))
                self.h23liste.setItem(r,1,item_value)
                item_path.setToolTip("no match")
                item_value.setToolTip("no match")

        def merge_codex(self):
                fname, filt = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.', '*.cfg;*.publi;*.xml')
                if ( fname) :
                        m_codex = Model.edit_codex()
                        if os.path.splitext(fname)[1]  == ".publi":
                                m_codex.parse_supports_publi(fname)
                        elif os.path.splitext(fname)[1]  == ".cfg": 
                                m_codex.parse_codex_cfg(fname)
                        elif os.path.splitext(fname)[1]  == ".xml": 
                                m_codex.parse_codex_xml(fname)
                        self.codex_dic.dico, fails = m_codex.fusionne(self.codex_dic.dico,m_codex.dico)
                        self.initiate() 
                        self.h14MergeList.clear()
                        for k, v in fails.iteritems():
                                self.h14MergeList.addItem("%s : %s"%(k,str(v)))
                        self.h14LabelNum.setText("%d fails" % len(fails))

        def saveCTX(self):
                if hasattr(self,"CTX_to_be_saved"):
                        for path,v in self.CTX_to_be_saved.iteritems():
                                if  not (os.path.isfile(path) and not self.h23BR.checkState())   :
                                        CTX = Model.parseCTX()
                                        CTX.path = path
                                        CTX.dico = v    
                                        CTX.savefile()



        
def main():
        app = QtGui.QApplication(sys.argv)

        translator = QtCore.QTranslator()
        #self.translator.load('translations/en_GB') 
        #translator.load('translations/fr_FR') 
        translator.load('translations/'+ QtCore.QLocale.system().name())
        app.installTranslator(translator)

        ex  = Principal()
        #ex.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
        main()
