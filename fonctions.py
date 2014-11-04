# -*- coding: ISO-8859-1 -*-
'''
Created on 24 févr. 2012
modif ...
@author: jean-pierre Charriau
'''
import re , random 
from datetime import datetime
#from globals import   save_log_file_lisp_eval, save_log_file_dialogue,save_session_log_file_name

#regex_var  = re.compile ( """(?P<VAR>/VAR=(.*?))(\s|$)""" , re.IGNORECASE  | re.VERBOSE  | re.DOTALL )
#regex_var  = re.compile ( """.*?(?P<VAR>(/VAR=.*?))(\s|$)""" , re.IGNORECASE  | re.VERBOSE  | re.DOTALL )
regex_var  = re.compile ( """(/VAR=[^\s]*)""" , re.IGNORECASE  | re.VERBOSE  | re.DOTALL )
regex_indice =  re.compile (r"""(?P<var>.*?)(?P<indice>[0-9]+?)$""",  re.VERBOSE | re.DOTALL )
regex_tranche =  re.compile (r"""(?P<var>.*?)\[(?P<tranche>.*?)\]""",  re.VERBOSE | re.DOTALL )


liste_var_list=["$list_cat_txt","$list_col_txt","$list_ac","$list_rep_present","$list_porteur"]
list_var_count=["nbpg","val","nbtxt","eno" ,"det"]
list_var_count_spec=["cpt"]
list_var_attribut=["auteur_txt","titre_txt","date_txt"]

def is_random_var(var):
	"""test si on a une variable aléatoire (non cachable !)
	PB  : $txt0.ph.+$txt0.act4   ph semble aléatoire ! tirage au sort ds les énoncés contrains par la présence d'un élément
	"""
	L = var.split('.')
	

	flg_is_alea_if_next_is_spec = flg_next_is_name_sfrm =  False
	pos=0
	size_of_list = len(L)
	for terme in L :
		r = regex_indice.search(terme)
		if r:
			flg_is_alea_if_next_is_spec = False
			continue
		r = regex_tranche.search(terme)
		if r:
			flg_is_alea_if_next_is_spec = False
			continue
		
		
		
		# ni indice ni tranche ? est-ce une aléatoire ou une exception
		if terme in liste_var_list : continue
		if terme in list_var_count : continue
		if terme in list_var_attribut : continue
		
		if flg_next_is_name_sfrm: # on a un nom de classe de frm
			flg_next_is_name_sfrm = False
			continue
			
		# cas des $sfrm.nom.    
		# pb avec $sfrm.recup_connexions.X=toto.forme[0:5] le split produisant 'x=toto' 
		if terme == '$sfrm':
			flg_next_is_name_sfrm = True
		if len(terme.split('='))==2:
			continue
		if terme.find('+') != -1:
			continue
		# "traitement des args présents dans les variaions $ph...+xxx+yyy
		# faut-il examiner la suite ... cas $ent.cpt { '$ent','cpt'}
		if  flg_is_alea_if_next_is_spec and  terme in list_var_count_spec:
			flg_is_alea_if_next_is_spec = False
			continue
		# $ent est aléatoire, $ent.cpt ne l'est pas , 
		# $nbpg ne l'est pas ( isolé -> si rien après, ne pas postionner flg_is_alea_if_next_is_spec)
		if 	flg_is_alea_if_next_is_spec == True:
			return True
		if pos + 1 < size_of_list :
			flg_is_alea_if_next_is_spec =True
		pos +=1
	
	if flg_is_alea_if_next_is_spec : # pas de spec traité, donc on a une var aléatoire
		return True
	return False

def save_log_dialogue(file_name,mess):
	if not save_log_file_dialogue: return
	save_log_lisp(file_name,mess)
	
def save_log_lisp(file_name,mess):
	if not save_log_file_lisp_eval: return
	f = open(file_name,'a' )
	line = datetime.today().strftime("%d/%m/%Y %H:%M:%S") + str(mess) + "\n"
	f.write(line)
	f.close()
	

