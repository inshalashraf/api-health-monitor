"""Tests for repeated monitoring cycles."""
import unittest
from unittest.mock import call

from api_health_monitor.scheduler import run_periodically


class SchedulerTests(unittest.TestCase):
    def test_runs_requested_number_of_cycles(self):
        outcomes = iter([0, 0, 0])
        sleeps = []
        count = run_periodically(lambda: next(outcomes), interval_seconds=10,
                                 max_runs=3, sleep=sleeps.append)
        self.assertEqual(count, 0)
        self.assertEqual(sleeps, [10, 10])

    def test_preserves_failure_if_later_cycle_is_healthy(self):
        outcomes = iter([1, 0])
        result = run_periodically(lambda: next(outcomes), interval_seconds=1,
                                  max_runs=2, sleep=lambda _: None)
        self.assertEqual(result, 1)

    def test_configuration_error_takes_precedence(self):
        outcomes = iter([1, 2, 0])
        result = run_periodically(lambda: next(outcomes), interval_seconds=1,
                                  max_runs=3, sleep=lambda _: None)
        self.assertEqual(result, 2)

    def test_rejects_infinite_schedule_without_interval(self):
        with self.assertRaises(ValueError):
            run_periodically(lambda: 0, interval_seconds=0)

    def test_rejects_zero_max_runs(self):
        with self.assertRaises(ValueError):
            run_periodically(lambda: 0, interval_seconds=1, max_runs=0)


if __name__ == "__main__":
    unittest.main()
