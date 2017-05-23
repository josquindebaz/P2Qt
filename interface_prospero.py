#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on 5 mars 2012

@author: jean-pierre Charriau

module de communication avec un serveur P-II pour l'évaluation des variables mrlw dont le rendu/l'évaluation dépend des calculs de P-II

une variable est transformée en une séquence de messages envoyés les uns à la suite des autres vers P-II, la séquence
se terminant par un message "F" signalant la fin de la séquence.
L'envois successifs de ces messages permet à P-II de retrouver s'ils ont déjà été calculés les différentes objets correspondant
aux composantes de la variable ( dans l'exemple ci-dessous, $aut0 puis $act1 seront retrouvés par P-II permettant de contextualiser/évaluer
correctement la dernière composante phadt ... un énoncé aléatoire avec auteur/date/titre, de l'acteur 1 chez l'auteur 0 )
  


			E:signature	# les objets que calcule P-II sont aussi mis en cache par P-II . la signature permet d'y accéder
			V:typeVariable:signature  		# V indique une variable
			P:n  		 # position/indice de la variable précédente
			BI:n   		# cas d'un accès par tranche  [] pour la variable précédente
			BS:m
			ARG:xxx		# lorsque des paramètres sont transmis ( $aut0.phadt[0:10].+xxx  spécifiant une contrainte supplémentaire (présence de xxx))
			F:			# fin du bloc de message 
			
			$aut0.act1.phadt sera transformé en la séquence suivante: 
			
			E:aut0.act1.phadt		# la signature complète
			V:aut:aut0		# la première composante variable 
			P:0				# position de la première V
			V:act:act1		# la seconde composante variable
			P:1				# position de la seconde V
			V:phadt:phadt	# troisième composante ( sans position ni tranche .. donc aléatoire)
			F				# code de fin de message
