# imddaily
imddaily is a python package to download and convert Daily Real Time data from 
India Meteorological Department.

The Daily Real Time Data available,
- rain = Daily Rainfall data
- raingpm = Daily Merged Satellite Guage Rainfall (GPM) data
- tmax = Daily Maximum Temperature data
- tmin = Daily Minimum Temperature Data
- tmaxone = Daily Maximum Temperature data (1.0 degree)
- tminone = Daily Minimum Temperature Data (1.0 degree)

# Installation
imddaily can be installed through pip,
```
pip install imddaily
```
dependencies include rasterio, numpy, affine, tqdm, requests.

# Usage
imddaily package can download and convert the IMD data
```
from imddaily import imddaily
data = imddaily.get_data('rain', '2020-01-01', '2020-12-31', '/Users/home/rain/grd/')
data.to_geotiff('/Users/home/rain/tif/')
```

# License
imddaily is available under the [MIT](https://mit-license.org) License.

# References
- GitHub: https://github.com/balakumaran247/imddaily
- IMD: https://www.imdpune.gov.in
- Data: https://www.imdpune.gov.in/Seasons/Temperature/temp.html