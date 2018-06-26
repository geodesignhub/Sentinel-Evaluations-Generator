import geopandas
from geopandas.tools import sjoin

import os, config
cwd = os.getcwd()

riverpath = os.path.join(cwd, config.settings['workingdirectory'], config.settings['rivers'])
watershedpath = os.path.join(cwd, config.settings['workingdirectory'], config.settings['rivers'])

point = geopandas.GeoDataFrame.from_file(riverpath) # or geojson etc
poly = geopandas.GeoDataFrame.from_file(watershedpath)
pointInPolys = sjoin(point, poly, how='inner', op='intersects')
county_counts = pointInPolys.groupby([
    "a_ARCID_left",
]).agg(dict(length_right="count")).reset_index()

print county_counts