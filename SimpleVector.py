import json, geojson, requests
import random, os, sys,httsleep
import GeodesignHub, config, ActiniaCredentials
from httsleep import httsleep
from httsleep.exceptions import Alarm
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape, mapping, shape, asShape
from shapely.geometry import MultiPolygon, MultiPoint, MultiLineString
from shapely.ops import unary_union
from urllib.parse import urlparse
from os.path import splitext, basename
import boto3
import config


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

	def downloadOutput(self, urls):
		
		for url in urls: 
			headers = {'content-type': 'application/json'}
			print("Downloading from %s..." % url)
			disassembled = urlparse(url)
			filename = basename(disassembled.path)
			cwd = os.getcwd()
			outputdirectory = os.path.join(cwd,config.settings['outputdirectory'])
			if not os.path.exists(outputdirectory):
				os.mkdir(outputdirectory)
			local_filename = os.path.join(outputdirectory, filename)
			r = requests.get(url,auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers, stream=True)
			with open(local_filename, 'wb') as f:
			    for chunk in r.iter_content(chunk_size=1024): 
			        if chunk: # filter out keep-alive new chunks
			            f.write(chunk)
			            #f.flush() commented by recommendation from J.F.Sebastian
			
	def pollStatusURL(self, statusurl):
		headers = {'content-type': 'application/json'}
		try:
			response = httsleep(statusurl, auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers, until = self.until, alarms = self.alarms, max_retries=5, polling_interval=30)
		except StopIteration as si:
			print("Max retries has been exhausted!")
		except Alarm as al:
			print("Got a response with status ERROR!")
			print("Here's the response:", al.response)
			print("And here's the alarm went off:", al.alarm)
		else:
			r = response.json()
			if r['status'] == 'finished':
				outputurls = r['urls']['resources']
				self.downloadOutput(outputurls)

class DOHelper(object):
	# Initialize a session using DigitalOcean Spaces.
	def __init__(self):
		self.session = boto3.session.Session()
		self.client = self.session.client('s3',
								region_name='ams3',
								endpoint_url='https://ams3.digitaloceanspaces.com',
								aws_access_key_id='FVCWIBVOJZTBZIVXH53S',
								aws_secret_access_key='1EcVfv6Fh4UeJ1uVdbRe2nAfVJ+w26Mp41vQm+Wuf0E')


		# # List all Spaces in the region
		# response = client.list_buckets()
		# for s in [space['Name'] for space in response['Buckets']]:
		# 	print(s)

		# Add a file to a Space
	def uploadFile(self, filepath):
		fname = os.path.basename(filepath)
		oppath = 'tmp/'+fname
		f = self.client.upload_file(filepath,
						'gdh-data',
						oppath,ExtraArgs={'ACL': 'public-read'})
		return 'https://gdh-data.ams3.digitaloceanspaces.com/'+oppath

if __name__ == '__main__':
	myEvaluationsFactory = EvaluationsFactory()
	allstatusurls = []
	files = []
	cwd = os.getcwd()
	fpath = os.path.join(cwd,config.settings['workingdirectory'],'point.geojson')
	myDoHelper = DOHelper()
	
	files.append(myDoHelper.uploadFile(fpath))
	
	for file in files: 
		simplificationprocesschain = {'list': [
		    {'id': 'importer_1', 'module': 'importer',
		     'inputs': [{'import_descr': {'source': file,
		     'type': 'vector'}, 'param': 'map', 'value': 'input_point'}]},
		    {'id': 'v_buffer', 'module': 'v.buffer', 'inputs': [{'param': 'input',
		     'value': 'map'},{'param': 'output',
		     'value': 'buf_point'}, {'param':'distance', 'value':'100'},{'param':'units', 'value':'meters'}]},

		    {'id': 'exporter_1', 'module': 'exporter',
		     'outputs': [{'export': {'type': 'vector', 'format': 'GeoJSON'},
		     'param': 'map', 'value': 'buf_point'}  ]},
		    ], 'version': '1'} 
		    	

		resp = myEvaluationsFactory.executeProcessChain(simplificationprocesschain)
		isSuccessful, statusurl = myEvaluationsFactory.parseProcessChainResponse(resp)
		print(statusurl)
		if isSuccessful: 
			allstatusurls.append(statusurl)

	# if allstatusurls:
	# 	myEvaluationsFactory.pollStatusURL(statusurl)



