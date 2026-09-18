import os
import unittest
from unittest.mock import patch

from src.rank_rent.tools.ahrefs import (
    AhrefsBacklinksTool,
    AhrefsCityKeywordTool,
    AhrefsDomainTool,
    AhrefsKeywordTool,
    AhrefsRelatedKeywordsTool,
    backlink_strength,
    city_keyword_status,
    cpc_to_dollars,
    organic_strength,
    volume_int,
)


class HelperTests(unittest.TestCase):
    def test_cpc_cents_to_dollars(self):
        self.assertEqual(cpc_to_dollars(221), 2.21)
        self.assertEqual(cpc_to_dollars(0), 0.0)
        self.assertEqual(cpc_to_dollars(None), 0.0)
        self.assertEqual(cpc_to_dollars(""), 0.0)

    def test_volume_int(self):
        self.assertEqual(volume_int(110), 110)
        self.assertEqual(volume_int("40"), 40)
        self.assertEqual(volume_int(None), 0)

    def test_city_thresholds(self):
        self.assertIn("volume too low", city_keyword_status(18, 1.85))
        self.assertIn("$0 CPC", city_keyword_status(40, 0.0))
        self.assertIn("too high", city_keyword_status(55, 6.20))
        self.assertEqual(city_keyword_status(70, 3.10), "PASS ✅")

    def test_backlink_and_organic_bands(self):
        self.assertIn("VERY WEAK", backlink_strength(0))
        self.assertIn("VERY HEAVY", backlink_strength(98))
        self.assertIn("WEAK", organic_strength(0))
        self.assertIn("STRONG", organic_strength(150))


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.key_patch = patch.dict(os.environ, {"AHREFS_API_KEY": "test-placeholder-key"})
        self.key_patch.start()

    def tearDown(self):
        self.key_patch.stop()

    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            out = AhrefsKeywordTool()._run("concrete contractor")
        self.assertIn("AHREFS_API_KEY", out)

    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_related_keywords(self, mock_get):
        mock_get.return_value = (
            200,
            {
                "keywords": [
                    {"keyword": "concrete contractor", "volume": 33100, "cpc": 310, "difficulty": 12},
                    {"keyword": "stamped concrete", "volume": 49500, "cpc": 185, "difficulty": 18},
                ]
            },
        )
        out = AhrefsRelatedKeywordsTool()._run("concrete", limit=10)
        self.assertIn("concrete contractor", out)
        self.assertIn("$   3.10", out)
        path = mock_get.call_args[0][0]
        self.assertEqual(path, "/keywords-explorer/matching-terms")

    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_keyword_lookup(self, mock_get):
        mock_get.return_value = (
            200,
            {"keywords": [{"keyword": "tree service", "volume": 60500, "cpc": 221, "difficulty": 14}]},
        )
        out = AhrefsKeywordTool()._run("tree service")
        self.assertIn("Monthly Volume: 60500", out)
        self.assertIn("CPC: $2.21", out)
        self.assertIn("Keyword Difficulty: 14/100", out)

    @patch("src.rank_rent.tools.ahrefs.cache_put")
    @patch("src.rank_rent.tools.ahrefs.cache_get", return_value=None)
    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_city_keyword_pass(self, mock_get, _cache_get, mock_put):
        mock_get.return_value = (
            200,
            {"keywords": [{"keyword": "tree service Monroe LA", "volume": 110, "cpc": 221}]},
        )
        out = AhrefsCityKeywordTool()._run("tree service", "Monroe", "LA")
        self.assertIn("PASS", out)
        self.assertIn("CPC: $2.21", out)
        mock_put.assert_called_once()

    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_domain_green_flag(self, mock_get):
        mock_get.return_value = (
            200,
            {"metrics": {"org_keywords": 0, "org_traffic": 0, "paid_keywords": 0}},
        )
        out = AhrefsDomainTool()._run("https://www.example-new-site.com/about")
        self.assertIn("GREEN FLAG", out)
        self.assertIn("example-new-site.com", out)
        self.assertNotIn("Semrush", out)

    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_backlinks_live_count(self, mock_get):
        mock_get.return_value = (
            200,
            {"metrics": {"live": 8, "live_refdomains": 3, "all_time": 20}},
        )
        out = AhrefsBacklinksTool()._run("competitor.com")
        self.assertIn("Total Backlinks: 8", out)
        self.assertIn("VERY WEAK", out)
        path = mock_get.call_args[0][0]
        self.assertEqual(path, "/site-explorer/backlinks-stats")

    @patch("src.rank_rent.tools.ahrefs.ahrefs_get")
    def test_auth_error_is_not_green_flag(self, mock_get):
        mock_get.return_value = (401, {"error": "unauthorized"})
        out = AhrefsDomainTool()._run("competitor.com")
        self.assertIn("auth failed", out)
        self.assertNotIn("GREEN FLAG", out)


if __name__ == "__main__":
    unittest.main()
