#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, os, datetime
from xml.dom import minidom

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
                for a in self.dico.keys():
                        if re.match("%s\d{2,}"%a,n):
                                if re.match("%s\d{2}[0-9A-Ca-c]\d{2}[A-Za-z]*\."%a,n):
                                        #FORME AAMMDD
                                        y,m,d = re.search("%s(\d{2})([0-9A-Ca-c])(\d{2})\w*\."%a,n).groups()
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
                                if re.match("%s\d{8}\S*\."%a,n):
                                        #FORME AAAAMMDD
                                        y,m,d = re.search("%s(\d{4})(\d{2})(\d{2})\w*\."%a,n).groups()
                                        r =  (a,  u"%s/%s/%s" % (d,m,y) )
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
                        

def main():
        test1 = edit_codex()
        if test1.cherche_codex_cfg():
                test1.parse_codex_cfg("codex.cfg")
                print len(test1.dico)
        if test1.cherche_supports():
                test2 = edit_codex()
                test2.parse_supports_publi("support.publi")
                print len(test2.dico)
        if test1.cherche_codex_cfg() & test1.cherche_supports():
                d,f = test2.fusionne(test2.dico,test1.dico)
                print len(d), len(f)
##                test.save_codex()
        if test1.cherche_codex():
                test3 = edit_codex()
                test3.parse_codex_xml("codex.xml")
                print len(test3.dico)
        

if __name__ == '__main__':
        main()

