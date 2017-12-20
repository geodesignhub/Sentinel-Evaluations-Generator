# Geodesignhub Sentinel Evaluation Maps Builder
This program uses open data from the EU [Copernicus](https://scihub.copernicus.eu/) program and [Mundialis Actinia Platform](https://www.mundialis.de/en/copernicus-and-sentinel/) to develop Evaluation maps for [Geodesignhub](https://www.geodesignhub.com/). This program uses a combination of image processing on Earth Observation images to develop evaluation maps in Raster at 10m resolution for any site across the world where Sentinel earth observation images are available. 
Making evaluation maps is the most time consuming part of a Geodesign study, using this script it can be automated. The following evaluation maps are generated: 

* Green Infrastructure (GI)
* Agriculture (AG)
* Hyrdology (HYDRO)
* Transport (TRANS)
* Urban (URBAN)

Find out more about evaluation maps at the [Making Evaluations Maps](https://community.geodesignhub.com/t/making-evaluation-maps/62) in our community page. 

At the moment, this is best suited for generating evaluations at regional level and for studies for where the study area is at a regional scale larger than a few neighbourhoods. Please take a look at the complementary [OSM evaluation maps builder](https://geodesignhub.github.io/OSM-Evaluations-Builder/). 



If you are new to Geodesignhub, please see our course at [Teachable.com](https://geodesignhub.teachable.com/p/geodesign-with-geodesignhub/)  

## Technical Details
This program takes in Earth Observation imagery and produces Evaluation maps for Agriculture, Green Infrastructure, Urban and Transport systems. Below are links to how these maps are generated in GIS and this script aims to replicate them using the Mundialis Actinia platform and open source GIS tools and libraries. 
The following PDFs detail the steps to be taken to generate these maps: 

1. [Generating Green Infrastructure Evaluation map](https://github.com/geodesignhub/Sentinel-Evaluations-Generator/blob/master/PPT/Methodology%20to%20produce%20a%20green%20map%20using%20GIS.pdf)
2. [Generating Agriculture Evaluation map](https://github.com/geodesignhub/Sentinel-Evaluations-Generator/blob/master/PPT/Methodology%20to%20produce%20the%20agri%20map%20using%20GIS.pdf)
3. [Generating Urban Infrastucture Evaluation map](https://github.com/geodesignhub/Sentinel-Evaluations-Generator/blob/master/PPT/Methodology%20to%20produce%20a%20urban%20and%20using%20GIS.pdf)
4. [Generating Transport Map](https://github.com/geodesignhub/Sentinel-Evaluations-Generator/blob/master/PPT/Methodology%20to%20produce%20a%20Transportation%20System%20using%20GIS.pdf) 

## Installation
Use the requirements.txt file to install libraries that are required for the program

```
pip install requirements.txt
```

## 4-Step process
**1. Study area boundary and Sentinel Scene**

1. Upload a GeoJSON boundary file to a publically accessible location e.g. [Google Storage](https://cloud.google.com/storage/) or [Digital Ocean Spaces](https://www.digitalocean.com/products/object-storage/) as a JSON file.
2. Use the [Sentinel Scene explorer](https://eome.mundialis.de/eome/client/index.html) to select a appropriate sentinel scene. 
3. Create file call `ActiniaCredentials.py` and enter your Mundialis Username and passwordin the following format (You can request your Mundialis credentials by filling out their contact [form](https://www.mundialis.de/contact/)): 

```python
cred = {
	"username" : 'YOUR_MUNDIALIS_USERNAME', 
	"password" : 'YOUR_MUNDIALIS_PASSWORD', 
}
```

**2. Update config.py**

1. In config.py set the URL of the boundary GeoJSON in the `aoi` variable
2. Set the Sentinel scence name in the `sentinelscene` parameter (e.g. S2A_MSIL1C_20170203T032931_N0204_R018_T47NQD_20170203T034408)

**3. Generate Evaluations**

1. Run the `Mundialis-Evaluations-Generator.py` script and check the `output` folder for the Evaluation Rasters
2. Run the `Raster-Evaluations-Processor.py` to further process the evaluations

**4. Post Processing**

1. One of the first things that you can do is use `RasterSimplifier.py` file to simplify the generated evaluation maps. This script will take the generated files from above and simplify it.
2. The script generates Raster files (*.tiff) that need to be further processed since Geodesignhub accepts only Vectors (GeoJSON). 
3. The script will generate GeoJSON based on the Rasters that are reclassfied, you can do it yourself using GIS and the following steps are recommended to enable uploads to Geodesignhub: 
	- Simplify the files using r.neighbours command
	- Convert to vectors
	- Reclassify the vectors to the approrpriate "areatype" attribute