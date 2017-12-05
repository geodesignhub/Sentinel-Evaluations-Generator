settings = {
	"aoi":"https://gdh-data-sandbox.ams3.digitaloceanspaces.com/data/petilang-jaya-boundary.geojson",
	"systems":["GI", "TRANS", "URBAN", "AG", "HYDRO"],
	# "systems":["GI"],
	"outputdirectory":"output",
	"workingdirectory": "working", 
	"sentinelscene": "S2A_MSIL1C_20170203T032931_N0204_R018_T47NQD_20170203T034408"
}
processchains = {
	"GI":{"list": [{"id": "importer_1",
          "module": "importer",
          "inputs": [{"import_descr": {"source": settings['sentinelscene'],
                                       "type": "sentinel2",
                                       "sentinel_band": "B04"},
                      "param": "map",
                      "value": "B04"},
                     {"import_descr": {"source": settings['sentinelscene'],
                                       "type": "sentinel2",
                                       "sentinel_band": "B08"},
                      "param": "map",
                      "value": "B08"},
                      {"import_descr": {"source": settings['aoi'],
                      	                "type": "vector"},
                       "param": "map",
                       "value": "aoi"}]},

         {"id": "g_region_1",
          "module": "g.region",
          "inputs": [{"param": "raster",
                      "value": "B04"}],
          "flags": "g"},

          {"id": "g_region_2",
          "module": "g.region",
          "inputs": [{"param": "vector",
                      "value": "aoi"}],
          "flags": "g"},

          {"id": "r_mask",
          "module": "r.mask",
          "inputs": [{"param": "vector",
                      "value": "aoi"}]},

         {"id": "rmapcalc_1",
          "module": "r.mapcalc",
          "inputs": [{"param": "expression",
                      "value": "NDVI = float((B08 - B04)/(B08 + B04))"}]},

          {"id": "r_univar_ndvi",
          "module": "r.univar",
          "inputs": [{"param": "map",
                      "value": "NDVI"}],
          "flags": "g"},

         {"id": "r_slope_aspect",
          "module": "r.slope.aspect",
          "inputs": [{"param": "elevation",
                      "value": "srtmgl1_v003_30m@srtmgl1_30m"},
                      {"param": "slope",
                      "value": "slope"}]},\
         {"id": "exporter_1",
          "module": "exporter",
          "outputs": [{"export": {"type": "raster", "format": "GTiff"},
                       "param": "map",
                       "value": "NDVI"},
                       {"export": {"type": "raster", "format": "GTiff"},
                       "param": "map",
                       "value": "slope"},
                       # {"export": {"type": "raster", "format": "GTiff"},
                       # "param": "map",
                       # "value": "B04"},
                       # {"export": {"type": "raster", "format": "GTiff"},
                       # "param": "map",
                       # "value": "B08"}
                       ]}
         ],
"version": "1"}
}
