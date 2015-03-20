#!/usr/bin/python
# -*- coding: utf-8 -*-


#TODO internationalisation QTranslator

import sys
import PySide
from PySide import QtCore 
from PySide import QtGui 

import interface_prospero
from fonctions import translate
import re
import datetime
import subprocess, threading
from PySide.QtGui import QMdiArea



class client(object):

	def __init__(self,h,p):

		self.c = interface_prospero.ConnecteurPII() 
		#self.c.start()
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
		#self.c.put_to_eval(var)
		
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

	def eval_set_ctx(self, sem_txt, field, val):
		return self.c.eval_set_ctx(sem_txt, field, val)

	def creer_msg_set_ctx(self,data):
		return self.c.creer_msg_set_ctx(data)


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
		#self.client.c.put_to_eval("$ctx")
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
			 
			#string_ctx = self.client.eval_var_ctx("%s"%champ,"[0:]") 
			self.client.eval_var("$ctx.%s%s"%(champ,"[0:]")) 
			string_ctx = self.client.eval_var_result
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
			for text in listeTextes :
				sem = u"$txt%s"%indice
				data = liste_data_ok_ctx[indice]
				#self.client.add_cache_var( sem + ".%s"%champ, data)
				# sématique avec les noms des champs anglais
				self.client.add_cache_var( sem + ".ctx.%s"%champ, data)
				indice +=1	
		# on se sert de la liste des champs dans l'onglet CTX			
		self.liste_champs_ctx = liste_champs_ajuste	
#TODO ordonner la liste pour la faire commencer par les champs typiques : titre, auteur, narrateur, destinataire, date, support, type support, observation, qualite auteur, lieu, CL1 (période),  CL2 (sous-corpus)
		
		prgbar_val = 50

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
				
				prgbar_val += 3
				self.PrgBar.setValue(  prgbar_val )
				QtGui.QApplication.processEvents()
			prgbar_val -= 2



		self.PrgBar.reset()





		

	
	def initUI(self):


		# create the menu bar
		Menubar = self.menuBar()

		Menu_Corpus = Menubar.addMenu('&Corpus')
		#Menu_Corpus.setShortcut('Ctrl+C')
		Menu_distant = QtGui.QAction(QtGui.QIcon('distant.png'), '&prosperologie.org', self)        
		Menu_distant.setStatusTip('Connect to prosperologie.org server')
		Menu_distant.triggered.connect(self.connect_server)
		Menu_Corpus.addAction(Menu_distant)
		Menu_local = QtGui.QAction(QtGui.QIcon('home.png'), '&local', self)        
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


		"""
		self.textCTX.setRowCount(1)
		itTest = QtGui.QTableWidgetItem("t1")
		self.textCTX.setItem(0,0,itTest)
		"""

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
		#self.SubWdwSETabs.addTab(self.textCTX,"Context")
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
		#self.CorpusTexts.itemClicked.connect(self.onSelectTextFromCorpus) #ne fonctionne pas avec le clavier
		self.CorpusTexts.currentItemChanged.connect(self.onSelectTextFromCorpus) #fonctionne avec clavier et souris, mais selectionne le 1er texte au chargement
		
		#l'onglet des réseaux
		self.tabNetworks = QtGui.QTabWidget()
		self.tabNetworks.setTabsClosable(True)
		self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

#TODO les expressions englobantes

		#mise en place des onglets

		self.SubWdwSO.addTab(self.SOT1,self.tr("Texts"))
		self.SubWdwSO.addTab(self.tabNetworks,self.tr("Networks"))


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
		#self.SubWdwNE.addTab(Param_Server,"Server")

# on donne le focus à la connection au serveur
		self.SubWdwNE.setCurrentIndex(2)





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
		self.NOT1Commands2.setIcon(QtGui.QIcon("gear.png"))
		self.NOT1Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
		NOT1Commands2Menu = QtGui.QMenu(self)
		NOT1Commands2Menu.addAction('network' , self.show_network)
		self.liste_text_lists= []	
		self.liste_text_lists_items= {}
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
		self.NOT12_E.doubleClicked.connect(self.teste_wording)


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
		self.NOT2Commands2.setIcon(QtGui.QIcon("gear.png"))
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
		self.Explo_commands.setIcon(QtGui.QIcon("gear.png"))
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
		tempImage = QtGui.QPixmap("Prospero-II.png")
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
		self.NOT5Commands1.setIcon(QtGui.QIcon("gear.png"))
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
#		self.NOT5_cont.currentItemChanged.connect() 





		self.SubWdwNO.addTab(NOT1,self.tr("Lexicon"))
		self.SubWdwNO.addTab(NOT2,"Concepts")
		self.SubWdwNO.addTab(NOT3,"Search")
		self.SubWdwNO.addTab(NOT5,"Metadatas")

		self.SubWdwNO.currentChanged.connect(self.change_NOTab)
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
		grid.addWidget(self.SubWdwNO,0,0)
		grid.addWidget(self.SubWdwNE,0,1)
		grid.addWidget(self.SubWdwSO,1,0)
		#grid.addWidget(SubWdwSE,1,1)
		grid.addWidget(self.SubWdwSETabs,1,1)
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


	def recup_liste_textes(self):
		"""display texts for the corpus"""
