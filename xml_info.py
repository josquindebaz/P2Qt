from xml.dom import minidom
import urllib


class myxml(object):
    def __init__(self,url ="http://prosperologie.org/P-II/info.xml" ):
        self.url = url

    def get(self): 
       try :
            self. buf = urllib.urlopen(self.url)
            return 1
       except:
            return 0

    def parse(self):
        try :
            self.xmlbuf = minidom.parse(self.buf)
            return 1
        except:
            return 0

    def getDataCorpus(self):
        items = self.xmlbuf.getElementsByTagName('projet')
        liste = []
        for item in items:
            liste.append([ item.attributes['nom'].value, item.attributes['port'].value])
        return liste

        

