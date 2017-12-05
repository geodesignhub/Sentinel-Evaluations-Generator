import rasterio
import numpy as np
from numpy import copy
import os, shutil
import fiona
from fiona.crs import from_string
from rasterio.features import shapes
from pprint import pprint
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import crs
from rasterio.tools.mask import mask
from pysal.esda.mapclassify import Natural_Breaks as nb
import config, requests
from urlparse import urlparse
from os.path import splitext, basename

class DataDownloader():
    def downloadFiles(self, urls):
        for url in urls: 
            disassembled = urlparse(url)
            filename = basename(disassembled.path)
            ext = os.path.splitext(disassembled.path)[1]
            cwd = os.getcwd()
            outputdirectory = os.path.join(cwd,config.settings['workingdirectory'])
            if not os.path.exists(outputdirectory):
                os.mkdir(outputdirectory)
            local_filename = os.path.join(outputdirectory, filename)
            if not os.path.exists(local_filename):
                print "Downloading from %s..." % url
                r = requests.get(url, stream=True)
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            #f.flush() commented by recommendation from J.F.Sebastian
            return local_filename

class EvaluationsProcessor():
    def __init__(self):
        self.files = {'ndvi_file':'', 'classified_cropped_ndvi_file':'','slope_file':'','normalized_cropped_urban_slope':'', 'normalized_cropped_ag_slope':'','normalized_cropped_trans':''}

    def createEvalDirectories(self):
        systems = config.settings['systems']
        cwd = os.getcwd()
        dirpath = os.path.join(cwd,config.settings['outputdirectory'],'evals')
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        for system in systems: 
            dirpath = os.path.join(cwd,config.settings['outputdirectory'],'evals',system)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            dirpath = os.path.join(cwd,config.settings['outputdirectory'],'evals',system)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)


    def computeTransportNaturalBreaks(self, rawtransfile):
        print "Computing Natural breaks on Transport.."

        myDataDownloader = DataDownloader()
        localfile = myDataDownloader.downloadFiles([config.settings['aoi']])

        with fiona.open(localfile, "r") as aoi:
            geoms = [feature["geometry"] for feature in aoi]

        with rasterio.open(rawtransfile) as src:
            profile = src.profile
            bands = src.read()
            stats = []
            for band in bands:
                b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                breaks = nb(b.ravel(),k=4,initial=1)
                bins = breaks.bins.tolist()
        
        # bins.insert(1,-1) # add -1 to the beginning of the breaks
        # print bins
        print "Writing new Transport with Natural break classes.."
        with rasterio.open(rawtransfile) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 

                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)

                # Reproject and write each band

            with rasterio.open('output/tmp/classified-transport.tiff', 'w', **profile) as dst:
                dst.write(bands)

        print "Cropping Transport.."
        with rasterio.open('output/tmp/classified-transport.tiff') as trans_src:
            trans_out_image, trans_out_transform = mask(trans_src, geoms, crop=True)
            trans_out_meta = trans_src.meta.copy()
            trans_out_meta.update({"driver": "GTiff",
                             "height": trans_out_image.shape[1],
                             "width": trans_out_image.shape[2],
                             "transform": trans_out_transform})

        with rasterio.open('output/classified-transport.tiff', "w", **trans_out_meta) as trans_dest:
            trans_dest.write(trans_out_image)

        TransClassification = dict([(1,2),(2,3),(3,1)])

        print "Reclassing GI file.."

        with rasterio.open('output/classified-transport.tiff') as transnogdhsrc:
            classifiedprofile = transnogdhsrc.profile
            classifiedbands = transnogdhsrc.read()
            classifiedbands1 = np.vectorize(TransClassification.get)(classifiedbands)
            classifiedbands2 = classifiedbands1.astype(np.float32)

            with rasterio.open('output/evals/TRANS/TRANS.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands2)
        print "Reclassing completed"
        print "..."


    def computeNDVINaturalBreaks(self, rawndvifile):
        print "Computing Natural breaks on NDVI.."
        self.files['ndvi_file'] = rawndvifile
        with rasterio.open(rawndvifile) as src:
            profile = src.profile
            bands = src.read()
            stats = []
            for band in bands:
                b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                breaks = nb(b.ravel(),k=4,initial=1)
                bins = breaks.bins.tolist()
        
        bins.insert(0,-1) # add -1 to the beginning of the breaks
        
        print "Writing new NDVI with Natural break classes.."
        with rasterio.open(rawndvifile) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 
                # b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)

                # Reproject and write each band

            with rasterio.open('output/tmp/classified-ndvi.tiff', 'w', **profile) as dst:
                dst.write(bands)


    def classifyUrbanSlope(self, rawslopepath):
        print "Classifying Slope file for Urban..."
        self.files['slope_file'] = rawslopepath
        bins = [-1,5,13,30,47]

        with rasterio.open(self.files['slope_file']) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 
                # b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)


                # Reproject and write each band
            with rasterio.open('output/tmp/classified-slope-urban.tiff', 'w', **profile) as dst:
                dst.write(bands)

        print "Making copy of initial slope file"
        self.files['classifiedurbanslope'] ='output/tmp/classified-slope-urban.tiff'
        shutil.copyfile(self.files['classifiedurbanslope'], 'output/classified-slope.tiff')

        print "Normalizing URB slope file.."
        with rasterio.open('output/tmp/classified-slope-urban.tiff') as classifedsrc:
            classifiedprofile = classifedsrc.profile
            classifiedbands = classifedsrc.read(masked=True)
            classifiedbands = classifiedbands * 100

            with rasterio.open('output/tmp/classified-slope-urban-normalized.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands)

    def classifyAGSlope(self, rawslopepath):
        self.files['slope_file'] = rawslopepath
        print "Classifying Slope file for AG..."
        bins = [-1, 5, 8, 15, 25]

        with rasterio.open(self.files['slope_file']) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 
                # b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)

                # Reproject and write each band
            with rasterio.open('output/tmp/classified-slope-AG.tiff', 'w', **profile) as dst:
                dst.write(bands)


        print "Normalizing AG Slope file.."
        with rasterio.open('output/tmp/classified-slope-AG.tiff') as classifedsrc:
            classifiedprofile = classifedsrc.profile
            classifiedbands = classifedsrc.read(masked=True)
            classifiedbands = classifiedbands * 100
            
            with rasterio.open('output/tmp/classified-slope-AG-normalized.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands)

    def cropSlopeAndNDVI(self):
        # Open the 
        myDataDownloader = DataDownloader()
        localfile = myDataDownloader.downloadFiles([config.settings['aoi']])

        with fiona.open(localfile, "r") as aoi:
            geoms = [feature["geometry"] for feature in aoi]

        self.files['normalized_cropped_urban_slope'] = "output/classified-slope-urban-cropped.tiff"

        self.files['normalized_cropped_ag_slope'] = "output/classified-slope-AG-cropped.tiff"

        self.files['classified_cropped_ndvi_file']="output/classified-ndvi-cropped.tiff"


        print "Cropping Classified Slope and NDVI.."
        with rasterio.open('output/tmp/classified-slope-urban-normalized.tiff') as urb_src:
            urb_out_image, urb_out_transform = mask(urb_src, geoms, crop=True)
            urb_out_meta = urb_src.meta.copy()
            urb_out_meta.update({"driver": "GTiff",
                             "height": urb_out_image.shape[1],
                             "width": urb_out_image.shape[2],
                             "transform": urb_out_transform})

        with rasterio.open(self.files['normalized_cropped_urban_slope'], "w", **urb_out_meta) as urb_dest:
            urb_dest.write(urb_out_image)

        with rasterio.open('output/tmp/classified-slope-AG-normalized.tiff') as ag_src:
            ag_out_image, ag_out_transform = mask(ag_src, geoms, crop=True)
            ag_out_meta = ag_src.meta.copy()
            ag_out_meta.update({"driver": "GTiff",
                             "height": ag_out_image.shape[1],
                             "width": ag_out_image.shape[2],
                             "transform": ag_out_transform})

        with rasterio.open(self.files['normalized_cropped_ag_slope'], "w", **ag_out_meta) as ag_dest:
            ag_dest.write(ag_out_image)



        with rasterio.open('output/tmp/classified-ndvi.tiff') as ndvi_src:
            ndvi_out_image, ndvi_out_transform = mask(ndvi_src, geoms, crop=True)
            ndvi_out_meta = ndvi_src.meta.copy()
            ndvi_out_meta.update({"driver": "GTiff",
                             "height": ndvi_out_image.shape[1],
                             "width": ndvi_out_image.shape[2],
                             "transform": ndvi_out_transform})
        with rasterio.open(self.files['classified_cropped_ndvi_file'], "w", **ndvi_out_meta) as ndvi_dest:
            ndvi_dest.write(ndvi_out_image)


    def generateGIOutput(self):
        print "Processing GI Output"
        shutil.copyfile(self.files['classified_cropped_ndvi_file'], 'output/tmp/gi-nogdhclasses.tiff')
        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        GIClassification = dict([(1,2),(2,5),(3,4),(4,1),(5,1)])

        print "Reclassing GI file.."

        with rasterio.open('output/tmp/gi-nogdhclasses.tiff') as ginogdhsrc:
            classifiedprofile = ginogdhsrc.profile
            classifiedbands = ginogdhsrc.read()
            classifiedbands1 = np.vectorize(GIClassification.get)(classifiedbands)
            classifiedbands2 = classifiedbands1.astype(np.float32)

            with rasterio.open('output/evals/GI/GI.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands2)
        print "Reclassing completed"
        print "..."

    def generateUrbanOutput(self):
        # Read Slope
        with rasterio.open(self.files['normalized_cropped_urban_slope'], "r") as src1:
            src1profile = src1.profile
            src1bands = src1.read(masked=True)  

        # Read NDVI
        with rasterio.open(self.files['classified_cropped_ndvi_file'], "r") as src2:
            src2bands = src2.read(masked=True)

        
        print "Combining Rasters.."
        with rasterio.open('output/tmp/urban-nogdhclasses.tiff', 'w', **src1profile) as dst:
            bands3 = src1bands + src2bands
            dst.write(bands3)

        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        URBClassification = dict([(501,2),(502,2),(503,2),(504,2),(104,2),(204,2), (304,2), (404,2), (101,2),(201,2),(301,2),(401,2), (402,3), (403,2),(102,4),(103,4), (201,5), (203,5), (302,5), (303,5),])

        print "Reclassing final URB file.."
        with rasterio.open('output/tmp/urban-nogdhclasses.tiff') as urbannogdhsrc:
            classifiedprofile = urbannogdhsrc.profile
            classifiedbands = urbannogdhsrc.read(masked=True)

            classifiedbands1 = np.vectorize(URBClassification.get)(classifiedbands)
            classifiedbands2 = classifiedbands1.astype(np.float32)

            with rasterio.open('output/evals/urban/urban.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands2)



    def generateAGOutput(self):
        # Read Slope
        with rasterio.open(self.files['normalized_cropped_ag_slope'], "r") as src1:
            src1profile = src1.profile
            src1bands = src1.read(masked=True)  

        # Read NDVI
        with rasterio.open(self.files['classified_cropped_ndvi_file'], "r") as src2:
            src2bands = src2.read(masked=True)

        
        print "Combining Rasters.."
        with rasterio.open('output/tmp/ag-nogdhclasses.tiff', 'w', **src1profile) as dst:
            bands3 = src1bands + src2bands
            dst.write(bands3)

        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        AGClassification = dict([(101,2),(104,2),(201,2),(204,2),(301,2),(302,2), (303,2), (304,2), (102,3),(103,3),(202,3),(203,3),(401,2),(402,3),(403,3),(404,2),(501,2),(502,2),(503,2),(504,2) ])

        print "Reclassing AG file file.."
        with rasterio.open('output/tmp/ag-nogdhclasses.tiff') as agnogdhsrc:
            classifiedprofile = agnogdhsrc.profile
            classifiedbands = agnogdhsrc.read(masked=True)

            classifiedbands1 = np.vectorize(AGClassification.get)(classifiedbands)
            classifiedbands2 = classifiedbands1.astype(np.float32)


            with rasterio.open('output/evals/ag/ag.tiff', 'w', **classifiedprofile) as classifieddst:
                classifieddst.write(classifiedbands2)


if __name__ == '__main__':
    if not os.path.exists('output/tmp'):
        os.mkdir('output/tmp')

    myEvaluationsProcessor = EvaluationsProcessor()


    myEvaluationsProcessor.createEvalDirectories()
    cwd = os.getcwd()
    rawndvipath = os.path.join(cwd, config.settings['outputdirectory'], 'ndvi.tiff')
    rawslopepath = os.path.join(cwd, config.settings['outputdirectory'], 'slope.tiff')
    rawtranspath = os.path.join(cwd, config.settings['outputdirectory'], 'trans.tiff')
    myEvaluationsProcessor.computeNDVINaturalBreaks(rawndvipath)
    myEvaluationsProcessor.computeTransportNaturalBreaks(rawtranspath)
    myEvaluationsProcessor.classifyUrbanSlope(rawslopepath)
    myEvaluationsProcessor.classifyAGSlope(rawslopepath)
    myEvaluationsProcessor.cropSlopeAndNDVI()

    myEvaluationsProcessor.generateGIOutput()
    myEvaluationsProcessor.generateUrbanOutput()
    myEvaluationsProcessor.generateAGOutput()

    # TODO: Transport 
    # TODO: Hydro

    # remove tmp files
    # shutil.rmtree('output/tmp')
