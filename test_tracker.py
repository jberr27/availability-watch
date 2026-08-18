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
