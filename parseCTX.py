#!/usr/bin/python
# -*- coding: utf-8 -*-

from xml.dom import minidom
import os, datetime,re

class CTX(object):
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

        
             

def main():
    test = CTX()
    test.path = "test.xml"
    test.dico = {"author" : "tester", "support" : "test" , "date" : datetime.datetime.now().strftime("%y/%m/%d")}
    test.savefile()
    
    print test.parsefile().toxml()

if __name__ == '__main__':
        main()


