#!/usr/bin/python
# -*- coding: utf-8 -*-
from xml.dom import minidom
import os
import re
import datetime
import interface_prospero
import urllib
import socket

class client(object):
    def __init__(self, h, p):
        self.c = interface_prospero.ConnecteurPII() 
        self.c.set(h, p)
        self.etat = self.c.connect_x(5)

    def disconnect(self):
        self.c.disconnect()

    def recup_liste_concept(self, sem):
        var = "%s[0:]" % sem
        return re.split(", ", self.c.eval_variable(var))
    
    def recup_liste_concepts_tot(self):
        gcs = []
        for i in range(6):
            result = re.split(', ', self.c.eval_variable('$gc%d.c[0:]'%i))
            gcs.append(result)
        return gcs

    def eval_vector(self, type, type_calc):
        return self.c.eval_vect_values(type, type_calc)

    def eval_var(self, var):
        return self.c.eval_variable(var)
        
    def eval_var_ctx(self, props, ctx_range):
        return self.c.eval_ctx(props, ctx_range)

    def eval_get_sem(self, exp, sem):
        """get element semantic getsem 'nucléaire' $ent -> $ent10"""
        return self.c.eval_fonct(u"getsem", u"%s"%exp, sem)

    def add_cache_var(self, cle, val):
        self.c.add_cache_var(cle, val)

    def creer_msg_search(self, fonc, element, pelement='', txt=False, 
                                    ptxt='', ph=False, pph='', val=False):
        return self.c.creer_msg_search(fonc, element, 
                        pelement, txt, ptxt, ph, pph, val)

    def eval(self, l):
        return self.c.eval(l)

    def eval_set_ctx(self, sem_txt, field, val):
        return self.c.eval_set_ctx(sem_txt, field, val)

    def eval_index(self, exp):
        return self.c.eval_index(exp)

class Texte(object):
    def __init__(self, sem, path):
        self.sem = sem 
        self.path = path
        self.CTX = {}

    def setCTX(self, field, value):
        self.CTX[field] = value
    
    def getCTXall(self):
        return self.CTX

    def getCTX(self, field):
        if (field in self.CTX.keys()): 
            return self.CTX[field]
        else :
            return False 

    def getResume(self):
        if "date" in self.CTX.keys():
            date = re.split(" ", self.CTX["date"])[0]
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

        return (date, author, title)

class parseCorpus(object):
    def __init__(self):
        self.corpus = 0

    def open(self, path):
        #FIXME use with open
        F = open(path, "rU")
        B = F.readlines()
        if re.search("<Projet-Prospéro-II", B[1]):
            F.seek(0)
            self.corpus  = minidom.parse(F)
            return True
        else:
            return False
        
    def textFileList(self):
        textFiles = []
        for F in self.corpus.getElementsByTagName('objet-texte'):
            textFiles.append([F.getAttribute("nom"), 
                F.getAttribute("date-insertion-projet")])
        return textFiles

    def conceptFileList(self):
        FileNames = []
        for F in self.corpus.getElementsByTagName('objet-gestionnaire'):
            FileNames.append(F.getAttribute("adresse"))
        return FileNames

    def dicFileList(self):
        FileNames = []
        for F in self.corpus.getElementsByTagName('ressource'):
            FileNames.append(F.getAttribute("adresse"))
        return FileNames

    def savefile(self, fname, langue=u"français", ressource_list=[], 
                                        concept_list=[], text_dic={}):
        content = minidom.Document()
        root = content.createElement(u'Projet-Prospéro-II')
        content.appendChild(root)
        root.setAttribute(u'date-creation', 
            u"%s"%datetime.datetime.now().strftime("%Y-%m-%d"))
        root.setAttribute(u'heure-creation', 
            u"%s"%datetime.datetime.now().strftime("%H:%M:%S"))
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
            ressource = content.createElement(u"ressource")
            ressources.appendChild(ressource)
            ressource.setAttribute("adresse", r)
            ressource.setAttribute("statut", "1")
        concepts = content.createElement(u'gestionnaire-de-concepts')
        root.appendChild(concepts)
        for c in concept_list:
            concept = content.createElement(u"objet-gestionnaire")
            concepts.appendChild(concept)
            concept.setAttribute("adresse", c)
            concept.setAttribute("statut", "1")
        textes = content.createElement(u'textes-du-projet')
        root.appendChild(textes)
        for t in text_dic.keys():
            texte = content.createElement(u"objet-texte")
            textes.appendChild(texte)
            texte.setAttribute(u"nom", t)
            texte.setAttribute(u"date-insertion-projet", u"%s" % text_dic[t])
        #FIXME use with open
        file_handle = open(fname, "wb")
        file_handle.write(content.toprettyxml(encoding="utf-8"))
        file_handle.close()

