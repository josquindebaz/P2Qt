#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,re,datetime
from xml.dom import minidom
                    
class Texte(object):
        def __init__(self,sem,path):
                self.sem = sem 
                self.path = path
                self.CTX = {}

        def setCTX(self,field, value):
                self.CTX[field] = value
        
        def getCTXall(self):
                return self.CTX

        def getCTX(self,field):
                if (field in self.CTX.keys()): 
                        return self.CTX[field]
                else :
                        return False 

        def getResume(self):
		if "date" in self.CTX.keys():
			date = re.split(" ",self.CTX["date"])[0]
		else:
			date = "00/00/0000"
		if "author" in self.CTX.keys():
			author = self.CTX["author"]
		else :
			author = "Anon."
		if "title" in self.CTX.keys():
			title = self.CTX["title"]
		else:
			title = "Untitled"
                return (date,author,title)


class parseCorpus(object):
        def __init__(self):
                self.corpus = 0

        def open(self,path):
                F = open(path,"rU")
                B = F.readlines()
                if re.search("<Projet-Prospéro-II",B[1]):
                        F.seek(0)
                        self.corpus  = minidom.parse(F)
                        return True
                else:
                        return False
                
        def textFileList(self):
                textFiles = []
                for F in self.corpus.getElementsByTagName('objet-texte'):
                        textFiles.append( [F.getAttribute("nom"),F.getAttribute("date-insertion-projet") ] )
                return textFiles

        def conceptFileList(self):
                FileNames = []
                for F in self.corpus.getElementsByTagName('objet-gestionnaire'):
                        FileNames.append( F.getAttribute("adresse")  )
                return FileNames

        def dicFileList(self):
                FileNames = []
                for F in self.corpus.getElementsByTagName('ressource'):
                        FileNames.append( F.getAttribute("adresse")  )
                return FileNames

        def savefile(self,fname,langue = u"français",ressource_list =[],concept_list =[],text_dic ={}):
                content = minidom.Document()
                root = content.createElement(u'Projet-Prospéro-II')
                content.appendChild(root)
                root.setAttribute(u'date-creation',u"%s"%datetime.datetime.now().strftime("%Y-%m-%d"))
                root.setAttribute(u'heure-creation',u"%s"%datetime.datetime.now().strftime("%H:%M:%S"))
                config = content.createElement(u'configuration')
                root.appendChild(config)
                label = u"config"
                node_config = content.createElement(label)
                config.appendChild(node_config)
                node_config.setAttribute (u"langue", langue)
                node_config = content.createElement(label)
                config.appendChild(node_config)
                node_config.setAttribute (u"mode_calcul_ele_in_expr", "0")
                node_config = content.createElement(label)
                config.appendChild(node_config)
                node_config.setAttribute (u"exclusion_type_multi", "0")
                node_config = content.createElement(label)
                config.appendChild(node_config)
                node_config.setAttribute (u"desact_calcul_de_listes_boot", "0")
                node_config = content.createElement(label)
                config.appendChild(node_config)
                node_config.setAttribute (u"mode-typage-auto-des-indéfinis", "1")
                ressources = content.createElement(u'statut-des-ressources')
                config.appendChild(ressources)
                for r in ressource_list:
                        ressource =  content.createElement(u"ressource")
                        ressources.appendChild(ressource)
                        ressource.setAttribute("adresse",r)
                        ressource.setAttribute("statut","1")
                concepts = content.createElement(u'gestionnaire-de-concepts')
                root.appendChild(concepts)
                for c in concept_list:
                        concept = content.createElement(u"objet-gestionnaire")
                        concepts.appendChild(concept)
                        concept.setAttribute("adresse",c)
                        concept.setAttribute("statut","1")
                textes = content.createElement(u'textes-du-projet')
                root.appendChild(textes)
                for t in text_dic.keys():
                        texte = content.createElement(u"objet-texte")
                        textes.appendChild(texte)
                        texte.setAttribute(u"nom",t)
                        texte.setAttribute(u"date-insertion-projet",u"%s"%text_dic[t])
                file_handle = open(fname,"wb")
                file_handle.write(content.toprettyxml( encoding="utf-8"))
                file_handle.close()

                



class parseCTX(object):
    def __init__(self):
        self.path = u""
        self.dico = {}

    def testefile(self):
        if (self.path):
            if os.path.isfile(self.path):
                return True
            else :
                return False
        else:
            return False

    def parsefile(self):
        if self.testefile():
            print 'a'
            F = open(self.path,"rU")
            return minidom.parse(F)

    def savefile(self):
        if (self.path and self.dico):
            content = minidom.Document()
            root = content.createElement(u'Projet-Prospero-II-Contexte')
            content.appendChild(root)
            root.setAttribute(u'version',u"1.00")
            root.setAttribute(u'date-creation',u"%s"%datetime.datetime.now().strftime("%y-%m-%d"))
            root.setAttribute(u'heure-creation',u"%s"%datetime.datetime.now().strftime("%H:%M:%S"))

            for k, v in self.dico.iteritems():
                x = content.createElement('objet')
                root.appendChild(x)
                x.setAttribute(u"champ",k)
                if (k == "date"):
                    x.setAttribute(u"type","DATETIME")
		    if re.search("^\d{2}\/\d{2}\/\d{4}$",v):
			v += " 00:00:00"
                else:
                    x.setAttribute(u"type","CHAR")
                x.setAttribute(u"value",v)

            file_handle = open(self.path,"wb")
            file_handle.write(content.toprettyxml( encoding="utf-8"))
            file_handle.close()

       