#TODO creer objet textes, meme methodes pour textes du corpus et sous-corpus,  faire un titre a afficher dans listes et en-tête du quadran, 
		#self.activity(u"Waiting for text list"   )
		self.client.recup_texts()
		self.activity(u"Displaying text list (%d items)" %len(self.client.txts)  )
		self.SOT1.tabBar().setTabText(0,"corpus (%d)"%len(self.client.txts))
		self.CorpusTexts.clear()

		self.liste_txt_corpus = {}


		for T in range(len(self.client.txts)):
			sem_txt = "$txt%d" % T
			#self.client.eval_var(u"%s.date_txt" % (sem_txt))


			self.client.eval_var(u"%s.ctx.date" % (sem_txt))
			date = re.sub("^\s*","",self.client.eval_var_result)
			#self.client.eval_var(u"%s.auteur_txt" % (sem_txt))
			self.client.eval_var(u"%s.ctx.author" % (sem_txt))
			author = re.sub("^\s*","",self.client.eval_var_result)
			self.client.eval_var(u"%s.ctx.title" % (sem_txt))
			title = re.sub("^\s*","",self.client.eval_var_result)

			self.liste_txt_corpus[self.client.txts[T]] = [date, author, title,sem_txt]

			self.PrgBar.setValue(T * 100 / len(self.client.txts) ) 
			QtGui.QApplication.processEvents()

		#ordonne chrono par defaut
		self.liste_txt_ord = []
		self.liste_semtxt_ord = []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : "%s%s%s".join(reversed(re.split("/",v[0])))):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			i = QtGui.QListWidgetItem()
			self.CorpusTexts.addItem(txt_resume)
			self.liste_txt_ord.append(T)
			self.liste_semtxt_ord.append(V[3])

		self.PrgBar.reset()

	def onSelectTextFromCorpus(self):
		"""When a text is selected from the list of texts for the entire corpus"""
		item_txt = self.liste_txt_ord[self.CorpusTexts.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.onSelectText(self.semantique_txt_item,item_txt)

	def onSelectTextFromElement(self):
		"""When a text is selected from the list of texts for a given item"""
		item_txt = self.l_corp_ord[self.show_texts_corpus.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.onSelectText(u"$txt%d"%self.client.txts.index(item_txt),item_txt)

	def onSelectTextFromAnticorpus(self):
		"""When a text is selected from the list of anticorpus texts for a given item"""
		item_txt = self.l_anticorp_ord[self.show_texts_anticorpus.currentRow()]
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.onSelectText(u"$txt%d"%self.client.txts.index(item_txt),item_txt)


	def onSelectText(self,sem_txt,item_txt):
		"""Update text properties windows when a text is selected """
		self.activity(u"%s (%s) selected " % (item_txt,sem_txt)) 
		self.deselectText()

		#V =  self.liste_txt_corpus[item_txt]
		#txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
		#self.SETabTextDescr.setText(item_txt)

		#pour accélérer l'affichage, on ne remplit que l'onglet sélectionné
		if ( self.SubWdwSETabs.currentIndex () == 0 ):
			self.show_textProperties( sem_txt)
		elif ( self.SubWdwSETabs.currentIndex () == 1 ):
			self.show_textCTX(sem_txt) 
		elif ( self.SubWdwSETabs.currentIndex () == 2 ):
			self.show_textContent( sem_txt)

		self.CorpusTexts.setCurrentRow(self.liste_semtxt_ord.index(self.semantique_txt_item))
		#TODO selectionner les memes textes selectionnes dans les listes differentes
		if (self.SOT1.count() > 1):
			for o in self.liste_text_lists:
				print o[1]



	def deselectText(self):
		"""vide les listes des proprietes saillantes pour eviter confusion"""
		self.saillantesAct.clear()
		self.saillantesCat.clear()
		self.saillantesCol.clear()
		#self.SETabTextDescr.setText("")
		self.CorpusTexts.clearSelection()
		if (self.SOT1.count() > 1):
			for o in self.liste_text_lists:
				o[0].clearSelection()
		self.efface_textCTX()
		self.textContent.clear()



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
		for r in range( self.textCTX.rowCount()):
			field = self.textCTX.item(r,0).text()
			val =  self.textCTX.item(r,1).text()
			#ask = u"%s.%s" % ( self.m_current_selected_semtext,field)
			ask = u"%s.ctx.%s" % ( self.m_current_selected_semtext,field)
			self.client.eval_var(ask)
			result = re.sub(u"^\s*","",self.client.eval_var_result)
#TODO ne met pas à jour le CTX, a un pb avec result
			if (result != val):
				print [field, result, val]
				self.client.eval_set_ctx( self.m_current_selected_semtext,field,val)
				self.client.add_cache_var(self.m_current_selected_semtext +".ctx."+field,val)
		
		#self.client.creer_msg_set_ctx ( (sem_txt, field, val) )
		#self.client.eval_set_ctx(sem_txt, field, val)
		#print (sem_txt, field, val)
		
		self.textCTX_valid.setEnabled(False)
		self.textCTX_reset.setEnabled(False)
#TODO verifier que le cache soit mis à jour
		self.show_textCTX(self.m_current_selected_semtext)


		

	def resetCTX(self):
		self.textCTX_valid.setEnabled(False)
		self.textCTX_reset.setEnabled(False)
		self.show_textCTX(self.m_current_selected_semtext)
		

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
		self.NOT12.addItems(content)


	def change_liste_concepts(self,content):
		self.NOT22.clear()
		self.NOT22_D.clear()
		self.NOT22_E.clear()
		self.NOT22.addItems(content)


	def choose_score_tick(self):
		"""tick and disable the choosen order selected, untick and enable others"""
		for act in self.NOT1Commands1Menu.actions():
			if (act.text() == self.which):
				act.setIcon(QtGui.QIcon("Tick.gif"))
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
				act.setIcon(QtGui.QIcon("Tick.gif"))
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
		self.choose_score_tick()
		self.affiche_concepts_scores()

	def affiche_concepts_scores_fapp(self):
		self.which_concepts = "first apparition"
		self.choose_score_tick()
		self.affiche_concepts_scores()


	def affiche_concepts_scores_lapp(self):
		self.which_concepts = "last apparition"
		self.choose_score_tick()
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


			self.client.eval_var( ask )

			try :
				if self.which_concepts  in ["first apparition",  "last apparition"]:
					val = re.sub(u"^\s*","",self.client.eval_var_result)
				else :
					val = int(self.client.eval_var_result)
			except:
				#en cas de non reponse
				print [ask]
				val = 0
			liste_valued.append([val,content[row]])
	
			self.PrgBar.setValue(row * 100 / len(content))
			QtGui.QApplication.processEvents()




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

		self.PrgBar.reset()




	def affiche_liste_scores(self):
		typ = self.NOT1select.currentText()
		self.sem_liste_concept = self.get_semantique()
		content = self.client.recup_liste_concept(self.sem_liste_concept)
		if ( self.sem_liste_concept not in ['ent']):
			self.lexicon_list_semantique = content
		self.activity(u"Displaying %s list (%d items) ordered by %s" % (typ,len(content), self.which))
		liste_valued =[]
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

			self.client.eval_var( ask )

			try :
				if self.which  in ["first apparition",  "last apparition"]:
					val = re.sub(u"^\s*","",self.client.eval_var_result)
				else :
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
			if ( sem  in ["$ent"])  :
				# recupere la designation semantique de l'element
				self.semantique_liste_item = self.client.eval_get_sem(item, sem )
				#liste les representants
				self.client.eval_var("%s.rep[0:]"% self.semantique_liste_item)
				result = re.split(", ", self.client.eval_var_result)
				
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
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
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
			self.client.eval_var(ask)
			result = self.client.eval_var_result
			if (result != "") :
				result = re.split(", ", result)
				if (self.which == "alphabetically"):
					liste_scoree = []
					for r in range(len(result)):
						ask = "%s.rep%d.rep%d.val"% (self.semantique_liste_item,row,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						liste_scoree.append([result[r],val])
						self.PrgBar.setValue(  r * 100 /len(result) )
						QtGui.QApplication.processEvents()
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
						self.PrgBar.setValue(  r * 100 /len(result) )
						QtGui.QApplication.processEvents()
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
			self.client.eval_var("%s.rep[0:]"% self.semantique_concept_item)
			result = re.split(", ", self.client.eval_var_result)
			
			if ( result != [u''] ):
				if (sem in ["$cat_ent"]):#affiche directement sur la liste E
					liste_scoree = []
					prgbar_val = 0
					for r in range(len(result)):
						if (self.which_concepts == "number of texts"):
#TODO corriger, il donne la valeur de la categorie entiere
							ask = "%s.rep%d.nbtxt"% (self.semantique_concept_item,r)
						else :
							ask = "%s.rep%d.val"% (self.semantique_concept_item,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						liste_scoree.append( [ result[r] , val ])
						self.PrgBar.setValue( r * 100 / len(result)  )
						QtGui.QApplication.processEvents()
					if (self.which_concepts == "alphabetically"):
						liste_scoree.sort()
					self.NOT22_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),liste_scoree))   
					self.PrgBar.reset()

				else:
					self.liste_D_concepts_unsorted = []
					for r in range(len(result)):
						if (self.which_concepts  == "occurences" or self.which_concepts == "alphabetically"):
							ask = "%s.rep%d.val"% (self.semantique_concept_item,r)
						elif (self.which_concepts  == "deployement" ):
							ask = "%s.rep%d.dep"% (self.semantique_concept_item,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
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
			self.client.eval_var(ask)
			result = self.client.eval_var_result
			if (result != "") :
				result = re.split(", ", result)
				if (self.which_concepts == "alphabetically"):
					liste_scoree = []
					for r in range(len(result)):
						ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item,row,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						liste_scoree.append([result[r],val])
						self.PrgBar.setValue(  r * 100 /len(result) )
						QtGui.QApplication.processEvents()
					self.NOT22_E.addItems(map(lambda x : "%d %s"% (x[1], x[0]),sorted(liste_scoree)))
				else :
					for r in range(len(result)):
						ask = "%s.rep%d.rep%d.val"% (self.semantique_concept_item,row,r)
						self.client.eval_var(ask)
						val = int(self.client.eval_var_result)
						#quand on atteint 0, on arrête la boucle et on affecte 0 à toutes les valeurs suivantes
						if (val == 0):
							self.NOT22_E.addItems( map(lambda x : "0 %s" %x ,result[r:]) )
							break
						self.NOT22_E.addItem("%d %s"%(val, result[r] )) 
						self.PrgBar.setValue(  r * 100 /len(result) )
						QtGui.QApplication.processEvents()
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
	
	def connect_server_localhost(self):
		#self.connect_server('localhost')
		self.connect_server(h='192.168.1.99',p='60000')

	def connect_server(self,h = 'prosperologie.org',p = '60000'):
		self.activity("Connecting to server")
		#self.client=client(self.Param_Server_val_host.text(),self.Param_Server_val_port.text())

		#self.client=client("prosperologie.org","60000")
		#self.client=client("192.168.1.99","4000")

		self.client=client(h,p)
		#self.client=client("prosperologie.org","60000")
		#self.client=client("localhost","60000")

		self.client.teste_connect()
		if (self.client.Etat):
			# calcule en avance
			self.pre_calcule()

			# affiche liste au demarrage
			self.select_liste(self.NOT1select.currentText())

			self.NOT1Commands1.setEnabled(True) 
			self.NOT1select.setEnabled(True) 
			self.NOT2Commands1.setEnabled(True) 
			self.NOT2select.setEnabled(True) 

			# affiche textes au demarrage
			self.recup_liste_textes()


			#Contexts
			self.recup_ctx()

			#self.Param_Server_B.clicked.connect(self.disconnect_server)
			#self.Param_Server_B.setText("Disconnect")
			#self.Param_Server_B.setStyleSheet(None)  #supprime css bouton vert
			# donne le focus a l'onglet history
			self.SubWdwNE.setCurrentIndex(self.History_index)

			#self.Explo_action.setEnabled(True) 
		
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
		
	def efface_textCTX(self):
		self.textCTX.clear()
		self.textCTX.setRowCount(0)
		self.textCTX.setHorizontalHeaderLabels([u'field',u'value']) #on remet les headers apres le clear

	def show_textCTX(self, sem_txt):
		"""Show text metadata"""
		self.m_current_selected_semtext = sem_txt	# on met de côté la sem du text
		self.efface_textCTX()
		self.textCTX.setRowCount(len(self.liste_champs_ctx))
		r = 0
		for props in self.liste_champs_ctx :
			props_sem = "%s.ctx.%s" % (sem_txt,props)
			self.client.eval_var(props_sem)
			value = re.sub(u"^\s*","",self.client.eval_var_result)
			#value = self.client.eval_var_result
			itemCTXwidget_field = QtGui.QTableWidgetItem(props)
			#font = itemCTXwidget_field.font()
			#font.setBold(True)
			#itemCTXwidget_field.setFont(font)
			self.textCTX.setItem(r,0,itemCTXwidget_field)
			itemCTXwidget_val = QtGui.QTableWidgetItem(value)
			self.textCTX.setItem(r,1,itemCTXwidget_val)
			r += 1
		#self.textCTX.resizeColumnsToContents()
		self.textCTX.resizeRowsToContents()

	def show_textProperties(self ,  sem_txt):
		"""Show text sailent properties"""
		#les actants
		#les actants en tête sont calculés par le serveur
		#self.saillantesAct.clear()
		self.saillantesAct_deployes = []
		list_act_sem = "%s.act[0:]" % sem_txt
		self.client.eval_var(list_act_sem)
		pos = 0
		list_act = self.client.eval_var_result.split(',')
		list_act_sem_val = list_act_sem + ".val"
		self.client.eval_var(list_act_sem_val)
		list_act_val = self.client.eval_var_result.split(',')
		for act in list_act :
			self.client.add_cache_var("%s.act%s"%(sem_txt,pos), act)
			self.client.add_cache_var("%s.act%s.val"%(sem_txt,pos), list_act_val[pos])
			pos +=1
		#list_act  = self.client.eval_var_result
		if (list_act):
			#self.list_act = re.split(", ",list_act)
			self.list_act = list_act
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
		self.client.eval_var(res_semantique)
		result_network =   re.split(", ",self.client.eval_var_result)
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
		motif = self.Explo_saisie.text()
		row =  self.Explo_liste.currentRow()
		ask = self.client.creer_msg_search("$search.rac",motif,"%d"%row,txt=True,ptxt="[0:]")
		result = self.client.eval( ask )
		liste_textes = re.split(", ",result)
		self.activity(u"Displaying %d texts for %s" % (len(liste_textes),motif))

		self.deselectText()

		show_texts_widget = QtGui.QWidget()
		HBox_texts = QtGui.QHBoxLayout()
		HBox_texts.setContentsMargins(0,0,0,0) 
		HBox_texts.setSpacing(0) 
		show_texts_widget.setLayout(HBox_texts)
		self.show_texts_corpus = QtGui.QListWidget()
		self.show_texts_corpus.setAlternatingRowColors(True)
		self.show_texts_corpus.currentItemChanged.connect(self.onSelectTextFromElement) 
		HBox_texts.addWidget(self.show_texts_corpus)
		self.liste_text_lists.append([self.show_texts_corpus,[]])
		self.show_texts_anticorpus = QtGui.QListWidget()
		self.show_texts_anticorpus.setAlternatingRowColors(True)
		self.show_texts_anticorpus.currentItemChanged.connect(self.onSelectTextFromAnticorpus) 
		HBox_texts.addWidget(self.show_texts_anticorpus)
		self.liste_text_lists.append([self.show_texts_anticorpus,"a"])

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
			if (re.search("^{%s} (\d*)"%motif,self.SOT1.tabText(i) ) ):
				self.SOT1.removeTab(i)
			
		index = self.SOT1.addTab(show_texts_widget,"{%s} (%d)" % (motif,len(liste_textes)))
		self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
		self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
		self.SOT1.tabBar().setTabToolTip(index,"{%s} %d"%(motif,len(liste_textes)))





	def show_texts(self):
#TODO scorer/trier
		"""Show texts containing a selected item"""
		self.deselectText()

		if ( self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
			sem,element = self.recup_element_lexicon()
		if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
			sem,element = self.recup_element_concepts()
		txts_semantique = "%s.txt[0:]" % (sem)

		self.client.eval_var(txts_semantique)
		if  (self.client.eval_var_result == ""):
			liste_textes = []
		else :
			liste_textes = re.split(", ",self.client.eval_var_result)
		self.activity(u"Displaying %d texts for %s" % (len(liste_textes),element) )


		show_texts_widget = QtGui.QWidget()
		HBox_texts = QtGui.QHBoxLayout()
		HBox_texts.setContentsMargins(0,0,0,0) 
		HBox_texts.setSpacing(0) 
		show_texts_widget.setLayout(HBox_texts)
		self.show_texts_corpus = QtGui.QListWidget()
		self.show_texts_corpus.setAlternatingRowColors(True)
		self.show_texts_corpus.currentItemChanged.connect(self.onSelectTextFromElement) 
		HBox_texts.addWidget(self.show_texts_corpus)
		self.liste_text_lists.append([self.show_texts_corpus,[]])
		self.show_texts_anticorpus = QtGui.QListWidget()
		self.show_texts_anticorpus.setAlternatingRowColors(True)
		self.show_texts_anticorpus.currentItemChanged.connect(self.onSelectTextFromAnticorpus) 
		HBox_texts.addWidget(self.show_texts_anticorpus)
		self.liste_text_lists.append([self.show_texts_anticorpus,[]])

		self.l_corp_ord = []
		self.l_anticorp_ord = []
		#self.liste_text_lists_items[self.show_texts_corpus] =  []
		for T,V in  sorted(self.liste_txt_corpus.items(),key=lambda (k,v) : "%s%s%s".join(reversed(re.split("/",v[0])))):
			txt_resume = u"%s %s %s" % (V[0],V[1],V[2])
			if T in liste_textes: 
				self.l_corp_ord.append(T)
				self.show_texts_corpus.addItem(txt_resume)
				#self.liste_text_lists[self.show_texts_corpus].append(V[3])
			else:
				self.l_anticorp_ord.append(T)
				self.show_texts_anticorpus.addItem(txt_resume)
				#self.liste_text_lists[self.show_texts_anticorpus].append(V[3])


		#si la tab de l'element existe déjà, on efface l'ancienne
		for i in range(0, self.SOT1.count() ):
			if (re.search("^%s (\d*)"%element,self.SOT1.tabText(i) ) ):
				self.SOT1.removeTab(i)
			

		index = self.SOT1.addTab(show_texts_widget,"%s (%d)" % (element,len(liste_textes)))
		self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
		self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
		self.SOT1.tabBar().setTabToolTip(index,"%s %d"%(element,len(liste_textes)))


                        
	def teste_wording(self):
		if ( self.SubWdwNO.currentIndex() == 0) : # si l'onglet lexicon
			item = self.NOT12_E.currentItem().text()
		if ( self.SubWdwNO.currentIndex() == 1) : # si l'onglet concepts
			item = self.NOT22_E.currentItem().text()

		score,item = re.search("^(\d*) (.*)",item).group(1,2)
		self.activity(u"%s double click" % (item))
		if (int(score)):
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
				for i in range(len(liste_result)):
					ask = self.client.creer_msg_search(type_search,motif,"%d"%i,val=True) #la valeur du match
#TODO get_sem, liste textes, énoncés
#TODO select all
					r = self.client.eval( ask )
					self.PrgBar.setValue(  100 * i / len(liste_result) )	
					QtGui.QApplication.processEvents()
					self.Explo_liste.addItem("%s %s"% (r,liste_result[i]))
				self.PrgBar.reset()
			else :
				self.activity("searching for {%s} : 0 result" % motif)
				result = re.split(", ", self.client.eval_var_result)


	def recup_ctx(self):
		self.NOT5_list.clear()
		self.activity("evaluating metadatas list")
		#self.client.eval_var(u"$ctx[0:]")
		self.client.eval_var(u"$ctx")
		result = re.split(", ",self.client.eval_var_result )
		self.NOT5_list.addItems(result)
		
	def contexts_contents(self):
		self.NOT5_cont.clear()
		champ = self.NOT5_list.currentItem().text()
		self.client.eval_var(u"$ctx.%s[0:]" % champ)
		result = self.client.eval_var_result
		result = re.split("(?<!\\\), ",result )#negative lookbehind assertion
		dic_CTX = {}
		for r in result:
			if r in dic_CTX.keys():
				dic_CTX[r] = dic_CTX[r] + 1
			else:
				dic_CTX[r] = 1
		for el in sorted(dic_CTX.items(), key= lambda (k,v) : (-v,k)):
			self.NOT5_cont.addItem(u"%d %s"%(el[1],re.sub("\\\,",",",el[0])))
				


def main():
	app = QtGui.QApplication(sys.argv)

	translator = QtCore.QTranslator()
	#self.translator.load('translations/en_GB') 
	#translator.load('translations/fr_FR') 
	translator.load('translations/'+ QtCore.QLocale.system().name())
	app.installTranslator(translator)

	ex  = Principal()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
