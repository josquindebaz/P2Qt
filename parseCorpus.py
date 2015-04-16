#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,re,datetime
from xml.dom import minidom

class parse(object):
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


if __name__ == '__main__':
        if os.path.isfile("socle.prc"):
                test = parse()
                if (test.open("socle.prc")):
                        print len(test.textFileList())
                else:
                        print "fichier non conforme"

                
