import pytest
from unittest.mock import patch, MagicMock

import numpy as np

from optionrra.model import Position
from optionrra.pl.plcalendar import PositionPLCalendar


@pytest.mark.parametrize("test_input, expected", [
    (
            (["+1 95 call 6.25"], 1),
            [0, 1]
    ),
    (
            (["+1 95 call 6.25"], 2),
            [0, 1, 2]
    ),
    (
            (["+1 95 call 6.25"], 7),
            list(range(0, 7+1))
    ),
    (
            (["+1 95 call 6.25"], 20),
            [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 20+1]
    ),
    (
            (["+1 95 call 6.25"], 30),
            [0, 2, 4, 6, 8, 11, 13, 15, 17, 19, 22, 24, 26, 28, 30+1]
    )
])
def test_days_until_expiration_interval(test_input, expected):
    with patch("optionrra.pl.plcalendar.num_workdays_until", return_value=test_input[1]):
        position = Position.from_str_list(test_input[0])
        plcalendar = PositionPLCalendar(position)
        result = plcalendar.days_until_expiration_interval
        assert len(result) <= plcalendar.MAX_DATE_SAMPLE_NUMBER
        assert result == expected


@pytest.mark.parametrize("test_input, expected_price_interval", [
    (
            (["+1 95 call 6.25"], (90, 100)),
            [90.0, 100.0]
    )
])
def test_generate_stock_price_interval(test_input, expected_price_interval):
    position = Position.from_str_list(test_input[0])
    plcalendar = PositionPLCalendar(position)
    price_interval = plcalendar.generate_stock_price_interval(test_input[1])
    lo, hi = expected_price_interval
    assert len(price_interval) == plcalendar.MAX_PRICE_SAMPLE_NUMBER
    assert price_interval[0] == lo
    assert price_interval[-1] == hi


@pytest.mark.parametrize("test_input", [
    (
            (["+1 95 call 6.25"], (100, 99)),
    ),
    (
            (["+1 95 call 6.25"], (100, 100)),
    ),
    (
        (["+1 95 call 6.25"], (100,)),
    )
])
def test_generate_stock_price_interval_not_a_valid_price_range(test_input):
    position = Position.from_str_list(test_input[0][0])
    plcalendar = PositionPLCalendar(position)
    with pytest.raises(ValueError):
        plcalendar.generate_stock_price_interval(test_input[0][1])


def test_days_until_expiration_interval():
    theor_val = 1.0
    days_int = [0, 1, 2]
    price_int = [90, 95, 100]
    position = Position.from_str_list(["+1 95 call 5.0 2023-05-01"])
    position.theoretical_value = MagicMock(return_value=theor_val)
    plcalendar = PositionPLCalendar(position)
    plcalendar.days_until_expiration_interval = days_int
    plcalendar.generate_stock_price_interval = MagicMock(return_value=price_int)
    result = plcalendar.expected_returns_simulation((price_int[0], price_int[-1]), 0.4, 0.05)
    assert len(result) == 3
    assert len(result[0]) == 3
    comp = result == np.full((3, 3), theor_val - abs(position.entry_cost))
    assert comp.all()
    assert position.theoretical_value.call_count == len(days_int) * len(price_int)
