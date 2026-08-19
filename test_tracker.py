import unittest

import tracker


class TrackerTests(unittest.TestCase):
    def test_strategic_targets_cover_only_high_value_dates(self):
        config = {
            "targets": [
                {
                    "label": "Opening day",
                    "target_date": "2026-12-18",
                    "url": "https://www.fandango.com/theater-page?format=all&date=2026-12-18",
                    "baseline_times": ["7:00p", "11:00p"],
                    "section_start": "Dune: Part Three (2026)",
                }
            ]
        }

        targets = tracker.build_strategic_targets(config)

        self.assertEqual(
            [item["target_date"] for item in targets],
            ["2026-12-18", "2026-12-27", "2027-01-03", "2027-01-09"],
        )
        self.assertEqual(targets[0]["baseline_times"], ["7:00p", "11:00p"])
        self.assertEqual(targets[1]["baseline_times"], [])
        self.assertIn("date=2027-01-09", targets[-1]["url"])
        self.assertIn("date=2027-01-09", targets[-1]["action_url"])

    def test_alert_header_contains_detected_date_range(self):
        detected = [
            ({"label": "December 27, 2026", "target_date": "2026-12-27", "action_url": "https://example.com/dec27"}, ["10:00a"]),
            ({"label": "January 9, 2027", "target_date": "2027-01-09", "action_url": "https://example.com/jan9"}, ["3:00p"]),
        ]

        message = tracker.build_alert_message(
            {"alert_title": "Dune tickets available", "mention": "@everyone"},
            detected,
            "2026-08-18 12:00:00 UTC",
        )

        self.assertIn(
            "**Dune tickets available — December 27, 2026–January 9, 2027**",
            message,
        )
        self.assertIn("December 27, 2026: 10:00a", message)
        self.assertIn("January 9, 2027: https://example.com/jan9", message)

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

    def test_coming_soon_times_without_ticket_links_do_not_trigger(self):
        item = {"baseline_times": ["7:00p", "11:00p"]}
        links = [
            {
                "text": "10:00a",
                "href": "https://www.fandango.com/dune-part-three-2026-244800/movie-overview",
            },
            {"text": "3:00p", "href": ""},
        ]

        self.assertEqual(tracker.new_purchasable_showtimes(links, item), [])

    def test_only_new_showtimes_with_purchase_links_trigger(self):
        item = {"baseline_times": ["7:00p", "11:00p"]}
        links = [
            {
                "text": "7:00p",
                "href": "https://tickets.fandango.com/transaction/ticketing/mobile/jump.aspx?sdate=2026-12-18%2B19%3A00&showtimehashcode=baseline",
            },
            {
                "aria_label": "Buy tickets for 10:00 AM showtime",
                "href": "https://tickets.fandango.com/transaction/ticketing/mobile/jump.aspx?sdate=2026-12-18%2B10%3A00&showtimehashcode=new",
            },
            {
                "text": "3:00p",
                "href": "https://www.fandango.com/dune-part-three-2026-244800/movie-overview",
            },
        ]

        self.assertEqual(
            tracker.new_purchasable_showtimes(links, item),
            ["10:00a"],
        )


if __name__ == "__main__":
    unittest.main()
