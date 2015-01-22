# -*- coding: ISO-8859-1 -*-
"""
Created on 5 mars 2012

@author: jean-pierre Charriau

module de communication avec un serveur P-II pour l'�valuation des variables mrlw dont le rendu/l'�valuation d�pend des calculs de P-II

une variable est transform�e en une s�quence de messages envoy�s les uns � la suite des autres vers P-II, la s�quence
se terminant par un message "F" signalant la fin de la s�quence.
L'envois successifs de ces messages permet � P-II de retrouver s'ils ont d�j� �t� calcul�s les diff�rentes objets correspondant
aux composantes de la variable ( dans l'exemple ci-dessous, $aut0 puis $act1 seront retrouv�s par P-II permettant de contextualiser/�valuer
correctement la derni�re composante phadt ... un �nonc� al�atoire avec auteur/date/titre, de l'acteur 1 chez l'auteur 0 )
  


			E:signature	# les objets que calcule P-II sont aussi mis en cache par P-II . la signature permet d'y acc�der
			V:typeVariable:signature  		# V indique une variable
			P:n  		 # position/indice de la variable pr�c�dente
			BI:n   		# cas d'un acc�s par tranche  [] pour la variable pr�c�dente
			BS:m
			ARG:xxx		# lorsque des param�tres sont transmis ( $aut0.phadt[0:10].+xxx  sp�cifiant une contrainte suppl�mentaire (pr�sence de xxx))
			F:			# fin du bloc de message 
			
			$aut0.act1.phadt sera transform� en la s�quence suivante: 
			
			E:aut0.act1.phadt		# la signature compl�te
			V:aut:aut0		# la premi�re composante variable 
			P:0				# position de la premi�re V
			V:act:act1		# la seconde composante variable
			P:1				# position de la seconde V
			V:phadt:phadt	# troisi�me composante ( sans position ni tranche .. donc al�atoire)
			F				# code de fin de message
"""
#from settings import hostPII , portPII , logger

import threading, socket, time , re
#from eval_variable import eval_variables
#from globals import getMapDossiers , log_file_name_messages
from fonctions import is_random_var

# on exclue le signe + pour ne pas reconna�tre +truc+bidule
regex_var = re.compile (r"""(?P<VAR>[a-zA-Z_]+)($|\s)+""", re.VERBOSE | re.DOTALL)
# pour $aut0.phadt[0:10].+truc+machin ou '+truc+machin' est analys�e par la regex
# Attention : aux lettres accentu�es !
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
# pour les variables li�s X=toto
regex_sfrm_link_var = re.compile (r"""(?P<VAR>.*?)=(?P<VAL>.*?)(\.|$)""", re.VERBOSE | re.DOTALL)

# regex compl�mentaire pour isoler les args dans le cas ou le premier arg n'a pas de '+' ( .$Obj+truc )
regex_ph_args_bis =  re.compile (r"""(?P<var>\$.*?)\.(?P<arg_incorrect>.*?)\+(?P<arg>.*?)$""",  re.VERBOSE | re.DOTALL )

