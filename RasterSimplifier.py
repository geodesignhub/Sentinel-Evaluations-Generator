import json, geojson, requests
import random, os, sys,httsleep
import GeodesignHub, config, ActiniaCredentials
from httsleep import httsleep
from httsleep.exceptions import Alarm
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape, mapping, shape, asShape
from shapely.geometry import MultiPolygon, MultiPoint, MultiLineString
from shapely.ops import unary_union
from urlparse import urlparse
from os.path import splitext, basename


class EvaluationsFactory():
	''' This is the main class to connect to Mundialis '''
	def __init__(self):
		''' Credentials '''
		self.MUNDIALIS_USERNAME = ActiniaCredentials.cred['username']
		self.MUNDIALIS_PASSWORD= ActiniaCredentials.cred['password']
		self.port = u'443'
		self.servername = 'https://actinia.mundialis.de'
		self.endpoint = 'locations/latlong/processing_async_export'
		self.url = self.servername+"/"+self.endpoint
		self.until = {
	    'status_code': 200,
	    'jsonpath': [{'expression': 'status', 'value': 'finished'}]
		}
		self.alarms = [
		    {'json': {'status': 'ERROR'}},
		    {'status_code': 404}
		]

	def executeProcessChain(self, processchain):
		headers = {'content-type': 'application/json', 'Accept':'application/json'}
		r = requests.post(self.url, auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers,  data= json.dumps(processchain))
		return r

	def parseProcessChainResponse(self, response):
		if response.status_code == 200:
		    resp = response.json()
		    # get data back from them
		    isSuccessful = 0
		    statusurl = ''
		    if resp['status']=='accepted':
			    statusurl =  resp['urls']['status']
			    isSuccessful = 1

		return isSuccessful, statusurl

	def pollStatusURL(self, statusurl):
		headers = {'content-type': 'application/json'}
		try:
			response = httsleep(statusurl, auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers, until = self.until, alarms = self.alarms, max_retries=5, polling_interval=30)
		except StopIteration as si:
			print "Max retries has been exhausted!"
		except Alarm as al:
			print "Got a response with status ERROR!"
			print "Here's the response:", al.response
			print "And here's the alarm went off:", al.alarm
		else:
			r = response.json()
			if r['status'] == 'finished':
				outputurls = r['urls']['resources']
				self.downloadOutput(outputurls)


if __name__ == '__main__':
	myEvaluationsFactory = EvaluationsFactory()
	allstatusurls = []
	files = ['https://gdh-data-sandbox.ams3.digitaloceanspaces.com/rasters/urban.tiff']	

	# files = ['https://gdh-data-sandbox.ams3.digitaloceanspaces.com/rasters/urban.tiff','https://gdh-data-sandbox.ams3.digitaloceanspaces.com/rasters/TRANS.tiff','https://gdh-data-sandbox.ams3.digitaloceanspaces.com/rasters/ag.tiff','https://gdh-data-sandbox.ams3.digitaloceanspaces.com/rasters/GI.tiff']
	for file in files: 
		simplificationprocesschain = {'list': [
		    {'id': 'importer_1', 'module': 'importer',
		     'inputs': [{'import_descr': {'source': file,
		     'type': 'raster'}, 'param': 'map', 'value': 'input_eval'}]},
		    {'id': 'r_neighbours', 'module': 'r.neighbours', 'inputs': [{'param': 'raster',
		     'value': 'input_eval'}, {'param':'size', 'value':'7'}]},

		    {'id': 'exporter_1', 'module': 'exporter',
		     'outputs': [{'export': {'type': 'raster', 'format': 'GTiff'},
		     'param': 'map', 'value': 'NDVI'}  ]},
		    ], 'version': '1'} 
		    	

		resp = myEvaluationsFactory.executeProcessChain(simplificationprocesschain)
		isSuccessful, statusurl = myEvaluationsFactory.parseProcessChainResponse(resp)
		print statusurl
		if isSuccessful: 
			allstatusurls.append(statusurl)

	if allstatusurls:
		myEvaluationsFactory.pollStatusURL(statusurl)