def save_log(code,file_name,user_env,data,obj_dial_rep=None,obj_dial_capteur=None):
	"""
		fichier de log
		invoquée après reception de la question et avant traitement
		invoquée après traitement.
		code = Q ou R  (question ou reponse)
		data = question ou réponse mrlw
		remplacer les \n par des <br>
	"""
	if not save_session_log_file_name :return
	data = str(data) # à cause des listes ...
	data = data.replace('\n','<BR>')
	f = open(file_name,'a' )
	if code == 'R':
		dial_rep = dial_capt = ""
		if obj_dial_rep :
			dial_rep = obj_dial_rep.m_nom
		if obj_dial_capteur :
			dial_capt = obj_dial_capteur.m_nom
		line = datetime.today().strftime("%d/%m/%Y %H:%M:%S") + " ," + user_env["$user_ip"] + " , " + user_env["$user_name"] + " , " + dial_capt+ " , " + dial_rep + " , " + data +"\n"
		try :
			f.write(line) #.decode('utf-8'))
		except :
			print "save_log pb utf-8" + line
	else:
		line = datetime.today().strftime("%d/%m/%Y %H:%M:%S") + " ," + user_env["$user_ip"] + " , " + user_env["$user_name"] + " , " + data +"\n"
		try :
			f.write(line) #.decode('utf-8'))
		except: 
			print "save_log pb utf-8" + line
	f.close()
	

def prepare_for_indexation(data):
	"""
		fonction appelée avant de faire indexer une string par P-II , pour retrouver les expressions existantes
		il faut isoler certains caractères : tiret, apostrophe
		
		la fonction est appelé pour indexer par P-II toutes les formes de capture . Dans ce cas on trouve les /VAR= avec des noms 
		pouvant contenir des tirets..
		 
		data représente une string 
		"que dis-tu sur max ?"
		"quelle heure est-il ?"
		
		la sortie est une liste d'éléments
		["que" , "dis" , "-", "tu" ,"sur" ,"max"]
		["quelle", "heure", "est", "-" , "il" , "?"]
		
		spécificité avec /VAR=INITIALES-USER-ORIGINE ( présence de tiret '-' )
		prepare_for_indexation('qui est /T=1 /VAR=INITIALES-USER-ORIGINE")
		['qui', 'est', '/T=1', '/VAR=INITIALES', '-', 'USER', '-', 'ORIGINE']
		/T=2 /VAR=VarTonTaTes /T=3 /VAR=VarPasser-Subir /T=3 /VAR=VarExamen /T=3
	"""
	dic_sub={}
	liste_variables = regex_var.findall(data)
	if liste_variables: 
		for var in liste_variables :
			dic_sub[var] = get_signature()
			data=data.replace(var,dic_sub[var])
	data = data.replace("-", " - ")
	data = data.replace ("'"," ' ")
	for var in liste_variables:
		data=data.replace(dic_sub[var],var)
	liste_tokens =[]
	L0 = data.split(" ")
	for x in L0:
		if x :
			liste_tokens.append(x)
	return liste_tokens
def get_signature():
	population = "ABCDEFGHIJ"
	random.seed()
	list = random.sample(population, 10) 
	id  =  "".join(list)
	return id
def Randomlist(lst):
	"""renvoit un élément tiré aléaoirement dans la liste
	"""
	random.seed()
	i = random.randint(0, len(lst)-1)
	return lst[i]
def ajuste_parentheses( L):
	""" essaye de corriger les pb des parenthèses du code lisp embarqué
	(setq $eno1.val (ENO $un_auteur)))
	(setq $premtxt (cs $un_auteur '.txt0))))
	(setq $premtxt.val  (eval $premtxt )))
	(if (member $un_auteur.val $l_act_auteur.val)
	(progn
	(setq $remarque2 "cet auteur est aussi un acteur du corpus , les autres auteurs-acteurs étant :")
	(setq $les_autres_auteurs_acteurs ( detach $un_auteur.val $l_act_auteur.val))
	(setq $remarque3 '())
	)
	( progn
	(setq $remarque3 "cet auteur n'est pas un acteur marquant du dossier")
	(setq $remarque2 '())
	)
	))))))))))))))))
	
	"""

	prec_lp = 0
	bloc_code =[]
	
	for line in L :
		line_code =''
		lp = rp = 0
		for c in line :
			if c == '(' : 
				lp+=1
			if c == ')':
				if rp + 1 > lp :
					if prec_lp > 0:
						prec_lp = prec_lp - 1
					else:
						continue # ne prend pas la fermante
				else:
					rp +=1
				
			line_code +=c
		
		prec_lp += ( lp - rp )	
		bloc_code.append(line_code)
	code =''
	for x in bloc_code :
		code += x

	return code
def is_parentheses_ok(data):
	lp = rp = 0
	for c in data :
		if c == '(' : 
			lp+=1
		if c == ')':
			rp +=1
	if lp == rp : return True
	return False
	
