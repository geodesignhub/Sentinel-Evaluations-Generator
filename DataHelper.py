
import config, requests
from urllib.parse import urlparse
from os.path import splitext, basename
import os

class DataDownloader():
    def __init__(self):
        self.cwd = os.getcwd()

    def download_files(self, urls):
        for url in urls: 
            disassembled = urlparse(url)
            filename = basename(disassembled.path)
            ext = os.path.splitext(disassembled.path)[1]

            workingdirectory = os.path.join(self.cwd,config.settings['workingdirectory'])
            if not os.path.exists(workingdirectory):
                os.mkdir(workingdirectory)
            local_filename = os.path.join(workingdirectory, filename)
            if not os.path.exists(local_filename):
                print("Downloading from %s..." % url)
                r = requests.get(url, stream=True)
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            #f.flush() commented by recommendation from J.F.Sebastian
            return local_filename
