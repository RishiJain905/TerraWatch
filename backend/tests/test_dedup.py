import unittest
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.dedup import (
    deduplicate_planes,
    deduplicate_ships,
    filter_stale_planes_adsblol,
    filter_stale_planes_open_sky,
    filter_stale_ships_ais_friends,
    filter_stale_ships_digitraffic,
)


class DedupTestCase(unittest.TestCase):
    def iso_now(self, offset_seconds: int = 0) -> str:
        return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()

    def make_plane(self, plane_id: str, timestamp: Any, **overrides):
        plane = {
            "id": plane_id,
            "lat": 60.0,
            "lon": 24.0,
            "alt": 30000,
            "heading": 90.0,
            "callsign": f"CS{plane_id}",
            "squawk": "7000",
            "speed": 450.0,
            "timestamp": timestamp,
        }
        plane.update(overrides)
        return plane

    def make_ship(self, ship_id: str, timestamp: Any, **overrides):
        ship = {
            "id": ship_id,
            "lat": 60.0,
            "lon": 24.0,
            "heading": 180.0,
            "speed": 12.0,
            "name": f"SHIP-{ship_id}",
            "destination": "FI HEL",
            "ship_type": "cargo",
            "timestamp": timestamp,
        }
        ship.update(overrides)
        return ship

    def plane_by_id(self, planes):
        return {plane["id"]: plane for plane in planes}

    def ship_by_id(self, ships):
        return {ship["id"]: ship for ship in ships}


