# Getting The Return Period for Cyclones in Bangladesh



This notebook replicates the work done to develop a framework for cyclones in Fiji. 
To note:
- This work is done for cyclones that cross into land and therefore distance from land is no longer useful.
- It looks at the whole country but the pilot will be for one division, Barisal.
- The aim is to get the return period for various categories of storms.
- This notebook uses shapefile data from IBTrACS. To replicate it, please download the data from https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/shapefile/
- The focus is on the Northern Indian Ocean Basin.
- A buffer is used to isolate cyclones close to the coastline. 
- More info on track data here: https://www.ncei.noaa.gov/sites/default/files/2021-07/IBTrACS_v04_column_documentation.pdf 


```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```


```python
# libraries
import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import os
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import ochanticipy as oap
from climada.hazard import Centroids, TCTracks, TropCyclone
from shapely.geometry import LineString
```


```python
# loading ibtracs
ibtracs_pointdf = gpd.read_file(
    Path(
        os.getenv("AA_DATA_DIR"),
        "public/raw/bgd/ibtracs/IBTrACS.NI.list.v04r00.points.zip",
    )
)
# ibtracs_linesdf = gpd.read_file(Path(os.getenv("AA_DATA_DIR"),"public/raw/bgd/ibtracs/IBTrACS.NI.list.v04r00.lines.zip",))
```


```python
# loading cod ab
country_config = oap.create_country_config(iso3="bgd")
codab = oap.CodAB(country_config)
bgd_admin1 = codab.load(admin_level=1)
bgd_admin0 = codab.load(admin_level=0)
```


```python
bgd_admin0.plot()
```


```python
bgd_admin0_buff = bgd_admin0.copy()
bgd_admin0_buff["geometry"] = bgd_admin0_buff.buffer(500 / 111)
bgd_admin0_buff.plot()
```


```python
barisal_ab = bgd_admin1[bgd_admin1["ADM1_EN"] == "Barisal"]
```


```python
barisal_ab_buff = barisal_ab.copy()
barisal_ab_buff["geometry"] = barisal_ab_buff.buffer(500 / 111)
barisal_ab_buff.plot()
```


```python
ibtracs_pointdf.crs == barisal_ab.crs
```


```python
ibtracs_pointdf["SEASON NAME"] = (
    ibtracs_pointdf["NAME"] + " " + ibtracs_pointdf["SEASON"].astype(str)
)
```


```python
bgd_cyclones = ibtracs_pointdf.loc[
    ibtracs_pointdf.within(barisal_ab_buff.geometry[0]), :
]
```


```python
bgd_cyclones.to_crs(epsg=3106).geometry
```


```python
# calculate distance between each point and adm0 (slow-ish)
bgd_cyclones["Distance (km)"] = (
    bgd_cyclones.to_crs(epsg=3106).apply(
        lambda point: point.geometry.distance(
            barisal_ab.to_crs(epsg=3106).geometry[0].boundary
        ),
        axis=1,
    )
    / 1000
)
```


```python
# starting point
start_yr = 0  # 1990
yr_len = (2023 - bgd_cyclones["year"].iloc[0]) + 1
if start_yr > 0:
    yr_len = (2023 - start_yr) + 1
# yr_len = (2023 - barisal_cyclones["year"].iloc[0]) + 1
```


```python
barisal_cyclonesdf = bgd_cyclones[bgd_cyclones["year"] >= start_yr]
```


```python
barisal_cyclonesdf.head(2)
```


```python
categories = barisal_cyclonesdf["NEW_GRADE"].unique()
```


```python
barisal_cyclonesdf["NEW_GRADE"].value_counts()
```


```python
stat_df = (
    barisal_cyclonesdf[["SEASON NAME", "NEW_GRADE"]]
    .drop_duplicates()
    .groupby(["NEW_GRADE"])
    .count()
    .reset_index()
)
stat_df["RP"] = yr_len / stat_df["SEASON NAME"]
stat_df["RP Rounded"] = round(yr_len / stat_df["SEASON NAME"])

stat_df
```


