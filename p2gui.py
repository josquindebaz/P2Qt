#!/usr/bin/python
# -*- coding: utf-8 -*-


#TODO internationalisation QTranslator

import sys
import PySide
from PySide import QtCore 
from PySide import QtGui 

import interface_prospero
import re
import datetime
import subprocess, threading
from PySide.QtGui import QMdiArea



class client(object):
	def __init__(self,h = 'prosperologie.org',p = '60000'):
		self.c = interface_prospero.ConnecteurPII() 
		self.c.set(h,p)
		self.teste_connect()
		self.liste_champs_ctx =[]	# init by pre_calcule()

	def teste_connect(self):
		teste = self.c.connect()
		if (teste):
			self.Etat = True
		else :
			self.Etat = False

	def disconnect(self):
		self.c.disconnect()

	def recup_liste_concept(self,sem):
		var = "%s[0:]" % sem
		return re.split(", ",self.c.eval_variable(var))
	
	def recup_texts(self):
		txts = self.c.eval_variable("$txt[0:]")
		self.txts = re.split(", ",txts)

	def eval_vector(self,type, type_calc):
		return self.c.eval_vect_values(type, type_calc)


	def eval_var(self,var):
		self.eval_var_result = self.c.eval_variable(var)
		
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
	


class Principal(QtGui.QMainWindow):
	def __init__(self):
		super(Principal, self).__init__()
		self.initUI()

		
		
	def pre_calcule(self):
		'''
			généralisation de l'accès aux props des ctx
			
			avec eval_var("$ctx") on récupère la liste des noms des champs ctx
			qq ajustements sont à faire pour mettre en cache 
				$txtX.titre_txt   à partir de title
				$txtX.date_txt   à partir de date
				
		'''
		self.client.recup_texts()
		listeTextes = self.client.txts
		indice = 0
		
		
		nbre_txt = len (listeTextes)
		# mise en cache  valeur - semtxt
		for text in listeTextes :
			sem = u"$txt%s"%indice
			txt_name = listeTextes[indice]
			cle = txt_name + u"$txt"
			self.client.add_cache_fonct(cle, sem )
			indice +=1
			
		# récupération des champs ctx
		self.client.eval_var("$ctx")
		string_ctx = self.client.eval_var_result 
		
		
		
		
		# les virgules contenues dans les titres ont été remplacées par \,
		# la manip suivante permet de remplacer dans un premier temps les \,par un TAG
		# ensuite de créer la liste, puis de remettre les virgules à la place des \,
		TAG="AZETYT"	# on peut mettre presque n'importe quoi ...
		
		
		string_ctx = string_ctx.replace ('\,', TAG )
		liste_ctx = string_ctx.split(',')
		self.liste_champs_ctx = []
		for champ_ctx in liste_ctx:
			champ_ctx = champ_ctx.strip()
			if champ_ctx.find (TAG) != -1 :
				champ_ctx = champ_ctx.replace(TAG,',')
			self.liste_champs_ctx.append ( champ_ctx)		
		
		liste_champs_ajuste = []
		for champ in self.liste_champs_ctx :
			 #title[0\]  date[0:]  etc on ne met pas le $ctx  ici...
			 
			string_ctx = self.client.eval_var_ctx("%s"%champ,"[0:]") 
			string_ctx = string_ctx.replace ('\,', TAG )
			liste_data_ctx = string_ctx.split(',')	
			liste_data_ok_ctx =[]	
			for data in liste_data_ctx :
				if data.find(TAG) != -1:
					data = data.replace(TAG,',')
				liste_data_ok_ctx.append ( data)
			indice = 0
			if len (liste_data_ok_ctx) != nbre_txt :
				print "problemo qq part les listes doivent avoir le même nbre d'éléments"
			if champ == "title" :
				champ = u"titre_txt"
			if champ == "date" :
				champ = u"date_txt"
			if champ == "author" :
				champ = u"auteur_txt"
				
			liste_champs_ajuste.append (champ)
			for text in listeTextes :
				sem = u"$txt%s"%indice
				data = liste_data_ok_ctx[indice]
				self.client.add_cache_var( sem + ".%s"%champ, data)
				indice +=1	
		# on se sert de la liste des champs dans l'onglet CTX			
		self.liste_champs_ctx = liste_champs_ajuste	
		
		# précalcule de valeurs associées 
		
		for type_calcul in ["freq","dep", "nbaut", "nbtxt","lapp","fapp"]:
			L = self.client.eval_vector("$ent", type_calcul)
			L = L.split(',')	 
			if (type_calcul == "freq"):
				t_calc = "val"
			else:
				t_calc = type_calcul
			indice = 0
			for val in L :
				self.client.add_cache_var ("$ent%s.%s"%(str(indice),t_calc),val)
				indice+=1
			
			
		'''
		v = c.eval_vect_values("$ent", "nbaut")
		v = c.eval_vect_values("$ent", "nbtxt")
		v = c.eval_vect_values("$ent", "lapp")
		v = c.eval_vect_values("$ent", "fapp")
		v = c.eval_vect_values("$ent", "dep")
		v = c.eval_vect_values("$ent", "freq")
		'''
	
	def initUI(self):


		# create the menu bar
		#menubar = self.menuBar()