class edit_codex(object):
        def __init__(self):
                self.dico = {}

        def champs(self):
                liste = [] 
                for i in self.dico.values():
                        liste.extend(i.keys())
                return list( set(liste) )

        def cherche_codex_cfg(self):
                return os.path.isfile("codex.cfg")

        def cherche_codex(self):
                return os.path.isfile("codex.xml")

        def parse_codex_xml(self,codex_path):
                F = open(codex_path,"rU")
                B = minidom.parse(F)
                C = B.firstChild
                self.dico = {}
                for E in C.getElementsByTagName('Entry'):
                        d = {}
                        for F in E.getElementsByTagName('Field'):
                                d[F.getAttribute('name')] = F.getAttribute('value')
                        self.dico [ E.getAttribute('ABREV') ] = d                        
                
        def parse_codex_cfg(self,codex_path):
                B = open(codex_path,"rU").read()
                items = re.split("#{2,}",B.decode('latin-1'))
                dico = {}
                tr = { "ABREV" : u"ABREV", "AUTEUR" : u"author" , "SUPPORT" : u"medium" , "TYPE-SUPPORT":u"media-type" ,
                       "STATUT-AUTEUR":u"authorship", u"LIEU-EMISSION":u"localisation" ,
                       "CHAMP-1":u"open-field-1", "CHAMP-2":u"open-field-2", "OBSERVATION":u"observations"}
                for item in items:
                        if not re.search("^\s*$",item):
                                dic = {}
                                for i in  re.split('\n',item):
                                        if i != '':
                                                k,v = re.split(":",i,1)
                                                v = re.sub("^\s*(.*)\s*$","\\1",v)
                                                if (v != ""):
                                                        if k in tr.keys():
                                                                dic[u"%s"%tr[k]]=u"%s"%v
                                if 'ABREV' in dic.keys():
                                        dico[dic['ABREV']] = {key : value for key  , value in dic.items() if key != 'ABREV'}
                                else:
                                        print "pb parse codex with", dic
                self.dico = dico

        def cherche_supports(self):
                return os.path.isfile("support.publi") 

        def parse_supports_publi(self,supports_path):
                B = open(supports_path,"rU").read()
                items = re.split("\n",B.decode('latin-1'))
                dico = {}
                for item in items:
                        if not re.search("^\s*$",item):
                                A = re.split("\s*;\s*",item)
                                if len(A) == 4:
                                        dico[A[3]] = {u'medium': u"%s"%A[1] , u'author': u"%s"%A[1] , u'media-type': u"%s"%A[2] }
                                else :
                                        print "pb parse supports with", item
                self.dico = dico

        def fusionne(self,dic1,dic2):
                """update dic2 with dic1, add new dic2 keys to dic1"""
                fails = {}
                for pb in set(dic1.keys()) & set(dic2.keys()):
                        fails[pb] =  dic2[pb] 
                dic2.update(dic1)
                for k,v in fails.iteritems():
                        for n in list(set(v.keys()) - set(dic2[k].keys())):
                                dic2[k][n] = fails[k][n]
                                del(fails[k][n])
                        for n in v.keys():
                                if n in dic2[k].keys():
                                        if  v[n] == dic2[k][n] :
                                                del(fails[k][n])
                return dic2, {k: v for k, v in fails.items() if v}

        def chercheValue(self,field,pattern):
                liste = []
                for m,l in self.dico.iteritems():
                        for k,v in  l.iteritems():
                                if  field =="":
                                        if re.search(pattern,v,re.IGNORECASE):
                                                liste.append( [m,k,v] )
                                elif k == field: 
                                        if re.search(pattern,v,re.IGNORECASE):
                                                liste.append( [m,v] )
                return liste
        
        def eval_file(self,path):
                p,n = os.path.split(path)
                r = False
		testAAMDD = re.compile("^(\S*)(\d{2})([0-9A-Ca-c])(\d{2})[^\d]\S*\.[txTX]*$")
		testAAAAMMDD = re.compile("^(\S*)(\d{4})(\d{2})(\d{2})[^\d]\S*\.[txTX]*$")

		if testAAAAMMDD.match(n): #FORME AAAAMMDD
			a,y,m,d = testAAAAMMDD.search(n).groups()
			if a in self.dico.keys():
				r =  (a,  u"%s/%s/%s" % (d,m,y) )
		elif testAAMDD.match(n): #FORME AAMDD
			a,y,m,d = testAAMDD.search(n).groups()
			if a in self.dico.keys():
				if int(y) > 50:
					y = "19%s" % y
				else:
					y = "20%s" % y

				if m in ["a","A"]:
					m = "10"
				elif m in ["b","B"]:
					m = "11"
				elif m in ["c","C"]:
					m = "11"
				else :
					m = "0%s" % m
					
				r = (a,  u"%s/%s/%s" % (d,m,y) )

                return r        

        def save_codex(self,path="codex.dat"):
                content = minidom.Document()
                root = content.createElement(u'Codex')
                content.appendChild(root)
                root.setAttribute(u'Entries',u"%d"%len(self.dico))
                root.setAttribute(u'Creation-date',u"%s"%datetime.datetime.now().isoformat())
                
                for k,fs in self.dico.iteritems():
                        e = content.createElement(u'Entry')
                        root.appendChild(e)
                        e.setAttribute(u'ABREV',u'%s'%k)
                        for f,v in fs.iteritems():
                                x = content.createElement('Field')
                                e.appendChild(x)
                                x.setAttribute(u'name',u'%s'%f)
                                x.setAttribute(u'value',u'%s'%v)

                        
                file_handle = open("codex.xml","wb")
                file_handle.write(content.toprettyxml( encoding="utf-8"))
                file_handle.close()
                        

