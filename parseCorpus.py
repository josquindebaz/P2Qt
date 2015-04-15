#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from xml.dom import minidom

class parse(object):
	def __init__(self):
		self.corpus = 0

	def open(self,path):
		F = open(path,"rU")
                self.corpus  = minidom.parse(F)
		
	def textFileList(self):
		textFileNames = []
                for F in self.corpus.getElementsByTagName('objet-texte'):
			textFileNames.append( F.getAttribute("nom")  )
		return textFileNames

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


if __name__ == '__main__':
	if os.path.isfile("socle.prc"):
		test = parse()
		test.open("socle.prc")
		print len(test.textFileList())
		