#		ParamMenu = menubar.addMenu('&Parameter')
# parametrage du Gui : langue etc
#		ConstelMenu = menubar.addMenu('&Constellation')
#		HelpMenu = menubar.addMenu('&Help')

		# create the status bar
		self.status = self.statusBar()
		self.status.showMessage(u"Ready")
	
		# create the toolbar
		toolbar = self.addToolBar("toolbar")	
		toolbar.setIconSize(QtCore.QSize(16, 16))
		toolbar.setMovable( 0 )

		#Saction = QtGui.QAction(QtGui.QIcon('Prospero-II.png'), 'Server', self)
		#toolbar.addAction(Saction)

		list1 = QtGui.QComboBox()
		#list1.addItem(u"Reference corpus")
#		list1.addItem(u"auteur : AFP")
		toolbar.addWidget(list1)

		spacer1 = QtGui.QLabel()
		spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		toolbar.addWidget(spacer1)
		
		etat1 = QtGui.QLabel()
#		etat1.setText("234 textes 5,44 pages volume 234")
		toolbar.addWidget(etat1)
		
		spacer2 = QtGui.QLabel()
		spacer2.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		toolbar.addWidget(spacer2)

		etat2 = QtGui.QLabel()
#		etat2.setText("/Users/gspr/corpus/Alarm and Controversies/AaC.prc")
		toolbar.addWidget(etat2)


##################################################
		#quart SE
##################################################


	# onglet proprietes du texte
		self.textProperties = QtGui.QTabWidget()
	# sous onglet proprietes saillantes
		saillantes = QtGui.QWidget()
		self.textProperties.addTab(saillantes,"Sailent structures")
	
	# une box horizontale pour contenir les 3 listes
		saillantesH = QtGui.QHBoxLayout()
		saillantes.setLayout(saillantesH)
		saillantesH.setContentsMargins(0,0,0,0) 
		saillantesH.setSpacing(0) 

	#Vbox des actants du texte
		saillantesVAct = QtGui.QVBoxLayout()
		saillantesActTitle = QtGui.QLabel()
		saillantesActTitle.setText("Actants")
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

	#Vbox des collections du texte
		saillantesVCol = QtGui.QVBoxLayout()
		saillantesColTitle = QtGui.QLabel()
		saillantesColTitle.setText("Collections")
		saillantesVCol.addWidget(saillantesColTitle)
		self.saillantesCol = QtGui.QListWidget()
		saillantesVCol.addWidget(self.saillantesCol)
		saillantesH.addLayout(saillantesVCol)


#		SET1.addTab(SET12,u"Apports et reprises")
#		SET1.addTab(SET13,u"Eléments du texte")
#		SET1.addTab(SET14,u"Textes proches")
#		SET1.addTab(SET15,u"Textes identiques")



	# onglet contenu du CTX
		self.textCTX = QtGui.QListWidget()	
		self.textCTX.currentItemChanged.connect(self.onSelectChampCtx) 

	# onglet contenu du texte
		self.textContent = QtGui.QTextEdit() 


		SubWdwSE = QtGui.QTabWidget()
		SubWdwSE.addTab(self.textProperties,"Properties")
		SubWdwSE.addTab(self.textCTX,"Context")
		SubWdwSE.addTab(self.textContent,"Text")


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
		#self.CorpusTexts.itemClicked.connect(self.onSelectTextFromCorpus) #ne fonctionne pas avec le clavier
		self.CorpusTexts.currentItemChanged.connect(self.onSelectTextFromCorpus) #fonctionne avec clavier et souris, mais selectionne le 1er texte au chargement
		
		#l'onglet des réseaux
		#self.tabNetworks = QtGui.QTabWidget()
		#self.tabNetworks.setTabsClosable(True)
		#self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

#TODO les expressions englobantes

		#mise en place des onglets

		self.SubWdwSO.addTab(self.SOT1,"Texts")
		#self.SubWdwSO.addTab(self.tabNetworks,"Networks")


##################################################
		#quart NE
##################################################


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
		#Param_Server_I.setPixmap(QtGui.QPixmap('Prospero-II.png'))
		#Param_Server_V.addWidget(Param_Server_I)

#configurer les parametres de connexion au serveur distant
		self.Param_Server_val_host = QtGui.QLineEdit()
		Param_Server_R.addRow("&host",self.Param_Server_val_host)
		self.Param_Server_val_host.setText('prosperologie.org')#prosperologie.org
		self.Param_Server_val_port = QtGui.QLineEdit()
		Param_Server_R.addRow("&port",self.Param_Server_val_port)
		self.Param_Server_val_port.setText('60000')
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
#		viewImage = QtGui.QPixmap("viewer.png")
#		T4.setPixmap(viewImage)



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

#mise en place des onglets
		self.SubWdwNE = QtGui.QTabWidget()
#		self.SubWdwNE.setTabsClosable(True)
#		self.SubWdwNE.tabCloseRequested.connect(self.SubWdwNE.removeTab)

#		SubWdwNE.addTab(T4,"Viewer")
#		SubWdwNE.addTab(NET1,"Marlowe")
		self.History_index = self.SubWdwNE.addTab(self.History,"History")
		self.SubWdwNE.addTab(server_vars,"Vars")
		self.SubWdwNE.addTab(Param_Server,"Server")

