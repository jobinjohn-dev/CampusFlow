import unittest

from campusflow.symbols import EventSymbol, SymbolTable, intervals_overlap


class SymbolTableTests(unittest.TestCase):
    def test_inserts_looks_up_and_cancels_event(self):
        table = SymbolTable()
        event = EventSymbol("TechFest", "2026-10-15", "10:00", "12:00")
        table.add_event(event)
        self.assertIs(table.lookup_event("TechFest"), event)
        table.cancel_event("TechFest")
        self.assertTrue(event.cancelled)

    def test_overlap_excludes_adjacent_intervals_and_other_dates(self):
        self.assertTrue(intervals_overlap(
            "2026-10-15", "10:00", "12:00",
            "2026-10-15", "11:00", "13:00",
        ))
        self.assertFalse(intervals_overlap(
            "2026-10-15", "10:00", "11:00",
            "2026-10-15", "11:00", "12:00",
        ))
        self.assertFalse(intervals_overlap(
            "2026-10-15", "10:00", "12:00",
            "2026-10-16", "10:30", "11:30",
        ))


if __name__ == "__main__":
    unittest.main()