#FIXME rename class
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
            #FIXME use with open
            F = open(self.path, "rU")
            return minidom.parse(F)

    def isP1(self, buf):
        """P1 or P2 CTX file test"""
        lines = re.split('\r\n', buf)
        if len(lines):
            if lines[0] == 'fileCtx0005':
                return "P1"
            elif lines[0] == '<?xml version="1.0" encoding="UTF-8" ?>':
                return "P2"
            else:
                return False
        else:
            return False

    def P1toP2(self, buf):
        """transform a P1 content to P2 format"""
        lines = re.split('\r\n', buf)
        champs = ["", "title", "author", "narrateur", "destinataire", "date", "medium", 
            "media-type", "observations", "authorship", "localisation", "CL1", "CL2"]
        if len(lines) > 15:
            for r, l in enumerate(lines):
                if r > 0 and r < 13:
                    if r in [1, 2, 5]:
                        self.dico[champs[r]] = l
                    elif len(l):
                        self.dico[champs[r]] = l
                if r > 14 and len(l):
                    if r == 15:
                        if l not in ["REF_HEURE:00:00", "REF_HEURE:0:0"]:
                            print r, l 
                    if r > 15:
                            print r, l 

            #print self.dico
        else:
            return False

    def savefile(self):
        if (self.path and self.dico):
            content = minidom.Document()
            root = content.createElement(u'Projet-Prospero-II-Contexte')
            content.appendChild(root)
            root.setAttribute(u'version', u"1.00")
            root.setAttribute(u'date-creation', 
                u"%s"%datetime.datetime.now().strftime("%y-%m-%d"))
            root.setAttribute(u'heure-creation', 
                u"%s"%datetime.datetime.now().strftime("%H:%M:%S"))

            for k, v in self.dico.iteritems():
                x = content.createElement('objet')
                root.appendChild(x)
                x.setAttribute(u"champ", k)
                if (k == "date"):
                    x.setAttribute(u"type", "DATETIME")
                    if re.search("^\d{2}\/\d{2}\/\d{4}$", v):
                        v += " 00:00:00"
                else:
                    x.setAttribute(u"type", "CHAR")
                x.setAttribute(u"value", v)

            #FIXME use with open
            file_handle = open(self.path, "wb")
            file_handle.write(content.toprettyxml(encoding="utf-8"))
            file_handle.close()
       

