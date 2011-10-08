#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
	Experimentation HTTP avec Couchdb avec la librairie urllib2
	Support du billet http://www.opikanoba.org/python/couchdb

	License LGPL : GNU LESSER GENERAL PUBLIC LICENSE

"""
import sys
import logging
import logging.config
import urllib2
import json

__author__= 'Frederic Laurent'
__version__= '1.0'
__license__ = "LGPL"
__email__ = "fl@opikanoba.org"


logging.config.fileConfig("logdb.conf")
logger = logging.getLogger("couchdbLogger")

def jsonify(data):
	"""
		Retourne une version json du dictionnaire python 
		(sans complexe encoder pour simplifier)

		data : donnees (type python) a retourner sous forme de string
	"""
	return json.dumps(data)


def retrieveRevision(res_url):
	"""
		Test si la ressource existe dans la base (HEAD) et 
		recuperation de sa revision si c'est le cas.
		La revision est mise dans l'entete HTTP Etag

		res_url : URL de la ressource
	"""

	assert res_url, "une ressource doit etre fournie"

	try:
		logger.info("""Recuperation de la revision de la ressource 
			Couchdb : %s"""%res_url)
		request = urllib2.Request(res_url)
		request.get_method = lambda: 'HEAD'
		resp=urllib2.urlopen(request)
		# suppression des " au debut et a la fin de l'etag
		rev=resp.info()["etag"][1:-1]
		logger.info("Document existant : rev %s "%rev)
		return rev
	except urllib2.HTTPError, e:
		logger.error("Existance de la ressource %s ? ERR HTTP (%s)"
			%(res_url,e.code))
	except urllib2.URLError, e:
		logger.error("Existance de la ressource %s ? ERR d'URL (%s)"
			%(res_url,e.code))

	# aucune revision trouvee
	return None


def store(res_url,data):
	"""
		Stockage des donnees dans couchDB
		- test pour savoir si la ressoure existe deja 
			-> recuperation de la revision
		- PUT de la ressource dans couchdb (la ressource a deja l'id)

		res_url : URL de la ressource
		data : donnees a stocker dans la base
	"""

	assert res_url, "une ressource doit etre fournie"
	assert isinstance(data, dict), """des donnees doivent etre 
									de type dictionnaire"""

	try:
		# Test pour savoir si le document existe
		rev=retrieveRevision(res_url)
		if rev:
			logger.info("""Positionnement de la revision actuelle 
				sur le document %s"""%rev)
			data["_rev"]=rev
			
		# Sauvegarde	
		logger.info("Store Couchdb : %s"%res_url)

		opener = urllib2.build_opener(urllib2.HTTPHandler)
		# les donnees sont encodees en JSON
		request = urllib2.Request(res_url, data=jsonify(data))
		# positionnement du Content-Type
		request.add_header('Content-Type', 'application/json')
		# positionnement du verbe HTTP PUT
		request.get_method = lambda: 'PUT'
		f = opener.open(request)
		result=f.read().decode('utf-8')
		
		logger.info("Reponse de Couchdb : %s"%result)
	except urllib2.HTTPError, e:
		logger.error("Erreur HTTP d'acces a la ressource %s (%d"
			%(res_url, e.code))
	except urllib2.URLError, e:
		logger.error("Erreur d'URL  %s (%d)"%(res_url, e.code))


def retrieve(res_url):
	"""
		Recuperation des donnees d'une ressource

		res_url : URL de la ressource
	"""

	assert res_url, "une ressource doit etre fournie"

	try:
		opener = urllib2.build_opener(urllib2.HTTPHandler)
		logger.info("Load Couchdb : %s"%res_url)

		request = urllib2.Request(res_url)
		f = opener.open(request)
		data=f.read().decode('utf-8')
		# conversion JSON -> dictionnaire Python
		result=json.loads(data)
	except urllib2.HTTPError, e:
		logger.error("Erreur HTTP d'acces a la ressource %s : %d"
			%(res_url, e.code))
	except urllib2.URLError, e:
		logger.error("Erreur d'URL  %s : %d"%(res_url, e.code))
	
	return result

def delete(res_url, revision):
	"""
		Suppression d'un document par sa revision

		res_url : URL de la ressource
		revision : revision du document a supprimer

	"""

	assert res_url, "une ressource doit etre fournie"
	assert revision, "une revision doit etre fournie"
	
	try:
		logger.info("Suppression de ressource %s REV [%s]"
			%(res_url,revision))

		url_rev=res_url+'?rev='+revision
		request = urllib2.Request(url_rev)
		request.add_header('Content-Type', 'application/json')
		request.get_method = lambda: 'DELETE'
		resp=urllib2.urlopen(request)
		rev=resp.info()["etag"][1:-1]

		logger.info("REV supprimee [%s]"%rev)
	except urllib2.HTTPError, e:
		logger.error("ERR HTTP pour le DELETE de la ressource %s (%s)"
			%(res_url,e.code))
	except urllib2.URLError, e:
		logger.error("Erreur d'URL  %s (%d)"%(res_url, e.code))

def main(argv=None):
	"""
		Programme principal
		 - recuperation de la revision d'un document inexistant
		 - stockage des donnees dans la base CouchDB
		 - recuperation de la revision du document cree
		 - modification du document et stockage des modifications
		 - suppression du document

		 Arguments du main :
		 [1] URL de la base
		 [2] donnees a stocker 

		 Les donnees doivent contenir l'information sur l'ID du
		 document a creer/modifier : _id dans le dictionnaire
		 Python
	"""

	if argv is None:
		argv = sys.argv

	assert len(sys.argv)==3, """Deux arguments a fournir : [1] URL de 
								la base, [2] donnnees"""

	dbaddr=sys.argv[1]
	data=eval(sys.argv[2])

	assert type(data)==type({}), """les donnees doivent etre de type 
									disctionnaire"""
	assert data["_id"], """l'ID du document doit etre present dans 
							les donnees"""

	# URL de la ressource
	res_url=dbaddr+"/"+data["_id"]
	
	# Test de l'existance de la ressource
	logger.info("Test de l'existence de la ressource : %s"%res_url)

	rev=retrieveRevision(res_url)
	if rev:
		logger.info("Cette ressource n'existe pas ! ")
	else:
		logger.info("Ressource existante, REV=%s"%rev)

	# Stockage des donnees dans couchdb
	logger.info("Stockage des donnees : %s"%data)
	store(res_url,data)
	
	logger.info("Test de l'existence de la ressource : %s"%res_url)
	rev=retrieveRevision(res_url)
	if rev:
		logger.info("Cette ressource n'existe pas ! ")
	else:
		logger.info("Ressource existante, REV=%s"%rev)
	
	# modification de la ressource
	logger.info("Modification de la ressource : %s"%res_url)
	data["author"]="fred"
	logger.info("Stockage des donnees modifiees : %s"%data)
	store(res_url,data)
	
	# suppression des donnees  
	logger.info("Suppression des donnees %s"%res_url)
	rev=retrieveRevision(res_url)
	logger.info("Derniere revision du document [%s]"%rev)
	delete(res_url,rev)

	return 0

if __name__ == "__main__":
	sys.exit(main())	

