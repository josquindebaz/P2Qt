#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, os

class edit_codex(object):
	def __init__(self):
		self.dico = {}

	def champs(self):
		liste = [] 
		for i in self.dico.values():
			liste.extend(i.keys())
		return list( set(liste) )

	def cherche_codex(self):
		return os.path.isfile("codex.cfg") 

	def parse_codex_cfg(self,codex_path):
		B = open(codex_path,"r").read()
		items = re.split("#{2,}",B)
		dico = {}
		for item in items:
			if not re.search("^\s*$",item):
				dic = {}
				for i in  re.split('\r\n',item):
					if i != '':
						k,v = re.split(":",i)
						v = re.sub("^\s*(.*)\s*$","\\1",v)
						if (v != ""):
							dic[k]=v
				if 'ABREV' in dic.keys():
					dico[dic['ABREV']] = {key : value for key  , value in dic.items() if key != 'ABREV'} 
				else:
					print "pb with", dic
		self.dico = dico
		return dico

	def cherche_supports(self):
		return os.path.isfile("support.publi") 

	def parse_supports_publi(self,supports_path):
		B = open(supports_path,"r").read()
		items = re.split("\r\n",B)
		dico = {}
		for item in items:
			if not re.search("^\s*$",item):
				A = re.split("\s*;\s*",item)
				if len(A) == 4:
					dico[A[3]] = {'SUPPORT': A[1] , 'AUTEUR': A[1] , 'TYPE-SUPPORT': A[2] }
				else :
					print "pb with", item
		return dico

	def fusionne(self,dic1,dic2):
		for pb in set(dic1.keys()) & set(dic2.keys()):
			print pb, dic1[pb], dic2[pb]
		dic2.update(dic1)
		return dic2
		
	
def main():
	test = edit_codex()
	if test.cherche_codex():
		dic1 = test.parse_codex_cfg("codex.cfg")
		print len(dic1)
	if test.cherche_supports():
		dic2 = test.parse_supports_publi("support.publi")
		print len(dic2)
	if test.cherche_codex() & test.cherche_supports():
		dic = test.fusionne(dic1,dic2)
		print len(dic)

if __name__ == '__main__':
	main()

