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



if __name__ == '__main__':
	if os.path.isfile("socle.prc"):
		test = parse()
		test.open("socle.prc")
		print len(test.textFileList())
		
