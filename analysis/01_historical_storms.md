# Historical storms

```python
%load_ext jupyter_black

```

```python
from climada.hazard import Centroids, TCTracks, TropCyclone
from shapely.geometry import LineString
import pandas as pd

from src import utils
```

```python
help(TCTracks.from_ibtracs_netcdf)
```

```python
# Download all tracks from the west pacific basin
sel_ibtracs = TCTracks.from_ibtracs_netcdf(basin="NI", provider="newdelhi")
sel_ibtracs.size
```

```python
tc_tracks = TCTracks()
for track in sel_ibtracs.data:
    line = LineString((y, x) for x, y in zip(track.lat, track.lon))
    bgd = utils.admin0.geometry[0].intersects(line)
    if bgd:
        tc_track = sel_ibtracs.get_track(track.sid)
        tc_tracks.append(tc_track)
len(tc_tracks.data)
```

```python
tc_tracks.plot()
```

```python
df = pd.DataFrame()
for track in tc_tracks.data:
    df = pd.concat(
        (
            df,
            pd.DataFrame(
                {
                    "name": track.name,
                    "category": track.category,
                    # "pressure_max": track.central_pressure.values.max(),
                    "wind_max": track.max_sustained_wind.values.max(),
                    "date": track.time.values[0],
                },
                index=[0],
            ),
        )
    )
df["year"] = df.date.dt.year
df = df.sort_values(by="date")

df
```

```python
df.to_csv("cyclones.csv", index=False)
```

```python
tc_tracks_strong = TCTracks()
tc_tracks_strong.data = [
    track for track in tc_tracks.data if track.category > 1
]
tc_tracks_strong.plot()
```

```python

```