def adjust_parenthesis(data):
	"""ajuste les parenthèses d'une expression ( retire les parenthèses en trop)
	et si il manque une parenthèse fermante !
	"""
	lp = rp = 0
	fdata =""
	for c in data :
		if c == '(' : 
			lp+=1
		if c == ')':
			if rp + 1 > lp :
				continue
			rp +=1
		fdata += c
	if lp > rp :
		print "adjust_parenthesis () erreur de parenthèse fermante ", data
		fdata += ")"*(lp-rp)
	return fdata
def check_lisp_code( code):
	"""
		le code doit être mis sur une seule ligne
		le parenthésage doit être strict
		
		? pose d'un try ? en cas d'échec de l'évaluation lisp
	"""
	if not code : return ''
	code = code.replace('\r\n', '\n')	
	L = code.split('\n')
	L1=[]
	# retirer les lignes commentaires , les lignes vides
	for line in L :
		if not line.strip(): continue
		if line.strip()[0]=='%':continue
		# commentaire en fin de ligne
		if line.find('%') != -1:
			line = line.split('%')[0]
			
		L1.append(line)
	code = "".join(L1)
	#code = code.replace('%', ';') # code commentaire
	
	code = adjust_parenthesis(code)
	return code

def get_fonc(data,ind):
	"""
	attention à :
	(define LTS(lambda (L string)(setq string ")"))
	nil
	"""
	lp = rp = 0
	fdata =""
	in_guillemet= False # signaliseur de guillement pour ")"
	data = data[ind:]
	for c in data :
		
		if c == '"':
			if not in_guillemet: # si pas de guillement right
				in_guillemet = True
			else : # il y avait un guillemet en cours
				in_guillemet = False
		
		ind += 1
			
		if c == '(' and not in_guillemet: 
			lp+=1
		if c == ')' and not in_guillemet:
			if rp + 1 > lp :
				continue
			rp +=1
		fdata += c
		if rp and rp == lp:
			break
	return fdata,ind
	
def create_list_fonc(data):
	""" creer la liste des fonctions
	"""
	L = []
	i=0
	max = len(data)
	while i < max :
		fonc, ind = get_fonc (data,i)
		L.append(fonc)
		i = ind
	return L

# pour remplacer l'appel à la fonction inf par '<' 
regex_inf = re.compile (r"""(\(|\s+)(?P<fonction>inf)(\(|\s+)""",  re.VERBOSE | re.DOTALL)
			
