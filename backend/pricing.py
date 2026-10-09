import math
import random
from collections.abc import Mapping


def calculate_next_prices(
    current_prices: Mapping[str, float],
    sales_counts: Mapping[str, int],
    elapsed_seconds: float,
    amplification: float = 100.0,
    noise_percent: float = 0.0,
    rng: random.Random | None = None,
) -> dict[str, float]:
    """Calculate one market interval from relative sales, with optional bounded noise."""
    if not current_prices:
        return {}
    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must not be negative")
    if amplification < 0 or noise_percent < 0:
        raise ValueError("amplification and noise_percent must not be negative")

    normalized_counts = {
        code: max(0, int(sales_counts.get(code, 0))) for code in current_prices
    }
    total_sales = sum(normalized_counts.values())
    average_sales = total_sales / len(current_prices)
    maximum_sales = max(max(normalized_counts.values()), 1)
    max_change = (
        math.atan(total_sales / 10)
        / (math.pi / 2)
        * amplification
        * elapsed_seconds
        / 60
    )
    random_source = rng or random

    next_prices: dict[str, float] = {}
    for code, price in current_prices.items():
        relative_sales = (normalized_counts[code] - average_sales) / maximum_sales
        change_percent = relative_sales * max_change
        if noise_percent:
            change_percent += random_source.uniform(-noise_percent, noise_percent)

        updated_price = max(0.0, price * (1 + change_percent / 100))
        next_prices[code] = math.floor(updated_price * 100 + 0.5) / 100

    return next_prices