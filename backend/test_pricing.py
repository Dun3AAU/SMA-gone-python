import random
import unittest

from backend.pricing import calculate_next_prices


class CalculateNextPricesTests(unittest.TestCase):
    def test_no_sales_leave_prices_unchanged(self):
        prices = {"ale": 44.0, "lager": 62.0}

        result = calculate_next_prices(prices, {}, 60)

        self.assertEqual(result, prices)

    def test_relative_sales_raise_popular_price_and_lower_other_price(self):
        result = calculate_next_prices(
            {"popular": 50.0, "quiet": 50.0},
            {"popular": 20, "quiet": 0},
            60,
            amplification=100,
        )

        self.assertGreater(result["popular"], 50.0)
        self.assertLess(result["quiet"], 50.0)

    def test_noise_is_reproducible_with_seeded_random_source(self):
        prices = {"ale": 44.0, "lager": 62.0}
        counts = {"ale": 3, "lager": 2}

        first = calculate_next_prices(
            prices, counts, 60, noise_percent=2, rng=random.Random(42)
        )
        second = calculate_next_prices(
            prices, counts, 60, noise_percent=2, rng=random.Random(42)
        )

        self.assertEqual(first, second)

    def test_invalid_negative_timing_or_amplification_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_next_prices({"ale": 44.0}, {}, -1)
        with self.assertRaises(ValueError):
            calculate_next_prices({"ale": 44.0}, {}, 60, amplification=-1)


if __name__ == "__main__":
    unittest.main()