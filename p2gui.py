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
	
	def creer_msg_search(self,fonc ,element, pelement='',txt=False,ptxt='',ph=False,pph='',val=False):
		return self.c.creer_msg_search(fonc ,element, pelement,txt,ptxt,ph,pph,val)

	def eval (self, L):
		return self.c.eval(L)


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
		

		self.activity("pre-computing : texts")

		
		nbre_txt = len (listeTextes)
		# mise en cache  valeur - semtxt
		for text in listeTextes :


			sem = u"$txt%s"%indice
			txt_name = listeTextes[indice]
			cle = txt_name + u"$txt"
			self.client.add_cache_fonct(cle, sem )
			indice +=1
			self.PrgBar.setValue(  indice   * 50 / nbre_txt )	
			QtGui.QApplication.processEvents()
		
			
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
		
		prgbar_val = 50

		# précalcule de valeurs associées 
		for type_var in [ "$ent" , "$ef" , "$col"] :
			self.activity("pre-computing : %s " % (type_var))
		#for type_var in [ "$ent" ]:
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
				
				prgbar_val += 3
				self.PrgBar.setValue(  prgbar_val )
				QtGui.QApplication.processEvents()
			prgbar_val -= 2

		self.PrgBar.reset()

			
			
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

		#create the progressebar
		self.PrgBar = QtGui.QProgressBar()
		self.PrgBar.setMaximumSize(199, 19)
		self.status.addPermanentWidget(self.PrgBar)

		

	
		# create the toolbar
		toolbar = self.addToolBar("toolbar")	
		#toolbar.setIconSize(QtCore.QSize(16, 16))
		toolbar.setMovable( 0 )

		

		#Saction = QtGui.QAction(QtGui.QIcon('Prospero-II.png'), 'Server', self)
		#toolbar.addAction(Saction)

		list1 = QtGui.QComboBox()
		#list1.addItem(u"Reference corpus")
#		list1.addItem(u"auteur : AFP")
		#toolbar.addWidget(list1)

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


#		SET1.addTab(SET12,u"Apports et reprises")
#		SET1.addTab(SET13,u"Eléments du texte")
#		SET1.addTab(SET14,u"Textes proches")
#		SET1.addTab(SET15,u"Textes identiques")



	# onglet contenu du CTX
		self.textCTX = QtGui.QListWidget()	
		self.textCTX.currentItemChanged.connect(self.onSelectChampCtx) 

	# onglet contenu du texte
		self.textContent = QtGui.QTextEdit() 


		SubWdwSETabs = QtGui.QTabWidget()

		SubWdwSE = QtGui.QWidget()

		SETabV = QtGui.QVBoxLayout()
		SETabV.setContentsMargins(0,0,0,0) 
		SETabV.setSpacing(0) 
		SETabVH = QtGui.QHBoxLayout()
		SETabV.addLayout(SETabVH)
		self.SETabTextDescr = QtGui.QLabel()
		SETabVH.addWidget(self.SETabTextDescr)
		SETabVH.addWidget(SubWdwSETabs)

		SubWdwSE.setLayout(SETabV)
		SETabV.addWidget(SubWdwSETabs)

		SubWdwSETabs.addTab(self.textProperties,"Properties")
		SubWdwSETabs.addTab(self.textCTX,"Context")
		SubWdwSETabs.addTab(self.textContent,"Text")


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
		#self.Param_Server_val_host.setText('prosperologie.org')#prosperologie.org
		self.Param_Server_val_host.setText('localhost')
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
		self.NOT1select.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 


	# un spacer pour mettre les commandes sur la droite
		spacer3 = QtGui.QLabel()
		spacer3.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
		NOT1VHC.addWidget(spacer3)

	#le champ de recherche
		self.list_research = QtGui.QLineEdit()
		self.list_research_button = QtGui.QPushButton()
		self.list_research_button.setIcon(QtGui.QIcon("loupe.png"))
		self.list_research_button.clicked.connect(self.list_concept_search)
		NOT1VHC.addWidget(self.list_research)
		NOT1VHC.addWidget(self.list_research_button)
		self.list_research_button.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
		



