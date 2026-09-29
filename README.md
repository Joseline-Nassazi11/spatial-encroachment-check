# Spatial Encroachment Check

A small GeoPandas/Shapely pipeline that checks which detected construction points fall inside a protected zone, and flags them for review.

## Problem

Given:

- a protected zone boundary as a WKT polygon in **EPSG:4326** (WGS 84, longitude/latitude)
- a list of detected activity points, each with `lon`, `lat` and a description

Find which points fall inside the protected zone.

## Input data

**Protected zone**

```
POLYGON ((32.5800 0.3200, 32.6000 0.3200, 32.6000 0.3400, 32.5800 0.3400, 32.5800 0.3200))
```

This is a rectangle:

- Longitude: 32.5800 → 32.6000
- Latitude: 0.3200 → 0.3400

**Detected points**

| Point   | Lon     | Lat    | Description                      |
|---------|---------|--------|----------------------------------|
| LOC_001 | 32.5900 | 0.3300 | Foundation excavation observed   |
| LOC_002 | 32.5750 | 0.3250 | Commercial warehouse structure   |
| LOC_003 | 32.5950 | 0.3350 | Active bricklaying site          |
| LOC_004 | 32.6100 | 0.3500 | Residential fence wall completed |
| LOC_005 | 32.5850 | 0.3220 | Grading of marshland vegetation  |

## Result

| Point   | Result             | Reason                                  |
|---------|--------------------|-----------------------------------------|
| LOC_001 | Flagged for review | Inside the zone                         |
| LOC_002 | Outside            | West of the boundary (32.5750 < 32.5800) |
| LOC_003 | Flagged for review | Inside the zone                         |
| LOC_004 | Outside            | North-east of the boundary              |
| LOC_005 | Flagged for review | Inside the zone                         |

**3 of 5 points flagged: LOC_001, LOC_003, LOC_005.**

## How it works

`src/main.py` has three steps:

1. **`create_protection_zone(zone_wkt, crs)`**
   Parses the WKT string into a Shapely polygon and wraps it in a GeoDataFrame with its CRS.

2. **`create_detected_points(records, crs)`**
   Turns each `lon` / `lat` pair into a Shapely `Point` (lon = x, lat = y) and builds a GeoDataFrame.

3. **`check_encroachment(protection_zone, detected_points)`**
   - Re-projects the points if their CRS differs from the zone's
   - Tests each point with `covered_by` against the polygon
   - Returns a copy of the points with a `flagged` column (`True` / `False`)

`main()` wires these together and prints the flagged records.

## How to run

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# source .venv/bin/activate      # macOS / Linux

pip install -r requirements.txt
python src/main.py
python -m pytest -q
```

Expected output:

```
Flagged for review: 3 of 5 detected points
point_id                     description    lon   lat
 LOC_001  Foundation excavation observed 32.590 0.330
 LOC_003         Active bricklaying site 32.595 0.335
 LOC_005 Grading of marshland vegetation 32.585 0.322
```

```
6 passed
```

## Design decisions

- **`covered_by` instead of `within`**
  `within` returns `False` for a point exactly on the boundary line. For a protected zone, a point on the edge should still be flagged.

- **CRS alignment**
  If the points arrive in a different CRS, they are re-projected to the zone's CRS before the check. Comparing geometries in different coordinate systems gives wrong answers without any error.

- **Explicit inputs**
  The loader functions take the WKT, records and CRS as arguments instead of reading globals. This keeps them easy to test and reuse with other zones and points.

- **No mutation of inputs**
  `check_encroachment` works on a copy, so the caller's data is unchanged.

## Tests

`tests/test_pipeline.py` has 6 tests:

| Test | What it checks |
|------|----------------|
| `test_flags_expected_points` | LOC_001, LOC_003, LOC_005 are flagged |
| `test_outside_points_not_flagged` | LOC_002, LOC_004 are not flagged |
| `test_crs_is_preserved` | Output stays in EPSG:4326 |
| `test_point_on_boundary_is_flagged` | A point on the edge is flagged (`covered_by` behaviour) |
| `test_input_not_modified` | The input GeoDataFrame is not changed |
| `test_points_in_different_crs_are_aligned` | Points given in EPSG:3857 are re-projected and give the same 3 flags |

## Limitations and next steps

- **A flag is not a violation.** It means the point falls inside the supplied boundary. It is a potential encroachment for review, not a confirmed legal finding.
- **Points are treated as exact.** Real detections have positional error. A production version could add a buffer around the zone, after projecting to a metric CRS such as UTM 36N (EPSG:32636).
- **One zone only.** Multiple protected zones could be handled with `geopandas.sjoin`.
- **Hard-coded input.** A next step would be loading zones and points from files (GeoJSON, CSV) and writing flagged results to a file.

## Project structure

```
spatial-encroachment-check/
├── src/
│   └── main.py
├── tests/
│   └── test_pipeline.py
├── requirements.txt
├── README.md
└── .gitignore
```