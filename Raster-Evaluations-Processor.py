import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import crs
from rasterio.mask import mask
import numpy as np
from numpy import copy
import os, shutil
import fiona
import json
from fiona.crs import from_string
from rasterio.features import shapes
from pprint import pprint
from pysal.esda.mapclassify import Natural_Breaks as nb
import config, requests
import DataHelper

class EvaluationsProcessor():
    def __init__(self):
        self.files = {'ndvi_file':'', 'classified_cropped_ndvi_file':'','slope_file':'','normalized_cropped_urban_slope':'', 'normalized_cropped_ag_slope':'','normalized_cropped_trans':''}
        self.cwd = os.getcwd()

    def create_output_directories(self):
        systems = config.settings['systems']

        dirpath = os.path.join(self.cwd,config.settings['outputdirectory'],'evals')
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        tmppath = os.path.join(self.cwd,config.settings['outputdirectory'],'tmp')
        if not os.path.exists(tmppath):
            os.mkdir(tmppath)
        for system in systems: 
            dirpath = os.path.join(self.cwd,config.settings['outputdirectory'],'evals',system)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            dirpath = os.path.join(self.cwd,config.settings['outputdirectory'],'evals',system)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)

    def compute_Transport_natural_breaks(self, rawtransfile):
        print("Computing Natural breaks on Transport..")

        my_data_downloader = DataHelper.DataDownloader()
        localfile = my_data_downloader.download_files([config.settings['aoi']])

        with fiona.open(localfile, "r") as aoi:
            geoms = [feature["geometry"] for feature in aoi]

        classified_trans_tmp_path = os.path.join(self.cwd,config.settings['outputdirectory'],'tmp','classified-transport.tiff')
            
        with rasterio.open(rawtransfile) as src:
            profile = src.profile
            bands = src.read()
            for band in bands:
                b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band)))]
                breaks = nb(b.ravel(), k=4, initial=1)
                bins = breaks.bins.tolist()
        
        # bins.insert(1,-1) # add -1 to the beginning of the breaks
        # print bins
        print("Writing new Transport with Natural break classes..")
        with rasterio.open(rawtransfile) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 

                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)

                # Reproject and write each band

            with rasterio.open(classified_trans_tmp_path, 'w', **profile) as dst:
                dst.write(bands)

        classfiedtranspath = os.path.join(self.cwd,config.settings['outputdirectory'],'classified-transport.tiff')
            
        print("Cropping Transport..")
        
        with rasterio.open(classified_trans_tmp_path) as trans_src:
            trans_out_image, trans_out_transform = mask(trans_src, geoms, crop=True)
            trans_out_meta = trans_src.meta.copy()
            trans_out_meta.update({"driver": "GTiff",
                             "height": trans_out_image.shape[1],
                             "width": trans_out_image.shape[2],
                             "transform": trans_out_transform})

        with rasterio.open(classfiedtranspath, "w", **trans_out_meta) as trans_dest:
            trans_dest.write(trans_out_image)

        transport_classifications = dict([(1,2),(2,3),(3,1),(4,1)])

        print("Reclassing Transport file..")

        finaltransevalpath = os.path.join(self.cwd,config.settings['outputdirectory'],'evals','TRANS', 'TRANS.tiff')
            
        with rasterio.open(classfiedtranspath) as transnogdhsrc:
            classified_profile = transnogdhsrc.profile
            classified_bands = transnogdhsrc.read()
            classified_bands_a = np.vectorize(transport_classifications.get)(classified_bands)
            classified_bands_b = classified_bands_a.astype(np.float32)

            with rasterio.open(finaltransevalpath, 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands_b)

        print("Reclassing completed")
        print("...")

    def compute_NDVI_natural_breaks(self, rawndvifile):
        print("Computing Natural breaks on NDVI..")
        self.files['ndvi_file'] = rawndvifile
        with rasterio.open(rawndvifile) as src:
            profile = src.profile
            bands = src.read()
            for band in bands:
                b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band)))]
                breaks = nb(b.ravel(),k=4,initial=1)
                bins = breaks.bins.tolist()
        
        bins.insert(0,-1) # add -1 to the beginning of the breaks
        
        classfied_ndvi_tmppath = os.path.join(self.cwd,config.settings['outputdirectory'],'tmp','classified-ndvi.tiff')
    
        print("Writing new NDVI with Natural break classes..")
        with rasterio.open(rawndvifile) as src:
            profile = src.profile
            bands = src.read(masked=True)
            for band in bands: 
                # b = band[(band != np.array(None)) & (np.logical_not(np.isnan(band))) ]
                for x in np.nditer(band, op_flags=['readwrite']):
                    x[...] = np.digitize(x,bins)

                # Reproject and write each band

            with rasterio.open(classfied_ndvi_tmppath, 'w', **profile) as dst:
                dst.write(bands)

    def classify_urban_slope(self, rawslopepath):
        print("Classifying Slope file for Urban...")
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

        print("Making copy of initial slope file")
        self.files['classifiedurbanslope'] ='output/tmp/classified-slope-urban.tiff'
        shutil.copyfile(self.files['classifiedurbanslope'], 'output/classified-slope.tiff')

        print("Normalizing URB slope file..")
        with rasterio.open('output/tmp/classified-slope-urban.tiff') as classifedsrc:
            classified_profile = classifedsrc.profile
            classified_bands = classifedsrc.read(masked=True)
            classified_bands = classified_bands * 100

            with rasterio.open('output/tmp/classified-slope-urban-normalized.tiff', 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands)

    def classify_ag_slope(self, rawslopepath):
        self.files['slope_file'] = rawslopepath
        print("Classifying Slope file for AG...")
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


        print("Normalizing AG Slope file..")
        with rasterio.open('output/tmp/classified-slope-AG.tiff') as classifedsrc:
            classified_profile = classifedsrc.profile
            classified_bands = classifedsrc.read(masked=True)
            classified_bands = classified_bands * 100
            
            with rasterio.open('output/tmp/classified-slope-AG-normalized.tiff', 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands)

    def crop_slope_and_ndvi(self):
        # Open the 
        my_data_downloader = DataHelper.DataDownloader()
        localfile = my_data_downloader.download_files([config.settings['aoi']])

        with fiona.open(localfile, "r") as aoi:
            geoms = [feature["geometry"] for feature in aoi]

        self.files['normalized_cropped_urban_slope'] = "output/classified-slope-urban-cropped.tiff"

        self.files['normalized_cropped_ag_slope'] = "output/classified-slope-AG-cropped.tiff"

        self.files['classified_cropped_ndvi_file']="output/classified-ndvi-cropped.tiff"


        print("Cropping Classified Slope and NDVI..")
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

    def generate_gi_output(self):
        print("Processing GI Output")
        shutil.copyfile(self.files['classified_cropped_ndvi_file'], 'output/tmp/gi-nogdhclasses.tiff')
        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        gi_classifications = dict([(1,2),(2,5),(3,4),(4,1),(5,1)])

        print("Reclassing GI file..")

        with rasterio.open('output/tmp/gi-nogdhclasses.tiff') as ginogdhsrc:
            classified_profile = ginogdhsrc.profile
            classified_bands = ginogdhsrc.read()
            classified_bands_a = np.vectorize(gi_classifications.get)(classified_bands)
            classified_bands_b = classified_bands_a.astype(np.float32)

            with rasterio.open('output/evals/GI/GI.tiff', 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands_b)
        print("Reclassing completed")
        print("...")
        return 'output/evals/GI/GI.tiff'

    def generate_urban_output(self):
        # Read Slope
        with rasterio.open(self.files['normalized_cropped_urban_slope'], "r") as src1:
            src1_profile = src1.profile
            src1_bands = src1.read(masked=True)  

        # Read NDVI
        with rasterio.open(self.files['classified_cropped_ndvi_file'], "r") as src2:
            src2_bands = src2.read(masked=True)
        
        print("Combining Rasters..")
        with rasterio.open('output/tmp/urban-nogdhclasses.tiff', 'w', **src1_profile) as dst:
            bands3 = src1_bands + src2_bands
            dst.write(bands3)

        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        urban_classifications = dict([(501,2),(502,2),(503,2),(504,2),(104,2),(204,2), (304,2), (404,2), (101,2),(201,2),(301,2),(401,2), (402,3), (403,2),(102,4),(103,4), (201,5), (203,5), (302,5), (303,5),])

        print("Reclassing final URB file..")
        with rasterio.open('output/tmp/urban-nogdhclasses.tiff') as urban_no_gdh_src:
            classified_profile = urban_no_gdh_src.profile
            classified_bands = urban_no_gdh_src.read(masked=True)

            classified_bands_a = np.vectorize(urban_classifications.get)(classified_bands)
            classified_bands_b = classified_bands_a.astype(np.float32)

            with rasterio.open('output/evals/urban/urban.tiff', 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands_b)


        return 'output/evals/urban/urban.tiff'

    def generate_ag_output(self):
        # Read Slope
        with rasterio.open(self.files['normalized_cropped_ag_slope'], "r") as src1:
            src1_profile = src1.profile
            src1_bands = src1.read(masked=True)  

        # Read NDVI
        with rasterio.open(self.files['classified_cropped_ndvi_file'], "r") as src2:
            src2_bands = src2.read(masked=True)

        print("Combining Rasters..")
        with rasterio.open('output/tmp/ag-nogdhclasses.tiff', 'w', **src1_profile) as dst:
            bands3 = src1_bands + src2_bands
            dst.write(bands3)

        # 1 existing 2 Not appropriate 3: Capable 4: Suitable 5: Feasable 
        agriculture_classifications = dict([(101,2),(104,2),(201,2),(204,2),(301,2),(302,2), (303,2), (304,2), (102,3),(103,3),(202,4),(203,4),(401,2),(402,3),(403,3),(404,2),(501,2),(502,2),(503,2),(504,2)])

        print("Reclassing AG file file..")
        with rasterio.open('output/tmp/ag-nogdhclasses.tiff') as agnogdhsrc:
            classified_profile = agnogdhsrc.profile
            classified_bands = agnogdhsrc.read(masked=True)

            classified_bands_a = np.vectorize(agriculture_classifications.get)(classified_bands)
            classified_bands_b = classified_bands_a.astype(np.float32)


            with rasterio.open('output/evals/ag/ag.tiff', 'w', **classified_profile) as urban_dst:
                urban_dst.write(classified_bands_b)

        return 'output/evals/ag/ag.tiff'


if __name__ == '__main__':

    if not os.path.exists('output/tmp'):
        os.mkdir('output/tmp')

    my_evaluations_processor = EvaluationsProcessor()

    my_evaluations_processor.create_output_directories()

    cwd = os.getcwd()
    rawndvipath = os.path.join(cwd, config.settings['outputdirectory'], 'NDVI.tiff')
    rawslopepath = os.path.join(cwd, config.settings['outputdirectory'], 'slope.tiff')
    rawtranspath = os.path.join(cwd, config.settings['outputdirectory'], 'trans.tiff')

    my_evaluations_processor.compute_NDVI_natural_breaks(rawndvipath)
    
    trans_raster = 0
    if os.path.exists(rawtranspath):
        trans_raster = my_evaluations_processor.compute_Transport_natural_breaks(rawtranspath)
    


    my_evaluations_processor.classify_urban_slope(rawslopepath)
    my_evaluations_processor.classify_ag_slope(rawslopepath)
    my_evaluations_processor.crop_slope_and_ndvi()

    gi_raster = my_evaluations_processor.generate_gi_output()
    urban_raster = my_evaluations_processor.generate_urban_output()
    ag_raster = my_evaluations_processor.generate_ag_output()

    
    