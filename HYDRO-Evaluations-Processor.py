import geopandas
from geopandas.tools import sjoin
from pysal.esda.mapclassify import Natural_Breaks as nb
import numpy as np
import DataHelper
import os, config


if __name__ == "__main__":        

    cwd = os.getcwd()
    
    myDataDownloader = DataHelper.DataDownloader()
    aoi_path = myDataDownloader.downloadFiles([config.settings['aoi']])

    river_path = os.path.join(cwd, config.settings['workingdirectory'], config.settings['rivers'])
    watershed_path = os.path.join(cwd, config.settings['workingdirectory'], config.settings['watersheds'])
    output_geojson= os.path.join(cwd,config.settings['outputdirectory'],'evals/HYDRO/HYDRO.geojson')
    river = geopandas.GeoDataFrame.from_file(river_path) # or geojson etc
    aoi = geopandas.GeoDataFrame.from_file(aoi_path) 
    watershed = geopandas.GeoDataFrame.from_file(watershed_path)

    watershed['area'] = watershed.apply(lambda row: (row['geometry'].area), axis=1) 
    river['length'] = river.apply(lambda row: (row['geometry'].length), axis=1)

    watershed_with_rivers = sjoin(watershed,river, how='inner', op='intersects')

    watershed_sum_by_river` = watershed_with_rivers.groupby(["HYBAS_ID"]).agg(dict(length="sum")).reset_index()
    watershed['riverlength'] = watershed.HYBAS_ID.map(watershed_sum_by_river`.set_index('HYBAS_ID')['length'].to_dict())
    # replace NaN with a very small number 

    watershed['riverlength'].fillna(1, inplace=True)
    watershed['density'] = watershed.apply(lambda row: (row.area / row.riverlength), axis=1)
    ii = watershed.as_matrix(['density'])
    breaks = nb(ii.ravel(),k=3,initial=1)

    digitizedbins = np.digitize(watershed.density, bins = breaks.bins.tolist())
    watershed['areatype']= digitizedbins

    watershed['areatype'] = watershed['areatype'].map({3:'green',2:'green2',1:'green2',0:'green3'})

    inter = geopandas.overlay(watershed, aoi, how='intersection')

    with open(output_geojson, 'w') as f:
        f.write(inter.to_json())
        