class edit_codex(object):
    def __init__(self):
        self.dico = {}

    def champs(self):
        liste = [] 
        for i in self.dico.values():
            liste.extend(i.keys())
        return list(set(liste))

    def cherche_codex_cfg(self):
        return os.path.isfile("codex.cfg")

    def cherche_codex(self):
        return os.path.isfile("codex.xml")

    def parse_codex_xml(self, codex_path):
        with open(codex_path, "rU") as F:
            B = minidom.parse(F)
            C = B.firstChild
            self.dico = {}
            for E in C.getElementsByTagName('Entry'):
                d = {}
                for F in E.getElementsByTagName('Field'):
                    d[F.getAttribute('name')] = F.getAttribute('value')
                self.dico [E.getAttribute('ABREV')] = d            
        
    def parse_codex_cfg(self, codex_path):
        with open(codex_path, "rU") as buf:
            B = buf.read() 
        items = re.split("#{2,}", B.decode('latin-1'))
        dico = {}
        tr = {"ABREV":u"ABREV", "AUTEUR":u"author", "SUPPORT":u"medium", 
                "TYPE-SUPPORT":u"media-type", "STATUT-AUTEUR":u"authorship",
                 u"LIEU-EMISSION":u"localisation", "CHAMP-1":u"open-field-1", 
                "CHAMP-2":u"open-field-2", "OBSERVATION":u"observations"}
        for item in items:
            if not re.search("^\s*$", item):
                dic = {}
                for i in  re.split('\n', item):
                    if i != '':
                        k, v = re.split(":", i, 1)
                        v = re.sub("^\s*(.*)\s*$", "\\1", v)
                        if (v != ""):
                            if k in tr.keys():
                                dic[u"%s"%tr[k]]=u"%s"%v
                if 'ABREV' in dic.keys():
                    dico[dic['ABREV']] = {key:value for key, 
                        value in dic.items() if key != 'ABREV'}
                else:
                    print "C19500 pb parse codex with", dic
        self.dico = dico

    def cherche_supports(self):
        return os.path.isfile("support.publi") 

    def parse_supports_publi(self, supports_path):
        with open(supports_path, "rU") as buf:
            B = buf.read()
        items = re.split("\n", B.decode('latin-1'))
        dico = {}
        for item in items:
            if not re.search("^\s*$", item):
                A = re.split("\s*;\s*", item)
                if len(A) == 4:
                    dico[A[3]] = {u'medium':u"%s"%A[1], u'author':u"%s"%A[1], 
                                                    u'media-type': u"%s"%A[2]}
                else :
                    print "C22168 pb parse supports with", item
        self.dico = dico

    def fusionne(self, dic1, dic2):
        """update dic2 with dic1, add new dic2 keys to dic1"""
        fails = {}
        for pb in set(dic1.keys()) & set(dic2.keys()):
            fails[pb] =  dic2[pb] 
        dic2.update(dic1)
        for k, v in fails.iteritems():
            for n in list(set(v.keys()) - set(dic2[k].keys())):
                dic2[k][n] = fails[k][n]
                del(fails[k][n])
            for n in v.keys():
                if n in dic2[k].keys():
                    if  v[n] == dic2[k][n] :
                        del(fails[k][n])
        return dic2, {k: v for k, v in fails.items() if v}

    def chercheValue(self, field, pattern):
        liste = []
        for m, l in self.dico.iteritems():
            for k, v in  l.iteritems():
                if  field =="":
                    if re.search(pattern, v, re.IGNORECASE):
                        liste.append([m, k, v])
                elif k == field: 
                    if re.search(pattern, v, re.IGNORECASE):
                        liste.append([m, v])
        return liste
    
    def eval_file(self, path):
        """check if the name of the file is in a correct form
            radicalYYMDD(supplement).txt (old P1 version) or
            radicalYYYYMMDD(supplement).txt
        """
        p, namefile = os.path.split(path)
        result = False
        test_date_YYMDD = re.compile("^(\S*)(\d{2})([0-9A-Ca-c])(\d{2})\S*\.[txTX]*")
        test_date_YYYYMMDD = re.compile("^(\S*)(\d{4})(\d{2})(\d{2})\S*\.[txTX]*")

        if test_date_YYYYMMDD.match(namefile):
            radical, year, month ,day = test_date_YYYYMMDD.search(namefile).groups()
            if radical in self.dico.keys():
                result =  (radical,  u"%s/%s/%s" % (day, month ,year) ) 

        elif test_date_YYMDD.match(namefile): # P-1 FORM: YYMDD
            radical, year, month , day = test_date_YYMDD.search(namefile).groups()
            if radical in self.dico.keys():
            #TODO verify retro-compatibility with p1 (1935?)
                if int(year) > 50:
                    year = "19%s" % year
                else:
                    year = "20%s" % year
                months = {"a":"10", "A":"10", "b":"11", "B":"11", "c":"12",
                                                                    "C":"12"}
                if month in months.keys():
                    month = months[month]
                else :
                       month = "0%s" % month
                result = (radical,  u"%s/%s/%s" % (day, month, year))
        
        return result

    def save_codex(self, path="codex.dat"):
        content = minidom.Document()
        root = content.createElement(u'Codex')
        content.appendChild(root)
        root.setAttribute(u'Entries', u"%d"%len(self.dico))
        root.setAttribute(u'Creation-date', 
            u"%s"%datetime.datetime.now().isoformat())
        
        for k, fs in self.dico.iteritems():
            e = content.createElement(u'Entry')
            root.appendChild(e)
            e.setAttribute(u'ABREV', u'%s'%k)
            for f, v in fs.iteritems():
                x = content.createElement('Field')
                e.appendChild(x)
                x.setAttribute(u'name', u'%s'%f)
                x.setAttribute(u'value', u'%s'%v)

        file_handle = open("codex.xml", "wb")
        file_handle.write(content.toprettyxml(encoding="utf-8"))
        file_handle.close()

