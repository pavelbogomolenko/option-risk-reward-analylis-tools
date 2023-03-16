import pytest

from optionrra.model import Position
from optionrra.pl.platexp import PositionPLAtExpiration


def __calc_expected_upper_bound(price):
    return round(price * PositionPLAtExpiration.LAST_PRICE_INTERVAL_MULTIPLIER, 2)


@pytest.mark.parametrize("test_input, expected", [
    (
            ["+1 95 call 6.25", "-1 105 call 1.75", "-2 105 put 7.75", "-2 stock 98"],
            {"0-95.0": 0, "95.0-105.0": 1, f"105.0-{__calc_expected_upper_bound(105)}": -2}
    ),
    (
            ["+1 95 call 6.25"],
            {"0-95.0": 0, f"95.0-{__calc_expected_upper_bound(95)}": +1}
    ),
    (
            ["+1 stock 100"],
            {f"0-{__calc_expected_upper_bound(100)}": +1}
    )
])
def test_adj_slopes(test_input, expected):
    position = Position.from_str_list(test_input)
    intervals = PositionPLAtExpiration(position)
    assert intervals.adj_slopes == expected


@pytest.mark.parametrize("test_input, expected", [
    (
            ["+1 95 call 6.25"],
            [(0, -6.25), (95.0, -6.25), (95.0 + 6.25, 0)]
    ),
    (
            ["-1 95 call 6.25"],
            [(0, 6.25), (95.0, 6.25), (95.0 + 6.25, 0)]
    ),
    (
            ["+1 95 put 6.25"],
            [(__calc_expected_upper_bound(95.0), -6.25), (95.0, -6.25), (95.0 - 6.25, 0)]
    ),
    (
            ["-1 95 put 6.25"],
            [(__calc_expected_upper_bound(95.0), 6.25), (95.0, 6.25), (95.0 - 6.25, 0)]
    ),
    (
            ["+1 97 put 9.15", "+1 97 call 6.7"],
            [(97.0, -round(9.15 + 6.7, 2)), (97.0 - (9.15 + 6.7), 0), (97 + (9.15 + 6.7), 0)]
    ),
    (
            ["-1 100 put 5.20", "-1 100 call 4.70"],
            [(100, 5.20 + 4.70), (100 - (5.20 + 4.70), 0), (100 + (5.20 + 4.70), 0)]
    ),
    (
            ["+1 50 call 9.30", "-1 55 call 5.5"],
            [(0, -3.8), (50.0, -3.8), (53.8, 0), (55.0, 1.2), (60.5, 1.2)]
    ),
])
def test_points(test_input, expected):
    position = Position.from_str_list(test_input)
    intervals = PositionPLAtExpiration(position)
    assert sorted(intervals.pl_points) == sorted(expected)