"""
#from settings import hostPII , portPII , logger

eval_status_done = 0
verbose = 0
import os.path
import threading, socket, time , re
#from eval_variable import eval_variables
#from globals import getMapDossiers , log_file_name_messages
from fonctions import is_random_var
# regex pour isoler les parties d'une variable ctx
#  $txt10.ctx.titre  $ctx  $ctx.titre[0:]  (?P<V_TRANCHE>(\[.*\]))
regex_txt_ctx = re.compile (r"""\$(?P<V_TXT>txt)(?P<V_POS>(\d+))(\$|\.)(?P<V_CTX>ctx)(\.)(?P<V_FIELD>(.*))""", re.VERBOSE | re.DOTALL)
regex_ctx = re.compile (r"""(\$|\.)(?P<V_CTX>(ctx))\.(?P<V_FIELD>(.*?))(?P<V_TRANCHE>(\[.*\]))""", re.VERBOSE | re.DOTALL)
regex_uniq_tranche  = re.compile (r"""(\[)(?P<BI>-?\d*):(?P<BS>-?\d*)(\])""", re.VERBOSE | re.DOTALL)
# on exclue le signe + pour ne pas reconnaître +truc+bidule
regex_var = re.compile (r"""(?P<VAR>[a-zA-Z_]+)($|\s)+""", re.VERBOSE | re.DOTALL)
# pour $aut0.phadt[0:10].+truc+machin ou '+truc+machin' est analysée par la regex
# Attention : aux lettres accentuées !
regex_var_args = re.compile (r"""\+(?P<ARG>.*?)$""", re.VERBOSE | re.DOTALL)
# reconnaissance de aut10
regex_indice = re.compile (r"""(?P<VAR>[a-zA-Z_]*)(?P<INDICE>\d+)$|\s""", re.VERBOSE | re.DOTALL)
# reconnaissance de aut[0:10]
#regex_tranche = re.compile (r"""(?P<VAR>[a-zA-Z_]*)\[(?P<BI>-?\d*):(?P<BS>-?\d*)\]""", re.VERBOSE | re.DOTALL)
# reconnaissance de aut[0:10]   et des formes {} txtp{0;9}	
regex_tranche = re.compile (r"""(?P<VAR>[a-zA-Z_]*)(\[|{)(?P<BI>-?\d*):(?P<BS>-?\d*)(\]|})""", re.VERBOSE | re.DOTALL)
# reconnaissance de aut[-1]
regex_tranche_indice = re.compile (r"""(?P<VAR>[a-zA-Z_]*)\[(?P<INDICE>-?\d*)\]""", re.VERBOSE | re.DOTALL)	
	
# pour reperer dans les var -> .res[0:10] ou .res123
regex_reseau_tranche = re.compile (r"""(.*?)(?P<res>\.res)\[(?P<BI>-?\d*):(?P<BS>-?\d*)\]""", re.VERBOSE | re.DOTALL)
regex_reseau_tranche_skip = re.compile (r"""(?P<SKIP>\[.*?\])""", re.VERBOSE | re.DOTALL)
regex_reseau_indice = re.compile (r"""(.*?)(?P<res>\.res)(\d+)""", re.VERBOSE | re.DOTALL)
regex_reseau_indice_skip = re.compile (r"""\.res(?P<SKIP>\d+)""", re.VERBOSE | re.DOTALL)
# retrouver le nom du gestionnaire de formule dans $gescdf.mesFormules0 $gescdf.mesFormules[0:]  (le $gescdf. est déjà traité)
regex_gescdf_name = re.compile (r"""(?P<NOM>.*?)($|\s|\d|\[)+""", re.VERBOSE | re.DOTALL)
# pour les sfrm
regex_sfrm_forme = re.compile (r"""(?P<VAR>forme.*)($|\s)+""", re.VERBOSE | re.DOTALL)
# pour les cdf + def  $cdf.def[0:]
regex_sfrm_def = re.compile (r"""(?P<VAR>def.*)($|\s)+""", re.VERBOSE | re.DOTALL)
# pour les phadt
# $sfrm.formule.phadt $sfrm.formule.phadt0 $sfrm.formule.ph $sfrm.formule.ph[0:]
#regex_sfrm_ph = re.compile (r"""(?P<VAR>ph.*?)(\d|\[)""", re.VERBOSE | re.DOTALL)
regex_sfrm_listvar = re.compile (r"""(?P<VAR>listvar.*?)""", re.VERBOSE | re.DOTALL)
regex_sfrm_ph = re.compile (r"""(?P<VAR>ph.*?)""", re.VERBOSE | re.DOTALL)
# pour les X ... ds les sfrm ... par defaut puisque les noms de variables sont libres X Y Z etc..
regex_sfrm_var = re.compile (r"""(?P<VAR>.*?)(\d|\[)""", re.VERBOSE | re.DOTALL)
# pour les variables liés X=toto
regex_sfrm_link_var = re.compile (r"""(?P<VAR>.*?)=(?P<VAL>.*?)(\.|$)""", re.VERBOSE | re.DOTALL)

# regex complémentaire pour isoler les args dans le cas ou le premier arg n'a pas de '+' ( .$Obj+truc )
regex_ph_args_bis =  re.compile (r"""(?P<var>\$.*?)\.(?P<arg_incorrect>.*?)\+(?P<arg>.*?)$""",  re.VERBOSE | re.DOTALL )

regex_VAR = re.compile (r"""(\s+|^)/VAR=(?P<var>.*?)(\s+|$)""",  re.VERBOSE | re.DOTALL)
regex_FILE_VAR = re.compile (r"""(\$\]\n.*?)\[""",  re.VERBOSE |  re.MULTILINE | re.DOTALL)

regex_POUR_VAR = re.compile (r"""\$\]\n(.*?)\n(.*)""",  re.VERBOSE |  re.MULTILINE | re.DOTALL)

regex_FILE_VAR2 = re.compile (r"""(\[\$\]\n.*?\[|$)*?""",  re.VERBOSE |   re.DOTALL)

class ConnecteurPII (threading.Thread): 
	""" Pourquoi dériver la class de threading.Thread ? -> utilisation du RLock
		car pas d'exec de la méthode start/run ...
	"""
	def __init__ (self):
		threading.Thread.__init__(self)
		self.host = ''
		self.port = '' 
		self.connexion = None
		self.m_cache_fonc = {}
		self.m_cache_index = {}
		self.m_cache_var ={}
		self.m_threadlock = threading.RLock() # verrou reentrant
		self.data_to_eval=None

	def set(self, ip, port):
		self.host = ip
		self.port = port 

	def run (self):
		if verbose : print "thread running"
		if not self.connexion : 
			if not self.connect():
				return ""			
		while 1:
			
			if self.data_to_eval :
				#if verbose : print "evalue " + self.data_to_eval
				ev= self.eval_variable(self.data_to_eval)	# bloquant
				#if verbose : print "valeur =  ",ev
				self.data_to_eval=None
				
				
	def put_to_eval(self,data):			
		self.data_to_eval=data		
				
	def connect(self):
		self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connexion.setblocking(1)
		while 1 :
			try:			
				if (verbose): print "connexion au serveur ", self.host, " port : ", self.port
				self.connexion.connect((self.host, int(self.port)))
				time.sleep(0.5)
				return True
			except socket.error:			
				print "Connection failed"
				time.sleep(1)
				return False
				
	def connect_x(self,x):
		"""try to connect x times with 10 intervals then return True or False"""
		i = 1
		r = False
		while ((i <= x) and (not r)):
			if (verbose): print " attempt to connect %d on %d" % (i,x)
			try:			
				if (verbose): print "connexion au serveur ", self.host, " port : ", self.port
				self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.connexion.setblocking(1)
				self.connexion.connect((self.host, int(self.port)))
				r = True
			except socket.error:			
				print "Connection failed"
				time.sleep(10)
			i += 1
		return r

	def disconnect(self):
		self.send_expression("CLOSE")
		time.sleep(1)
		self.connexion.close()
		self.connexion = None

	def send_var_for_frm_old(self, dic_of_frm_var):
		"""envois des variables utilisées par les frm
		"""
		if not self.connexion : 
			if not self.connect():
				return ""
		for var in dic_of_frm_var.keys():
			
			mess = "E:VAR_CONSTRUCTOR"
			self.send_expression(mess)
			mess = "VAR:" + var
			self.send_expression(mess)
			for terme in dic_of_frm_var[var].getTextExpanded() :
				mess = "ARG:" + terme
				self.send_expression(mess)
			self.send_expression("F")
			self.get_value("send_var_for_frm")

	def send_dossiers(self):
		"""
		envois des définitions de dossier à P-II
		"""
		if not self.connexion : 
			if not self.connect():
				return ""
		dic_dossier = getMapDossiers()
		for dossier in dic_dossier.keys():
			if (verbose) :
				print "dossier envoyé" , dossier
			mess = "E:DOSSIER_CONSTRUCTOR"
			self.send_expression(mess)
			mess = "DOSSIER:" + dossier
			self.send_expression(mess)
			for definition in dic_dossier[dossier] :
				mess = "ARG:" + definition
				self.send_expression(mess)
			self.send_expression("F")
			value = self.get_value("send_dossiers")

		self.send_expression("E:DOSSIER_CONSTRUCTOR")
		self.send_expression("DOSSIER_EXEC")
		self.send_expression("F")
		self.get_value("send_dossiers")			

	def add_cache_var(self,cle,val):
		self.m_cache_var[cle] = val

	def remove_from_cache(self , sem):
		'''
			on retire ttes les cles contenant sem
			$entef sera retire si sem==ent ou sem=ef
		'''
		lkey = self.m_cache_fonc.keys()
		for k in lkey:
			if k.find(sem) != -1:
				del self.m_cache_fonc[k]
		lkey = self.m_cache_index.keys()
		for k in lkey:
			if k.find(sem) != -1:
				del self.m_cache_index[k]
		lkey = self.m_cache_var.keys()
		for k in lkey:
			if k.find(sem) != -1:
				del self.m_cache_var[k]
	def add_cache_fonc (self, data, value):
		self.m_cache_fonc[data] = value

	def add_cache_index(self, data, value):
		self.m_cache_index[data] = value

	def eval_vect_values(self,  sem_type, type_value):
		'''
			sem_type = $ent
			type_value= freq
			renvoit le vecteur des frequence des entités
		'''
		#print sem_type,"     ",type_value
		self.m_threadlock.acquire()
		
		cle = sem_type + type_value
		if cle in self.m_cache_var.keys():
			self.m_threadlock.release()
			return self.m_cache_var[cle]
		
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_vect( sem_type,type_value) 
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value()
		self.add_cache_var(cle, value)
		self.m_threadlock.release()
		return value		

	def eval_set_ctx(self,text, props,value):
		'''
	
		'''
		self.m_threadlock.acquire()
		
		cle = text + props +value
		if cle in self.m_cache_var.keys():
			self.m_threadlock.release()
			return self.m_cache_var[cle]
		
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_set_ctx( (text,props,value) )
		for exp in lexpr :
			if (verbose) :
				print "exp:%s" % exp
			self.send_expression(exp)
		#value = self.get_value()
		# est-ce nécessaire ????
		self.get_value()
		# on met en cache la nouvelle valeur
		self.add_cache_var(cle, value)
		self.m_threadlock.release()
		return value		

	def eval_ctx(self,props,ctx_range):
		'''
		usage vecteur de data 
			props = titre
			ctx_range = [0:]
			
			signature -> $ctx.titre[0:]
		'''
		self.m_threadlock.acquire()
		
		cle = "$ctx." + props +  ctx_range
		if cle in self.m_cache_var.keys():
			self.m_threadlock.release()
			return self.m_cache_var[cle]
		
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_ctx(props,ctx_range )
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value()
		self.add_cache_var(cle, value)
		self.m_threadlock.release()
		return value

	def eval (self, L):
		"""
			on calcul la forme/clé et la lexpr  avant.
			ex :
				L = c.creer_msg_search ( u"$search.rac" , u"présid" , pelement="0" ,txt=True, ptxt="0", ph=True ,pph="[0:]")
				cle = "$search.rac" +	
		"""
		cle = L[0]
		lexpr = L[1]
		self.m_threadlock.acquire()
		
		if cle in self.m_cache_fonc.keys():
			self.m_threadlock.release()
			return self.m_cache_fonc[cle]
		
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""

		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value()
		
		
		# il faut tester la cle pour voir si on met en cache ou pas la valeur
		if not is_random_var(cle):	
			self.add_cache_fonc(cle, value)
			
		self.m_threadlock.release()
		return value

	def eval_fonct (self, fonc, element,sem):
		"""
			cas du getsem : on interroge P-II pour obtenir la sémantique avec indice
			 d'un élément ( on fournit la sémantique ..)
			 getsem "ELEMENT-NT*" $col
			 dans le cache 
			 on peut aussi avoir
			 getsem "ELEMENT-NT*" $ent ....
			 donc mémorise une clé ok
			 clé : "ELEMENT-NT*$col" et val sera $col0
			 
			 
		"""
		
		self.m_threadlock.acquire()
		cle = element + sem 
		if cle in self.m_cache_fonc.keys():
			self.m_threadlock.release()
			return self.m_cache_fonc[cle]
		
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_fonct(fonc , element, sem)
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value()
		self.add_cache_fonc(cle, value)
		self.m_threadlock.release()
		return value


		
	def eval_sfrm(self, data):
		
		self.m_threadlock.acquire()
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_sfrm(data)
		for exp in lexpr :
			self.send_expression(exp)
		ev = self.get_value(data)
		
		self.m_threadlock.release()
		return ev

	def eval_index(self, data):
		""" interrogation de P-II sur le/les types associés à data
		"""
		self.m_threadlock.acquire()
		# si le/les types de data ont déjà été recherché on les retrouve dans le cache
		if data in  self.m_cache_index.keys():
			self.m_threadlock.release()
			return self.m_cache_index[data]

		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		
			
			
		lexpr = [ "FONC:index", "ARG:" + data, "F"]
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value(data)
		# renvoyer
		# [[ que [ $mo] ][peuxs-tu [ $epre] [dire ..][sur []] ]...
		# [['fais', ['$epreuve']], ['un', ['$mo']], ['micro-rapport', ['$ent', '$entef']] ,[sur [] ]
		L = []
		LE = []
		SL = []
		try :
			for x in value.split('\n'):
				if x :
					x = x.replace('\n', '')
					code , val = x.split(':', 1)
					if code == 'OBJ':
						if LE : 
							LE.append(SL)
							L.append(LE)
						LE = [val]
						SL = []
					elif code == 'SEM' :
						if not val in SL :SL.append(val)
			if LE : 
				LE.append(SL)
				L.append(LE)
		except:
			if (verbose) :
				print "exception pb encodage"
			logger.info("exception  pb encodage")
			self.m_threadlock.release()
			return ""
		# mise en cache pour la fois suivante 
		self.add_cache_index(data, L)
		self.m_threadlock.release()
		
		return L




	def get_value(self ,info=None)  :
		#	version tenant compte du code S ou L en premiere position
		try:
			taille = self.connexion.recv(10)
			taille_mess = int(taille)
			#print "---taille data à recevoir : " ,taille_mess
			#data = self.connexion.recv(taille_mess)
			data = self.connexion.makefile().read(taille_mess)
			#print "---taille data reçue :  " ,len(data)
			#print data
		except :
			print "get_value() echec connexion  ressaye"
			if not self.connect(): # on ressaye
				return ""
			try :
				taille = self.connexion.recv(10) 
				taille_mess = int(taille)
				if (verbose) :
					print taille_mess
				data = self.connexion.makefile().read(taille_mess)
				
			except :
				print "get_value() echec connexion  ECHEC "
				return ""
		if data :

			if data[0] == 'L':	# L"xxx\,yyyy\,zzzz"
				data = data[1:].split('\,')
			elif data == "SNone": # "SNone"
				data = ""
			else: # "Sxxxxxx"
				data = data[1:]

		data = data.decode('utf-8')	
		return data					


	
	def eval_variable(self, var,user_env=None,corpus_env=None,env_dialogue=None):
		""" 
			
		"""


		if (verbose):
			print var 

		self.m_threadlock.acquire()

		if var in self.m_cache_var.keys():
			self.m_threadlock.release()
			ev = self.m_cache_var[var]
			print " in cache ", ev
			return ev
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lmess = self.creer_msg(var,user_env,corpus_env,env_dialogue)
		if not lmess :
			self.m_threadlock.release() 
			return ''
		for exp in lmess :
			self.send_expression(exp)
			
		ev = self.get_value(var)
		
		if not is_random_var(var):
			self.m_cache_var[var]  = ev
		self.m_threadlock.release()
		#if (verbose):	# avec py2exe -> erreur de charmap
		#	print var , "  " , ev
		return ev
	

	
	def stop(self):
		self.m_threadlock.acquire()
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
			
		self.send_expression("STOP")
		self.m_threadlock.release()
		
	def load(self, path):
		self.m_threadlock.acquire()
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
			
		self.send_expression("LOAD:" + path)
		self.m_threadlock.release()		
		
	


	def send_expression(self, expression):
		""" 
			test avec un autre serveur
			buf[0]= 0XBE
			buf[1]= size
			buf[..]= data
			
			Si PB avec le serveur ... relancer la connexion 
		"""
		
		try:
			expression = expression.encode('utf-8')
		except:
			pass
		#data = chr(190) # ':' 0XBE 190
		data = chr(16)  # DLE ? .. 0X10 16
		try :
			
			
			data += chr(len(expression))
			data += expression
		except:
			print "send_expression pb" , expression
			return 
		try :
			self.connexion.send(data)
		except :
			if not self.connect():
				print "acces P-II impossible"
				return 

	def creer_msg_search(self,fonc ,element, pelement='',txt=False,ptxt='',ph=False,pph='',val=False):
		"""
			calculer la liste des messages aux serveurs
			renvoyer cette liste et la clé pour la mise en cache locale
		
		fonc = $search.rac  $search.pre $search.suf
		element = chaine recherchée
		
		indice_resultat  (  O (indice), [0:] (tranche) , "" (rien, aléatoire) )
		
		creer_msg_search ( "$search.rac" , "présid" , "0" )
			$search.rac.présid.pO
		creer_msg_search ( "$search.rac" , "présid" , "[0:]" )
			$search.rac.présid.p[0: ]
		creer_msg_search ( "$search.rac" , "présid" , "0" , val=True)	
			$search.rac.présid.pO.val
		creer_msg_search ( "$search.rac" , "présid" , "0" ,txt=True, ptxt="0", val=True)	
			$search.rac.présid.pO.txt0.val
		creer_msg_search ( "$search.rac" , "présid" , "0" ,txt=True, ptxt="[0:]")		
			$search.rac.présid.pO.txt[0:]
		creer_msg_search ( "$search.rac" , "présid" , "0" ,txt=True, ptxt="0", ph=True ,pph="[0:]")		
			$search.rac.présid.pO.txt0.ph[0:]
		
		"""	
		
		lexpr = []
		# E:search.rac.chaine recherchée
		# la signature étant : "search.rac.chaine recherchée" + indice , txt etc...
		fonc = fonc.encode('utf-8')
		fonc = fonc[1:] # vire le $
		
		element =  element.encode('utf-8')

		if verbose : print [fonc, element]

		#signature = fonc + '.' + element
		# la signature doit integre ttes les specifications (pour se distinguer entre elles (utilisee comme cle pour les acces aux objets))
		signature = fonc + '.' + element + "." + pelement
		if txt :
			signature += ".txt" + ptxt	#   .txt0 .txt[0] etc
		if ph :
			signature += ".ph" + pph
		if val:
			signature += ".val"	
		cle = signature
		
		lexpr.append("E:" +signature)
		''' 	search
				ou searchcs
		'''
		
		f =  fonc.split('.')[0]
		#lexpr.append("V:search:" +signature + "." +  pelement )
		# 
		#lexpr.append("V:" + f +":" +signature + "." +  pelement )
		lexpr.append("V:" + f +":" + fonc + "." + element + "." +  pelement )
		# le premier ARG indiquera rac pre ou suf
		if signature.find('.rac.') != -1:
			lexpr.append("ARG:rac" )
		if signature.find('.pre.') != -1:
			lexpr.append("ARG:pre" )
		if signature.find('.suf.') != -1:
			lexpr.append("ARG:suf" )
		lexpr.append("ARG:" +element)
		lexpr.append("FARG:")	# ajouté pour signaler la fin des arg sur WSearch
		
		if pelement:  
                        L = self.get_token_tranche(pelement)
			lexpr += L
			cle += pelement
			
		if txt :
			lexpr.append("V:txt:txt" + ptxt  )
			cle += "txt"
			if ptxt:
				L = self.get_token_tranche(ptxt)
				lexpr += L
				cle +=ptxt
				
		if ph:
			
			lexpr.append("V:ph:ph" + pph  )
			cle += "ph"
			if pph:
				L = self.get_token_tranche(pph)
				lexpr += L
				cle += pph
		if val:
			lexpr.append("V:val:val" )
			cle +="val"
		lexpr.append('F')

		if (verbose) :
			print lexpr

		return (cle, lexpr)

	def get_token_tranche(self, data):
		lexpr=[]
		m2 = regex_tranche.search(data) 
		if m2 :
 			if not m2.groupdict('BI')['BI'] : g1 = 999999
			else : g1 = m2.groupdict('BI')['BI']
			if not m2.groupdict('BS')['BS'] : g2 = 999999
			else : g2 = m2.groupdict('BS')['BS']
			g1 = str(g1)
			g2 = str(g2)
			lexpr.append("BI:" + g1)
			lexpr.append("BS:" + g2)
		else:
			lexpr.append("P:"+ data  )		
		return lexpr
	
	def eval_op_concept(self, concept_or_rep, op,type_concept,concept=u"",rep_or_new_name=u""):
		'''
			concept_or_rep est soit gestion_concept operations sur les concepts 
			soit "gestion_rep_concept" operation (add remove), sur les rep d'un concept
			
			rep_or_new_name est soit un new_name ds le cas 1 avec rename, soit un rep dans le cas 2
			
			reseter le cache pour les cles contenant type_concept (ef col cat_ent)
			et + encore . une modif sur un ef peut modifier la liste des $ent $entef etc..
			
			
			
		'''
		if concept_or_rep == "gestion_concept":
			L = self.creer_msg_concept(concept_or_rep , op, type_concept, concept, rep_or_new_name)
		if concept_or_rep == "gestion_rep_concept":
			L = self.creer_msg_rep_concept(concept_or_rep , op, type_concept, concept, rep_or_new_name)
			
		ev =  self.eval (  (concept_or_rep, L) )
		self.remove_from_cache(type_concept)
		if type_concept == 'ef':
			self.remove_from_cache("ent")
		
		return ev
		
	def creer_msg_concept(self,concept_or_rep, op,type_concept,concept=u"",new_name=u""):
		'''
			FONC:gestion_concept
			ARG:save add remove rename
			ARG:type concept ( col ef cat_ent cat_mar cat_epr cat_qua )
			ARG:le concept
			ARG:le nouveau nom (si rename)
			F:
			
			FONC:gestion_concept
			ARG:save
			ARG:type concept
			F:
			
			FONC:gestion_concept
			ARG:rename
			ARG:type concept
			ARG:ETAT@->ministère
			ARG:ETAT@->Ministères
			F:

			FONC:gestion_concept
			ARG:add
			ARG:type concept
			ARG:ETAT@->...
			F:

		'''
		lexpr = []
		lexpr.append("FONC:" + concept_or_rep.encode('utf-8'))
		lexpr.append("ARG:" + op.encode('utf-8'))
		lexpr.append("ARG:" + type_concept.encode('utf-8'))
		if concept: 
			lexpr.append("ARG:" + concept.encode('utf-8'))
		if new_name: 
			lexpr.append("ARG:" + new_name.encode('utf-8'))

		lexpr.append('F')
		if (verbose) :
			print lexpr
		return lexpr	
	def creer_msg_rep_concept(self,concept_or_rep, op,type_concept,concept=u"",rep=u""):
		'''
			FONC:gestion_rep_concept
			ARG:add remove
			ARG:type concept (ef col cat_ent)
			ARG:le concept
			ARG:le rep
			F:
			
		'''
		lexpr = []
		lexpr.append("FONC:" + concept_or_rep.encode('utf-8'))
		lexpr.append("ARG:" + op.encode('utf-8'))
		lexpr.append("ARG:" + type_concept.encode('utf-8'))
		if concept: 
			lexpr.append("ARG:" + concept.encode('utf-8'))
		if rep: 
			lexpr.append("ARG:" + rep.encode('utf-8'))

		lexpr.append('F')
		if (verbose) :
			print lexpr
		return lexpr			
	def creer_msg_fonct(self,fonc,element,sem):
		"""
		
			pour l'appel de getsem + ARG
			FONC:getsem
			ARG:pirate
			ARG:$entef
			F
			
			bogue : 
				c:corpus
				$txt
				le : est maltraité dans le split
				
		
		"""	
		
		lexpr = []
		lexpr.append("FONC:" +fonc)
		lexpr.append("ARG:" +element.encode('utf-8')) 
		lexpr.append("ARG:" +sem.encode('utf-8'))
		lexpr.append('F')
		if (verbose) :
			print lexpr
		return lexpr

	def creer_msg_set_ctx (self,data):
		'''
			data -> ($txt4 , champ, valeur)
			data -> ($txt4 , "title" , "ceci est un titre")
			data -> ($txt4 , "author" , "Max")
	
			ARG:$txt4
			ARG:title
			ARG:ceci est un titre
			F

			E:txt4.title.ceci est un titre
			C:txt:txt4		cible du message suivant
			M:SETCTX
			P:4
			ARG:title
			ARG:ceci est un titre
			F
			
			
		'''
		
		lexpr = []
		vtext,champ,valeur = data	
		if vtext[0] == '$' : 
			vtext = vtext[1:]# vire le $
		indice = vtext.replace ('txt','')
		lexpr.append("E:" + vtext + "." + champ + "." + valeur)
		lexpr.append("C:txt:" +vtext)
		lexpr.append("M:SETCTX")
		lexpr.append("P:"+indice)		# P sert à repérer la cible du message
		lexpr.append("ARG:"+champ)
		lexpr.append("ARG:"+valeur)
		lexpr.append('F')
		if (verbose) :
			print lexpr
		return lexpr



	def getSignature (self, v):
		"""
		 pour le message E:signature
		 on corrige certaines choses 
		"""
		r = regex_reseau_indice.search(v)
		if r:
			r1 = regex_reseau_indice_skip.search(v)
			v = v.replace(r1.group('SKIP'), '')
		r = regex_reseau_tranche.search(v)
		if r:
			r1 = regex_reseau_tranche_skip.search(v)
			v = v.replace(r1.group('SKIP'), '')
		return v
	def creer_msg_sfrm(self, data):
		"""spécifique aux sfrm !
		$sfrm.Evts-marquants.forme0
			E:sfrm.Evts-marquants.forme0
			S:SFRM:Evts-marquant
			S:FORM:forme0n
			P:0
		
		$sfrm.Evts-marquants.X0
			E:sfrm.Evts-marquants.X0
			S:SFRM:Evts-marquant
			S:V:X:X0
			P:0
		$sfrm.Evts-marquants.val
			E:sfrm.Evts-marquants.X0
			S:SFRM:Evts-marquant
			S:val:val
			P:0			
		$sfrm.Evts-marquants.X=xyz.forme0
			E:sfrm.Evts-marquants.X=xyz.forme0
			S:SFRM.Evts-marquants
			S:VL:X:xyz
			S:forme:forme0
			P:0
			F:
			
		$sfrm.Evts-marquants.X0.forme0.phadt[0:10]
			E:sfrm.Evts-marquants.X0.forme0.phadt[0:10]
			S:sfrm.Evts-marquants
			S:V:X:X0
			P:0
			S:FORM:forme0
			P:0
			S:PH:phadt[0:10]
			BI:0
			BS:10

		$cdf.mesFormules[0:]
			E:gescdf.mesFormules[0:]
			S:GESCDF:mesFormules
			BI:0
			BS:999999
			F
		$cdf.mesFormules0
			E:gescdf.mesFormules[0:]
			S:GESCDF:mesFormules
			P:0
			F			
		"""
		if data[0] == '$' : data = data[1:]
		L = data.split('.')

		lexpr = []
		
		# signature particuliere pour les .res
		signature = self.getSignature(data)
		lexpr.append("E:" + signature)
		
		
		last_var_expr = ''  
		
		flag_next_is_gescdf_name = flag_next_is_class_name = False
		construct_exp = ''
		for terme in L :
			if terme == 'cdf':
				construct_exp = "S:SFRM:"  # on y consera le nom de la cfrm (exception $cdf.def !)
				flag_next_is_class_name = True
				continue
			if terme == 'gescdf':
				construct_exp = "S:GESCDF:"  
				flag_next_is_gescdf_name = True # ce qui suit est le nom du gestionnaire de formule ...
				continue			
			# definition des classes -> pour avoir la liste des formules
			# $cdf.def[0:]
			# $cdf.def
			m = regex_sfrm_def.search(terme)
			if m: 
				# on finit lexpr.append(construct_exp) dans le cas $cdf.def[0:]
				# mais dans $cdf.maformule.def[0:] construct_exp a été traité
				if construct_exp:
					construct_exp += terme
					lexpr.append(construct_exp)
				lexpr.append("V:def:" + terme)
				flag_next_is_class_name = False
				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue		
			if flag_next_is_class_name:
				construct_exp += terme
				flag_next_is_class_name = False
				lexpr.append(construct_exp)
				construct_exp = ''
				continue
			if flag_next_is_gescdf_name :  # $gescdf.mesFormules[0:] $gescdf.mesFormules0 $gescdf.mesFormules0.def0 $gescdf.mesFormules0.val
				# on doit isoler 'mesFormules' dans terme 
				flag_next_is_gescdf_name = False
				m = regex_gescdf_name.search(terme)
				if m:
					nom_gescdf = m.groupdict('NOM')['NOM']
					construct_exp += nom_gescdf
					lexpr.append(construct_exp)
					construct_exp =''
				else:
					print "erreur de reconnaissance du nom du gestionnaire de formules " + terme 
				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue				
				continue
			m = regex_sfrm_forme.search(terme)
			if m : 
				# indice ou tranche ... ou aleatoire ?
				# m.groupdict ->  forme[0:5]

				lexpr.append("S:FORM:" + terme)

				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue
				# pour les cas phadt[-1]
				m = regex_tranche_indice.search(terme)
				if m:  # on enverra un indice negatif ... gerer par P-II
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("PL:" + m.groupdict('INDICE')['INDICE'])
					continue
					
			m = regex_sfrm_ph.search(terme)
			if m :

				lexpr.append("S:PH:" + terme)

				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue
				m = regex_tranche_indice.search(terme)
				if m:  # on enverra un indice negatif ... gerer par P-II
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("PL:" + m.groupdict('INDICE')['INDICE'])
					continue
			# $sfrm.FORMULEX.val
			if terme == "val":
				lexpr.append("V:val:" + terme)
				continue
			m = regex_sfrm_listvar.search(terme)
			if m :

				lexpr.append("S:listvar:" + terme)

				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue
				m = regex_tranche_indice.search(terme)
				if m:  # on enverra un indice negatif ... gerer par P-II
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("PL:" + m.groupdict('INDICE')['INDICE'])
					continue			
			# cas des X X0 X[0:10]  par defaut 
			m = regex_sfrm_var.search(terme)
			if m : 

				nom_var = m.groupdict('VAR')['VAR']
				lexpr.append("S:V:" + nom_var + ":" + terme) # ???   S:V:X:X0
				#last_var_expr="V:" + m.groupdict('VAR')['VAR']+ ":" + m.groupdict('VAR')['VAR']
				# indice ou tranche ?
				m = regex_indice.search(terme)
				m2 = regex_tranche.search(terme) 
				if m :
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("P:" + m.groupdict('INDICE')['INDICE'])
					continue
				elif m2 : 

					if not m2.groupdict('BI')['BI'] : g1 = 999999
					else : g1 = m2.groupdict('BI')['BI']
					if not m2.groupdict('BS')['BS'] : g2 = 999999
					else : g2 = m2.groupdict('BS')['BS']
					g1 = str(g1)
					g2 = str(g2)
					lexpr.append("BI:" + g1)
					lexpr.append("BS:" + g2)
					continue
				m = regex_tranche_indice.search(terme)
				if m:  # on enverra un indice negatif ... gerer par P-II
 
					#last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":"+ m.groupdict('VAR')['VAR']+m.groupdict('INDICE')['INDICE']
					#lexpr.append(last_var_expr)
					lexpr.append("PL:" + m.groupdict('INDICE')['INDICE'])
					continue
			m = regex_sfrm_link_var.search(terme)
			if m:	

				nom_var = m.groupdict('VAR')['VAR']
				val = m.groupdict('VAL')['VAL']
				lexpr.append('S:VL:' + nom_var + ":" + val)
			# par defaut il reste des variables ... sans indice ni tranche ( $gescdf.mesFormules0.X $gescdf.mesFormules0.def0.X
			# mais conflit avec les variables aléatoires (sans indice ni tranche) -> utiliser listvar0 ..
			

		lexpr.append('F')
		return lexpr
	def creer_msg_vect(self, type, type_value):
		'''
			type -> ent qual col fic
			type_value -> frequence déploiement ,nbtxt nbaut date first apparition , date last apparition ...
			E:ent[0:999999].freq			#signature de l'objet correspondant sur le serveur
			C:ent				# pour la construction d'un WType sur ent
			M:freq					# indique le mode de valuation de la liste
			BI:0
			BS:999999
			F
		'''
		if type[0] == '$' : type = type[1:]
		L=[]
		# juste les tranches max [0:]
		L.append("E:" + type +"[0:]." + type_value)
		L.append ("C:"  + type)
		L.append ("M:"  + type_value)
		VBI = "BI:0"
		VBS = "BS:999999"
		L.append(VBI)
		L.append(VBS)
		L.append("F")
		return L

	def creer_msg_ctx_old(self,props, ctx_range):
		'''
			$ctx.titre[0:]
			$ctx.date[0:]
			$ctx.auteur[0:]
			$ctx.champ libre 1[0:]		# ??? � voir
			
			
			E:signature	# les objets que calcule P-II sont mis en cache . la signature permet d'y acc�der
			V:typeVariable:signature  
			P:n  		 # position/indice de la variable
			BI:n   		# cas d'un acc�s par tranche  []
			BS:m
			ARG:xxx		# lorsque des param�tres sont transmis ( $aut0.phadt[0:10].+xxx  sp�cifiant une contrainte suppl�mentaire (pr�sence de xxx))
			F:	
			E:ctx.titre[0:]
			PROPS:titre						# Ajouté
			V:ctx:ctx.titre[0:]
			BI:0
			BS:99999
			ARG:titre
			F
		'''
		typevar = "ctx"
		var  = typevar + "." + props  + ctx_range
		L = []
		L.append("E:" + var)
		L.append("PROPS:"+props)
		L.append("V:" + typevar + ":" + var  )
		# juste les tranches max [0:]
		VBI = "BI:0"
		VBS = "BS:999999"
		L.append(VBI)
		L.append(VBS)
		
		L.append ("F")
		return L

	def creer_msg_ctx(self,data):
		'''
		data = 
			$ctx.titre[0:]
			$ctx.date[0:]
			$ctx.auteur[0:]
			$ctx.champ libre 1[0:]		# ??? � voir
			
			$txt0.ctx.titre
			$txt0.ctx.champ du cadre de ref
			
			
			E:signature	# les objets que calcule P-II sont mis en cache . la signature permet d'y acc�der
			V:typeVariable:signature  
			P:n  		 # position/indice de la variable
			BI:n   		# cas d'un acc�s par tranche  []
			BS:m
			ARG:xxx		# lorsque des param�tres sont transmis ( $aut0.phadt[0:10].+xxx  sp�cifiant une contrainte suppl�mentaire (pr�sence de xxx))
			F:	
			E:ctx.titre[0:]
			PROPS:titre						# Ajouté
			V:ctx:ctx.titre[0:]
			BI:0
			BS:99999
			ARG:titre
			F
		'''
		#print data
		L=[]
		L.append("E:" + data)
		
		if data == "$ctx":
			L.append("V:ctx:ctx")
			L.append ("F")
			return L
		r = regex_txt_ctx.search(data)
		if r:
			#print r.groupdict()
			L.append("V:txt:"+r.groupdict()['V_TXT']+r.groupdict()['V_POS']) 
			L.append("P::"+r.groupdict()['V_POS']) 
			L.append("PROPS:"+r.groupdict()['V_FIELD'])
			L.append("V:ctx:"+r.groupdict()['V_CTX']) 
			L.append ("F")
			return L
		r = regex_ctx.search(data)
		if r:
			#print r.groupdict()
			L.append("PROPS:"+r.groupdict()['V_FIELD'])
			L.append("V:ctx:"+ data[1:])	# signature côté serveur
			tranche = r.groupdict()['V_TRANCHE']
			r1 = regex_uniq_tranche.search(tranche)
			if r1:
				#print r1.groupdict()
				if not r1.groupdict('BI')['BI'] : g1 = 999999
				else : g1 = r1.groupdict('BI')['BI']
				if not r1.groupdict('BS')['BS'] : g2 = 999999
				else : g2 = r1.groupdict('BS')['BS']
				VBI = "BI:"+str(g1)
				VBS =  "BS:"+str(g2)
				L.append(VBI)
				L.append(VBS)
			L.append ("F")
		return L


			

	def creer_msg_old(self, data,user_env,corpus_env,env_dialogue):
		"""
			transforme l'expression en une séquence de messages qui seront envoyés à P-II
			
			
			E:signature	# les objets que calcule P-II sont mis en cache . la signature permet d'y accéder
			V:typeVariable:signature  
			P:n  		 # position/indice de la variable
			BI:n   		# cas d'un accès par tranche  []
			BS:m
			ARG:xxx		# lorsque des paramètres sont transmis ( $aut0.phadt[0:10].+xxx  spécifiant une contrainte supplémentaire (présence de xxx))
			F:			# fin du bloc de message 
			
			$aut0.act1.phadt sera converti en 
			
			E:aut0.act1.phadt
			V:aut:aut0
			P:0
			V:act:act1
			P:1
			V:phadt:phadt
			F
	
			code 'PL' pour indiquer une position partant de la fin d'une liste ( $act[-1]  )
	
			E:aut0.act1.phadt[-1]
			V:aut:aut0
			P:0
			V:act:act1
			P:1
			V:phadt:phadt
			PL:-1
			F



			avec des paramètres ...
			$aut0.act1.phadt[0:10].+truc+machin sera converti en 
			E:aut0.act1.phadt[0:10]   # signature
			V:aut:aut0		
			P:0
			V:act:act1
			P:1
			V:phadt:phadt[0:10].+truc+machin   # il faut les args ds la signature !
			BI:0
			BS:10
			ARG:truc
			ARG:machin
			F


			E:signature utilisée ds le cache
			remarque : pour les reseaux, (res, inf ,resact,respers ) la signature doit être sans les indices/tranches
			puisque P-II calcule le réseau (d'entités, de catégories, d'acteurs,de personnes) d'un objet une fois,
			$act0.res est calculé une fois, les accès $act0.res1 $act0.res2 $act0.res[0:10] se résumant à une sélection d'éléments
			dans le réseau existant.
			
			$act0.res[0:10] -> $act0.res
			$act0.res[0:98] -> $act0.res
			$act0.res0 -> $act0.res
			$act0.res1 -> $act0.res
			$aut4.ph.+$aut4.act0+$aut4.act0.res1 --> d'où l'utilisation du mask, et l'évaluation des args 
			
			modification 3/07/2012
			traitement des {} formes liste à renvoyer
			
				Pb du séparateur ',' utilisé dans les formes [] (quasi identique aux formes [] )
				mais les variables $ph utilisées avec [] ou {} peuvent renvoyer du contenu avec des "," !!
				il faut donc que le code de séparation des items renvoyés soit différent de "," dans le cas des {}
			
				chaque message reçu (getvalue) contiendra en première position S ou L indiquant le type string ou list
				ds le cas du type list, getvalue créera une liste ( split(separ)) 
				
				il faut reconnaître les {} dans les variables afin d'envoyer un code 'L' à P-II pour qu'il indique 
				
			
		"""
		data = data.encode('utf-8')
		
		if data.find ('ctx'):
			return 
		
		
		
		
		mask = "TUVXYZ"

		# provisoire : repérage des {}
		if data.find('{') != -1:
			forme_liste = True
		else:
			forme_liste = False
		

		if data[0] == '$' : data = data[1:]
		
		# si on a une variable contenant des args $aut0.act0.ph.+$aut4.act0+$aut4.act0.res1 on masque '+...'

		liste_eval_args=[]
		r = regex_var_args.search(data)
		if r:
			args = r.group('ARG') # tout ce qui suit le premier '+'
			data = data.replace(args,mask) 
			"""
				évaluer les args commençant par $ pour construire la liste des args évalués
			"""
			#largs =  r.group('arg_incorrect').split('+') # ['$V', '$X', 'bidule'] ???
			largs = args.split('+')
			for a in largs :
				if not a : continue  # quand .+xxx+yyy arg_incorrect  ne contient rien !
				if a[0] =='$' :
					ev = eval_variables( a , user_env, corpus_env,env_dialogue)
					if not ev: # échec de l'évaluation
						return []
					liste_eval_args.append(ev)
				else:
					liste_eval_args.append(a)
			if not liste_eval_args:  # eviter le cas $phxxx.+
				return []
			new_args = "" + "+".join(liste_eval_args)
		L = data.split('.')
		lmess = [] # contiendra les messages à envoyer à P-II
		
		# signature particuliere pour les .res
		signature = self.getSignature(data)
		lmess.append("E:" + signature)

		last_var_expr = ''  # pour l'accrochage des args  V:phadt:phadt0 --> V:phadt:phadt0.+xxx+yyy
		
		for terme in L :
			
			
			m = regex_var_args.search(terme) # recherche in '+TUVXYZ' en premier avant regex_var
			if m:
				forme = "."
				for arg in liste_eval_args :
					lmess.append("ARG:" + arg)
					forme = forme + "+" + arg
					
				# mettre à jour la signature de la dernière variable V:
				if last_var_expr :
					last_var_expr_with_args = last_var_expr + forme
					# maj de la forme ds la liste lmess
					for i in range(len(lmess)) :
						if lmess[i] == last_var_expr : 
							lmess[i] = last_var_expr_with_args
							break
				else:
					print "error !" 
				continue # !!


			m = regex_var.search(terme)
			if m : 

				last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":" + m.groupdict('VAR')['VAR']
				lmess.append(last_var_expr)

				
			m = regex_indice.search(terme) 
			if m :
 
				last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":" + m.groupdict('VAR')['VAR'] + m.groupdict('INDICE')['INDICE']
				lmess.append(last_var_expr)
				lmess.append("P:" + m.groupdict('INDICE')['INDICE'])
			m = regex_tranche.search(terme) 
			if m : 
				# pb des aut[:-3] traduit par ('aut', '', '-3')
				# ou aut[3:] ('aut', '3', '')

				if not m.groupdict('BI')['BI'] : g1 = 999999
				else : g1 = m.groupdict('BI')['BI']
				if not m.groupdict('BS')['BS'] : g2 = 999999
				else : g2 = m.groupdict('BS')['BS']
				g1 = str(g1)
				g2 = str(g2)
				nom_var= m.groupdict('VAR')['VAR']
				if forme_liste:
					last_var_expr = "V:" + nom_var + ":" + nom_var + "{" + g1 + ":" + g2 + "}"
				else:
					last_var_expr = "V:" + nom_var + ":" + nom_var + "[" + g1 + ":" + g2 + "]"
				lmess.append(last_var_expr)
				lmess.append("BI:" + g1)
				lmess.append("BS:" + g2)
				
			m = regex_tranche_indice.search(terme)
			if m:  # on enverra un indice negatif ... gerer par P-II
 
				indice =  m.groupdict('INDICE')['INDICE']
				nom_var =  m.groupdict('VAR')['VAR']
				
				if forme_liste :
					lmess.append("V:" + nom_var +":" + nom_var + "{" + indice + "}")
				else:
					lmess.append("V:" + nom_var +":" + nom_var + "[" + indice + "]")
				lmess.append("PL:" + indice)
				continue
			
			
		if forme_liste:
			lmess.append('L')
		lmess.append('F')
		
		# si un mask , il reste un mask sur une signature ..
		if r :
			L = []
			for terme in lmess:
				L.append(terme.replace(mask,new_args))
			lmess = L
		return lmess

		
	def creer_msg(self, data,user_env='',corpus_env='',env_dialogue=''):
		"""
			transforme l'expression en une séquence de messages qui seront envoyés à P-II
			
			
			E:signature	# les objets que calcule P-II sont mis en cache . la signature permet d'y accéder
			V:typeVariable:signature  
			P:n  		 # position/indice de la variable
			BI:n   		# cas d'un accès par tranche  []
			BS:m
			ARG:xxx		# lorsque des paramètres sont transmis ( $aut0.phadt[0:10].+xxx  spécifiant une contrainte supplémentaire (présence de xxx))
			F:			# fin du bloc de message 
			
			$aut0.act1.phadt sera converti en 
			
			E:aut0.act1.phadt
			V:aut:aut0
			P:0
			V:act:act1
			P:1
			V:phadt:phadt
			F
	
			code 'PL' pour indiquer une position partant de la fin d'une liste ( $act[-1]  )
	
			E:aut0.act1.phadt[-1]
			V:aut:aut0
			P:0
			V:act:act1
			P:1
			V:phadt:phadt
			PL:-1
			F



			avec des paramètres ...
			$aut0.act1.phadt[0:10].+truc+machin sera converti en 
			E:aut0.act1.phadt[0:10]   # signature
			V:aut:aut0		
			P:0
			V:act:act1
			P:1
			V:phadt:phadt[0:10].+truc+machin   # il faut les args ds la signature !
			BI:0
			BS:10
			ARG:truc
			ARG:machin
			F


			E:signature utilisée ds le cache
			remarque : pour les reseaux, (res, inf ,resact,respers ) la signature doit être sans les indices/tranches
			puisque P-II calcule le réseau (d'entités, de catégories, d'acteurs,de personnes) d'un objet une fois,
			$act0.res est calculé une fois, les accès $act0.res1 $act0.res2 $act0.res[0:10] se résumant à une sélection d'éléments
			dans le réseau existant.
			
			$act0.res[0:10] -> $act0.res
			$act0.res[0:98] -> $act0.res
			$act0.res0 -> $act0.res
			$act0.res1 -> $act0.res
			$aut4.ph.+$aut4.act0+$aut4.act0.res1 --> d'où l'utilisation du mask, et l'évaluation des args 
			
			modification 3/07/2012
			traitement des {} formes liste à renvoyer
			
				Pb du séparateur ',' utilisé dans les formes [] (quasi identique aux formes [] )
				mais les variables $ph utilisées avec [] ou {} peuvent renvoyer du contenu avec des "," !!
				il faut donc que le code de séparation des items renvoyés soit différent de "," dans le cas des {}
			
				chaque message reçu (getvalue) contiendra en première position S ou L indiquant le type string ou list
				ds le cas du type list, getvalue créera une liste ( split(separ)) 
				
				il faut reconnaître les {} dans les variables afin d'envoyer un code 'L' à P-II pour qu'il indique 
				
			
		"""
		data = data.encode('utf-8')
		
		if data.find('ctx') != -1 :
			return self.creer_msg_ctx(data)
		
		
		mask = "TUVXYZ"

		# provisoire : repérage des {}
		if data.find('{') != -1:
			forme_liste = True
		else:
			forme_liste = False
		

		if data[0] == '$' : data = data[1:]
		
		# si on a une variable contenant des args $aut0.act0.ph.+$aut4.act0+$aut4.act0.res1 on masque '+...'

		liste_eval_args=[]
		r = regex_var_args.search(data)
		if r:
			args = r.group('ARG') # tout ce qui suit le premier '+'
			data = data.replace(args,mask) 
			"""
				évaluer les args commençant par $ pour construire la liste des args évalués
			"""
			#largs =  r.group('arg_incorrect').split('+') # ['$V', '$X', 'bidule'] ???
			largs = args.split('+')
			for a in largs :
				if not a : continue  # quand .+xxx+yyy arg_incorrect  ne contient rien !
				if a[0] =='$' :
					ev = eval_variables( a , user_env, corpus_env,env_dialogue)
					if not ev: # échec de l'évaluation
						return []
					liste_eval_args.append(ev)
				else:
					liste_eval_args.append(a)
			if not liste_eval_args:  # eviter le cas $phxxx.+
				return []
			new_args = "" + "+".join(liste_eval_args)
		L = data.split('.')
		lmess = [] # contiendra les messages à envoyer à P-II
		
		# signature particuliere pour les .res
		#signature = self.getSignature(data)
		signature = data
		lmess.append("E:" + signature)

		last_var_expr = ''  # pour l'accrochage des args  V:phadt:phadt0 --> V:phadt:phadt0.+xxx+yyy
		
		for terme in L :
			
			
			m = regex_var_args.search(terme) # recherche in '+TUVXYZ' en premier avant regex_var
			if m:
				forme = "."
				for arg in liste_eval_args :
					lmess.append("ARG:" + arg)
					forme = forme + "+" + arg
					
				# mettre à jour la signature de la dernière variable V:
				if last_var_expr :
					last_var_expr_with_args = last_var_expr + forme
					# maj de la forme ds la liste lmess
					for i in range(len(lmess)) :
						if lmess[i] == last_var_expr : 
							lmess[i] = last_var_expr_with_args
							break
				else:
					print "error !" 
				continue # !!


			m = regex_var.search(terme)
			if m : 

				last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":" + m.groupdict('VAR')['VAR']
				lmess.append(last_var_expr)

				
			m = regex_indice.search(terme) 
			if m :
 
				last_var_expr = "V:" + m.groupdict('VAR')['VAR'] + ":" + m.groupdict('VAR')['VAR'] + m.groupdict('INDICE')['INDICE']
				lmess.append(last_var_expr)
				lmess.append("P:" + m.groupdict('INDICE')['INDICE'])
			m = regex_tranche.search(terme) 
			if m : 
				# pb des aut[:-3] traduit par ('aut', '', '-3')
				# ou aut[3:] ('aut', '3', '')

				if not m.groupdict('BI')['BI'] : g1 = 999999
				else : g1 = m.groupdict('BI')['BI']
				if not m.groupdict('BS')['BS'] : g2 = 999999
				else : g2 = m.groupdict('BS')['BS']
				g1 = str(g1)
				g2 = str(g2)
				nom_var= m.groupdict('VAR')['VAR']
				if forme_liste:
					last_var_expr = "V:" + nom_var + ":" + nom_var + "{" + g1 + ":" + g2 + "}"
				else:
					last_var_expr = "V:" + nom_var + ":" + nom_var + "[" + g1 + ":" + g2 + "]"
				lmess.append(last_var_expr)
				lmess.append("BI:" + g1)
				lmess.append("BS:" + g2)
				
			m = regex_tranche_indice.search(terme)
			if m:  # on enverra un indice negatif ... gerer par P-II
 
				indice =  m.groupdict('INDICE')['INDICE']
				nom_var =  m.groupdict('VAR')['VAR']
				
				if forme_liste :
					lmess.append("V:" + nom_var +":" + nom_var + "{" + indice + "}")
				else:
					lmess.append("V:" + nom_var +":" + nom_var + "[" + indice + "]")
				lmess.append("PL:" + indice)
				continue
			
			
		if forme_liste:
			lmess.append('L')
		lmess.append('F')
		
		# si un mask , il reste un mask sur une signature ..
		if r :
			L = []
			for terme in lmess:
				L.append(terme.replace(mask,new_args))
			lmess = L
		return lmess
	def send_var_for_frm(self, dic_of_frm_var):
		"""envois des variables utilisées par les frm
			pas d'expansion ... des /VAR imbriqués ...
		"""
		if not self.connexion : 
			if not self.connect():
				return ""
		test=''
		for var in dic_of_frm_var.keys():
			
			mess = "E:VAR_CONSTRUCTOR"
			self.send_expression(mess)
			mess = "VAR:" + var
			self.send_expression(mess)
			for terme in dic_of_frm_var[var]:
				
				termeUTF8 = terme.encode('utf8')
				try:
					test += chr(len(termeUTF8))
				except:
					print termeUTF8
					print len(termeUTF8)
				
				mess = "ARG:" + terme
				self.send_expression(mess)
			self.send_expression("F")
			self.get_value("send_var_for_frm")
		
	def send_frm(self, dic_formules):
		"""envois des classe des formule vers P-II
			entête CFRM:nom_de_la_classe
					FRM:formule
					F:	
		"""
		if not self.connexion : 
			if not self.connect():
				return ""
		for cfrm in dic_formules.keys():
			
			mess = "E:CFRM_CONSTRUCTOR"
			self.send_expression(mess)
			mess = "CFRM:" + cfrm
			self.send_expression(mess)
			for frm in dic_formules[cfrm] :
				mess = "ARG:" + frm
				self.send_expression(mess)
			self.send_expression("F")
			value = self.get_value("send_frm")
		'''	
		# exec des frm par p-II
		self.send_expression("E:CFRM_CONSTRUCTOR")
		self.send_expression("CFRM_EXEC")
		self.send_expression("F")
		self.get_value("send_frm")
		'''

				
	def exec_frm (self):
		# exec des frm par p-II
		# on ne sait pas quel gestionnaire de formule va s'executer !
		self.send_expression("E:CFRM_CONSTRUCTOR")
		self.send_expression("CFRM_EXEC")
		self.send_expression("F")
		self.get_value("send_frm")
	def set_gesfrm_name (self, nom_du_gestionnaire):
		# exec des frm par p-II
		# on ne sait pas quel gestionnaire de formule va s'executer !
		# on nomme le gestionnaire avant d'initialiser les formules
		self.send_expression("E:CFRM_CONSTRUCTOR")
		self.send_expression("CFRM_NAME")
		mess = "ARG:" + nom_du_gestionnaire
		self.send_expression(mess)
		self.send_expression("F")
		self.get_value("send_gesfrm_name")

#############################################################################################
#	lecture des /VAR et des FRM (format P1)
# placer dans un dictionnaire
# 	et envois vers le serveur
def load_var( file,dic):
	
	f = open(file)
	data= f.read()
	data = unicode(data,"cp1252")
	f.close()
	#L2 = regex_FILE_VAR2.findall(data)
	
	L = regex_FILE_VAR.findall(data)
	test=''
	for r in L:
		x = regex_POUR_VAR.findall(r)
		var,data =x[0]
		var = var.replace('\n','').strip()
		data = data.split(u'\n')[:-1]
		
		#dataUTF8 = data.encode('utf8')
		#test += chr(len(dataUTF8))
		dic[var] = data
	return dic

def load_frm( file ,dic_var):
	"""
		format P1
		[DEF_FRM]
		ma_formule
		/!X /ENTITE est /!Y /QUALITE
		[DEF_FRM]
		qui-accuse-qui
		/!X /MAJENT /MO dénoncé /T=1 /!Y /MAJENT
		
		suite a la présence ds ces fichiers de définitions de variable [$]
		on passe le dic_var en paramètre.
	"""
	dic={}
	
	f = open(file)
	data= f.read()
	data = unicode(data,"cp1252")
	f.close()
	lines = data.split(u"\n")
	nomVAR = nomFRM =''
	LDEF = L =[]
	flg_nom=False
	flg_frm=False
	flg_def_var= flg_var_name = False
	
	for line in lines:
		line= line.strip()
		if line == "[$]": # présence de def de variable ds le fichier ... 
			if flg_frm : # on a qq chose a enregistrer
				dic[nomFRM] = L
				L=[]
			if flg_def_var : # on était déjà sur une variable
				if nomVAR :
					dic_var[nomVAR] = LDEF
					LDEF =[]
					nomVar=''
			
			flg_def_var = flg_nom = flg_frm = False
			flg_var_name = True	# la ligne suivante contient le nom de la var
			continue
		if line =="[DEF_FRM]":
			
			if flg_frm : # on a qq chose a enregistrer
				dic[nomFRM] = L
				L=[]
			if flg_def_var : # on était sur une variable
				if nomVAR :
					dic_var[nomVAR] = LDEF
					LDEF =[]
					nomVar=''
			flg_def_var = flg_frm = False					
			
			flg_nom=True
			continue
		if flg_nom :
			nomFRM = line
			L=[]
			flg_nom=False
			flg_frm=True
			continue
		if flg_frm:
			L.append(line)
		if flg_var_name:
			nomVAR = line
			flg_var_name = False
			flg_def_var = True
			continue
		if flg_def_var:
			LDEF.append(line)
			continue
	if flg_frm:
		dic[nomFRM]=L		
	if flg_def_var:
		if nomVAR :
			dic_var[nomVAR] = LDEF
	return (dic,dic_var)

def send_formules_mini(connecteur_pII , dic_formules, dic_Variables):
	"""
		lister les /VAR disponibles mentionnées dans les formules, pour pouvoir les envoyer à P-II
		avant d'envoyer les formules
		 
		 on envois ttes les variables ...
		 
		 puis on envois les définitions des variables au serveur. 
	"""
	#dic_formules = getMapFormules()
	#m_connecteur_pII.send_frm ( dic_formules)
	'''
	dic_of_vars_in_frm  = {}
	for cdf in dic_formules.keys():

		
		for frm in dic_formules[cdf]:
			copy = frm
			while 1:
				r = regex_VAR.search(copy)
				if r : 
					var = r.groupdict()['var']
					if var in dic_Variables.keys():
						obj_var = dic_Variables[var]
						obj_var.expansion(getMapVariables())
						dic_of_vars_in_frm[var]=  getMapVariables()[var]
					else :
						print " la variable n'existe pas !!!!!!!!!!!"
						
					copy=copy.replace("/VAR="+var,"",1)
				else:
					break	
	'''			
	#connecteur_pII.send_var_for_frm (dic_of_vars_in_frm )
	connecteur_pII.send_var_for_frm (dic_Variables )
	connecteur_pII.send_frm ( dic_formules)
	
def SHOW (V):		
	R = c.eval_variable(V)
	print R
def EVAL_SHOW_SFRM (V):		
	print V
	R = c.eval_sfrm(V)
	print V , " --> " ,R

	
def init_frm(c):
	folder_path="C:\Users\jean-pierre\workspace\PII\P2Qt"
	dic_var={}
	L = [ "mrlw_varm.txt", "mrlw_varm2.txt", "mrlw_varoutils.txt",  "mrlw_varu.txt", "mrlw_varvar.txt" ]
	L = [ "mrlw_varm.txt"]
	for F in L :
		dic_var =  load_var(os.path.join(folder_path,F),dic_var)
	# on lit un fichier de frm , pouvant aussi contenir des definitions de variables
	dic_frm,dic_var = load_frm (os.path.join(folder_path,"mrlw_frm_small.frm")  , dic_var)
	# evnois des variables et des formules
	# .. lance le calcul directement ...
	# peut-être isolé ça
	#send_formules_mini( c, dic_frm,dic_var)
	# un flag à positionner sur le serveur ... pour la fin du calcul
	
	c.set_gesfrm_name("mesFormules")
	c.send_var_for_frm (dic_var )
	c.send_frm ( dic_frm)
	c.exec_frm()
	
def console_eval(c):
	
	while True:
		exp = raw_input("entrer une expression : " )
		if exp == "exit":
			return
		if exp.find("$sfrm") != -1:
			EVAL_SHOW_SFRM(exp)
		if exp.find("$cdf") != -1:
			EVAL_SHOW_SFRM(exp)		
		if exp.find("$gescdf") != -1:
			EVAL_SHOW_SFRM(exp)					
		else:
			SHOW(exp)
		
def eval_frm (c):
	
	LVAR =[ u"$volume_corpus",u"$status"]
	for V in LVAR :
		SHOW(V)	
	
	
m_connecteur_pII = ConnecteurPII()


	
if __name__ == "__main__" :

	
	c = ConnecteurPII()
	#c.set( '192.168.1.35','60000' )
	c.set( 'marloweb.eu','60001' )
	c.connect()

	rep = raw_input("je lance l'initialisation des formules ? " )
	if rep == 'o' :
		init_frm(c)
	L = [	"$gescdf.mesFormules[0:]",
			"$gescdf.mesFormules0.listvar[0:]",
			"$gescdf.mesFormules0.X0.formes[0:]",
			"$gescdf.mesFormules0.listvar0.formes[0:]",
			"$gescdf.mesFormules0.val",
			"$gescdf.mesFormules1.val",
			"$gescdf.mesFormules2.val",
			
			"$gescdf.mesFormules0.def[0:]",
			"$gescdf.mesFormules0.def0",
			"$gescdf.mesFormules0.def0.val",		
			"$gescdf.mesFormules0.def1",
			"$gescdf.mesFormules0.def1.val",		
			"$gescdf.mesFormules0.def2",
			"$gescdf.mesFormules0.def2.val",		

			"$gescdf.mesFormules1.def[0:]",
			"$gescdf.mesFormules1.def0",
			"$gescdf.mesFormules1.def0.val",		
			"$gescdf.mesFormules1.def1",
			"$gescdf.mesFormules1.def1.val",		
			"$gescdf.mesFormules1.def2",
			"$gescdf.mesFormules1.def2.val",		
			
			"$gescdf.mesFormules2.def[0:]",	
			"$gescdf.mesFormules2.def0",
			"$gescdf.mesFormules2.def0.val",		
			"$gescdf.mesFormules2.def1",
			"$gescdf.mesFormules2.def1.val",		
			"$gescdf.mesFormules2.def2",
			"$gescdf.mesFormules2.def2.val",			
			"$gescdf.mesFormules2o.def3",
			"$gescdf.mesFormules2.def3.val",			

			"$gescdf.mesFormules0.X[0:]",
			"$gescdf.mesFormules0.def0.ph[0:]",
			"$gescdf.mesFormules0.def0.X0.ph[0:]",
			"$gescdf.mesFormules0.def0.X1.ph[0:]",
			"$gescdf.mesFormules0.def0.Y0.ph[0:]"
			
			"$gescdf.mesFormules1.X0.val",
			"$gescdf.mesFormules1.Y0.val",
			"$gescdf.mesFormules1.def0.X0.val",
			"$gescdf.mesFormules1.def1.X0.val",
			"$gescdf.mesFormules1.def2.X0.val",
			]
	L = [	
			"$gescdf.mesFormules[0:]",
			"$gescdf.mesFormules0.listvar[0:]",
			"$gescdf.mesFormules0.X0.forme[0:]",
			"$gescdf.mesFormules0.listvar0.forme[0:]",
			"$gescdf.mesFormules0.def0.listvar0.forme[0:]",
			"$gescdf.mesFormules0.def0.listvar0.forme0.ph0",
			"$gescdf.mesFormules0.def0.listvar0.forme0.ph1",
			"$gescdf.mesFormules0.def0.listvar0.forme0.ph2",
			"$gescdf.mesFormules0.def0.listvar0.forme0.ph0",
			"$gescdf.mesFormules0.def1.listvar0.forme0.ph1",
			"$gescdf.mesFormules0.def1.listvar0.forme0.ph2",
			"$gescdf.mesFormules0.def1.listvar0.forme0.val",
			"$gescdf.mesFormules0.def1.listvar0.forme1.val",
			"$gescdf.mesFormules0.def1.listvar0.forme2.val",
			"$gescdf.mesFormules0.listvar[0:]",
			"$gescdf.mesFormules0.listvar0",
			"$gescdf.mesFormules0.listvar0.val",
			"$gescdf.mesFormules0.listvar1",
			"$gescdf.mesFormules0.listvar1.val",			
			"$gescdf.mesFormules0",
			"$gescdf.mesFormules0.val",
			"$gescdf.mesFormules0.X0",
			"$gescdf.mesFormules0.X0.forme[0:]",
			"$gescdf.mesFormules0.Y0.forme[0:]",
			"$gescdf.mesFormules1.X0",
			"$gescdf.mesFormules1.X0.val",
			"$gescdf.mesFormules1.Y0",
			"$gescdf.mesFormules1.Y0.forme[0:]",
			"$gescdf.mesFormules1.Y0.val",
			"$gescdf.mesFormules1.X[0:]",
			"$gescdf.mesFormules1.X0.ph[0:]"
			]
	rep = raw_input("évaluation d'une liste de formules ? " )
	if rep == 'o' :
		for exp in L:
			EVAL_SHOW_SFRM(exp)
		
		
		
	console_eval( c)
	'''
	folder_path="C:\Users\jean-pierre\workspace\PII\P2Qt"
	dic_var={}
	L = [ "mrlw_varm.txt", "mrlw_varm2.txt", "mrlw_varoutils.txt",  "mrlw_varu.txt", "mrlw_varvar.txt" ]
	for F in L :
		dic_var =  load_var(os.path.join(folder_path,F),dic_var)
	# on lit un fichier de frm , pouvant aussi contenir des definitions de variables
	dic_frm,dic_var = load_frm (os.path.join(folder_path,"mrlw_frm1.txt")  , dic_var)
	'''
	
	
	# envois des variables et des formules
	# .. lance le calcul directement ...
	# peut-être isolé ça
	'''
	send_formules_mini( c, dic_frm,dic_var)
	# un flag à positionner sur le serveur ... pour la fin du calcul
	c.send_var_for_frm (dic_var )
	c.send_frm ( dic_frm)
	c.exec_frm()
	
	#L= c.creer_msg_ctx("titre","[0:]")
	#c.set( '192.168.1.63','6000' )
	
	
	#c.set( '192.168.1.35','60000' )
	#path="C:\corpus\chronique\projet_chronique.prc"
	#path="/home/jeanjean/monProjet.prc"
	#c.load(path)
	'''
	i = 0
	while 1:
		status = c.eval_variable("$status")
		print status , "   " , i
		i+=1 
		time.sleep(1)
		if status == "1" :
			break
		time.sleep(1)
	#eval_fonct (self, fonc, element,sem):
	
	# variables uniques , état du serveur
	LVAR =[ u"$volume_corpus",u"$status"]
	for V in LVAR :
		SHOW(V)
	
	LVAR = [u"$pers0",u"$pers[0:10]", u"$ef0" ,]
	for V in LVAR :
		SHOW(V)
	# variable incorporant le tri dans la partie préfix du nom
	LVAR = [u"$val_freq_ent[0:20]",u"$val_nbaut_ent[0:]", u"$val_lapp_ent[0:]" ]
	for V in LVAR :
		SHOW(V)	

	LVAR = [u"$gc0",u"$gc0.c[0:10]", u"$gc0.c0" , u"$gc0.c0.val" ]
	for V in LVAR :
		SHOW(V)	
	data = c.eval_variable("$ent[20:25]")
	print data
	c.eval_op_concept("gestion_concept",'remove', "ef", "TRUC@")
	print c.eval_variable("$ef[0:]" )
	
	c.eval_op_concept("gestion_concept",'add', "ef", "TRUC@")
	print c.eval_variable("$ef[0:]" )	
	data = c.eval_variable("$ent[20:25]")
	print data
	
	data = c.eval_variable("$ent[20:25]")
	L = data.split(",")
	for element in L:
		element= element.strip()
		if element[-1] == '@' : continue
		c.eval_op_concept("gestion_rep_concept",'add', "ef", "TRUC@",element)
		
	print c.eval_variable("$ef[0:]" )
	for element in L:
		element= element.strip()
		if element[-1] == '@' : continue
		c.eval_op_concept("gestion_rep_concept",'remove', "ef", "TRUC@",element)
	print c.eval_op_concept("gestion_concept",'save', "ef")
	print c.eval_variable("$ef[0:]" )
	
	print c.eval_variable("$cat_ent[0:]" )

	print c.eval_op_concept("gestion_concept",'add', "ef", "ZIGO@")

	print c.eval_op_concept("gestion_concept",'remove', "ef", "ZIGO@")

	print c.eval_op_concept("gestion_concept",'save', "ef")


	x = c.eval_fonct("getsem","plusieurs","$qualite" )
	print x	
	x = c.eval_variable("$volume_corpus" )
	print x
	L = c.eval_variable("$cat_ent[0:]" )
	print L
	L = L.split(",")
	for element in L :
		element = element.strip()
		sem = c.eval_fonct("getsem",element,"$cat_ent" )
		print element , "   ", sem , " val = ", c.eval_variable(sem +".val")
		
			
	L = c.creer_msg_search ( u"$searchcs.rac" , u"La" , "0" )
	for  x in L : print x
	print c.eval(L)
	L = c.creer_msg_search ( u"$searchcs.rac" , u"la" , "0" )
	for  x in L : print x
	print c.eval(L)
	L = c.creer_msg_search ( u"$searchcs.rac" , u"la" , "[0:]" )
	print c.eval(L)
	
	L = c.creer_msg_search ( u"$searchcs.rac" , u"me" , "[0:]" , txt=True, ptxt="[0:10]")
	print c.eval(L)

	
	v = c.eval (c.creer_msg_search ( u"$search.rac" , u"le" , pelement="0" ,txt=True, ptxt="[0:10]", ph=True ,pph="[0:]",val=False))
	print v
	v = c.eval (c.creer_msg_search ( u"$searchcs.rac" , u"le" , pelement="0" ,txt=True, ptxt="[0:10]", ph=True ,pph="[0:]",val=False))
	print v
		
	x = c.eval_variable("$col[O:]" )
	print x
	x = c.eval_variable("$col[O:99999].val" )
	print x

	x = c.eval_variable("$txt2.ctx.title" )
	print x
	x = c.eval_variable("$ctx.title[0:]" )
	print x
	x = c.eval_variable("$ctx.title[0:20]" )
	print x
	x = c.eval_variable("$txt2.ctx.title" )
	print x
	x = c.eval_variable("$ctx" )
	print x
	x = c.creer_msg("$ctx.titre[0:]" )
	#c.set( 'marloweb.eu','60000' )
	v =c.eval_ctx("title","[0:]")
	x = c.eval_set_ctx(  "$txt0","title","ceci est un nouveau titre")
	v =c.eval_ctx("title","[0:]")
	v = c.eval_variable ("$ctx")
	#c.set( 'marloweb.eu','60000' )
	#v = c.eval_variable("$ent0")
	L = c.creer_msg_vect("$ent", "freq")
	v = c.eval_variable("$ent[0:]")
	v = c.eval_variable("$col[0:]")
	v = c.eval (c.creer_msg_search ( u"$search.suf" , u"aient" , pelement="0" ,txt=True, ptxt="[0:10]", ph=True ,pph="[0:]",val=False))
	print v
	v = c.eval (c.creer_msg_search ( u"$search.rac" , u"api" , pelement="0" ,txt=True, ptxt="[0:]", ph=False ,pph="[0:]",val=False))
	
	v = c.eval (c.creer_msg_search ( u"$search.rac" , u"api" , pelement="[0:]" ,txt=False, ptxt="0", ph=False ,pph="[0:]", val=False))
		
	v = c.eval (c.creer_msg_search ( u"$search.rac" , u"api" , pelement="0" ,txt=True, ptxt="[0:]", ph=False ,pph="[0:]",val=False))

	v = c.eval (c.creer_msg_search ( u"$search.rac" , u"api" , pelement="[0:]" ,txt=False, ptxt="0", ph=False ,pph="[0:]", val=True))

	L= c.creer_msg_search ( u"$search.rac" , u"api" , pelement="[0:]" ,txt=True, ptxt="")
	for  x in L : print x	
	L = c.creer_msg_search ( u"$search.rac" , u"présid" , "0" )
	for  x in L : print x
	L = c.creer_msg_search ( u"$search.rac" , u"présid" , "0" , val=True)
	for  x in L : print x
	L = c.creer_msg_search ( u"$search.rac" , u"présid" , "0" ,txt=True, ptxt="0", val=True)	
	for  x in L : print x
	L = c.creer_msg_search ( u"$search.rac" , u"présid" , "0" ,txt=True, ptxt="[0:]")	
	for  x in L : print x
	L = c.creer_msg_search ( u"$search.rac" , u"présid" , "0" ,txt=True, ptxt="0", ph=True ,pph="[0:]")
	for  x in L : print x	

	
	L = c.creer_msg_vect("$ent", "freq")
	v = c.eval_vect_values("$ent", "nbaut")
	v = c.eval_vect_values("$ent", "nbtxt")
	v = c.eval_vect_values("$ent", "lapp")
	v = c.eval_vect_values("$ent", "fapp")
	v = c.eval_vect_values("$ent", "dep")
	v = c.eval_vect_values("$ent", "freq")
	L = c.creer_msg_set_ctx(  ("$txt1","title","ceci était un nouveau titre"))
	x = c.eval_set_ctx(  "$txt1","title","ceci est un titre")
	v = c.eval_variable ("$ctx")
	v = c.eval_ctx("title","[0:]")
	#c.set( '127.0.0.1','4000' )

	try :
		lvar = ["$cat_ent", "$cat_ent0", "$cat_ent[0:9]",  "$ef0", "$ef[0:10]",  "$col2", "$col[0:10]", "$cat_ent[0:5]", "$ent0", "$ent0.txt[0:10]", "$ent0.txtp0", "$act0.txtp0"]
		for v in lvar :
			if (verbose) :
				print "variable : ", v , "  valeur ->  ", c.eval_variable (v)
			
		lv = ["$ent", "$act", "$entef"]
		for v in lv:
			for i in range (100):
				ev = v + str (i)
			if (verbose) :
				print "variable : ", ev , "  valeur ->  ", c.eval_variable (ev) 
	except:
		c.send_expression("CLOSE")
	