##pquoi ici le popup de CTX ???
	# essai popup
		self.popupCtx = QtGui.QMenu(self)
		self.popupCtx.addMenu('modifier')

	# les commandes
		self.NOT1Commands1 = QtGui.QPushButton()
		self.NOT1Commands1.setText(u"\u2195")
		self.NOT1Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
		self.NOT1Commands1Menu = QtGui.QMenu(self)
		#NOT1Commands1Menu.addAction('&search')
		#submenu_sort = QtGui.QMenu('&sort')
		#NOT1Commands1Menu.addMenu(submenu_sort)
		self.menu_occurences = self.NOT1Commands1Menu.addAction('occurences',self.affiche_liste_scores_oc)
		self.menu_deployement = self.NOT1Commands1Menu.addAction('deployement',self.affiche_liste_scores_dep)
		self.menu_alphabetical = self.NOT1Commands1Menu.addAction('alphabetical',self.affiche_liste_scores_alpha)
#TODO ajouter pondere, nb textes, nb auteurs, nb jours presents, relatif nb jours, nb representants, nb elements reseau
		#NOT1Commands1Menu.addAction('&sort')
		#NOT1Commands1Menu.addAction('&filter')
		self.NOT1Commands1.setMenu(self.NOT1Commands1Menu)
		NOT1VHC.addWidget(self.NOT1Commands1)


		self.NOT1Commands2 = QtGui.QPushButton()
		self.NOT1Commands2.setIcon(QtGui.QIcon("gear.png"))
		self.NOT1Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
		NOT1Commands2Menu = QtGui.QMenu(self)
		NOT1Commands2Menu.addAction('network' , self.show_network)
		self.liste_text_lists= []	
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

################################################

		#NOT2 =  QtGui.QLabel()
#		FrmlImage = QtGui.QPixmap("formul.png")
#		NOT2.setPixmap(FrmlImage)

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


		Explo_spacer1 = QtGui.QLabel()
		Explo_spacer1.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		NOT3VH.addWidget(Explo_spacer1)

		self.Explo_action = QtGui.QPushButton("search")
		self.Explo_action.setEnabled(False) #desactivé au lancement
		self.Explo_action.clicked.connect(self.Explorer)
		NOT3VH.addWidget(self.Explo_action)

		NOT3VH2 = QtGui.QHBoxLayout()
		NOT3V.addLayout(NOT3VH2)
		self.Explo_liste = QtGui.QListWidget()
		NOT3VH2.addWidget(self.Explo_liste)
		self.Explo_concepts = QtGui.QLabel()
		tempImage = QtGui.QPixmap("Prospero-II.png")
		self.Explo_concepts.setPixmap(tempImage)
		NOT3VH2.addWidget(self.Explo_concepts)

		# on prend toute la place
		#NOT3VH2.setContentsMargins(0,0,0,0) 
		#NOT3VH2.setSpacing(0) 
		



		SubWdwNO.addTab(NOT1,"Lists")
