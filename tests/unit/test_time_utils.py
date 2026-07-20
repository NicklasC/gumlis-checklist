import unittest
from types import SimpleNamespace

from src.core.time_utils import history_date, parse_timestamp, timestamp_as_utc


class TimeUtilsTests(unittest.TestCase):
    def test_completion_offset_preserves_swedish_calendar_date(self):
        value = SimpleNamespace(
            completed_at="2026-07-20T00:30:00+02:00",
            created_at="2026-07-19T22:30:00Z",
        )
        self.assertEqual(history_date(value).isoformat(), "2026-07-20")

    def test_legacy_z_timestamp_is_parsed_as_utc(self):
        parsed = parse_timestamp("2026-07-19T22:30:00Z")
        self.assertEqual(parsed.utcoffset().total_seconds(), 0)

    def test_timestamp_can_be_normalized_for_retention(self):
        parsed = timestamp_as_utc("2026-07-20T00:30:00+02:00")
        self.assertEqual(parsed.isoformat(), "2026-07-19T22:30:00+00:00")
