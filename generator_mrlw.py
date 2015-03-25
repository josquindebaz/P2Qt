#!/usr/bin/python
# -*- coding: utf-8 -*-

import re,random,os


class mrlw_variables(object):
        def __init__(self):
                self.mrlw_vars  = {}
                self.mrlw_vars_index  = []
                self.files = []

                self.add_vars(self.get_file_content("mrlw/mrlw_varm.txt"))
                self.add_vars(self.get_file_content("mrlw/mrlw_varu.txt"))

        def get_file_content(self,path):
                if os.path.isfile(path):
                        self.files.append(path)
                        B= open(path).read()
                        return B.decode('latin1')
                else :
                        print "pb path", path
                        return ""

        def add_vars(self,file_content):
                V =  re.split("\s*\[\$\]\s*",file_content[:-2])
                for v in V[1:]:
                        if (re.search("\r\n",v) ):
                                vs = re.split("\r\n",v)
                        else :
                                vs = re.split("\n",v)
                        self.mrlw_vars[ vs[0] ] = vs[1:]
                        self.mrlw_vars_index.extend(vs[1:])
        
        def teste_var(self,expr):
                return expr in self.mrlw_vars_index
                
        def repere_vars(self,sentence):
                liste = []
                for k,vs in self.mrlw_vars.iteritems():
                        for v in vs:
                                if u" %s "%v in " %s " % sentence:
                                        liste.append([v,k])
                return liste

        def repere_vars2(self,sentence):
                liste = []
                for k,vs in self.mrlw_vars.iteritems():
                        for v in vs:
                                if v == sentence:
                                        liste.append([v,k])
                return liste

        def get_vars_sentence(self,sentence):
                while len(self.repere_vars(sentence)):
                        var_liste =  self.repere_vars(sentence)
                        choix =  random.choice(var_liste)
                        s = re.split(choix[0],sentence,1)
                        sentence = u"%s/%s%s" % (s[0],choix[1],s[1])
                return sentence

        def genere_phrase(self,sentence):
                for v in re.findall("\/Var\S{1,}",sentence):
                        choix = random.choice(self.mrlw_vars[v[1:]])
                        sentence = re.sub(v,choix ,sentence)
                return sentence 


if __name__ == '__main__':
        main = mrlw_variables()
        print len(main.mrlw_vars), len(main.mrlw_vars_index)
        for k in main.mrlw_vars.keys()[0:2]:
                print k, main.mrlw_vars[k]

        t  = u"mot"
        print main.teste_var(t)

        p = u"Une phrase informatique de test accentuée, pour avoir un avis partisan d'une myopie informatique, une causerie à l'EHESS, hein"
        print p

        v = main.get_vars_sentence(p)           
        print v
        for i in range(3):
                print main.genere_phrase(v)