```python
# convert word grades into numeric
grade2num = {
    "D": -1,
    "DD": 0,
    "CS": 1,
    "SCS": 2,
    "VSCS": 3,
    "ESCS": 4,
    "SCS(H)": 5,
    "SUCS": 5,
}
barisal_cyclonesdf["GRADE_NUM"] = barisal_cyclonesdf["NEW_GRADE"].replace(
    grade2num
)
barisal_cyclonesdf = barisal_cyclonesdf.dropna(subset="GRADE_NUM")
```


```python
distances = [1, 100, 200, 350, 500]
categories = [2, 3, 4, 5]

triggers = pd.DataFrame()

for distance in distances:
    for category in categories:
        thresholds = [
            {
                "distance": distance,
                "category": category,
            },
        ]
        dff = pd.DataFrame()
        for threshold in thresholds:
            # cycle through composite thresholds
            df_add = barisal_cyclonesdf[
                (
                    barisal_cyclonesdf["Distance (km)"]
                    <= threshold.get("distance")
                )
                & (
                    barisal_cyclonesdf["GRADE_NUM"]
                    >= threshold.get("category")
                )
            ]
            dff = pd.concat([dff, df_add])
        dff = dff.sort_values("ISO_TIME", ascending=False)
        nameseasons = dff["SEASON NAME"].unique()
        df_add = pd.DataFrame(
            {
                "distance": distance,
                "category": category,
                "count": len(nameseasons),
                "nameseasons": "<br>".join(nameseasons),
            },
            index=[0],
        )
        triggers = pd.concat([triggers, df_add], ignore_index=True)

triggers["return"] = (
    len(pd.to_datetime(barisal_cyclonesdf["ISO_TIME"]).dt.year.unique())
    / triggers["count"]
)

# reshape return period
df_freq = triggers.pivot(
    index="category",
    columns="distance",
    values="return",
)
df_freq = df_freq.sort_values("category", ascending=False)
df_freq.columns = df_freq.columns.astype(str)
df_freq.index = df_freq.index.astype(str)
df_freq = df_freq.astype(float).round(2)

# reshape lists of cyclones triggered
df_records = triggers.pivot(
    index="category",
    columns="distance",
    values="nameseasons",
)
df_records = df_records.sort_values("category", ascending=False)
df_records.columns = df_records.columns.astype(str)
df_records.index = df_records.index.astype(str)

fig = px.imshow(
    df_freq,
    text_auto=True,
    range_color=[1, 5],
    color_continuous_scale="Reds",
)
# add lists of cyclones triggered as customdata for hover
fig.update(
    data=[
        {
            "customdata": df_records,
            "hovertemplate": "Cyclones triggered:<br>%{customdata}",
        }
    ]
)

fig.update_traces(name="")
fig.update_layout(
    coloraxis_colorbar_title="Return<br>period<br>(years)",
)
fig.update_xaxes(side="top", title_text=f"Distance (km)")
fig.update_yaxes(title_text=f"Category")

# note: can change renderer to show in browser instead

# if plot doesn't initially show up, switch to renderer="svg"
# then back to "notebook"
fig.show(renderer="notebook")
```


```python
# Download all tracks
sel_ibtracs = TCTracks.from_ibtracs_netcdf(basin="NI", provider="newdelhi")
sel_ibtracs.size
```


```python
country_config = oap.create_country_config(iso3="bgd")
codab = oap.CodAB(country_config)
bgd_admin0 = codab.load(admin_level=0)
bgd_admin1 = codab.load(admin_level=1)
barisal_ab = bgd_admin1[bgd_admin1["ADM1_EN"] == "Barisal"]
```


```python
tc_tracks = TCTracks()
for track in sel_ibtracs.data:
    line = LineString((y, x) for x, y in zip(track.lat, track.lon))
    bgd = barisal_ab.geometry[0].intersects(line)
    if bgd:
        tc_track = sel_ibtracs.get_track(track.sid)
        tc_tracks.append(tc_track)
len(tc_tracks.data)
```


```python
tc_tracks.plot()
```