class TestPlaneDeduplication(DedupTestCase):
    def test_no_plane_overlap(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-30)),
            self.make_plane("def456", self.iso_now(-25)),
        ]
        adsblol = [
            self.make_plane("ghi789", self.iso_now(-20)),
            self.make_plane("jkl012", self.iso_now(-15)),
        ]

        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual([plane["id"] for plane in merged], ["abc123", "def456", "ghi789", "jkl012"])

    def test_full_plane_overlap_same_timestamp_open_sky_wins(self):
        timestamp = self.iso_now(-30)
        open_sky = [
            self.make_plane("abc123", timestamp, callsign="OPEN1", heading=10.0),
            self.make_plane("def456", timestamp, callsign="OPEN2", heading=20.0),
        ]
        adsblol = [
            self.make_plane("ABC123", timestamp, callsign="ADSB1", heading=110.0),
            self.make_plane("DEF456", timestamp, callsign="ADSB2", heading=120.0),
        ]

        merged = self.plane_by_id(deduplicate_planes(open_sky, adsblol))

        self.assertEqual(set(merged), {"abc123", "def456"})
        self.assertEqual(merged["abc123"]["callsign"], "OPEN1")
        self.assertEqual(merged["abc123"]["heading"], 10.0)
        self.assertEqual(merged["abc123"]["sources"], ["open_sky", "adsblol"])
        self.assertEqual(merged["def456"]["callsign"], "OPEN2")
        self.assertEqual(merged["def456"]["heading"], 20.0)
        self.assertEqual(merged["def456"]["sources"], ["open_sky", "adsblol"])

    def test_full_plane_overlap_different_timestamps_newer_wins(self):
        open_sky = [self.make_plane("abc123", self.iso_now(-120), callsign="OLDER")]
        adsblol = [self.make_plane("ABC123", self.iso_now(-30), callsign="NEWER", heading=275.0)]

        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "abc123")
        self.assertEqual(merged[0]["callsign"], "NEWER")
        self.assertEqual(merged[0]["heading"], 275.0)
        self.assertEqual(merged[0]["sources"], ["open_sky", "adsblol"])

    def test_partial_plane_overlap(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-50), callsign="A"),
            self.make_plane("def456", self.iso_now(-100), callsign="OLD-B"),
        ]
        adsblol = [
            self.make_plane("DEF456", self.iso_now(-10), callsign="NEW-B"),
            self.make_plane("ghi789", self.iso_now(-15), callsign="C"),
        ]

        merged = self.plane_by_id(deduplicate_planes(open_sky, adsblol))

        self.assertEqual(set(merged), {"abc123", "def456", "ghi789"})
        self.assertEqual(merged["abc123"]["callsign"], "A")
        self.assertEqual(merged["def456"]["callsign"], "NEW-B")
        self.assertEqual(merged["ghi789"]["callsign"], "C")

    def test_stale_open_sky_filtered(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-60)),
            self.make_plane("def456", self.iso_now(-301)),
        ]
        adsblol = [self.make_plane("ghi789", self.iso_now(-30))]

        direct_filtered = filter_stale_planes_open_sky(open_sky)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual([plane["id"] for plane in direct_filtered], ["abc123"])
        self.assertEqual([plane["id"] for plane in merged], ["abc123", "ghi789"])

    def test_stale_adsblol_filtered(self):
        open_sky = [self.make_plane("abc123", self.iso_now(-60))]
        adsblol = [self.make_plane("DEF456", self.iso_now(-301))]

        direct_filtered = filter_stale_planes_adsblol(adsblol)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual(direct_filtered, [])
        self.assertEqual([plane["id"] for plane in merged], ["abc123"])

    def test_adsblol_missing_or_unparseable_timestamp_filtered_before_merge(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-60), callsign="OPEN-A"),
            self.make_plane("def456", self.iso_now(-55), callsign="OPEN-B"),
        ]
        adsblol = [
            self.make_plane("ABC123", None, callsign="DROP-MISSING"),
            self.make_plane("DEF456", "not-a-real-timestamp", callsign="DROP-BAD"),
        ]

        direct_filtered = filter_stale_planes_adsblol(adsblol)
        merged = self.plane_by_id(deduplicate_planes(open_sky, adsblol))

        self.assertEqual(direct_filtered, [])
        self.assertEqual(set(merged), {"abc123", "def456"})
        self.assertEqual(merged["abc123"]["callsign"], "OPEN-A")
        self.assertEqual(merged["abc123"]["sources"], ["open_sky"])
        self.assertEqual(merged["def456"]["callsign"], "OPEN-B")
        self.assertEqual(merged["def456"]["sources"], ["open_sky"])

    def test_adsblol_time_position_alias_is_used_for_filtering_and_conflict_resolution(self):
        alias_timestamp = self.iso_now(-15)
        open_sky = [self.make_plane("abc123", self.iso_now(-120), callsign="OPEN", heading=10.0)]
        adsblol = [
            self.make_plane(
                "ABC123",
                None,
                time_position=alias_timestamp,
                callsign="ADSB-ALIAS",
                heading=210.0,
            )
        ]

        direct_filtered = filter_stale_planes_adsblol(adsblol)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual(len(direct_filtered), 1)
        self.assertEqual(direct_filtered[0]["id"], "abc123")
        self.assertEqual(direct_filtered[0]["timestamp"], alias_timestamp)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "abc123")
        self.assertEqual(merged[0]["callsign"], "ADSB-ALIAS")
        self.assertEqual(merged[0]["heading"], 210.0)
        self.assertEqual(merged[0]["timestamp"], alias_timestamp)
        self.assertEqual(merged[0]["sources"], ["open_sky", "adsblol"])

    def test_adsblol_valid_time_position_alias_overrides_invalid_timestamp(self):
        alias_timestamp = self.iso_now(-10)
        open_sky = [self.make_plane("abc123", self.iso_now(-120), callsign="OPEN", heading=10.0)]
        adsblol = [
            self.make_plane(
                "ABC123",
                "not-a-real-timestamp",
                time_position=alias_timestamp,
                callsign="ADSB-ALIAS-VALID",
                heading=220.0,
            )
        ]

        direct_filtered = filter_stale_planes_adsblol(adsblol)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual(len(direct_filtered), 1)
        self.assertEqual(direct_filtered[0]["timestamp"], alias_timestamp)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["callsign"], "ADSB-ALIAS-VALID")
        self.assertEqual(merged[0]["heading"], 220.0)
        self.assertEqual(merged[0]["timestamp"], alias_timestamp)

    def test_empty_open_sky(self):
        adsblol = [
            self.make_plane("ABC123", self.iso_now(-30)),
            self.make_plane("DEF456", self.iso_now(-25)),
        ]

        merged = deduplicate_planes([], adsblol)

        self.assertEqual([plane["id"] for plane in merged], ["abc123", "def456"])

    def test_empty_adsblol(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-30)),
            self.make_plane("def456", self.iso_now(-25)),
        ]

        merged = deduplicate_planes(open_sky, [])

        self.assertEqual([plane["id"] for plane in merged], ["abc123", "def456"])

    def test_timestamped_plane_wins_over_missing_timestamp_cross_source(self):
        open_sky = [self.make_plane("abc123", None, callsign="OPEN", heading=10.0)]
        adsblol = [self.make_plane("ABC123", self.iso_now(-30), callsign="ADSB", heading=110.0)]

        direct_filtered = filter_stale_planes_open_sky(open_sky)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual([plane["id"] for plane in direct_filtered], ["abc123"])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "abc123")
        self.assertEqual(merged[0]["callsign"], "ADSB")
        self.assertEqual(merged[0]["heading"], 110.0)
        self.assertEqual(merged[0]["timestamp"], adsblol[0]["timestamp"])
        self.assertEqual(merged[0]["sources"], ["open_sky", "adsblol"])

    def test_same_source_plane_duplicates_prefer_newer_timestamp(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-120), callsign="OLDER", heading=15.0),
            self.make_plane("ABC123", self.iso_now(-15), callsign="NEWER", heading=215.0),
        ]

        merged = deduplicate_planes(open_sky, [])

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "abc123")
        self.assertEqual(merged[0]["callsign"], "NEWER")
        self.assertEqual(merged[0]["heading"], 215.0)

    def test_future_plane_timestamp_filtered(self):
        open_sky = [self.make_plane("abc123", self.iso_now(3600))]
        adsblol = [self.make_plane("DEF456", self.iso_now(-30))]

        direct_filtered = filter_stale_planes_open_sky(open_sky)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual(direct_filtered, [])
        self.assertEqual([plane["id"] for plane in merged], ["def456"])

    def test_malformed_plane_records_are_skipped(self):
        open_sky = [
            self.make_plane("abc123", self.iso_now(-30), callsign="VALID"),
            self.make_plane("bad123", self.iso_now(-25), lat="not-a-float", callsign="BROKEN"),
        ]
        adsblol = [self.make_plane("DEF456", self.iso_now(-20), callsign="ADSB")]

        direct_filtered = filter_stale_planes_open_sky(open_sky)
        merged = deduplicate_planes(open_sky, adsblol)

        self.assertEqual([plane["id"] for plane in direct_filtered], ["abc123"])
        self.assertEqual([plane["id"] for plane in merged], ["abc123", "def456"])