class ConnecteurPII (threading.Thread): 
	""" Pourquoi d�river la class de threading.Thread ? -> utilisation du RLock
		car pas d'exec de la m�thode start/run ...
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
				print "Connexion : �chec"
				time.sleep(1)
				

	def disconnect(self):
		self.send_expression("CLOSE")
		time.sleep(1)
		self.connexion.close()
		self.connexion = None

	def send_var_for_frm(self, dic_of_frm_var):
		"""envois des variables utilis�es par les frm
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
			ent�te CFRM:nom_de_la_classe
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
		envois des d�finitions de dossier � P-II
		"""
		if not self.connexion : 
			if not self.connect():
				return ""
		dic_dossier = getMapDossiers()
		for dossier in dic_dossier.keys():
			print "dossier envoy�" , dossier
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



	def add_cache_fonc (self, data, value):
		self.m_cache_fonc[data] = value
	def add_cache_index(self, data, value):
		self.m_cache_index[data] = value
	def eval_fonct (self, fonc, element,sem):
		"""
			cas du getsem : on interroge P-II pour obtenir la s�mantique avec indice
			 d'un �l�ment ( on fournit la s�mantique ..)
		"""
		
		self.m_threadlock.acquire()
		'''  
		if data in self.m_cache_fonc.keys():
			self.m_threadlock.release()
			return self.m_cache_fonc[data]
		'''
		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_fonct(fonc , element, sem)
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value()
		#self.add_cache_fonc(data, value)
		self.m_threadlock.release()
		return value

	def eval_fonc(self, data):
		"""
			cas du getsem : on interroge P-II pour obtenir la s�mantique exacte d'un �l�ment
		"""
		self.m_threadlock.acquire()
		if data in self.m_cache_fonc.keys():
			self.m_threadlock.release()
			return self.m_cache_fonc[data]

		
		if not self.connexion : 
			if not self.connect():
				self.m_threadlock.release()
				return ""
		lexpr = self.creer_msg_fonc(data)
		for exp in lexpr :
			self.send_expression(exp)
		value = self.get_value(data)
		self.add_cache_fonc(data, value)
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
		""" interrogation de P-II sur le/les types associ�s � data
		"""
		self.m_threadlock.acquire()
		# si le/les types de data ont d�j� �t� recherch� on les retrouve dans le cache
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
	def creer_msg_fonct(selfself,fonc,element,sem):
		"""
		
			pour l'appel de getsem + ARG
			FONC:getsem
			ARG:pirate
			ARG:$entef
			F
			
			bogue : 
				c:corpus
				$txt
				le : est maltrait� dans le split
				
		
		"""	
		
		lexpr = []
		lexpr.append("FONC:" +fonc)
		lexpr.append("ARG:" +element)
		lexpr.append("ARG:" +sem)
		lexpr.append('F')
		print lexpr
		return lexpr
	def creer_msg_fonc(self, data):
		"""
		
			pour l'appel de getsem + ARG
			FONC:getsem
			ARG:pirate
			ARG:$entef
			F
			
			bogue : 
				c:corpus
				$txt
				le : est maltrait� dans le split
				
		
		"""	
		L = data.split(":")
		lexpr = []
		lexpr.append("FONC:" + L[0])
		lexpr.append("ARG:" + L[1])
		lexpr.append("ARG:" + L[2])
		lexpr.append('F')
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
		"""sp�cifique aux sfrm !
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

			

	def creer_msg(self, data,user_env,corpus_env,env_dialogue):
		"""
			transforme l'expression en une s�quence de messages qui seront envoy�s � P-II
			
			
			E:signature	# les objets que calcule P-II sont mis en cache . la signature permet d'y acc�der
			V:typeVariable:signature  
			P:n  		 # position/indice de la variable
			BI:n   		# cas d'un acc�s par tranche  []
			BS:m
			ARG:xxx		# lorsque des param�tres sont transmis ( $aut0.phadt[0:10].+xxx  sp�cifiant une contrainte suppl�mentaire (pr�sence de xxx))
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



			avec des param�tres ...
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


			E:signature utilis�e ds le cache
			remarque : pour les reseaux, (res, inf ,resact,respers ) la signature doit �tre sans les indices/tranches
			puisque P-II calcule le r�seau (d'entit�s, de cat�gorise, d'acteurs,de personnes) d'un objet une fois,
			$act0.res est calcul� une fois, les acc�s $act0.res1 $act0.res2 $act0.res[0:10] se r�sumant � une s�lection d'�l�ments
			dans le r�seau existant.
			
			$act0.res[0:10] -> $act0.res
			$act0.res[0:98] -> $act0.res
			$act0.res0 -> $act0.res
			$act0.res1 -> $act0.res
			$aut4.ph.+$aut4.act0+$aut4.act0.res1 --> d'o� l'utilisation du mask, et l'�valuation des args 
			
			modification 3/07/2012
			traitement des {} formes liste � renvoyer
			
				Pb du s�parateur ',' utilis� dans les formes [] (quasi identique aux formes [] )
				mais les variables $ph utilis�es avec [] ou {} peuvent renvoyer du contenu avec des "," !!
				il faut donc que le code de s�paration des items renvoy�s soit diff�rent de "," dans le cas des {}
			
				chaque message re�u (getvalue) contiendra en premi�re position S ou L indiquant le type string ou list
				ds le cas du type list, getvalue cr�era une liste ( split(separ)) 
				
				il faut reconna�tre les {} dans les variables afin d'envoyer un code 'L' � P-II pour qu'il indique 
				
			
		"""
		mask = "TUVXYZ"

		# provisoire : rep�rage des {}
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
				�valuer les args commen�ant par $ pour construire la liste des args �valu�s
			"""
			#largs =  r.group('arg_incorrect').split('+') # ['$V', '$X', 'bidule'] ???
			largs = args.split('+')
			for a in largs :
				if not a : continue  # quand .+xxx+yyy arg_incorrect  ne contient rien !
				if a[0] =='$' :
					ev = eval_variables( a , user_env, corpus_env,env_dialogue)
					if not ev: # �chec de l'�valuation
						return []
					liste_eval_args.append(ev)
				else:
					liste_eval_args.append(a)
			if not liste_eval_args:  # eviter le cas $phxxx.+
				return []
			new_args = "" + "+".join(liste_eval_args)
		L = data.split('.')
		lmess = [] # contiendra les messages � envoyer � P-II
		
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
					
				# mettre � jour la signature de la derni�re variable V:
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
	c.set( '127.0.0.1','4000' )
	try :
		lvar = ["$cat_ent", "$cat_ent0", "$cat_ent[0:9]", "$ef0", "$ef[0:10]",  "$col2", "$col[0:10]", "$cat_ent[0:5]", "$ent0", "$ent0.txt[0:10]", "$ent0.txtp0", "$act0.txtp0"]
		for v in lvar :
			print "variable : ", v , "  valeur ->  ", c.eval_variable (v)
			
		lv = ["$ent", "$act", "$entef"]
		for v in lv:
			for i in range (100):
				ev = v + str (i)
			print "variable : ", ev , "  valeur ->  ", c.eval_variable (ev) 
	except:
		c.send_expression("CLOSE")
	
