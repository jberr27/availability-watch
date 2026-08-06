import unittest

import tracker


class TrackerTests(unittest.TestCase):
    def test_health_check_does_not_depend_on_dune_listing(self):
        page = tracker.normalize(
            """
            AMC Lincoln Square 13
            Movie Times Calendar
            Avengers: Doomsday (2026)
            Nearby theaters
            """
        )

        self.assertTrue(tracker.page_is_healthy(page, {}))

    def test_missing_dune_section_is_not_a_target(self):
        page = tracker.normalize(
            """
            AMC Lincoln Square 13
            Movie Times Calendar
            Avengers: Doomsday (2026)
            7:20a
            Nearby theaters
            """
        )
        item = {
            "section_start": "Dune: Part Three (2026)",
            "section_end": "Nearby theaters",
            "baseline_times": ["7:00p", "11:00p"],
        }

        self.assertEqual(tracker.new_showtimes(page, item), [])

    def test_only_incremental_dune_showtimes_trigger(self):
        page = tracker.normalize(
            """
            Dune: Part Three (2026)
            IMAX 70MM
            10:00a
            3:00p
            7:00p
            11:00p
            Nearby theaters
            """
        )
        item = {
            "section_start": "Dune: Part Three (2026)",
            "section_end": "Nearby theaters",
            "baseline_times": ["7:00p", "11:00p"],
        }

        self.assertEqual(tracker.new_showtimes(page, item), ["10:00a", "3:00p"])


if __name__ == "__main__":
    unittest.main()