# on donne le focus à la connection au serveur
		self.SubWdwNE.setCurrentIndex(2)

		# on fait disparaître le bouton close des tabs, a gauche pour les mac
#		if self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.RightSide):
#			self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.RightSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.RightSide).hide()
#		elif self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.LeftSide):
#			self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).hide()
#		if self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.RightSide):
#			self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.RightSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.RightSide).hide()
#		elif self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.LeftSide):
#			self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.LeftSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(1, QtGui.QTabBar.LeftSide).hide()
#		if self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.RightSide):
#			self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.RightSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.RightSide).hide()
#		elif self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.LeftSide):
#			self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.LeftSide).resize(0,0)
#			self.SubWdwNE.tabBar().tabButton(2, QtGui.QTabBar.LeftSide).hide()






##################################################
	#quart NO
##################################################

		SubWdwNO =  QtGui.QTabWidget()
		

##### L'onglet des listes
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
		self.NOT1select.addItem(u"collections")
		self.NOT1select.addItem(u"fictions")
		self.NOT1select.addItem(u"entitie's categories")
		NOT1VHC.addWidget(self.NOT1select)
		self.connect(self.NOT1select,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.select_liste)



	# un spacer pour mettre les commandes sur la droite
		spacer3 = QtGui.QLabel()
		spacer3.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
		NOT1VHC.addWidget(spacer3)

	#le champ de recherche
		self.list_research = QtGui.QLineEdit()
		NOT1VHC.addWidget(self.list_research)



##pquoi ici le popup de CTX ???
	# essai popup
		self.popupCtx = QtGui.QMenu(self)
		self.popupCtx.addMenu('modifier')
	# les commandes
		self.NOT1Commands1 = QtGui.QPushButton()
		self.NOT1Commands1.setText(u"\u2195")
		#self.NOT1Commands1.setIcon(QtGui.QIcon("loupe.png"))
		self.NOT1Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
		NOT1Commands1Menu = QtGui.QMenu(self)
		#NOT1Commands1Menu.addAction('&search')
		#submenu_sort = QtGui.QMenu('&sort')
		#NOT1Commands1Menu.addMenu(submenu_sort)
		self.menu_occurences = NOT1Commands1Menu.addAction('occurences',self.affiche_liste_scores_oc)
		self.menu_deployement = NOT1Commands1Menu.addAction('deployement',self.affiche_liste_scores_dep)
#TODO ajouter pondere, nb textes, nb auteurs, nb jours presents, relatif nb jours, nb representants, nb elements reseau
		#NOT1Commands1Menu.addAction('&sort')
		#NOT1Commands1Menu.addAction('&filter')
		self.NOT1Commands1.setMenu(NOT1Commands1Menu)
		NOT1VHC.addWidget(self.NOT1Commands1)


		self.NOT1Commands2 = QtGui.QPushButton()
		self.NOT1Commands2.setIcon(QtGui.QIcon("gear.png"))
		self.NOT1Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
		NOT1Commands2Menu = QtGui.QMenu(self)
		NOT1Commands2Menu.addAction('network' , self.show_network)
		NOT1Commands2Menu.addAction('texts' , self.show_texts)
		self.NOT1Commands2.setMenu(NOT1Commands2Menu)
		NOT1VHC.addWidget(self.NOT1Commands2)


#TODO ajouter un déselect
	#une box horizontale pour liste, score et deploiement
		NOT1VH = QtGui.QHBoxLayout()
		NOT1V.addLayout(NOT1VH) 
	#la liste
		self.NOT12 = QtGui.QListWidget()
		self.NOT12.setAlternatingRowColors(True)
		self.NOT12.currentItemChanged.connect(self.liste_item_changed) #changement d'un item
		NOT1VH.addWidget(self.NOT12)
	#le deploiement
		self.NOT12_D = QtGui.QListWidget()
		NOT1VH.addWidget(self.NOT12_D)
		self.NOT12_D.currentItemChanged.connect(self.liste_D_item_changed) #changement d'un item
	#le deploiement II
		self.NOT12_E = QtGui.QListWidget()
		NOT1VH.addWidget(self.NOT12_E)
		self.NOT12_E.currentItemChanged.connect(self.liste_E_item_changed) #changement d'un item
#TODO desactiver si presence nulle
		self.NOT12_E.doubleClicked.connect(self.teste_wording)


		#NOT2 =  QtGui.QLabel()
#		FrmlImage = QtGui.QPixmap("formul.png")
#		NOT2.setPixmap(FrmlImage)

		#NOT3 =  QtGui.QLabel()
#		ExploImage = QtGui.QPixmap("explo.png")
#		NOT3.setPixmap(ExploImage)



		SubWdwNO.addTab(NOT1,"Lists")
#		SubWdwNO.addTab(NOT2,"Formulae")
#		SubWdwNO.addTab(NOT3,"Explorer")

################################################
################################################
		### layout qui supprime le bug de rotation des cadrans mais qui genere des problemes de taille d'affichage sur chaque cadran
		# 1 layout vertical dans lequel sont insérés 2 layout horizontals
