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
		B = open(codex_path,"rU").read()
		items = re.split("#{2,}",B.decode('latin-1'))
		dico = {}
		for item in items:
			if not re.search("^\s*$",item):
				dic = {}
				#for i in  re.split('\r\n',item):
				for i in  re.split('\n',item):
					if i != '':
						k,v = re.split(":",i)
						v = re.sub("^\s*(.*)\s*$","\\1",v)
						if (v != ""):
							dic[u"%s"%k]=u"%s"%v
				if 'ABREV' in dic.keys():
					dico[dic['ABREV']] = {key : value for key  , value in dic.items() if key != 'ABREV'}
				else:
					print "pb parse codex with", dic
		self.dico = dico
		return dico

	def cherche_supports(self):
		return os.path.isfile("support.publi") 

	def parse_supports_publi(self,supports_path):
		B = open(supports_path,"rU").read()
##		items = re.split("\r\n",B)
		items = re.split("\n",B)
		dico = {}
		for item in items:
			if not re.search("^\s*$",item):
				A = re.split("\s*;\s*",item)
				if len(A) == 4:
					dico[A[3]] = {'SUPPORT': A[1] , 'AUTEUR': A[1] , 'TYPE-SUPPORT': A[2] }
				else :
					print "pb parse supports with", item
		return dico

	def fusionne(self,dic1,dic2):
		for pb in set(dic1.keys()) & set(dic2.keys()):
			print pb, dic1[pb], dic2[pb]
		dic2.update(dic1)
		return dic2

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