class TestShipDeduplication(DedupTestCase):
    def test_no_ship_overlap(self):
        digitraffic = [
            self.make_ship("111000111", self.iso_now(-60)),
            self.make_ship("222000222", self.iso_now(-50)),
        ]
        ais_friends = [
            self.make_ship("333000333", self.iso_now(-40)),
            self.make_ship("444000444", self.iso_now(-30)),
        ]

        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(
            [ship["id"] for ship in merged],
            ["111000111", "222000222", "333000333", "444000444"],
        )

    def test_full_ship_overlap_same_timestamp_digitraffic_wins(self):
        timestamp = self.iso_now(-60)
        digitraffic = [
            self.make_ship("111000111", timestamp, name="DT-A", destination="FI TKU", heading=15.0),
            self.make_ship("222000222", timestamp, name="DT-B", destination="FI HEL", heading=25.0),
        ]
        ais_friends = [
            self.make_ship("111000111", timestamp, name="AF-A", destination="SE STO", heading=115.0),
            self.make_ship("222000222", timestamp, name="AF-B", destination="EE TLL", heading=125.0),
        ]

        merged = self.ship_by_id(deduplicate_ships(digitraffic, ais_friends))

        self.assertEqual(set(merged), {"111000111", "222000222"})
        self.assertEqual(merged["111000111"]["name"], "DT-A")
        self.assertEqual(merged["111000111"]["destination"], "FI TKU")
        self.assertEqual(merged["111000111"]["heading"], 15.0)
        self.assertEqual(merged["111000111"]["sources"], ["digitraffic", "aisstream"])
        self.assertEqual(merged["222000222"]["name"], "DT-B")
        self.assertEqual(merged["222000222"]["destination"], "FI HEL")
        self.assertEqual(merged["222000222"]["heading"], 25.0)
        self.assertEqual(merged["222000222"]["sources"], ["digitraffic", "aisstream"])

    def test_full_ship_overlap_different_timestamps_newer_wins(self):
        digitraffic = [self.make_ship("111000111", self.iso_now(-180), name="OLDER", heading=10.0)]
        ais_friends = [
            self.make_ship(
                "111000111",
                self.iso_now(-30),
                name="NEWER",
                heading=222.0,
                destination="EE TLL",
            )
        ]

        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "111000111")
        self.assertEqual(merged[0]["name"], "NEWER")
        self.assertEqual(merged[0]["heading"], 222.0)
        self.assertEqual(merged[0]["destination"], "EE TLL")
        self.assertEqual(merged[0]["sources"], ["digitraffic", "aisstream"])

    def test_partial_ship_overlap(self):
        digitraffic = [
            self.make_ship("111000111", self.iso_now(-50), name="A"),
            self.make_ship("222000222", self.iso_now(-150), name="OLD-B"),
        ]
        ais_friends = [
            self.make_ship("222000222", self.iso_now(-10), name="NEW-B"),
            self.make_ship("333000333", self.iso_now(-20), name="C"),
        ]

        merged = self.ship_by_id(deduplicate_ships(digitraffic, ais_friends))

        self.assertEqual(set(merged), {"111000111", "222000222", "333000333"})
        self.assertEqual(merged["111000111"]["name"], "A")
        self.assertEqual(merged["222000222"]["name"], "NEW-B")
        self.assertEqual(merged["333000333"]["name"], "C")

    def test_stale_ships_filtered_and_unparseable_timestamps_are_kept(self):
        digitraffic = [
            self.make_ship("111000111", self.iso_now(-60)),
            self.make_ship("222000222", self.iso_now(-601)),
        ]
        ais_friends = [
            self.make_ship("333000333", self.iso_now(-30)),
            self.make_ship("444000444", "not-a-real-timestamp"),
        ]

        direct_digitraffic = filter_stale_ships_digitraffic(digitraffic)
        direct_ais_friends = filter_stale_ships_ais_friends(ais_friends)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual([ship["id"] for ship in direct_digitraffic], ["111000111"])
        self.assertEqual([ship["id"] for ship in direct_ais_friends], ["333000333", "444000444"])
        self.assertEqual([ship["id"] for ship in merged], ["111000111", "333000333", "444000444"])

    def test_ship_attribute_merge(self):
        timestamp = self.iso_now(-45)
        digitraffic = [
            self.make_ship(
                "111000111",
                timestamp,
                name="",
                destination="",
                ship_type="",
                heading=40.0,
                speed=9.5,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                timestamp,
                name="MERGED NAME",
                destination="FI TKU",
                ship_type="tanker",
                heading=250.0,
                speed=18.0,
            )
        ]

        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(merged), 1)
        ship = merged[0]
        self.assertEqual(ship["id"], "111000111")
        self.assertEqual(ship["name"], "MERGED NAME")
        self.assertEqual(ship["destination"], "FI TKU")
        self.assertEqual(ship["ship_type"], "tanker")
        self.assertEqual(ship["heading"], 40.0)
        self.assertEqual(ship["speed"], 9.5)

    def test_ship_type_other_is_not_treated_as_missing(self):
        timestamp = self.iso_now(-45)
        digitraffic = [
            self.make_ship(
                "111000111",
                timestamp,
                name="",
                destination="",
                ship_type="other",
                heading=40.0,
                speed=9.5,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                timestamp,
                name="MERGED NAME",
                destination="FI TKU",
                ship_type="tanker",
                heading=250.0,
                speed=18.0,
            )
        ]

        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(merged), 1)
        ship = merged[0]
        self.assertEqual(ship["id"], "111000111")
        self.assertEqual(ship["name"], "MERGED NAME")
        self.assertEqual(ship["destination"], "FI TKU")
        self.assertEqual(ship["ship_type"], "other")
        self.assertEqual(ship["heading"], 40.0)
        self.assertEqual(ship["speed"], 9.5)

    def test_timestamped_ship_wins_over_unparseable_timestamp_cross_source(self):
        digitraffic = [
            self.make_ship(
                "111000111",
                "not-a-real-timestamp",
                name="DT",
                destination="FI TKU",
                heading=15.0,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                self.iso_now(-30),
                name="AF",
                destination="EE TLL",
                heading=115.0,
            )
        ]

        direct_filtered = filter_stale_ships_digitraffic(digitraffic)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual([ship["id"] for ship in direct_filtered], ["111000111"])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "111000111")
        self.assertEqual(merged[0]["name"], "AF")
        self.assertEqual(merged[0]["destination"], "EE TLL")
        self.assertEqual(merged[0]["heading"], 115.0)
        self.assertEqual(merged[0]["timestamp"], ais_friends[0]["timestamp"])
        self.assertEqual(merged[0]["sources"], ["digitraffic", "aisstream"])

    def test_ship_last_position_alias_is_used_for_filtering_and_conflict_resolution(self):
        alias_timestamp = self.iso_now(-20)
        digitraffic = [
            self.make_ship(
                "111000111",
                None,
                last_position=alias_timestamp,
                name="DT-ALIAS",
                destination="FI TKU",
                heading=25.0,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                self.iso_now(-180),
                name="AF-OLDER",
                destination="EE TLL",
                heading=125.0,
            )
        ]

        direct_filtered = filter_stale_ships_digitraffic(digitraffic)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(direct_filtered), 1)
        self.assertEqual(direct_filtered[0]["id"], "111000111")
        self.assertEqual(direct_filtered[0]["timestamp"], alias_timestamp)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "111000111")
        self.assertEqual(merged[0]["name"], "DT-ALIAS")
        self.assertEqual(merged[0]["destination"], "FI TKU")
        self.assertEqual(merged[0]["heading"], 25.0)
        self.assertEqual(merged[0]["timestamp"], alias_timestamp)
        self.assertEqual(merged[0]["sources"], ["digitraffic", "aisstream"])

    def test_last_position_alias_overrides_invalid_ship_timestamp(self):
        alias_timestamp = self.iso_now(-12)
        digitraffic = [
            self.make_ship(
                "111000111",
                "not-a-real-timestamp",
                last_position=alias_timestamp,
                name="DT-ALIAS-VALID",
                destination="FI TKU",
                heading=35.0,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                self.iso_now(-180),
                name="AF-OLDER",
                destination="EE TLL",
                heading=135.0,
            )
        ]

        direct_filtered = filter_stale_ships_digitraffic(digitraffic)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(direct_filtered), 1)
        self.assertEqual(direct_filtered[0]["timestamp"], alias_timestamp)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["name"], "DT-ALIAS-VALID")
        self.assertEqual(merged[0]["destination"], "FI TKU")
        self.assertEqual(merged[0]["heading"], 35.0)
        self.assertEqual(merged[0]["timestamp"], alias_timestamp)
        self.assertEqual(merged[0]["sources"], ["digitraffic", "aisstream"])

    def test_missing_ship_timestamp_digitraffic_priority_is_reachable(self):
        digitraffic = [
            self.make_ship(
                "111000111",
                None,
                name="DT",
                destination="FI TKU",
                heading=15.0,
            )
        ]
        ais_friends = [
            self.make_ship(
                "111000111",
                None,
                name="AF",
                destination="EE TLL",
                heading=115.0,
            )
        ]

        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "111000111")
        self.assertEqual(merged[0]["name"], "DT")
        self.assertEqual(merged[0]["destination"], "FI TKU")
        self.assertEqual(merged[0]["heading"], 15.0)
        self.assertIsNone(merged[0]["timestamp"])
        self.assertEqual(merged[0]["sources"], ["digitraffic", "aisstream"])

    def test_same_source_ship_duplicates_prefer_newer_timestamp(self):
        digitraffic = [
            self.make_ship("111000111", self.iso_now(-180), name="OLDER", heading=10.0),
            self.make_ship("111000111", self.iso_now(-20), name="NEWER", heading=210.0),
        ]

        merged = deduplicate_ships(digitraffic, [])

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "111000111")
        self.assertEqual(merged[0]["name"], "NEWER")
        self.assertEqual(merged[0]["heading"], 210.0)

    def test_future_ship_timestamp_filtered(self):
        digitraffic = [self.make_ship("111000111", self.iso_now(3600))]
        ais_friends = [self.make_ship("333000333", self.iso_now(-30))]

        direct_filtered = filter_stale_ships_digitraffic(digitraffic)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual(direct_filtered, [])
        self.assertEqual([ship["id"] for ship in merged], ["333000333"])

    def test_malformed_ship_records_are_skipped(self):
        digitraffic = [
            self.make_ship("111000111", self.iso_now(-60), name="VALID"),
            self.make_ship("222000222", self.iso_now(-55), lat="not-a-float", name="BROKEN"),
        ]
        ais_friends = [self.make_ship("333000333", self.iso_now(-30), name="AF")]

        direct_filtered = filter_stale_ships_digitraffic(digitraffic)
        merged = deduplicate_ships(digitraffic, ais_friends)

        self.assertEqual([ship["id"] for ship in direct_filtered], ["111000111"])
        self.assertEqual([ship["id"] for ship in merged], ["111000111", "333000333"])


if __name__ == "__main__":
    unittest.main()