#		SubWdwNO.addTab(NOT2,"Formulae")
		SubWdwNO.addTab(NOT3,"Explorer")
		#SubWdwNO.setCurrentIndex(0) #Focus sur l'onglet listes concepts

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
#TODO creer objet textes, meme methodes pour textes du corpus et sous-corpus, deselectionner texte dans un onglet quand il l'est dans l'autre, faire un titre a afficher dans listes et en-tête du quadran, ne demander proprietes que quand clic sur onglet
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

			self.PrgBar.setValue(T * 100 / len(self.client.txts) ) 
			QtGui.QApplication.processEvents()

		#ordonne chrono par defaut
		self.liste_txt_ord = []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : "%s%s%s".join(reversed(re.split("/",v[0])))):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			i = QtGui.QListWidgetItem()
			self.CorpusTexts.addItem(txt_resume)
			self.liste_txt_ord.append(T)

		self.PrgBar.reset()

	def onSelectTextFromCorpus(self):
		"""When a text is selected from the list of texts for the entire corpus"""
		item_txt = self.liste_txt_ord[self.CorpusTexts.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.onSelectText(self.semantique_txt_item,item_txt)
		#self.activity(u"%s (%s) selected " % (item_txt,self.semantique_txt_item)) 

	def onSelectTextFromElement(self):
		"""When a text is selected from the list of texts for a given item"""
		item_txt = self.l_corp_ord[self.show_texts_corpus.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		#self.activity(u"%s (%s) selected" % (item_txt,self.semantique_txt_item)) 
		self.onSelectText(u"$txt%d"%self.client.txts.index(item_txt),item_txt)

	def onSelectTextFromAnticorpus(self):
		"""When a text is selected from the list of anticorpus texts for a given item"""
		item_txt = self.l_anticorp_ord[self.show_texts_anticorpus.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		#self.activity(u"%s (%s) selected" % (item_txt,self.semantique_txt_item)) 
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
		self.deselectText()
		#V =  self.liste_txt_corpus[item_txt]
		#txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
		#self.SETabTextDescr.setText(txt_resume)
		self.show_textProperties( sem_txt)
		self.show_textCTX(sem_txt) 
		self.show_textContent( sem_txt)


	def deselectText(self):
		#vide les listes des proprietes saillantes pour eviter confusion
		self.saillantesAct.clear()
		self.saillantesCat.clear()
		self.saillantesCol.clear()
		self.SETabTextDescr.setText("")
#TODO effacer CTX, content
		self.CorpusTexts.clearSelection()
		if (self.SOT1.count() > 1):
			for o in self.liste_text_lists:
				o.clearSelection()


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

		self.detect = ["abracadabri"]

		if (self.sem_liste_concept in ["$ef","$ent","$cat_ent"]):
			self.affiche_liste_scores_oc()
		elif (self.sem_liste_concept in ["$col"]):
			self.affiche_liste_scores_dep()
		

	def change_liste(self,content):
		self.NOT12.clear()
		self.NOT12_D.clear()
		self.NOT12_E.clear()
		self.NOT12.addItems(content)

	def choose_score_tick(self):
		"""tick and disable the choosen order selected, untick and enable others"""
		for act in self.NOT1Commands1Menu.actions():
			if (act.text() == self.which):
				act.setIcon(QtGui.QIcon("Tick.gif"))
				act.setEnabled(False)
			else :
				act.setEnabled(True)
				act.setIcon(QtGui.QIcon())
		self.NOT1Commands1.setText(u"\u2195 %s"%self.which)
			

	def affiche_liste_scores_alpha(self):
		self.which = "alphabetical"
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

	def affiche_liste_scores(self):
		typ = self.NOT1select.currentText()
		self.sem_liste_concept = self.get_semantique()
		content = self.client.recup_liste_concept(self.sem_liste_concept)
		self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,len(content), self.which))
		liste_valued =[]
		for row  in range(len(content)):
			if (self.which == "occurences" or self.which == "alphabetical"):
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
	
			self.PrgBar.setValue(row * 100 / len(content))
			QtGui.QApplication.processEvents()




		liste_final =[]
		self.content_liste_concept = []
		if (self.which == "alphabetical" ):
			for i in sorted(liste_valued,key=lambda x : x[1],reverse = 0):
				item_resume = u"%s %s" % (i[0], i[1])
				liste_final.append(item_resume) 
				self.content_liste_concept.append(i[1])
		else :
			for i in sorted(liste_valued,key=lambda x : x[0],reverse = 1):
				item_resume = u"%s %s" % (i[0], i[1])
				liste_final.append(item_resume) 
				self.content_liste_concept.append(i[1])
		self.change_liste(liste_final)

		self.PrgBar.reset()



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
			if ( sem  in ["$col", "$ef",  "$cat_ent" , "$ent"])  :
				# recupere la designation semantique de l'element
				self.semantique_liste_item = self.client.eval_get_sem(item, sem )
				#liste les representants
				self.client.eval_var("%s.rep[0:]"% self.semantique_liste_item)
				result = re.split(", ", self.client.eval_var_result)
				
				if ( result != [u''] ):

					if (sem in ["$cat_ent"]):#affiche directement sur la liste E
						liste_scoree = []
						for r in range(len(result)):
							ask = "%s.rep%d.val"% (self.semantique_liste_item,r)
							self.client.eval_var(ask)
							val = int(self.client.eval_var_result)
							liste_scoree.append( [ result[r] , val ])
						if (self.which == "alphabetical"):
							liste_scoree.sort()
						self.NOT12_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),liste_scoree))   

					else:
						self.liste_D_unsorted = []
						for r in range(len(result)):
							if (self.which  == "occurences" or self.which == "alphabetical"):
								ask = "%s.rep%d.val"% (self.semantique_liste_item,r)
							elif (self.which  == "deployement" ):
								ask = "%s.rep%d.dep"% (self.semantique_liste_item,r)
							self.client.eval_var(ask)
							val = int(self.client.eval_var_result)
							to_add = "%d %s"%(val, result[r] )
							#quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
							if (val == 0):
								self.liste_D_unsorted.extend( map(lambda x : "0 %s" %x ,result[r:]) )
								break
							self.liste_D_unsorted.append(to_add)
							
					if (sem not in ["$cat_ent"]):
						if (self.which == "alphabetical"):
							liste_D_sorted = sorted(self.liste_D_unsorted,key = lambda x : re.split(" ",x)[1],reverse =  0)
						else :
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
			#self.activity("%s selected" % item)
			self.NOT12_E.clear() # on efface la liste
			ask = "%s.rep%d.rep[0:]" % (self.semantique_liste_item,row)
			self.semantique_liste_item_D = u"%s.rep%d" % (self.semantique_liste_item,  row)
			self.client.eval_var(ask)
			result = self.client.eval_var_result
			if (result != "") :
				result = re.split(", ", result)
				if (self.which == "alphabetical"):
					liste_scoree = []
					for r in range(len(result)):
						ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						liste_scoree.append([result[r],val])
					self.NOT12_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),sorted(liste_scoree)))
				else :
					for r in range(len(result)):
						ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						#quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
						if (val == 0):
							self.NOT12_E.addItems( map(lambda x : "0 %s" %x ,result[r:]) )
							break
						self.NOT12_E.addItem("%d %s"%(val, result[r] )) 

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
			self.list_research_button.setEnabled(True) 
			self.NOT1select.setEnabled(True) 

			# affiche textes au demarrage
			self.recup_liste_textes()

			self.Param_Server_B.clicked.connect(self.disconnect_server)
			self.Param_Server_B.setText("Disconnect")
			self.Param_Server_B.setStyleSheet(None)  #supprime css bouton vert
			# donne le focus a l'onglet history
			self.SubWdwNE.setCurrentIndex(self.History_index)

			self.Explo_action.setEnabled(True) 
		
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
		#les actants
		#les actants en tête sont calculés par le serveur
		#self.saillantesAct.clear()
		self.saillantesAct_deployes = []
		list_act_sem = "%s.act[0:]" % sem_txt
		self.client.eval_var(list_act_sem)
		list_act  = self.client.eval_var_result
		if (list_act):
			self.list_act = re.split(", ",list_act)
			self.liste_act_valued = {}
			for i in range(len(self.list_act)) :
				self.client.eval_var(u"%s.act%d.val"%(sem_txt,i))
				val = int(self.client.eval_var_result)
				self.liste_act_valued [self.list_act[i]] = [ val, 0 ] 
				self.saillantesAct.addItem(u"%d %s" % (val, self.list_act[i]))
				self.PrgBar.setValue ( i * 33 / len(self.list_act) )
				QtGui.QApplication.processEvents()
			

		#les catégories
		#le serveur renvoie toutes les éléments de la catégorie
		#si len(cat_ent[0:]) > 2, deux algos a tester pour économiser les interactions avec le serveur :
		# si cat_ent0.val < len(cat_ent[0:]) on approxime le cumul des frequences de valeur par celui du rapport du nb d'element analysés sur le nb d'element total qu'on multiplie par cat_ent0.val, on arrête quand on atteint 0,5 ou on affiche les cat tant qu'elles ont le même score
		# si cat_ent0.val > len(cat_ent[0:]) on fait le rapport des valeurs cumulees sur la somme totale si les valeurs suivantes avaient le même score que le dernier obtenu : Val_cumul / ( (len(cat_ent[0:]) - i ) * cat_ent[i].val + Val_cumul ) on s'arrete en atteignant 0,25 ou etc

		self.list_cat_valued = {}
		self.list_cat_txt = {} 
		#self.saillantesCat.clear()
		self.saillantesCat_deployes = []
		#for typ in [u"cat_qua",u"cat_mar",u"cat_epr",u"cat_ent"]:
		for typ in [u"cat_ent"]: #uniquement les cat_ent
			list_cat_sem = "%s.%s[0:]" % (sem_txt,typ)
			self.client.eval_var(list_cat_sem)
			list_cat  = self.client.eval_var_result
			if (list_cat != u''):
				list_cat_items = re.split(", ",list_cat)
				r = 0
				for c in list_cat_items:
					self.list_cat_txt[c] = [typ,r]
					r += 1
				cum = 0
				old_val = 0
				#old_val2 = 0
				for i in range(len(list_cat_items)):
					ask = u"%s.%s%d.val"%(sem_txt,typ,i)
					self.client.eval_var(ask)
					val = int(self.client.eval_var_result)
					if (val < old_val):
						break
					cum += val
					C = float(cum) / (cum + ( (len(list_cat_items) - i ) * val ) )
					#C2 = float(i) / len(list_cat_items) * val
					#if (C2 > 0.50 and old_val2 == 0) :
					#	old_val2 = val	
					if (C > 0.25 and old_val == 0) :
						old_val = val	
					self.list_cat_valued[list_cat_items[i]] = val
					self.PrgBar.setValue ( 33 + ( i * 34 / len(list_cat_items) ) )
					QtGui.QApplication.processEvents()

		self.list_cat_valued_ord = []
		for cat in sorted( self.list_cat_valued.items(), key = lambda(k,v) : v,reverse=1):
			self.list_cat_valued_ord.append(cat[0])
			resume = u"%d %s" % (int(cat[1]), cat[0])
			#if int(cat[1]) < old_val:
			#	resume = "D" + resume
			#if int(cat[1]) < old_val2:
			#	resume = "E" + resume
			self.saillantesCat.addItem(resume)
			

		# les collections
		# on met toutes les collections parce que leur émergence est donnée par leur déploiement