regex_test = re.compile (r"""(?P<exp>\(.*?\))$""",  re.VERBOSE | re.DOTALL)
regex_setq =re.compile (r"""(?P<exp>\(setq\s*.*?\))$""",  re.VERBOSE | re.DOTALL)
#regex_de =re.compile (r"""(?P<nom>\(\s*de\s+.*?)\s*\(\s*(?P<param>.*?)\s*\)(?P<corps>.*?)\s*\) )""",  re.VERBOSE | re.DOTALL)
regex_de =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s*\(""",  re.VERBOSE | re.DOTALL)
regex_param =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s*\(\s*(?P<param>.*?)\s*\)""",  re.VERBOSE | re.DOTALL)
regex_corps =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s*\(\s*(?P<param>.*?)\s*\)\s*(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_de_old =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s*\(\s*(?P<param>.*?)\s*\)\s*(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_de_old =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s+\(\s*(?P<param>[^\(\)]*)\s*\)\s*(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_de =re.compile (r"""\(\s*de\s+(?P<nom>[^\(\)\s]*)\s*\(\s*(?P<param>[^\(\)]*)\s*\)\s*(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
# (de css L ( ..))
regex_fonction_de_arg_var_old =re.compile (r"""\(\s*de\s+(?P<nom>.*?)\s+(?P<param>[^\(\)]*)\s+(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_de_arg_var =re.compile (r"""\(\s*de\s+(?P<nom>[^\(\)]*)\s+(?P<param>[^\(\)]*)\s+(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_df =re.compile (r"""\(\s*df\s+(?P<nom>.*?)\s+(?P<param>.*?)\s+(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)
regex_fonction_defmar =re.compile (r"""\(\s*DEFMAR\s+(?P<nom>.*?)\s*\(\s*(?P<param>.*?)\s*\)\s*(?P<corps>.*?) \s*\)$""",  re.VERBOSE | re.DOTALL)

# (if x cond-true cond-false  cond-false) -> (if x cond-true (begin cond-false  cond-false))
# (if (foo ) cond-true cond-false  cond-false )-> (if (foo) cond-true (begin cond-false  cond-false))
#regex_if_x =re.compile (r"""\(\s*if\s+(?P<cond>\(.*?\))\s*(?P<exp_true>\(.*?\))\s*(?P<exp_false>\(.*?\))\s*\)\s*\)\s*$""",  re.VERBOSE | re.DOTALL)
regex_if_x =re.compile (r"""\(\s*if\s+(?P<cond>\(.*?\))\s*(?P<exp_true>\(.*?\))\s*(?P<exp_false>\(.*?\))""",  re.VERBOSE | re.DOTALL)
regex_if_cond =re.compile (r"""\(\s*if\s+(?P<cond>\(.*?\))""",  re.VERBOSE | re.DOTALL)
def rewrite (data):
	"""
		(setq var val) -> le setq est conservé car liant dans l'env global 
		nil -> () ou plutôt '()
		
		eq
		neq
		(cm '/) ????
		réécriture du (if cond exp-true exp-false exp-false) en (if cond exp-true (begin exp-false exp-false))  
		réécriture des définitions de fonction  à l'aide de define & lambda
		(de foo (x) ()) ->(define foo (lambda(x) ())
		
	"""
	if not data:
		return data

	#print "avant :" ,data
	#x = parse_exp(data)
	data = data.replace('progn','begin')
	data =data.replace('nil' , " '() ")
	data = data.replace('atom', 'atomp')
	# pb de 'inf' .. float valeur spéciale
	# avec regex pour éviter date_inf -> date_< !
	# tolère (inf  ou inf( ou inf '
	r = regex_inf.search(data)
	if  r : 
		data = data.replace('inf','<')

	r = regex_fonction_de.search(data)
	if r:

		# reconstruction . (de foo (x)() ) -> (define foo (lambda (x) () )
		
		data = '(define ' + r.group('nom') + '(lambda (' + r.group('param') + ')' + r.group('corps') + '))'
	r = regex_fonction_de_arg_var.search(data)
	if r:
		# reconstruction . (de css L (...) ) -> (define css (lambda L (...) )
		# fonction a nbre variable d'arg
		data = '(define ' + r.group('nom') + '(lambda '  + r.group('param') +  r.group('corps') + '))'	

	#on retire df et les définitions DEFMAR !
	r = regex_fonction_df.search(data)
	if r:
		data =""
	r = regex_fonction_defmar.search(data)
	if r:
		data =""		


	#print "après : ", data
		
	return data
	
if 	__name__ == '__main__' :
	#save_log_eval_var("mrlw-II-eval.log","$var.truc.machin", "toto")
	#save_log_eval_var("mrlw-II-eval.log","$var.truc.machin.bidule.truc", "toto")
	x = "/T=2 /VAR=VarTonTaTes /T=3 /VAR=VarPasser-Subir /T=3 /VAR=VarExamen /T=3"
	prepare_for_indexation(x)
	save_log("ok","mlk","ooo","oo","olol")
	
	data =["(setq $eno1.val (ENO $un_auteur)))","(setq $premtxt (cs $un_auteur '.txt0))))","	(setq $premtxt.val  (eval $premtxt )))",
	"(if (member $un_auteur.val $l_act_auteur.val)",
	"(progn ",
	'(setq $remarque2 "cet auteur est aussi un acteur du corpus , les autres auteurs-acteurs étant :")',
	'(setq $les_autres_auteurs_acteurs ( detach $un_auteur.val $l_act_auteur.val))',
	"(setq $remarque3 '())",
	")",
	"( progn",
	'(setq $remarque3 "cet auteur n est pas un acteur marquant du dossier")',
	"(setq $remarque2 '())",
	")",
	"))))))))))))))))",
	"(setq x a)))"
	]
	ajuste_parentheses(data)
if __name__ == '__oldmain__':

	x = "/T=2 /VAR=VarTonTaTes /T=3 /VAR=VarPasser-Subir /T=3 /VAR=VarExamen /T=3"
	prepare_for_indexation(x)
	for x in [" (inf 2 3)" ,"(de date_inf(d1)", " (inf(+x 1) "] :
		print "x : " , x
		r = regex_inf.search(x)
		if  r : 
			print r.groupdict()
			print r.groupdict()['fonction']
			x = x.replace('inf','<')

	L=[5,4,3,6,1,2,10,9,8,7]
	while True:
		Randomlist (L)
