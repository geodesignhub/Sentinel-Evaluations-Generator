# Geodesignhub Sentinel Evaluation Maps Builder
This program uses open data from the EU [Copernicus](https://scihub.copernicus.eu/) program and [Mundialis Actinia Platform](https://www.mundialis.de/en/copernicus-and-sentinel/) to develop Evaluation maps for [Geodesignhub](https://www.geodesignhub.com/). This program uses a combination of image processing on Earth Observation images to develop evaluation maps in Raster at 10m resolution for any site across the world where Sentinel earth observation images are available. 
Making evaluation maps is the most time consuming part of a Geodesign study, using this script it can be automated. The following evaluation maps are generated: 

* Green Infrastructure (GI)
* Agriculture (AG)
* Hyrdology (HYDRO)
* Transport (TRANS)
* Urban (URBAN)

Find out more about evaluation maps at the [Making Evaluations Maps](https://community.geodesignhub.com/t/making-evaluation-maps/62) in our community page. 

At the moment, this is best suited for generating evaluations at regional level and for studies for where the study area is at a regional scale larger than a few neighbourhoods. Please take a look at the complementary [OSM evaluation maps builder](https://geodesignhub.github.io/OSM-Evaluations-Builder/)

If you are new to Geodesignhub, please see our course at [Teachable.com](https://geodesignhub.teachable.com/p/geodesign-with-geodesignhub/)  

## Technical Details
TBC: Complete the technical details of how these files are generated. 

## Installation
Use the requirements.txt file to install libraries that are required for the program

```
pip install requirements.txt
```

## 3-Step process
**1. Study area boundary and Sentinel Scene**

1. Upload a GeoJSON boundary file to a publically accessible location e.g. Google Storage or Digital Ocean Spaces.
2. Use the [Sentinel Scene explorer](https://eome.mundialis.de/eome/client/index.html) to select a appropriate sentinel scene. 
3. Enter your Mundialis Username and password. 


**2. Update config.py**

1. In config.py set the URL of the boundary GeoJSON in the `aoi` variable
2. Set the Sentinel scence name in the `sentinelscene` parameter (e.g. S2A_MSIL1C_20170203T032931_N0204_R018_T47NQD_20170203T034408)

**3. Upload Evaluations**

1. Run the `Mundialis-Evaluations-Generator.py` script and check the `output` folder for the Evaluation Rasters
2. Run the `Raster-Evaluations-Processor.py` to further process the evaluations
