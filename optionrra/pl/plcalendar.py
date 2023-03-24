from typing import List, Tuple
import numpy as np

from optionrra.misc.dateutils import num_workdays_until
from optionrra.model import Position


class PositionPLCalendar:
    MAX_DATE_SAMPLE_NUMBER: int = 15
    MAX_PRICE_SAMPLE_NUMBER: int = 10

    def __init__(self, position: Position):
        self.position = position
        self.days_until_expiration_interval = self.__days_until_expiration_interval()

    def __days_until_expiration_interval(self) -> List[int]:
        """
        Return evenly spaced days range over the [`0`, `max_expiration_date + 1`] interval.

        :return:
        """
        num_days_until_exp = num_workdays_until(self.position.max_expiration_date) + 1
        samples_num = min(num_days_until_exp, self.MAX_DATE_SAMPLE_NUMBER)
        if samples_num < 10:
            return list(np.arange(0, samples_num))

        days_interval = np.linspace(0, num_days_until_exp, samples_num)
        return [int(d) for d in days_interval]

    def generate_stock_price_interval(self, price_range: Tuple[float, float]) -> List[float]:
        lo, hi = price_range
        if lo >= hi:
            raise ValueError("Not a valid price range")

        return list(np.linspace(lo, hi, self.MAX_PRICE_SAMPLE_NUMBER))

    def expected_returns_simulation(self, price_range: Tuple[float, float], sigma: float, r: float) -> np.array:
        """
        Simulates position "expected returns"

        Expected returns it is an absolute difference between position entry cost
        and it's theoretical value at a given date

        :param price_range: A tuple of underlying stock expected low and high price range
        :param sigma: Standard deviation of stock or underlying contract
        :param r: risk-free rate
        :return:
        """
        position_entry_cost = self.position.entry_cost
        price_interval = self.generate_stock_price_interval(price_range)
        expected_returns = np.zeros((len(price_interval), len(self.days_until_expiration_interval)))
        for i, price in enumerate(price_interval):
            for j, t in enumerate(self.days_until_expiration_interval):
                theoretical_value_t = self.position.theoretical_value(price, sigma, r, t)
                value_at_t = theoretical_value_t - abs(position_entry_cost)
                expected_returns[i, j] = value_at_t

        return expected_returns