#		main = QtGui.QWidget()
#		h1_layout = QtGui.QVBoxLayout()
#		vl1_layout = QtGui.QHBoxLayout()
#		vl2_layout =QtGui.QHBoxLayout()
#		
#		h1_layout.addLayout(vl1_layout)
#		h1_layout.addLayout(vl2_layout)
#		
#		vl1_layout.addWidget(SubWdwNO)
#		vl1_layout.addWidget(self.SubWdwNE)
#		
#		vl2_layout.addWidget(self.SubWdwSO)
#		vl2_layout.addWidget(SubWdwSE)
#		
#		main.setLayout(h1_layout)
#		self.setCentralWidget(main)
################################################
################################################
#               voir avec des splitters sinon
################################################
################################################
		###tentative avec une mdiarea, mais les tiles jouent au taquin a chaque resize/deplacement de la fenetre principale
		#la MdiArea 
#		Area = QtGui.QMdiArea()
#		Area.tileSubWindows()
#		#Area.AreaOption(QMdiArea.DontMaximizeSubWindowOnActivation)
#		self.setCentralWidget(Area)
#		
#		sw1 = Area.addSubWindow(SubWdwSE, flags = QtCore.Qt.FramelessWindowHint)
#		sw2 = Area.addSubWindow(self.SubWdwSO, flags = QtCore.Qt.FramelessWindowHint)
#		sw3 = Area.addSubWindow(self.SubWdwNE , flags = QtCore.Qt.FramelessWindowHint)
#		sw4 = Area.addSubWindow(SubWdwNO , flags = QtCore.Qt.FramelessWindowHint)
#
#		
#		self.show() 
#		self.showMaximized() #à appeler après show pour que ça marche sous windows!
#		Area.setFixedSize( Area.size()) #preserver l'ordre des subwindows en cas de resize -> les subwindows ne sont pas max sous linux
		
