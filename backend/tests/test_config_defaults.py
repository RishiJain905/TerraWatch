import importlib
import os
import unittest
from unittest.mock import patch

import app.config as config_module


def reload_config_without_dotenv():
    with patch("dotenv.load_dotenv", return_value=False):
        return importlib.reload(config_module)


class ConfigDefaultsTests(unittest.TestCase):
    def test_adsblol_defaults_prefill_known_good_public_point_region(self):
        keys = [
            "ADSBLOL_API_URL",
            "ADSBLOL_BASE_URL",
            "ADSBLOL_LAT",
            "ADSBLOL_LON",
            "ADSBLOL_RADIUS_NM",
            "ADSBLOL_REFRESH_SECONDS",
            "ADSB_REFRESH_SECONDS",
            "AVIATIONSTACK_ACCESS_KEY",
            "AVIATIONSTACK_BASE_URL",
            "AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS",
            "AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS",
        ]
        original = {key: os.environ.get(key) for key in keys}

        try:
            for key in keys:
                os.environ.pop(key, None)

            reloaded = reload_config_without_dotenv()

            self.assertEqual(reloaded.settings.ADSBLOL_API_URL, "")
            self.assertEqual(reloaded.settings.ADSBLOL_BASE_URL, "https://api.adsb.lol")
            self.assertEqual(reloaded.settings.ADSBLOL_LAT, 37.6188056)
            self.assertEqual(reloaded.settings.ADSBLOL_LON, -122.3754167)
            self.assertEqual(reloaded.settings.ADSBLOL_RADIUS_NM, 250)
            self.assertEqual(reloaded.settings.ADSBLOL_REFRESH_SECONDS, 120)
            self.assertEqual(reloaded.settings.ADSB_REFRESH_SECONDS, 120)
            self.assertEqual(reloaded.settings.AVIATIONSTACK_ACCESS_KEY, "")
            self.assertEqual(reloaded.settings.AVIATIONSTACK_BASE_URL, "https://api.aviationstack.com/v1")
            self.assertEqual(reloaded.settings.AVIATIONSTACK_ROUTE_CACHE_TTL_SECONDS, 600)
            self.assertEqual(reloaded.settings.AVIATIONSTACK_AIRPORT_CACHE_TTL_SECONDS, 86400)
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(config_module)

    def test_stale_threshold_defaults_match_spec(self):
        keys = [
            "STALE_PLANE_SECONDS",
            "STALE_SHIP_SECONDS",
            "STALE_EVENT_SECONDS",
            "STALE_CONFLICT_SECONDS",
        ]
        original = {key: os.environ.get(key) for key in keys}

        try:
            for key in keys:
                os.environ.pop(key, None)

            reloaded = reload_config_without_dotenv()

            self.assertEqual(reloaded.settings.STALE_PLANE_SECONDS, 300)
            self.assertEqual(reloaded.settings.STALE_SHIP_SECONDS, 600)
            self.assertEqual(reloaded.settings.STALE_EVENT_SECONDS, 3600)
            self.assertEqual(reloaded.settings.STALE_CONFLICT_SECONDS, 3600)
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(config_module)

    def test_stale_thresholds_override_from_env(self):
        keys = [
            "STALE_PLANE_SECONDS",
            "STALE_SHIP_SECONDS",
            "STALE_EVENT_SECONDS",
            "STALE_CONFLICT_SECONDS",
        ]
        original = {key: os.environ.get(key) for key in keys}

        try:
            os.environ["STALE_PLANE_SECONDS"] = "60"
            os.environ["STALE_SHIP_SECONDS"] = "120"
            os.environ["STALE_EVENT_SECONDS"] = "1800"
            os.environ["STALE_CONFLICT_SECONDS"] = "7200"

            reloaded = reload_config_without_dotenv()

            self.assertEqual(reloaded.settings.STALE_PLANE_SECONDS, 60)
            self.assertEqual(reloaded.settings.STALE_SHIP_SECONDS, 120)
            self.assertEqual(reloaded.settings.STALE_EVENT_SECONDS, 1800)
            self.assertEqual(reloaded.settings.STALE_CONFLICT_SECONDS, 7200)
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(config_module)


if __name__ == "__main__":
    unittest.main()
