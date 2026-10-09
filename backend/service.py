import json
import random
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.pricing import calculate_next_prices


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = ROOT_DIR / "data" / "beers.json"
DEFAULT_DATABASE_PATH = ROOT_DIR / "data" / "market.sqlite3"


class MarketService:
    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE_PATH,
        catalog_path: str | Path = DEFAULT_CATALOG_PATH,
        noise_percent: float | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.catalog_path = Path(catalog_path)
        self.noise_percent = noise_percent
        self.catalog: dict[str, dict[str, Any]] = json.loads(
            self.catalog_path.read_text(encoding="utf-8")
        )
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _to_cents(amount: float) -> int:
        return int(amount * 100 + 0.5)

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS market_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    interval_seconds INTEGER NOT NULL,
                    amplification REAL NOT NULL,
                    noise_percent REAL NOT NULL,
                    simulation_enabled INTEGER NOT NULL DEFAULT 0,
                    simulation_sales_per_minute REAL NOT NULL DEFAULT 4,
                    simulation_seed INTEGER NOT NULL DEFAULT 1,
                    revision INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS beers (
                    code TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    initial_cents INTEGER NOT NULL,
                    krach_cents INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS price_intervals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at REAL NOT NULL,
                    ended_at REAL,
                    is_krach INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS interval_prices (
                    interval_id INTEGER NOT NULL REFERENCES price_intervals(id),
                    beer_code TEXT NOT NULL REFERENCES beers(code),
                    price_cents INTEGER NOT NULL,
                    PRIMARY KEY (interval_id, beer_code)
                );
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL UNIQUE,
                    beer_code TEXT NOT NULL REFERENCES beers(code),
                    price_cents INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    simulated INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS sales_created_at_idx ON sales(created_at);
                """
            )
            connection.execute(
                """INSERT OR IGNORE INTO market_settings
                   (id, interval_seconds, amplification, noise_percent)
                   VALUES (1, 60, 100, ?)""",
                (self.noise_percent or 0.0,),
            )
            if self.noise_percent is not None:
                connection.execute(
                    """UPDATE market_settings SET noise_percent = ?,
                       revision = revision + (noise_percent != ?) WHERE id = 1""",
                    (self.noise_percent, self.noise_percent),
                )

            stored_beers = connection.execute(
                "SELECT code, full_name, initial_cents, krach_cents FROM beers"
            ).fetchall()
            if not stored_beers:
                connection.executemany(
                    """INSERT INTO beers (code, full_name, initial_cents, krach_cents)
                       VALUES (?, ?, ?, ?)""",
                    [
                        (
                            code,
                            beer["full_name"],
                            self._to_cents(beer["initial_price"]),
                            self._to_cents(beer["krach_price"]),
                        )
                        for code, beer in self.catalog.items()
                    ],
                )

            interval = connection.execute(
                "SELECT id FROM price_intervals ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if interval is None:
                cursor = connection.execute(
                    "INSERT INTO price_intervals (started_at) VALUES (?)", (time.time(),)
                )
                connection.executemany(
                    """INSERT INTO interval_prices (interval_id, beer_code, price_cents)
                       SELECT ?, code, initial_cents FROM beers WHERE code = ?""",
                    [(cursor.lastrowid, code) for code in self.catalog],
                )

    def _advance_due_intervals(self, now: float) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            settings = connection.execute(
                "SELECT * FROM market_settings WHERE id = 1"
            ).fetchone()

            while True:
                current = connection.execute(
                    "SELECT * FROM price_intervals ORDER BY id DESC LIMIT 1"
                ).fetchone()
                end_at = current["started_at"] + settings["interval_seconds"]
                if end_at > now:
                    break

                rows = connection.execute(
                    "SELECT beer_code, price_cents FROM interval_prices WHERE interval_id = ?",
                    (current["id"],),
                ).fetchall()
                current_prices = {
                    row["beer_code"]: row["price_cents"] / 100 for row in rows
                }
                sale_rows = connection.execute(
                    """SELECT beer_code, COUNT(*) AS count FROM sales
                       WHERE created_at >= ? AND created_at < ? GROUP BY beer_code""",
                    (current["started_at"], end_at),
                ).fetchall()
                sales_counts = {row["beer_code"]: row["count"] for row in sale_rows}

                if settings["simulation_enabled"] and settings["simulation_sales_per_minute"]:
                    rng = random.Random(settings["simulation_seed"] + current["id"])
                    expected = settings["simulation_sales_per_minute"] * (
                        settings["interval_seconds"] / 60
                    )
                    simulated_count = int(expected)
                    if rng.random() < expected - simulated_count:
                        simulated_count += 1
                    simulated_counts: dict[str, int] = dict.fromkeys(self.catalog, 0)
                    for _ in range(simulated_count):
                        simulated_counts[rng.choice(list(self.catalog))] += 1
                    for code, count in simulated_counts.items():
                        sales_counts[code] = sales_counts.get(code, 0) + count
                        for _ in range(count):
                            connection.execute(
                                """INSERT INTO sales
                                   (request_id, beer_code, price_cents, created_at, simulated)
                                   VALUES (?, ?, ?, ?, 1)""",
                                (
                                    f"sim-{current['id']}-{uuid4()}",
                                    code,
                                    self._to_cents(current_prices[code]),
                                    end_at - 0.001,
                                ),
                            )

                new_prices = calculate_next_prices(
                    current_prices,
                    sales_counts,
                    settings["interval_seconds"],
                    settings["amplification"],
                    settings["noise_percent"],
                    random.Random(settings["simulation_seed"] + current["id"]),
                )
                connection.execute(
                    "UPDATE price_intervals SET ended_at = ? WHERE id = ?",
                    (end_at, current["id"]),
                )
                cursor = connection.execute(
                    "INSERT INTO price_intervals (started_at) VALUES (?)", (end_at,)
                )
                connection.executemany(
                    """INSERT INTO interval_prices (interval_id, beer_code, price_cents)
                       VALUES (?, ?, ?)""",
                    [
                        (cursor.lastrowid, code, self._to_cents(price))
                        for code, price in new_prices.items()
                    ],
                )
                connection.execute(
                    "UPDATE market_settings SET revision = revision + 1 WHERE id = 1"
                )
                settings = connection.execute(
                    "SELECT * FROM market_settings WHERE id = 1"
                ).fetchone()

    def record_sale(self, beer_code: str, request_id: str) -> dict[str, Any]:
        self._advance_due_intervals(time.time())
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            beer = connection.execute(
                "SELECT code FROM beers WHERE code = ?", (beer_code,)
            ).fetchone()
            if beer is None:
                raise KeyError(beer_code)
            existing = connection.execute(
                "SELECT * FROM sales WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing:
                return {
                    "id": existing["id"],
                    "beer_code": existing["beer_code"],
                    "price": existing["price_cents"] / 100,
                    "created_at": existing["created_at"],
                    "duplicate": True,
                }

            current_interval = connection.execute(
                "SELECT id FROM price_intervals ORDER BY id DESC LIMIT 1"
            ).fetchone()
            price = connection.execute(
                "SELECT price_cents FROM interval_prices WHERE interval_id = ? AND beer_code = ?",
                (current_interval["id"], beer_code),
            ).fetchone()["price_cents"]
            created_at = time.time()
            cursor = connection.execute(
                """INSERT INTO sales (request_id, beer_code, price_cents, created_at)
                   VALUES (?, ?, ?, ?)""",
                (request_id, beer_code, price, created_at),
            )
            connection.execute(
                "UPDATE market_settings SET revision = revision + 1 WHERE id = 1"
            )
            return {
                "id": cursor.lastrowid,
                "beer_code": beer_code,
                "price": price / 100,
                "created_at": created_at,
                "duplicate": False,
            }

    def state(self) -> dict[str, Any]:
        self._advance_due_intervals(time.time())
        with self._connection() as connection:
            settings = connection.execute(
                "SELECT * FROM market_settings WHERE id = 1"
            ).fetchone()
            intervals = connection.execute(
                "SELECT * FROM price_intervals ORDER BY id"
            ).fetchall()
            prices_by_code: dict[str, list[float]] = {
                row["code"]: []
                for row in connection.execute("SELECT code FROM beers ORDER BY rowid")
            }
            for row in connection.execute(
                """SELECT beer_code, price_cents FROM interval_prices
                   ORDER BY interval_id, beer_code"""
            ):
                prices_by_code[row["beer_code"]].append(row["price_cents"] / 100)

            beer_rows = connection.execute(
                "SELECT * FROM beers ORDER BY rowid"
            ).fetchall()
            beers = {
                row["code"]: {
                    "full_name": row["full_name"],
                    "initial_price": row["initial_cents"] / 100,
                    "krach_price": row["krach_cents"] / 100,
                    "colour": f"hsl({int(index * 360 / (len(beer_rows) + 1))}, 90%, 60%)",
                }
                for index, row in enumerate(beer_rows)
            }
            current = intervals[-1]
            active_counts = {
                row["beer_code"]: row["count"]
                for row in connection.execute(
                    """SELECT beer_code, COUNT(*) AS count FROM sales
                       WHERE created_at >= ? AND simulated = 0 GROUP BY beer_code""",
                    (current["started_at"],),
                )
            }
            recent_sales = [
                {
                    "id": row["id"],
                    "beer_code": row["beer_code"],
                    "price": row["price_cents"] / 100,
                    "created_at": row["created_at"],
                }
                for row in connection.execute(
                    """SELECT * FROM (
                           SELECT id, beer_code, price_cents, created_at FROM sales
                           WHERE simulated = 0 ORDER BY id DESC LIMIT 30
                       ) ORDER BY id"""
                )
            ]
            last_prices = {code: history[-1] for code, history in prices_by_code.items()}

        now = time.time()
        return {
            "revision": settings["revision"],
            "default_prices": beers,
            "prices": {
                "prices_history": prices_by_code,
                "amplification": settings["amplification"],
                "number_of_drinks": len(beers),
            },
            "indexes": {
                "party_index": [
                    [
                        round(interval["started_at"] * 1000),
                        round(interval["ended_at"] * 1000)
                        if interval["ended_at"] is not None
                        else None,
                        bool(interval["is_krach"]),
                    ]
                    for interval in intervals
                ],
                "refresh_period": settings["interval_seconds"],
            },
            "current_prices": last_prices,
            "active_sales": active_counts,
            "recent_sales": recent_sales,
            "is_krach": bool(current["is_krach"]),
            "time_until_next": max(
                0,
                round(
                    current["started_at"]
                    + settings["interval_seconds"]
                    - now
                ),
            ),
        }

    def update_simulation(
        self, enabled: bool, sales_per_minute: float, seed: int, noise_percent: float
    ) -> None:
        if sales_per_minute < 0 or noise_percent < 0:
            raise ValueError("simulation rate and noise must not be negative")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """UPDATE market_settings SET simulation_enabled = ?,
                   simulation_sales_per_minute = ?, simulation_seed = ?,
                   noise_percent = ?, revision = revision + 1 WHERE id = 1""",
                (int(enabled), sales_per_minute, seed, noise_percent),
            )