class recupTXT_CTX(object):
    def __init__(self, parent):
        self.parent=parent
        self.recup_texts() #texts
        self.recup_ctx() #ctx

    def recup_texts(self):
        """cache text list"""
        txts = self.parent.client.eval_var("$txt[0:]")
        self.listeTextes  = re.split(", ", txts)
        self.listeObjetsTextes = {}
        self.dicTxtSem = {}
        for i, t in enumerate(self.listeTextes):
            sem_texte = u"$txt%d"%(i)
            self.listeObjetsTextes[sem_texte] = Texte(sem_texte, t)
            self.dicTxtSem[t] = sem_texte

    def recup_ctx(self):
        """cache ctx content"""
        #get ctx field titles, comma+space separated, 
        #comma protected by antislash
        string_ctx = self.parent.client.eval_var("$ctx")
        liste_champs_ctx = re.split("(?<!\\\), ", #negative lookbehind assertion
                                        string_ctx) 
        self.liste_champs_ctx = map(self.delAntiSlash, liste_champs_ctx)

        for champ in self.liste_champs_ctx :
            string_ctx = self.parent.client.eval_var("$ctx.%s%s"%(champ,
                                                                 "[0:]")) 
            liste_data_ok_ctx =  re.split("(?<!\\\), ", string_ctx)
            liste_data_ok_ctx = map(self.delAntiSlash, liste_data_ok_ctx)

            if len (liste_data_ok_ctx) != len (self.listeTextes):
                print "C10008 problemo qq part les listes doivent avoir \
                                            le même nbre d'éléments"
                print liste_data_ok_ctx 
            #else : print liste_data_ok_ctx

            for indice in range (len(self.listeTextes)):
                sem_texte = "$txt%d"%(indice)
                txt = self.listeObjetsTextes[sem_texte]
                data = liste_data_ok_ctx[indice]
                if data != "":
                    self.parent.client.add_cache_var(txt.sem +
                                             ".ctx.%s" % champ, data)
                    txt.setCTX(champ, data)

    def delAntiSlash(self, elt):
        return re.sub('\\\\,', ',', elt)
    
#REMOVEME>
#class preCompute(object):
    #"""cache values"""
    #def __init__(self, parent):
        #self.parent=parent
        #
        #self.recup_texts() #texts
        #self.recup_ctx() #ctx
        #self.type_var =  [ 
            #"$act",
            #"$aut",
            #"$ent",
            #"$ef",
            #"$col",
            #"$ent_sf",
            #"$qualite",
            #'$marqueur',
            #'$epr',
            #'$pers',
            #'$undef',
            #'$expr',
            #'$cat_ent',
            #'$cat_epr',
            #'$cat_qua',
            #'$cat_mar',
            #'$mo',
        #] 
        #self.type_calcul = [
            #"val",
            #"freq",
            #"dep",
            #"nbaut",
            #"nbtxt",
            #"lapp",
            #"fapp",
            #"res"
            #"txt",
        #]

        #self.nbpg = self.parent.client.eval_var("$nbpg")
        #self.nbtxt = self.parent.client.eval_var("$nbtxt")

    #def recup_texts(self):
        #"""cache text list"""
        #txts = self.parent.client.eval_var("$txt[0:]")
        #self.listeTextes  = re.split(", ", txts)
        #self.listeObjetsTextes = {}
        #self.dicTxtSem = {}
        #for i, t in enumerate(self.listeTextes):
            #sem_texte = u"$txt%d"%(i)
            #self.listeObjetsTextes[sem_texte] =  Texte(sem_texte, t)
            #self.dicTxtSem[t] = sem_texte

    #def recup_ctx(self):
        #"""cache ctx content"""
        ##get ctx field titles, comma+space separated, 
        ##comma protected by antislash
        #string_ctx = self.parent.client.eval_var("$ctx")
        #liste_champs_ctx = re.split("(?<!\\\), ", #negative lookbehind assertion
                                        #string_ctx) 
        #self.liste_champs_ctx = map(self.delAntiSlash, liste_champs_ctx)

        #for champ in self.liste_champs_ctx :
            #string_ctx = self.parent.client.eval_var("$ctx.%s%s"%(champ,
                                                                 #"[0:]")) 
            #liste_data_ok_ctx =  re.split("(?<!\\\), ", string_ctx)
            #liste_data_ok_ctx = map(self.delAntiSlash, liste_data_ok_ctx)

            #if len (liste_data_ok_ctx) != len (self.listeTextes):
                #print "C10008 problemo qq part les listes doivent avoir \
                                            #le même nbre d'éléments"
                #print liste_data_ok_ctx 
            ##else : print liste_data_ok_ctx

            #for indice in range (len(self.listeTextes)):
                #sem_texte = "$txt%d"%(indice)
                #txt = self.listeObjetsTextes[sem_texte]
                #data = liste_data_ok_ctx[indice]
                #if data != "":
                    #self.parent.client.add_cache_var(txt.sem +
                                             #".ctx.%s" % champ, data)
                    #txt.setCTX(champ, data)

    #def delAntiSlash(self, elt):
        #return re.sub('\\\\,', ',', elt)
    #
    #def cacheAssocValue(self, type_var, type_calcul):    
        #ask = self.parent.client.eval_vector(type_var, type_calcul)

        ##if (type_calcul == "freq"):
            ##type_calcul = "val"

        #for indice, val in enumerate(ask.split(', ')):
            #m = "%s%s.%s"%(type_var, str(indice), type_calcul)
            #self.parent.client.add_cache_var(m, val)
