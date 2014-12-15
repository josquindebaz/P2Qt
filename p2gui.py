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
	def __init__(self,h = '127.0.0.1',p = '4000'):
		self.c = interface_prospero.ConnecteurPII() 
		self.c.set(h,p)
		self.teste_connect()

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

	def eval_var(self,var):
		self.eval_var_result = self.c.eval_variable(var)

	def eval_get_sem(self,exp,sem):
		# jp : pour retrouver la sémantique d'un élément : (getsem 'nucléaire' $ent )
		exp = exp.encode('utf-8')
		return self.c.eval_fonc("getsem:%s:%s" % (  exp , sem) )


class Principal(QtGui.QMainWindow):
	def __init__(self):
		super(Principal, self).__init__()
		self.initUI()
		

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

		SET11 =  QtGui.QLabel()
#		Prop1Image = QtGui.QPixmap("prop1.png")
#		SET11.setPixmap(Prop1Image)
		SET12 =  QtGui.QLabel()
#		Prop2Image = QtGui.QPixmap("prop2.png")
#		SET12.setPixmap(Prop2Image)
		SET13 =  QtGui.QLabel()
#		Prop3Image = QtGui.QPixmap("prop3.png")
#		SET13.setPixmap(Prop3Image)
		SET14 =  QtGui.QLabel()
#		Prop4Image = QtGui.QPixmap("prop4.png")
#		SET14.setPixmap(Prop4Image)
		SET15 =  QtGui.QLabel()
#		Prop5Image = QtGui.QPixmap("prop5.png")
#		SET15.setPixmap(Prop5Image)

		SET1 = QtGui.QTabWidget()
		#SET1.addTab(SET11,u"Propriétés saillantes")
#		SET1.addTab(SET12,u"Apports et reprises")
#		SET1.addTab(SET13,u"Eléments du texte")
#		SET1.addTab(SET14,u"Textes proches")
#		SET1.addTab(SET15,u"Textes identiques")


		T2 =  QtGui.QLabel()
#		CTXImage = QtGui.QPixmap("CTX.png")
#		T2.setPixmap(CTXImage)

		T3 =  QtGui.QLabel()
#		TextImage = QtGui.QPixmap("Text.png")
#		T3.setPixmap(TextImage)


		SubWdwSE = QtGui.QTabWidget()
#		SubWdwSE.addTab(SET1,"Prop")
#		SubWdwSE.addTab(T2,"CTX")
#		SubWdwSE.addTab(T3,"Text")


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
		#<jp>
		self.CorpusTexts.itemClicked.connect(self.onSelectTextFromCorpus)
		#</jp>
		self.SOT1.addTab(self.CorpusTexts,"corpus")
		# on fait disparaître le bouton close de la tab CorpusTexts, a gauche pour les mac
		if self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide):
			self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide).resize(0,0)
			self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.RightSide).hide()
		elif self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide):
			self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).resize(0,0)
			self.SOT1.tabBar().tabButton(0, QtGui.QTabBar.LeftSide).hide()
		
		#l'onglet des réseaux
		self.tabNetworks = QtGui.QTabWidget()
		self.tabNetworks.setTabsClosable(True)
		self.tabNetworks.tabCloseRequested.connect(self.tabNetworks.removeTab)

		# <jp>
		# onglet proprietes des textes
		self.textProperties = QtGui.QTabWidget()
		self.textProperties.setTabsClosable(True)
		self.textProperties.tabCloseRequested.connect(self.textProperties.removeTab)
		# </jp>
