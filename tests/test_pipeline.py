import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import (  # noqa: E402
    DETECTED_POINTS,
    PROTECTION_ZONE_CRS,
    PROTECTION_ZONE_WKT,
    check_encroachment,
    create_detected_points,
    create_protection_zone,
)


def run(records=None):
    zone = create_protection_zone(PROTECTION_ZONE_WKT, PROTECTION_ZONE_CRS)

    if records is None:
        records = DETECTED_POINTS

    points = create_detected_points(records, PROTECTION_ZONE_CRS)
    return check_encroachment(zone, points)


def test_flags_expected_points():
    results = run()
    flagged_ids = set(results.loc[results["flagged"], "point_id"])
    assert flagged_ids == {"LOC_001", "LOC_003", "LOC_005"}


def test_outside_points_not_flagged():
    results = run()
    outside = set(results.loc[~results["flagged"], "point_id"])
    assert outside == {"LOC_002", "LOC_004"}


def test_crs_is_preserved():
    assert run().crs.to_string() == PROTECTION_ZONE_CRS


def test_point_on_boundary_is_flagged():
    edge = [{"point_id": "EDGE", "lon": 32.5800, "lat": 0.3300, "description": "on west edge"}]
    assert run(edge)["flagged"].iloc[0]


def test_input_not_modified():
    zone = create_protection_zone(PROTECTION_ZONE_WKT, PROTECTION_ZONE_CRS)
    points = create_detected_points(DETECTED_POINTS, PROTECTION_ZONE_CRS)
    check_encroachment(zone, points)
    assert "flagged" not in points.columns


def test_points_in_different_crs_are_aligned():
    zone = create_protection_zone(PROTECTION_ZONE_WKT, PROTECTION_ZONE_CRS)

    # Same points, but re-projected to Web Mercator (metres) before the check
    points_3857 = create_detected_points(DETECTED_POINTS, PROTECTION_ZONE_CRS).to_crs("EPSG:3857")

    results = check_encroachment(zone, points_3857)

    assert results.crs.to_string() == PROTECTION_ZONE_CRS
    flagged_ids = set(results.loc[results["flagged"], "point_id"])
    assert flagged_ids == {"LOC_001", "LOC_003", "LOC_005"}