#TODO ordonner
		#self.saillantesCol.clear()
		self.saillantesCol_deployees = []
		list_col_sem = "%s.col[0:]" % sem_txt
		self.client.eval_var(list_col_sem)
		result = self.client.eval_var_result
		if (result != u""):
			self.list_col = re.split(", ",result)	
			self.list_col_valued = {}
			for i in range(len(self.list_col)) :
				self.client.eval_var(u"%s.col%d.dep"%(sem_txt,i))
				val = int(self.client.eval_var_result)
				self.saillantesCol.addItem(u"%d %s" % (val, self.list_col[i]))
				self.list_col_valued[self.list_col[i]] = val
				self.PrgBar.setValue ( 66 + ( i * 34 / len(self.list_col) ) )
				QtGui.QApplication.processEvents()

		self.PrgBar.reset()


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
                                self.client.eval_var(ask)
                                result = self.client.eval_var_result
				if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.list_col_valued.keys() ):
                                                        ask = "%s.col%d.rep_present%d.val"%(self.semantique_txt_item,self.list_col.index(r),sub_n)
                                                        self.client.eval_var(ask)
                                                        res = self.client.eval_var_result
                                                        self.list_col_valued[result[sub_n]] = res
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.list_col_valued[result[sub_n]],result[sub_n]))
#TODO trouver couleur par defaut du alternate
                                                i.setBackground(QtGui.QColor( 245,245,245))
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
                                self.client.eval_var(ask)
                                result = self.client.eval_var_result
                                if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.list_cat_valued.keys() ):
							ask = "%s.%s%d.rep_present%d.val"%(self.semantique_txt_item,sem[0],sem[1],sub_n)
                                                        self.client.eval_var(ask)
                                                        res = self.client.eval_var_result
                                                        self.list_cat_valued[result[sub_n]] = res
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.list_cat_valued[result[sub_n]][0],result[sub_n]))
#TODO trouver couleur par defaut du alternate
                                                i.setBackground(QtGui.QColor( 245,245,245))
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
                                self.client.eval_var(ask)
				result = self.client.eval_var_result
                                if (result != u''):
                                        result = re.split(", ",result)
                                        for sub_n in range(len(result)) :
                                                if ( result[sub_n] not in self.liste_act_valued.keys() ):
                                                        ask = "%s.act%d.rep_present%d.val"%(self.semantique_txt_item,self.list_act.index(r),sub_n)
                                                        self.client.eval_var(ask)
                                                        res = self.client.eval_var_result
                                                        self.liste_act_valued[result[sub_n]] = [res,2]
                                                i = QtGui.QListWidgetItem()
                                                i.setText(u"  %s %s"%(self.liste_act_valued[result[sub_n]][0],result[sub_n]))