################################################
################################################
#TODO corriger resize des grids sur petits ecrans
		###Layout en grid
		main = QtGui.QWidget()
		grid = QtGui.QGridLayout()
		grid.addWidget(SubWdwNO,0,0)
		grid.addWidget(self.SubWdwNE,0,1)
		grid.addWidget(self.SubWdwSO,1,0)
		grid.addWidget(SubWdwSE,1,1)
		main.setLayout(grid)
		self.setCentralWidget(main)

		self.setWindowTitle(u'Prospéro interface')
		self.show() 
		



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


	def get_semantique(self):
		if (self.NOT1select.currentText()=="entities") : 
			return '$ent'
		elif (self.NOT1select.currentText()=="collections") : 
			return '$col'
		elif ( self.NOT1select.currentText()=="fictions" ) : 
			return '$ef'
		elif (self.NOT1select.currentText()=="entitie's categories") : 
			return '$cat_ent'
		else : 
			return False

	def activity(self,message):
		"""Add message to the history window"""
		self.status.showMessage(message)
		time = u"%s" % datetime.datetime.now()
		self.History.append("%s %s" % (time[:19],message))


	def recup_liste_textes(self):
		"""display texts for the corpus"""
		#self.activity(u"Waiting for text list"   )
		self.client.recup_texts()
		self.activity(u"Displaying text list (%d items)" %len(self.client.txts)  )
		self.SOT1.tabBar().setTabText(0,"corpus (%d)"%len(self.client.txts))
		self.CorpusTexts.clear()

		self.liste_txt_corpus = {}
		for T in range(len(self.client.txts)):
			sem_txt = "$txt%d" % T
			self.client.eval_var(u"%s.date_txt" % (sem_txt))
			date = re.sub("^\s*","",self.client.eval_var_result)
			self.client.eval_var(u"%s.auteur_txt" % (sem_txt))
			auteur = re.sub("^\s*","",self.client.eval_var_result)
			self.client.eval_var(u"%s.titre_txt" % (sem_txt))
			titre = re.sub("^\s*","",self.client.eval_var_result)
			self.liste_txt_corpus[self.client.txts[T]] = [date, auteur, titre]
		#ordonne chrono par defaut
		self.liste_txt_ord = []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : v[0]):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			self.CorpusTexts.addItem(txt_resume)
			self.liste_txt_ord.append(T)

	def onSelectTextFromCorpus(self):
		"""When a text is selected from the list of texts for the entire corpus"""
		item_txt = self.liste_txt_ord[self.CorpusTexts.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.onSelectText(self.semantique_txt_item,item_txt)
		self.activity(u"%s (%s) selected " % (item_txt,self.semantique_txt_item)) 

	def onSelectTextFromElement(self):
		"""When a text is selected from the list of texts for a given item"""
		item_txt = self.l_corp_ord[self.show_texts_corpus.currentRow()]
		self.activity(u"%s selected " % (item_txt)) 
		self.onSelectText(u"$txt%d"%self.client.txts.index(item_txt),item_txt)

	def onSelectTextFromAnticorpus(self):
		"""When a text is selected from the list of anticorpus texts for a given item"""
		item_txt = self.l_anticorp_ord[self.show_texts_anticorpus.currentRow()]
		self.activity(u"%s selected " % (item_txt)) 
		self.onSelectText(u"$txt%d"%self.client.txts.index(item_txt),item_txt)


	def onSelectChampCtx(self):	
		'''essais pour modifier un champ ctx
		
		self.m_current_selected_semtext contient le $txtX
		
		# appel pour enregistrer un titre pour un texte ( mettre ensuite à jour le cache local avec le titre)
		# rappel : PII a des noms de champ en anglais par défaut.
		eval_set_ctx(  "$txt1","title","ceci est un titre")
		eval_set_ctx(  "$txt1","date","04/02/2015")
		
		'''
		item_txt = self.textCTX.currentItem().text() 
		
		champ = item_txt.split(':::')[0].strip()
		value  = item_txt.split(':::')[1].strip()
		print champ
		print value
		print self.m_current_selected_semtext
		#P =QtGui.QMouseEvent.globalX()
		#P = PySide.QtGui.QMouseEvent.globalPos()
		#print P
		#self.popupCtx.popup()

	def onSelectText(self,sem_txt,item_txt):
		"""Update text properties windows when a text is selected """
		self.show_textProperties( sem_txt)
		self.show_textCTX(sem_txt) 
		self.show_textContent( sem_txt)

	def getvalueFromSem(self,item_txt,type):	
		sem = self.client.eval_get_sem(item_txt, type )
		val = self.client.eval_var(sem)
		return val

	def select_liste(self,typ):
		""" quand un type de liste est selectionné """
		#self.activity(u"Waiting for  %s list" % (typ)) 
		self.sem_liste_concept = self.get_semantique()
		#content = self.client.recup_liste_concept(self.sem_liste_concept)
		#self.activity(u"Displaying %s list (%d items)" % (typ,len(content)))
		#self.change_liste(content)
		#self.which = None
		if (self.sem_liste_concept in ["$ef","$ent","$cat_ent"]):
			self.affiche_liste_scores_oc()
		elif (self.sem_liste_concept in ["$col"]):
			self.affiche_liste_scores_dep()
		

	def change_liste(self,content):
		self.NOT12.clear()
		self.NOT12_D.clear()
		self.NOT12_E.clear()
		self.NOT12.addItems(content)

	def affiche_liste_scores_oc(self):
		self.which = "occurences"
		self.affiche_liste_scores()
		self.menu_deployement.setIcon(QtGui.QIcon())
		self.menu_deployement.setEnabled(True) 
		self.menu_occurences.setIcon(QtGui.QIcon("Tick.gif"))
		self.menu_occurences.setEnabled(False) 

	def affiche_liste_scores_dep(self):
		self.which = "deployement"
		self.affiche_liste_scores()
		self.menu_occurences.setIcon(QtGui.QIcon())
		self.menu_occurences.setEnabled(True) 
		self.menu_deployement.setIcon(QtGui.QIcon("Tick.gif"))
		self.menu_deployement.setEnabled(False) 

	def affiche_liste_scores(self):
		typ = self.NOT1select.currentText()
		self.sem_liste_concept = self.get_semantique()
		content = self.client.recup_liste_concept(self.sem_liste_concept)
		self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,len(content), self.which))
		liste_valued =[]
		for row  in range(len(content)):
			if (self.which == "occurences"):
				order = "val"
				ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
			elif (self.which == "deployement"):
				order = "dep"
				ask = "%s%d.%s"% ( self.sem_liste_concept, row, order)
			self.client.eval_var( ask )
			try :
				val = int(self.client.eval_var_result)
				if (self.sem_liste_concept == "$ent" and self.which == "deployement" and val == 0):
					val = 1
			except:
				#en cas de non reponse
				print [ask]
				val = 0
			liste_valued.append([val,content[row]])
		liste_final =[]
		for i in sorted(liste_valued,key=lambda x : x[0],reverse = 1):
			item_resume = u"%s %s" % (i[0], i[1])
			liste_final.append(item_resume) 
		self.change_liste(liste_final)


	def liste_item_changed(self):
		""" suite au changement de sélection , mettre à jour les vues dépendantes """ 

		itemT = self.NOT12.currentItem()
		if (itemT):
			if (self.which in ["occurences","deployement"]):
				item = re.sub("^\d* ","",itemT.text())
			else :
				item = itemT.text() # l'element selectionné
			self.activity("%s selected" % item)
			self.NOT12_D.clear() # on efface la liste
			self.NOT12_E.clear()
			sem = self.sem_liste_concept
			if ( sem  in ["$col", "$ef",  "$cat_ent" , "$ent"])  :
				# recupere la designation semantique de l'element
				self.semantique_liste_item = self.client.eval_get_sem(item, sem )
				#liste les representants
				self.client.eval_var("%s.rep[0:]"% self.semantique_liste_item)
				result = re.split(", ", self.client.eval_var_result)
				
				if ( result != [u''] ):
					self.liste_D_unsorted = []
					for r in range(len(result)):
                                                #affiche directement sur la liste E
						if (sem in ["$cat_ent"]):
							ask = "%s.rep%d.val"% (self.semantique_liste_item,r)
							self.client.eval_var(ask)
							val = int(self.client.eval_var_result)
							to_add = "%d %s"%(val, result[r] )
							self.NOT12_E.addItem( to_add  ) 
						else :
							if (self.which  == "occurences" ):
								ask = "%s.rep%d.val"% (self.semantique_liste_item,r)
								self.client.eval_var(ask)
								val = int(self.client.eval_var_result)
								to_add = "%d %s"%(val, result[r] )
								#quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
								if (val == 0):
                                                                        self.liste_D_unsorted.extend( map(lambda x : "0 %s" %x ,result[r:]) )
                                                                        break
							elif (self.which  == "deployement" ):
								ask = "%s.rep%d.dep"% (self.semantique_liste_item,r)
								self.client.eval_var(ask)
								val = int(self.client.eval_var_result)
								to_add = "%d %s"%(val, result[r] )
								#quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
								if (val == 0):
                                                                        self.liste_D_unsorted.extend( map(lambda x : "0 %s" %x ,result[r:]) )
                                                                        break
							else :
								to_add = "%s"% result[r] 
							self.liste_D_unsorted.append(to_add)
							#self.NOT12_D.addItem( to_add  )
							
					if (sem not in ["$cat_ent"]):
						liste_D_sorted = sorted(self.liste_D_unsorted,key = lambda x : int(re.split(" ",x)[0]),reverse =  1)
						self.NOT12_D.addItems(liste_D_sorted)

                                                if len(result) == 1 : # afficher directement E s'il ny a qu'une sous-catégorie
                                                        self.NOT12_D.setCurrentItem(self.NOT12_D.item(0))
                                                        self.liste_D_item_changed()



			#activation des boutons de commande
			self.NOT1Commands2.setEnabled(True) 


	def liste_D_item_changed(self):
                """quand un item de D est sélectionné, afficher représentants dans E"""
		itemT = self.NOT12_D.currentItem()
		if (itemT):
			if (self.which in ["occurences","deployement"]):
				item = re.sub("^\d* ","",itemT.text())
			else :
				item = itemT.text() # l'element selectionné
			#row = self.NOT12_D.currentRow() 
			row = self.liste_D_unsorted.index(itemT.text())
			self.activity("%s selected" % item)
			self.NOT12_E.clear() # on efface la liste
			ask = "%s.rep%d.rep[0:]" % (self.semantique_liste_item,row)
			self.semantique_liste_item_D = u"%s.rep%d" % (self.semantique_liste_item,  row)
			self.client.eval_var(ask)
			result = self.client.eval_var_result
			if (result != "") :
				result = re.split(", ", result)
				for r in range(len(result)):
					ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
					self.client.eval_var(ask)
					val = int(self.client.eval_var_result)
                                        #quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
					if (val == 0):
                                                self.NOT12_E.addItems( map(lambda x : "0 %s" %x ,result[r:]) )
                                                break
					self.NOT12_E.addItem("%d %s"%(val, result[r] )) 
					#self.NOT12_E.addItem( r ) 

	def liste_E_item_changed(self):
		itemT = self.NOT12_E.currentItem()
		if (itemT):
			item = re.sub("^\d* ","",itemT.text())
			#item = itemT.text() # l'element selectionné
			row = self.NOT12_E.currentRow() 
			self.activity("%s selected" % item)
			sem = self.sem_liste_concept
			if (sem in ["$cat_ent"]):
				self.semantique_liste_item_E = u"%s.rep%d" % (self.semantique_liste_item,  row)
			else :
				self.semantique_liste_item_E = u"%s.rep%d" % (self.semantique_liste_item_D,  row)
		
			
	def server_vars_Evalue(self):
		var = self.server_vars_champ.text()
		self.server_vars_champ.clear()
		self.client.eval_var(var)
		self.server_vars_result.setColor("red")
		self.server_vars_result.append("%s" % var)
		self.server_vars_result.setColor("black")
		self.server_vars_result.append(self.client.eval_var_result)


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
	

	def connect_server(self):
		self.activity("Connecting to server")
		self.client=client(self.Param_Server_val_host.text(),self.Param_Server_val_port.text())
		self.client.teste_connect()
		if (self.client.Etat):
			# calcule en avance
			self.pre_calcule()
			# affiche liste au demarrage
			self.select_liste(self.NOT1select.currentText())
			self.NOT1Commands1.setEnabled(True) 
			# affiche textes au demarrage
			self.recup_liste_textes()
			self.Param_Server_B.clicked.connect(self.disconnect_server)
			self.Param_Server_B.setText("Disconnect")
			self.Param_Server_B.setStyleSheet(None)  #supprime css bouton vert
			# donne le focus a l'onglet history
			self.SubWdwNE.setCurrentIndex(self.History_index)
		
	def disconnect_server(self):
		"""Disconnect"""
		self.activity("Disconnecting")
		self.client.disconnect()
		self.Param_Server_B.setText('Connect to server')
		self.Param_Server_B.clicked.connect(self.connect_server)


	def show_textContent(self ,  sem_txt):
		"""Insert text content in the dedicated window"""
		contentText_semantique = "%s.ph[0:]" % sem_txt
		self.client.eval_var(contentText_semantique)
		txt_content = self.client.eval_var_result
		self.textContent.clear()
		self.textContent.append(txt_content)
		#move cursor to the beginning of the text
		self.textContent.moveCursor(QtGui.QTextCursor.Start)
		
	def show_textCTX(self, sem_txt):
		"""Show text metadata"""
		self.m_current_selected_semtext = sem_txt	# on met de côté la sem du text
		self.textCTX.clear()
		for props in self.liste_champs_ctx :
			props_sem = "%s.%s" % (sem_txt,props)
			self.client.eval_var(props_sem)
			value = self.client.eval_var_result
			# vite fait -- pour exemple
			self.textCTX.addItem(props + u" :::  "  +value)
		
	def show_textProperties(self ,  sem_txt):
		"""Show text sailent properties"""