#TODO les expressions englobantes

		#mise en place des onglets

		self.SubWdwSO.addTab(self.SOT1,"Texts")
		self.SubWdwSO.addTab(self.tabNetworks,"Networks")
		# <jp>
		self.SubWdwSO.addTab(self.textProperties,"Text properties")
		# </jp>


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
		self.Param_Server_path_P2.setText("/Users/gspr/Documents/Prospero-II-serveur/prospero-II.app/Contents/MacOS/prospero-II")

		Param_Server_path_P2_button = QtGui.QPushButton("select local server path")
		Param_Server_R.addWidget(Param_Server_path_P2_button)
		Param_Server_path_P2_button.clicked.connect(self.select_P2_path)

		self.Param_Server_path_PRC = QtGui.QLineEdit()
		#Param_Server_R.addRow("Corpus path",self.Param_Server_path_PRC)
		Param_Server_R.addRow(self.Param_Server_path_PRC)
		self.Param_Server_path_PRC.setText("/Users/gspr/corpus/telephonie/0-projets/TELasso.prc")

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
		self.Param_Server_val_host.setText('127.0.0.1')
		self.Param_Server_val_port = QtGui.QLineEdit()
		Param_Server_R.addRow("&port",self.Param_Server_val_port)
		self.Param_Server_val_port.setText('4000')
		self.Param_Server_B = QtGui.QPushButton('Connect to server')
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

		server_vars_Hbox = QtGui.QHBoxLayout()
		server_vars_champL = QtGui.QFormLayout()
		self.server_vars_champ = QtGui.QLineEdit()
		self.server_vars_champ.returnPressed.connect(self.server_vars_Evalue)
		server_vars_champL.addRow("&var",self.server_vars_champ)
		server_vars_Hbox.addLayout(server_vars_champL)
		server_vars_button_eval = QtGui.QPushButton('Eval')
		server_vars_Hbox.addWidget(server_vars_button_eval)
		server_vars_button_eval.clicked.connect(self.server_vars_Evalue)
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
		self.NOT1select.addItem(u"collections")
		#self.NOT1select.addItem(u"entities") # trop long a répondre
		self.NOT1select.addItem(u"fictions")
		self.NOT1select.addItem(u"entitie's categories")
		NOT1VHC.addWidget(self.NOT1select)
		self.connect(self.NOT1select,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.select_liste)


	# un spacer pour mettre les commandes sur la droite
		spacer3 = QtGui.QLabel()
		spacer3.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
		NOT1VHC.addWidget(spacer3)
		
	# les commandes
		self.NOT1Commands1 = QtGui.QPushButton()
		self.NOT1Commands1.setIcon(QtGui.QIcon("loupe.png"))
		self.NOT1Commands1.setEnabled(False) #desactivé au lancement, tant qu'on a pas d'item 
		NOT1Commands1Menu = QtGui.QMenu(self)
		#NOT1Commands1Menu.addAction('&search')
		#NOT1Commands1Menu.addAction('&sort')
		#NOT1Commands1Menu.addAction('&filter')
		NOT1VHC.addWidget(self.NOT1Commands1)


		self.NOT1Commands2 = QtGui.QPushButton()
		self.NOT1Commands2.setIcon(QtGui.QIcon("gear.png"))
		self.NOT1Commands2.setEnabled(False) #desactivé au lancement, tant qu'on a pas de liste
		NOT1Commands2Menu = QtGui.QMenu(self)
		NOT1Commands2Menu.addAction('network' , self.show_network)
		NOT1Commands2Menu.addAction('texts' , self.show_texts)
		self.NOT1Commands2.setMenu(NOT1Commands2Menu)
		NOT1VHC.addWidget(self.NOT1Commands2)


	#une box horizontale pour liste, score et deploiement
		NOT1VH = QtGui.QHBoxLayout()
		NOT1V.addLayout(NOT1VH) 
	#la liste
		self.NOT12 = QtGui.QTableWidget()
		NOT1VH.addWidget(self.NOT12)

		#police un peu plus petite
		self.NOT12.setFont(QtGui.QFont("DejaVu Sans", 11))
		#pas de header de ligne
		self.NOT12.verticalHeader().setVisible(False)
		
		#selection d'un item
		self.NOT12.itemClicked.connect(self.liste_item_clicked)

		#le deploiement
		self.NOT12_D = QtGui.QListWidget()
		NOT1VH.addWidget(self.NOT12_D)
		self.NOT12_D.itemClicked.connect(self.liste_D_item_clicked)

		self.NOT12_E = QtGui.QListWidget()
		NOT1VH.addWidget(self.NOT12_E)


		#NOT2 =  QtGui.QLabel()
