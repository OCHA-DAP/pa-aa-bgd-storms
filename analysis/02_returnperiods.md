# Getting The Return Period for Cyclones in Bangladesh



This notebook replicates the work done to develop a framework for cyclones in Fiji. 
To note:
- This work is done for cyclones that cross into land and therefore distance from land is no longer useful.
- It only looks at one division, Barisal.
- The aim is to get the return period for various categories of storms.
- This notebook uses shapefile data from IBTrACS. To replicate it, please download the data from https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/shapefile/
- The focus is on the Northern Indian Ocean Basin.


```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```



<script type="application/javascript" id="jupyter_black">
(function() {
    if (window.IPython === undefined) {
        return
    }
    var msg = "WARNING: it looks like you might have loaded " +
        "jupyter_black in a non-lab notebook with " +
        "`is_lab=True`. Please double check, and if " +
        "loading with `%load_ext` please review the README!"
    console.log(msg)
    alert(msg)
})()
</script>




```python
#libraries
import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import os
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import ochanticipy as oap
```


```python
# loading cod ab
country_config = oap.create_country_config(iso3="bgd")
codab = oap.CodAB(country_config)
bgd_admin1 = codab.load(admin_level=1)
```


```python
barisal_ab = bgd_admin1[bgd_admin1["ADM1_EN"] == "Barisal"]
```


```python
# loading ibtracs
ibtracs_pointdf = gpd.read_file(
    Path(
        os.getenv("AA_DATA_DIR"),
        "public/raw/bgd/ibtracs/IBTrACS.NI.list.v04r00.points.zip",
    )
)
ibtracs_linesdf = gpd.read_file(
    Path(
        os.getenv("AA_DATA_DIR"),
        "public/raw/bgd/ibtracs/IBTrACS.NI.list.v04r00.lines.zip",
    )
)
```


```python
ibtracs_pointdf.crs == barisal_ab.crs
```




    True




```python
ibtracs_pointdf["SEASON NAME"] = (
    ibtracs_pointdf["NAME"] + " " + ibtracs_pointdf["SEASON"].astype(str)
)
ibtracs_linesdf["SEASON NAME"] = (
    ibtracs_linesdf["NAME"] + " " + ibtracs_linesdf["SEASON"].astype(str)
)
```


```python
barisal_cyclones = ibtracs_pointdf.loc[
    ibtracs_pointdf.within(barisal_ab.geometry[0]), :
]
```


```python
# starting point
start_yr = 1990  # 1990
yr_len = (2023 - barisal_cyclones["year"].iloc[0]) + 1
if start_yr > 0:
    yr_len = (2023 - start_yr) + 1
# yr_len = (2023 - barisal_cyclones["year"].iloc[0]) + 1
```


```python
barisal_cyclonesdf = barisal_cyclones[barisal_cyclones["year"] >= start_yr]
```


```python
categories = barisal_cyclonesdf["NEW_GRADE"].unique()
```


```python
barisal_cyclonesdf["NEW_GRADE"].value_counts()
```




    NEW_GRADE
    D      18
    DD      7
    SCS     1
    CS      1
    Name: count, dtype: int64




```python
stat_df = (
    barisal_cyclonesdf[["SEASON NAME", "NEW_GRADE"]]
    .groupby(["NEW_GRADE"])
    .count()
    .reset_index()
)
stat_df["RP"] = yr_len / stat_df["SEASON NAME"]
stat_df["RP Rounded"] = round(yr_len / stat_df["SEASON NAME"])

stat_df
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>NEW_GRADE</th>
      <th>SEASON NAME</th>
      <th>RP</th>
      <th>RP Rounded</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>CS</td>
      <td>1</td>
      <td>34.000000</td>
      <td>34.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>D</td>
      <td>18</td>
      <td>1.888889</td>
      <td>2.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>DD</td>
      <td>7</td>
      <td>4.857143</td>
      <td>5.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>SCS</td>
      <td>1</td>
      <td>34.000000</td>
      <td>34.0</td>
    </tr>
  </tbody>
</table>
</div>



There does not seem to be storms larger than a deep depression occurring frequently.

- The RP for a cyclone storm is 1-in-34 years which is the same for a severe cyclone storm.
- A depression has a RP of 1-in-2 years.
- A deep depression has a RP of 1-in-5-years.
