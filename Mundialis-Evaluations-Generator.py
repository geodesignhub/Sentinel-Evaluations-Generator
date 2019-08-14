import json, geojson, requests
import random, os, sys,httsleep
import GeodesignHub, config
from httsleep import httsleep
from httsleep.exceptions import Alarm
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape, mapping, shape, asShape
from shapely.geometry import MultiPolygon, MultiPoint, MultiLineString
from shapely.ops import unary_union
from urllib.parse import urlparse
from os.path import splitext, basename
from dotenv import load_dotenv, find_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class EvaluationsFactory():
	''' This is the main class to connect to Mundialis '''
	def __init__(self):
		''' Credentials '''
		self.MUNDIALIS_USERNAME =  os.environ.get('ACTINIA_USERNAME')
		self.MUNDIALIS_PASSWORD=  os.environ.get('ACTINIA_PASSWORD')
		self.port = u'443'
		self.servername = 'https://actinia.mundialis.de/api/v1'
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

	def execute_process_chain(self, processchain):
		headers = {'content-type': 'application/json', 'Accept':'application/json'}
		r = requests.post(self.url, auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers,  data= json.dumps(processchain))
		return r

	def parse_process_chain(self, response):
		if response.status_code == 200:
		    resp = response.json()
		    # get data back from them
		    is_successful = 0
		    status_url = ''
		    if resp['status']=='accepted':
			    status_url =  resp['urls']['status']
			    is_successful = 1

		return is_successful, status_url

	def poll_status_url(self, status_url):
		headers = {'content-type': 'application/json'}
		try:
			response = httsleep(status_url, auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers, until = self.until, alarms = self.alarms, max_retries=5, polling_interval=60)
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
				self.download_output(outputurls)



	def download_output(self, urls):
		
		for url in urls: 
			headers = {'content-type': 'application/json'}
			print("Downloading from %s..." % url)
			disassembled = urlparse(url)
			filename = basename(disassembled.path)
			cwd = os.getcwd()
			output_directory = os.path.join(cwd,config.settings['output_directory'])
			if not os.path.exists(output_directory):
				os.mkdir(output_directory)
			local_filename = os.path.join(output_directory, filename)
			r = requests.get(url,auth=(self.MUNDIALIS_USERNAME,self.MUNDIALIS_PASSWORD),headers= headers, stream=True)
			with open(local_filename, 'wb') as f:
			    for chunk in r.iter_content(chunk_size=1024): 
			        if chunk: # filter out keep-alive new chunks
			            f.write(chunk)
			            #f.flush() commented by recommendation from J.F.Sebastian
			

if __name__ == '__main__':
	aoiurl = config.settings['aoi']
	my_evaluations_factory = EvaluationsFactory()
	allstatusurls = []
	ndviprocchain = config.processchains[0]
	resp = my_evaluations_factory.execute_process_chain(ndviprocchain)	
	is_successful, status_url = my_evaluations_factory.parse_process_chain(resp)

	if is_successful: 
		print("Status URL: %s"% status_url)
		allstatusurls.append(status_url)

	if allstatusurls:
		my_evaluations_factory.poll_status_url(status_url)

	