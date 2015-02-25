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


verbose = 1

import threading, socket, time , re
#from eval_variable import eval_variables
#from globals import getMapDossiers , log_file_name_messages
from fonctions import is_random_var

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
# pour les sfrm
regex_sfrm_forme = re.compile (r"""(?P<VAR>forme.*)($|\s)+""", re.VERBOSE | re.DOTALL)
# pour les phadt
regex_sfrm_ph = re.compile (r"""(?P<VAR>ph.*?)(\d|\[)""", re.VERBOSE | re.DOTALL)
# pour les X ... ds les sfrm ... par defaut puisque les noms de variables sont libres X Y Z etc..
regex_sfrm_var = re.compile (r"""(?P<VAR>.*?)(\d|\[)""", re.VERBOSE | re.DOTALL)
# pour les variables liés X=toto
regex_sfrm_link_var = re.compile (r"""(?P<VAR>.*?)=(?P<VAL>.*?)(\.|$)""", re.VERBOSE | re.DOTALL)

# regex complémentaire pour isoler les args dans le cas ou le premier arg n'a pas de '+' ( .$Obj+truc )
regex_ph_args_bis =  re.compile (r"""(?P<var>\$.*?)\.(?P<arg_incorrect>.*?)\+(?P<arg>.*?)$""",  re.VERBOSE | re.DOTALL )

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
	def set(self, ip, port):
		self.host = ip
		self.port = port 

	def connect(self):
		self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connexion.setblocking(1)
		while 1 :
			try:			
				#print "connexion au serveur ", self.host, " port : ", self.port
				self.connexion.connect((self.host, int(self.port)))
				time.sleep(0.5)
				return True
			except socket.error:			
				print "Connexion : échec"
				time.sleep(1)
				

	def disconnect(self):
		self.send_expression("CLOSE")
		time.sleep(1)
		self.connexion.close()
		self.connexion = None

	def send_var_for_frm(self, dic_of_frm_var):
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

		# exec des frm par p-II
		self.send_expression("E:CFRM_CONSTRUCTOR")
		self.send_expression("CFRM_EXEC")
		self.send_expression("F")
		self.get_value("send_frm")

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
			self.send_expression(exp)
		value = self.get_value()
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

			#data = self.connexion.recv(taille_mess)
			data = self.connexion.makefile().read(taille_mess)

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

		self.m_threadlock.acquire()

		if var in self.m_cache_var.keys():
			self.m_threadlock.release()
			ev = self.m_cache_var[var]
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
		if (verbose):
			print var , "  " , ev
		return ev
	

	def run(self):
		"""

		
		"""
		pass
	


	def send_expression(self, expression):
		""" 
			test avec un autre serveur
			buf[0]= 0XBE
			buf[1]= size
			buf[..]= data
			
			Si PB avec le serveur ... relancer la connexion 
		"""
		

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
		# la signature étant : "search.rac.chaine recherchée"
		fonc = fonc.encode('utf-8')
		element =  element.encode('utf-8')
		signature = fonc + '.' + element
		cle = signature
		
  		lexpr.append("E:" +signature)
  		'''
		if pelement:
			POS = "P:"+pelement
		else:
			POS=""
		'''
		lexpr.append("V:search:" +signature + "." +  pelement )
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
			S:FORM:forme0
			P:0
		
		$sfrm.Evts-marquants.X0
			E:sfrm.Evts-marquants.X0
			S:SFRM:Evts-marquant
			S:V:X:X0
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

		"""
		if data[0] == '$' : data = data[1:]
		L = data.split('.')

		lexpr = []
		
		# signature particuliere pour les .res
		signature = self.getSignature(data)
		lexpr.append("E:" + signature)
		
		
		last_var_expr = ''  
		
		flag_next_is_class_name = False
		construct_exp = ''
		for terme in L :
			if terme == 'sfrm':
				construct_exp = "S:SFRM:"  # on y consera le nom de la cfrm
				flag_next_is_class_name = True
				continue
			if flag_next_is_class_name:
				construct_exp += terme
				flag_next_is_class_name = False
				lexpr.append(construct_exp)
				construct_exp = ''
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
	def creer_msg_ctx(self,props, ctx_range):
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

			

	def creer_msg(self, data,user_env,corpus_env,env_dialogue):
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

		
	
	
m_connecteur_pII = ConnecteurPII()


	
if __name__ == "__main__" :

	c = ConnecteurPII()
	#L= c.creer_msg_ctx("titre","[0:]")
	c.set( '192.168.1.99','4000' )
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
	