#		FrmlImage = QtGui.QPixmap("formul.png")
#		NOT2.setPixmap(FrmlImage)

		#NOT3 =  QtGui.QLabel()
#		ExploImage = QtGui.QPixmap("explo.png")
#		NOT3.setPixmap(ExploImage)



		SubWdwNO.addTab(NOT1,"Lists")
#		SubWdwNO.addTab(NOT2,"Formulae")
#		SubWdwNO.addTab(NOT3,"Explorer")

		# 1 layout vertical dans lequel sont insérés 2 layout horizontals
		main = QtGui.QWidget()
		h1_layout = QtGui.QVBoxLayout()
		vl1_layout = QtGui.QHBoxLayout()
		vl2_layout =QtGui.QHBoxLayout()
		
		h1_layout.addLayout(vl1_layout)
		h1_layout.addLayout(vl2_layout)
		
		vl1_layout.addWidget(SubWdwNO)
		vl1_layout.addWidget(self.SubWdwNE)
		
		vl2_layout.addWidget(self.SubWdwSO)
		vl2_layout.addWidget(SubWdwSE)
		
		main.setLayout(h1_layout)
		self.setCentralWidget(main)
		#la MdiArea 
		'''
		Area = QtGui.QMdiArea()
		sw4 = Area.addSubWindow(SubWdwNO , flags = QtCore.Qt.FramelessWindowHint)
		sw3 = Area.addSubWindow(self.SubWdwNE , flags = QtCore.Qt.FramelessWindowHint)
		sw2 = Area.addSubWindow(self.SubWdwSO, flags = QtCore.Qt.FramelessWindowHint)
		sw1 = Area.addSubWindow(SubWdwSE, flags = QtCore.Qt.FramelessWindowHint)

		#QMdiArea.WindowOrder = QMdiArea.CreationOrder
		Area.setActivationOrder(QtGui.QMdiArea.CreationOrder) 
		
		#PySide.QtGui.QWorkspace.scrollBarsEnabled(True)
		#AreascrollBarsEnabled()
		Area.tileSubWindows()

		self.setCentralWidget(Area)
		'''	
		self.setWindowTitle(u'Prospéro II 28/10/2014')	
		#self.showMaximized() 
		self.show()

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
		self.status.showMessage(message)
		self.History.append("%s: %s" % (datetime.datetime.now(),message))

	def recup_liste_textes(self):
		self.activity(u"Waiting for text list"   )
		self.client.recup_texts()
		self.activity(u"Displaying text list (%d items)" %len(self.client.txts)  )
		self.SOT1.tabBar().setTabText(0,"corpus (%d)"%len(self.client.txts))
		self.CorpusTexts.clear()
		listeTextes = self.client.txts
		self.CorpusTexts.addItems(listeTextes)
	#<jp>
	def onSelectTextFromCorpus(self):
		print"onSelectTextFromCorpus"
		item_txt = self.CorpusTexts.currentItem().text()
		self.onSelectText(item_txt)
		
	def onSelectText(self,item_txt):
		"""
		essai - sur la sélection d'un texte (ds les textes du corpus) on met à jour
		un/des tab dans text Properties
		"""
		#item_txt = self.CorpusTexts.currentItem().text()
		self.activity(u"%s selected " % (item_txt)) 
		self.semantique_txt_item = self.client.eval_get_sem(item_txt, "$txt" )
		self.show_textContent(item_txt , self.semantique_txt_item)
		self.show_textProperties(item_txt , self.semantique_txt_item)
	def getvalueFromSem(self,item_txt,type):	
		sem = self.client.eval_get_sem(item_txt, type )
		val = self.client.eval_var(sem)
		return val
	#</jp>
	def select_liste(self,typ):
		""" quand un type de liste est selectionné """
			
		self.activity(u"Waiting for  %s list" % (typ)) 
		self.sem_liste_concept = self.get_semantique()
		content = self.client.recup_liste_concept(self.sem_liste_concept)
		self.activity(u"Displaying %s list (%d items)" % (typ,len(content)))
		self.change_liste(content)


	def change_liste(self,content):
		self.NOT12.clearContents()
		self.NOT12_D.clear()
		self.NOT12_E.clear()
		self.NOT12.setRowCount(len(content))
		self.NOT12.setColumnCount(2)
		self.NOT12.setHorizontalHeaderLabels(['Score','Object'])

		row = 0 
		for item in content:
			itemwidget = QtGui.QTableWidgetItem(item)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable

			#C'EST TROP LENT !!!!! C'EST PAS DANS L'ORDRE !!!!
			#semantique = self.client.eval_get_sem(item,self.sem_liste_concept) #NE RENVOIE PAS $col2 sur AaC, pb sur le dico, manque type ?
			#sem_poids = semantique + ".val" 
			#self.client.eval_var(sem_poids)	
			#itemwidgetS = QtGui.QTableWidgetItem(self.client.eval_var_result)
			#itemwidgetS.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non editable

			#self.NOT12.setItem(row,0,itemwidgetS) 
			self.NOT12.setItem(row,1,itemwidget)
			row += 1

		self.NOT12.resizeColumnToContents(0)
		self.NOT12.horizontalHeader().setStretchLastSection(True)
		# definir la hauteur apres la largeur donne un resultat plus propre et constant
		self.NOT12.resizeRowsToContents()

	

	def liste_item_clicked(self):
		"""
						suite au changement de sélection d'un élément , mettre à jour
					les vues dépendantes 
		"""

		item = self.NOT12.currentItem().text() # l'element selectionné
		self.activity("%s selected" % item)
		self.NOT12_D.clear() # on efface la liste
		self.NOT12_E.clear()
		sem = self.sem_liste_concept
		if ( sem  == "$col" or sem == "$ef" )  :
			# recupere la designation semantique de l'element
			self.semantique_liste_item = self.client.eval_get_sem(item, sem )
			self.client.eval_var("%s.rep[0:]"% self.semantique_liste_item)
			result = re.split(", ", self.client.eval_var_result)
			for r in result:
				self.NOT12_D.addItem( r ) 
			## il coupe la fin du dernier element ???????

		#activation des boutons de commande
		#self.NOT1Commands1.setEnabled(True) 
		self.NOT1Commands2.setEnabled(True) 


	def liste_D_item_clicked(self):
		item = self.NOT12_D.currentItem().text() # l'element selectionné
		row = self.NOT12_D.currentRow() 
		self.activity("%s selected" % item)
		self.NOT12_E.clear() # on efface la liste
		ask = "%s.list_rep%d.rep[0:]" % (self.semantique_liste_item,row)
		self.client.eval_var(ask)
		result = re.split(", ", self.client.eval_var_result)
		for r in result:
			self.NOT12_E.addItem( r ) 
			
	def server_vars_Evalue(self):
		var = self.server_vars_champ.text()
		self.server_vars_champ.clear()
		self.client.eval_var(var)
		self.server_vars_result.setColor("red")
		self.server_vars_result.append("%s" % var)
		self.server_vars_result.setColor("black")
		self.server_vars_result.append(self.client.eval_var_result)

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
			self.select_liste(self.NOT1select.currentText())
			self.recup_liste_textes()
			self.Param_Server_B.clicked.connect(self.disconnect_server)
			self.Param_Server_B.setText("Disconnect")
			# donne le focus a l'onglet history
			self.SubWdwNE.setCurrentIndex(self.History_index)
	
	def disconnect_server(self):
		self.activity("Disconnecting")
		self.client.disconnect()
		self.Param_Server_B.setText('Connect to server')
		self.Param_Server_B.clicked.connect(self.connect_server)
	#<jp>
	def show_textContent(self ,txt,  sem_txt):
		"""
			on met le contenu du texte 
			puis un ctrl layout horizontal dans lequel on insert 2 ctrl de liste
		"""
		show_txt_widget = QtGui.QWidget()
		show_VBox_layout = QtGui.QVBoxLayout()
		show_VBox_layout.setContentsMargins(0,0,0,0) 
		show_VBox_layout.setSpacing(0) 

		show_txt_widget.setLayout(show_VBox_layout)
		index = self.textProperties.addTab(show_txt_widget,"%s" % txt)
		
		contentText_semantique = "%s.ph[0:]" % sem_txt
		self.activity(u"Displaying text for %s " % contentText_semantique )
		
		self.client.eval_var(contentText_semantique)
		txt_content = self.client.eval_var_result
		
		text_widget =  QtGui.QTextEdit(txt_content)
		show_VBox_layout.addWidget(text_widget)
		
		# un Vbox horizontal dans lequel on place 3 listes
		# essai visualisation acteurs principaux
		show_HBox_layout = QtGui.QHBoxLayout()
		show_HBox_layout.setContentsMargins(0,0,0,0) 
		show_HBox_layout.setSpacing(0)
		#show_txt_widget.setLayout(show_txt_box)
		show_VBox_layout.addLayout(show_HBox_layout)


		list_atcants_box =  QtGui.QListWidget()
		show_HBox_layout.addWidget(list_atcants_box)
		list_act_sem = "%s.act[0:]" % sem_txt
		self.activity(u"Wating for %s " % list_act_sem )
		self.client.eval_var(list_act_sem)
		list_act  = self.client.eval_var_result
		L = re.split(", ",list_act)
		list_atcants_box.addItems(L)
		
		# les collections

		list_col_box =  QtGui.QListWidget()
		show_HBox_layout.addWidget(list_col_box)
		list_col_sem = "%s.col[0:]" % sem_txt
		self.activity(u"Wating for %s " % list_col_sem )
		self.client.eval_var(list_col_sem)
		list_col_box.addItems(re.split(", ",self.client.eval_var_result))	
		self.textProperties.setCurrentIndex(index)# donne le focus a l'onglet créé		
		
		
		
		self.SubWdwSO.setCurrentIndex(2)
		
		
		actants_tableView = QtGui.QTableWidget()
		show_HBox_layout.addWidget(actants_tableView)
		actants_tableView.setRowCount(len(L))
		actants_tableView.setColumnCount(2)
		actants_tableView.setHorizontalHeaderLabels(['Score','Element'])

		row = 0 
		for item in L:
			itemwidget = QtGui.QTableWidgetItem(item)
			itemwidget.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non-editable
			# $txt123.act3.val
			# PB ne peut pas retrouver/calculer une sémantique interne à une autre
			# genre $txt4.act2  ou $ent3.res3  avec "$txt" "$act" -- > 2 inconnues
			# mais on peut le faire si la première variable est connue ; ex "$txt3"
			#on n'aura plus qu'à chercher le $act ... mais il faut l'implémenter sous P-II 
			sem= self.client.eval_get_sem(item,"%s.%s.self.sem_liste_concept") 
			#C'EST TROP LENT !!!!! C'EST PAS DANS L'ORDRE !!!!
			#semantique = self.client.eval_get_sem(item,self.sem_liste_concept) #NE RENVOIE PAS $col2 sur AaC, pb sur le dico, manque type ?
			#sem_poids = semantique + ".val" 
			#self.client.eval_var(sem_poids)	
			#itemwidgetS = QtGui.QTableWidgetItem(self.client.eval_var_result)
			#itemwidgetS.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable) #non editable

			#self.NOT12.setItem(row,0,itemwidgetS) 
			actants_tableView.setItem(row,1,itemwidget)
			row += 1

		
		
	def show_textProperties(self ,txt,  sem_txt):
		"""
			on met le contenu du texte 
		"""
		show_txt_widget = QtGui.QWidget()
		show_txt_box = QtGui.QVBoxLayout()
		show_txt_box.setContentsMargins(0,0,0,0) 
		show_txt_box.setSpacing(0) 

		show_txt_widget.setLayout(show_txt_box)
		index = self.textProperties.addTab(show_txt_widget,"%s" % txt)
		
		props_widget = QtGui.QTextEdit()
		show_txt_box.addWidget(props_widget)
		
		
		
		for props in [u"auteur_txt", u"titre_txt", u"date_txt"] :
			props_sem  = "%s.%s" % (sem_txt,props)
			self.activity(u"Displaying  %s " % props_sem )
		
			self.client.eval_var(props_sem)
			value = self.client.eval_var_result
		
			props_widget.append(value )
			
		
		self.textProperties.setCurrentIndex(index)# donne le focus a l'onglet créé		

		self.SubWdwSO.setCurrentIndex(2)
		
				
		
		
	#</jp>
	def show_network(self):