#TODO  pouvoir deployer
		#les actants
		self.saillantesAct.clear()
		list_act_sem = "%s.act[0:]" % sem_txt
		self.client.eval_var(list_act_sem)
		list_act  = self.client.eval_var_result
		list_act = re.split(", ",list_act)
		for i in range(len(list_act)) :
			self.client.eval_var(u"%s.act%d.val"%(sem_txt,i))
			val = int(self.client.eval_var_result)
			self.saillantesAct.addItem(u"%d %s" % (val, list_act[i]))
		#self.saillantesAct.addItems())

		#les catégories
#TODO trier par le poids ?
		for typ in [u"cat_qua",u"cat_mar",u"cat_epr",u"cat_ent"]:
			list_cat_sem = "%s.%s[0:]" % (sem_txt,typ)
			self.client.eval_var(list_cat_sem)
			list_cat  = self.client.eval_var_result
			self.saillantesCat.clear()
			liste_cat_items = re.split(", ",list_cat)
			for i in range(len(liste_cat_items)):
				ask = u"%s.%s%d.val"%(sem_txt,typ,i)
				self.client.eval_var(ask)
				val = int(self.client.eval_var_result)
				self.saillantesCat.addItem(u"%d %s" % (val, liste_cat_items[i]))
			#self.saillantesCat.addItems(re.split(", ",list_cat)) 

		# les collections
		list_col_sem = "%s.col[0:]" % sem_txt
		self.client.eval_var(list_col_sem)
		self.saillantesCol.clear()
		list_col = re.split(", ",self.client.eval_var_result)	
		for i in range(len(list_col)) :
