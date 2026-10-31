"""CLI argument validation tests."""
import unittest
from unittest.mock import patch

from api_health_monitor.cli import main


class CliValidationTests(unittest.TestCase):
    def test_non_finite_timing_options_are_rejected(self):
        for option in ("--timeout", "--retry-delay", "--interval"):
            for value in ("nan", "inf", "-inf"):
                with self.subTest(option=option, value=value):
                    with patch("sys.argv", ["api-health-monitor", option, value]), \
                         self.assertRaises(SystemExit) as raised:
                        main()
                    self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