#TODO recuperer les autres niveaux de liste
		#if  self.NOT12_E.currentItem() :
		#	element = self.NOT12_E.currentItem().text() 
		#elif self.NOT12_D.currentItem():
		#	element = self.NOT12_D.currentItem().text() 
		#else :
		#	element = self.NOT12.currentItem().text() 
		element = self.NOT12.currentItem().text() 

#TODO si la tab de l'element existe déjà, la raffraichir et ne pas en créer une nouvelle
		show_network_widget = QtGui.QWidget()
		show_network_box = QtGui.QVBoxLayout()
		# on prend toute la place
		show_network_box.setContentsMargins(0,0,0,0) 
		show_network_box.setSpacing(0) 

		show_network_widget.setLayout(show_network_box)
		index = self.tabNetworks.addTab(show_network_widget,"%s" % element)
		self.activity(u"Displaying network for %s (limited to 200 items)" % element )

		#selecteur de concept
		net_sel_concept = QtGui.QComboBox()
		net_sel_concept.addItems([u"entities"])
		show_network_box.addWidget(net_sel_concept)

#TODO scores
#TODO deploiement
#TODO pb encodage sur certains concepts

		Network_list =  QtGui.QListWidget()
		show_network_box.addWidget(Network_list)
		res_semantique = "%s.res[0:200]" % self.semantique_liste_item  
		self.client.eval_var(res_semantique)
		Network_list.addItems(re.split(", ",self.client.eval_var_result))
		self.tabNetworks.setCurrentIndex(index)# donne le focus a l'onglet créé
		self.SubWdwSO.setCurrentIndex(1)# donne le focus a l'onglet Networks

	def show_texts(self):
		element = self.NOT12.currentItem().text() 
#TODO recuperer les autres niveaux de liste
#TODO scores/date/titre
		self.client.eval_var("%s.txt[0:]"%self.semantique_liste_item)
		liste_textes = re.split(", ",self.client.eval_var_result)
		self.activity(u"Displaying %d texts for %s" % (len(liste_textes),element) )

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
			
			
			
			txt_sem = self.client.eval_get_sem(txt, "$txt" )
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
		

		index = self.SOT1.addTab(show_texts_widget,"%s (%d)" % (element,len(liste_textes)))
		self.SOT1.setCurrentIndex(index)# donne le focus a l'onglet
		self.SubWdwSO.setCurrentIndex(0)# donne le focus a l'onglet Texts
		self.SOT1.tabBar().setTabToolTip(index,"%s %d"%(element,len(liste_textes)))
		



def main():
	app = QtGui.QApplication(sys.argv)
	ex  = Principal()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
