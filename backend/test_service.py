import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.service import MarketService


class MarketServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = MarketService(Path(self.temp_dir.name) / "market.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sale_uses_server_price_and_retry_is_idempotent(self):
        state = self.service.state()
        code = next(iter(state["default_prices"]))

        accepted = self.service.record_sale(code, "retry-key")
        retry = self.service.record_sale(code, "retry-key")

        self.assertEqual(accepted["price"], state["current_prices"][code])
        self.assertFalse(accepted["duplicate"])
        self.assertTrue(retry["duplicate"])
        self.assertEqual(accepted["id"], retry["id"])

    def test_concurrent_sales_are_all_recorded_once(self):
        code = next(iter(self.service.state()["default_prices"]))

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(
                executor.map(
                    lambda index: self.service.record_sale(code, f"click-{index}"),
                    range(24),
                )
            )

        self.assertEqual(len({sale["id"] for sale in results}), 24)
        self.assertEqual(self.service.state()["active_sales"][code], 24)

    def test_elapsed_interval_writes_a_new_price_snapshot(self):
        connection = sqlite3.connect(self.service.database_path)
        current_start = time.time() - 61
        connection.execute(
            "UPDATE price_intervals SET started_at = ? WHERE ended_at IS NULL",
            (current_start,),
        )
        connection.commit()
        connection.close()

        self.service.state()

        state = self.service.state()
        self.assertEqual(len(state["indexes"]["party_index"]), 2)
        self.assertTrue(all(len(history) == 2 for history in state["prices"]["prices_history"].values()))

    def test_explicit_noise_setting_overrides_existing_database_value(self):
        self.service.update_simulation(False, 4, 1, 0)

        MarketService(
            Path(self.temp_dir.name) / "market.sqlite3",
            noise_percent=3.5,
        )

        connection = sqlite3.connect(self.service.database_path)
        try:
            noise = connection.execute(
                "SELECT noise_percent FROM market_settings WHERE id = 1"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(noise, 3.5)


if __name__ == "__main__":
    unittest.main()