#WARNING donne occurences pas deploiement
			self.client.eval_var(u"%s.col%d.dep"%(sem_txt,i))
			val = int(self.client.eval_var_result)
			self.saillantesCol.addItem(u"%d %s" % (val, list_col[i]))
		#self.saillantesCol.addItems(re.split(", ",self.client.eval_var_result))	



	def show_network(self):
#TODO scorer
		"""Show the network of a selected item"""
		if  self.NOT12_E.currentItem() :
			element = self.NOT12_E.currentItem().text() 
			element = re.sub("^\d* ","",element)
			res_semantique = "%s.res[0:]" % (self.semantique_liste_item_E)
		elif self.NOT12_D.currentItem():
			element1 = self.NOT12.currentItem().text() 
			element1 = re.sub("^\d* ","",element1)
			element2 = self.NOT12_D.currentItem().text() 
			element2 = re.sub("^\d* ","",element2)
			element = u"%s:%s" % (element1,element2 )
			res_semantique = "%s.res[0:]" % self.semantique_liste_item_D  
		else :
			element = self.NOT12.currentItem().text() 
			element = re.sub("^\d* ","",element)
			res_semantique = "%s.res[0:]" % self.semantique_liste_item  

		#cree l'onglet des réseaux si premier reseau calculé
		tab_networks = 0
		for i in range(self.SubWdwSO.count()):
			if (self.SubWdwSO.tabText(i) == "Networks"):
				tab_networks = 1
				pass

		if (tab_networks == 0):
			self.tabNetworks = QtGui.QTabWidget()
			self.tabNetworks.setTabsClosable(True)
			self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)
			self.SubWdwSO.addTab(self.tabNetworks,"Networks")
		

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
		self.client.eval_var(res_semantique)
		result_network =   re.split(", ",self.client.eval_var_result)
		self.activity(u"Displaying network for %s (%d items)" % (element,len(result_network))  )
		Network_list.addItems(result_network)
		self.tabNetworks.setCurrentIndex(index)# donne le focus a l'onglet créé
		self.SubWdwSO.setCurrentIndex(1)# donne le focus a l'onglet Networks

	def show_texts(self):
		"""Show texts containing a selected item"""
		if  self.NOT12_E.currentItem() :
			element = self.NOT12_E.currentItem().text() 
			element = re.sub("^\d* ","",element)
			txts_semantique = "%s.txt[0:]" % (self.semantique_liste_item_E)
		elif self.NOT12_D.currentItem():
			element1 = self.NOT12.currentItem().text() 
			element1 = re.sub("^\d* ","",element1)
			element2 = self.NOT12_D.currentItem().text() 
			element2 = re.sub("^\d* ","",element2)
			element = u"%s:%s" % (element1,element2 )
			#element = u"%s:%s" % (self.NOT12.currentItem().text(),self.NOT12_D.currentItem().text() )
			txts_semantique = "%s.txt[0:]" % self.semantique_liste_item_D  
		else :
			element = self.NOT12.currentItem().text() 
			element = re.sub("^\d* ","",element)
			txts_semantique = "%s.txt[0:]" % self.semantique_liste_item  

		self.client.eval_var(txts_semantique)
		if  (self.client.eval_var_result == ""):
			liste_textes = []
		else :
			liste_textes = re.split(", ",self.client.eval_var_result)
		self.activity(u"Displaying %d texts for %s" % (len(liste_textes),element) )


		"""ancien affichage
		texts_list = QtGui.QTableWidget()
		texts_list.verticalHeader().setVisible(False)
		texts_list.setRowCount(len(liste_textes))
		texts_list.setColumnCount(3)
		texts_list.setHorizontalHeaderLabels([u'date',u'name',u'title'])
		row = 0 
		for txt in liste_textes:
			name = re.split("/",txt)[-1]

			itemwidget = QtGui.QTableWidgetItem(name)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable
			texts_list.setItem(row,1,itemwidget)


			txt_sem = self.client.eval_get_sem(txt, u"$txt" )
			self.client.eval_var(u"%s.titre_txt"%txt_sem)
			txt_title = self.client.eval_var_result
			
			
			itemwidget = QtGui.QTableWidgetItem(txt_title)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable
		
			texts_list.setItem(row,2,itemwidget)
			
			
			
			self.client.eval_var("%s.date_txt"%txt_sem)
			txt_title = self.client.eval_var_result
			
			
			itemwidget = QtGui.QTableWidgetItem(txt_title)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable
		
			texts_list.setItem(row,0,itemwidget)
			
			
			
			row += 1
		texts_list.resizeColumnToContents(0)
		texts_list.resizeColumnToContents(1)
		texts_list.horizontalHeader().setStretchLastSection(True)
		texts_list.resizeRowsToContents()

		# anticorpus
		Lanticorpus = list( set(self.client.txts)-set(liste_textes))
		anticorpus = QtGui.QTableWidget()
		anticorpus.verticalHeader().setVisible(False)
		anticorpus.setRowCount(len(Lanticorpus))
		anticorpus.setColumnCount(2)
		anticorpus.setHorizontalHeaderLabels(['date','name'])
		row = 0 
		for txt in Lanticorpus:
			name = re.split("/",txt)[-1]
			itemwidget = QtGui.QTableWidgetItem(name)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable
			anticorpus.setItem(row,1,itemwidget)
			row += 1
		anticorpus.resizeColumnToContents(0)
		anticorpus.resizeColumnToContents(1)
		anticorpus.resizeRowsToContents()
		
		show_texts_widget = QtGui.QListWidget()
		show_texts_box = QtGui.QHBoxLayout()
		show_texts_box.setContentsMargins(0,0,0,0) 
		show_texts_box.setSpacing(0) 
		show_texts_widget.setLayout(show_texts_box)		
		show_texts_box.addWidget(texts_list)
		show_texts_box.addWidget(anticorpus)
		"""
		show_texts_widget = QtGui.QWidget()
		HBox_texts = QtGui.QHBoxLayout()
		HBox_texts.setContentsMargins(0,0,0,0) 
		HBox_texts.setSpacing(0) 
		show_texts_widget.setLayout(HBox_texts)
		self.show_texts_corpus = QtGui.QListWidget()
		self.show_texts_corpus.currentItemChanged.connect(self.onSelectTextFromElement) 
		HBox_texts.addWidget(self.show_texts_corpus)
		self.show_texts_anticorpus = QtGui.QListWidget()
		self.show_texts_anticorpus.currentItemChanged.connect(self.onSelectTextFromAnticorpus) 
		HBox_texts.addWidget(self.show_texts_anticorpus)

		self.l_corp_ord = []
		self.l_anticorp_ord = []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : v[0]):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			if T in liste_textes: 
				self.l_corp_ord.append(T)
				self.show_texts_corpus.addItem(txt_resume)
			else:
				self.l_anticorp_ord.append(T)
				self.show_texts_anticorpus.addItem(txt_resume)


		index = self.SOT1.addTab(show_texts_widget,"%s (%d)" % (element,len(liste_textes)))
		self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
		self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
		self.SOT1.tabBar().setTabToolTip(index,"%s %d"%(element,len(liste_textes)))

	def deploie_Actant(self):