#REMOVEME>
    

class myxml(object):
    def __init__(self, url="http://prosperologie.org/P-II/info.xml",
            ip="prosperologie.org"):
        self.url = url
        self.ip = ip

    def get(self): 
        try :
            self.buf = urllib.urlopen(self.url)
            return 1
        except:
            return 0

    def parse(self):
        try :
            self.xmlbuf = minidom.parse(self.buf)
            return 1
        except:
            return 0

    def test_port(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try :
            s.connect((self.ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    def getDataCorpus(self):
        items = self.xmlbuf.getElementsByTagName('projet')
        liste = []
        for item in items:
            if self.test_port(int(item.attributes['port'].value)):
                liste.append([item.attributes['nom'].value, 
                                item.attributes['port'].value])
        return liste

def sp_el(element):
    return element.split(' ', 1)

def iterdays(start, end):
    incr = start
    while incr  <= end:
        yield incr 
        incr += datetime.timedelta(days=1)

def cumul_days(l):
    f = {}
    for d in l:
        if d in f.keys():
            f[d] += 1
        else:
            f[d] = 1
    l.sort()
    d0 = datetime.date(*map(lambda x: int(x), re.split("-", l[0])))
    dn = datetime.date(*map(lambda x: int(x), re.split("-", l[-1])))
    lf = []
    for d in iterdays(d0, dn):
        ds = d.strftime("%Y-%m-%d")
        if ds in f.keys():
            lf.append('"%s"\t%s'%(ds, f[ds]))
        else:
            lf.append('"%s"\t%s'%(ds, 0))
    return lf    

def cumul_dates(l, delta):
    if delta == "years":
        cut = 5
    elif delta == "months":
        cut = 8
    nd = {} 
    for e in l:
        d, v = re.split("\t", e)
        d = d[0:cut]
        if d in nd.keys():
            nd['%s"'%d] += int(v)
        else:
            nd['%s"'%d] = int(v)
    lf = []
    for ds in sorted(nd.keys()):
        lf.append('%s\t%s' %(ds, nd[ds]))
    return lf

#For eval_index result
explo_lexic = {
    '$ent_sf': 'entity',
    '$qual': 'quality',
    '$marqueur': 'marker', 
    '$epreuve': 'verbs',
    '$mo': 'function word',
    '$majent': 'capitalised entity',
    '$prenom': 'first name',
    '$act': 'actant',
    '$pers': 'person',
    }
#NB $entef = entite out of fictions + fictions + entities in fictions

#For affiche_concepts_scores
hash_sort = {
    "occurences": "freq",
    "alphabetically": "freq",
    "deployment": "dep",
    "number of texts": "nbtxt",
    #"number of pages": "nbpg",
    "number of authors": "nbaut",
    "first apparition": "fapp",
    "last apparition": "lapp",
}

sorting_concepts_list = [
        u"occurences",
       u"deployment",
       u"alphabetically",
       "number of texts",
       #"number of pages",
       "number of authors",
       "first apparition",
       "last apparition",
       "weigthed",
       "day present number",
       "relatif nb jours",
       "representant number",
       "network element number"
] 

sorting_lexicon_list = [
       u"occurences",
      #u"deployment",
       u"alphabetically",
       "number of texts",
       #"number of pages",
       "number of authors",
       "first apparition",
       "last apparition",
       "weigthed",
       "day present number",
       "relatif nb jours",
       "representant number",
       "network element number"
]

semantiques = {
        'collections': '$col',
	'fictions': '$ef',
	'entity categories': '$cat_ent',
	'verb categories': '$cat_epr',
	'marker categories': '$cat_mar',
	'quality categories': '$cat_qua',
	'entities': '$ent_sf',
	'qualities': '$qualite',
	'markers': '$marqueur',
	'verbs': '$epr',
	'persons': '$pers',
	'undefined': '$undef',
        'actants': '$act',
	'expressions': '$expr',
	'entities&fictions': '$ent',
        'function words': '$mo',
}