#TODO trouver couleur par defaut du alternate
                                                i.setBackground(QtGui.QColor( 245,245,245))
                                                self.saillantesAct.addItem(i)
                                        
                                
                        


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
#TODO scorer/trier
		"""Show texts containing a selected item"""
		
		
		self.deselectText()

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
		self.liste_text_lists.append(self.show_texts_corpus)
		self.show_texts_anticorpus = QtGui.QListWidget()
		self.show_texts_anticorpus.currentItemChanged.connect(self.onSelectTextFromAnticorpus) 
		HBox_texts.addWidget(self.show_texts_anticorpus)
		self.liste_text_lists.append(self.show_texts_anticorpus)

		self.l_corp_ord = []
		self.l_anticorp_ord = []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : "%s%s%s".join(reversed(re.split("/",v[0])))):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			if T in liste_textes: 
				self.l_corp_ord.append(T)
				self.show_texts_corpus.addItem(txt_resume)
			else:
				self.l_anticorp_ord.append(T)
				self.show_texts_anticorpus.addItem(txt_resume)

		#si la tab de l'element existe déjà, on efface l'ancienne
		for i in range(0, self.SOT1.count() ):
			if (re.search("^%s (\d*)"%element,self.SOT1.tabText(i) ) ):
				self.SOT1.removeTab(i)
			

		index = self.SOT1.addTab(show_texts_widget,"%s (%d)" % (element,len(liste_textes)))
		self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
		self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
		self.SOT1.tabBar().setTabToolTip(index,"%s %d"%(element,len(liste_textes)))


                        
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

	def list_concept_search(self):
		"""recherche un motif dans la liste gauche du type de concept selectionné"""
		motif = self.list_research.text()
		if (motif != ""):
			if (self.detect[0] != motif or len(self.detect) == 1):
				self.activity(u"searching for %s" % (motif))
				self.detect = filter(lambda m : re.search(motif,m),self.content_liste_concept)
				self.detect.insert(0, motif)
			if len(self.detect) > 1:
				elt  = self.detect.pop(1)
				row =  self.content_liste_concept.index(elt)
				self.NOT12.setCurrentRow(row)

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
				for i in range(len(liste_result)):
					ask = self.client.creer_msg_search(type_search,motif,"%d"%i,val=True) #la valeur du match
#TODO comprendre les 0, get_sem, liste textes, énoncés
					r = self.client.eval( ask )
					self.Explo_liste.addItem("%s %s"% (r,liste_result[i]))
			else :

				self.activity("searching for [%s] : 0 result")
				

def main():
	app = QtGui.QApplication(sys.argv)
	ex  = Principal()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