#TODO double-clic replie
#TODO Seulement pour concepts
#TODO decale row si deploye
		item = self.saillantesAct.currentItem().text()
		item = re.sub("^\d* ","",item)
		self.activity(u"%s selected from text %s" % (item,self.semantique_txt_item))
		ask = "%s.act%d.rep_present[0:]"%(self.semantique_txt_item,self.saillantesAct.currentRow())
		self.client.eval_var(ask)
		result = self.client.eval_var_result
		if (result != [u'']):
                        r = self.saillantesAct.currentRow() 
			sub_n = 0
                        for sub_item in re.split(", ",result):
				ask = "%s.act%d.rep_present%d.val"%(self.semantique_txt_item,self.saillantesAct.currentRow(),sub_n)
				self.client.eval_var(ask)
				res = self.client.eval_var_result
                                r += 1
                                self.saillantesAct.insertItem(r,u"  %s %s"%(res,sub_item))
				sub_n += 1
                        
	def teste_wording(self):
		item = self.NOT12_E.currentItem().text()
		item = re.sub("^\d* ","",item)
		self.activity(u"%s double click" % (item))
		ask = "$ph.+%s"%(item)
		self.client.eval_var(ask)
		result = self.client.eval_var_result
		
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
		self.SubWdwNE.setCurrentIndex(3)# donne le focus a l'onglet Networks

def main():
	app = QtGui.QApplication(sys.argv)
	ex  = Principal()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
