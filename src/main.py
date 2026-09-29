import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point

PROTECTION_ZONE_WKT = (
    "POLYGON ((32.5800 0.3200, "
    "32.6000 0.3200, "
    "32.6000 0.3400, "
    "32.5800 0.3400, "
    "32.5800 0.3200))"
)

PROTECTION_ZONE_CRS = "EPSG:4326"

DETECTED_POINTS = [
    {"point_id": "LOC_001", "lon": 32.5900, "lat": 0.3300, "description": "Foundation excavation observed"},
    {"point_id": "LOC_002", "lon": 32.5750, "lat": 0.3250, "description": "Commercial warehouse structure"},
    {"point_id": "LOC_003", "lon": 32.5950, "lat": 0.3350, "description": "Active bricklaying site"},
    {"point_id": "LOC_004", "lon": 32.6100, "lat": 0.3500, "description": "Residential fence wall completed"},
    {"point_id": "LOC_005", "lon": 32.5850, "lat": 0.3220, "description": "Grading of marshland vegetation"},
]


def create_protection_zone(zone_wkt, crs):
    geometry = wkt.loads(zone_wkt)
    return gpd.GeoDataFrame({"name": ["protected_zone"]}, geometry=[geometry], crs=crs)


def create_detected_points(records, crs):
    return gpd.GeoDataFrame(
        records,
        geometry=[Point(r["lon"], r["lat"]) for r in records],
        crs=crs,
    )


def check_encroachment(protection_zone, detected_points):
    # Make sure both layers use the same coordinate system before comparing
    if detected_points.crs != protection_zone.crs:
        detected_points = detected_points.to_crs(protection_zone.crs)

    protected_geometry = protection_zone.geometry.iloc[0]
    detected_points = detected_points.copy()

    # covered_by = inside OR on the boundary line (within() excludes the edge)
    detected_points["flagged"] = detected_points.geometry.covered_by(protected_geometry)
    return detected_points


def main():
    protection_zone = create_protection_zone(PROTECTION_ZONE_WKT, PROTECTION_ZONE_CRS)
    detected_points = create_detected_points(DETECTED_POINTS, PROTECTION_ZONE_CRS)
    results = check_encroachment(protection_zone, detected_points)

    flagged = results[results["flagged"]]

    print(f"Flagged for review: {len(flagged)} of {len(results)} detected points")
    print(flagged[["point_id", "description", "lon", "lat"]].to_string(index=False))


if __name__ == "__main__":
    main()