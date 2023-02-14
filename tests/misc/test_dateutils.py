from datetime import datetime

from optionrra.misc.dateutils import num_workdays_between

import pytest


@pytest.mark.parametrize("test_input, expected", [
    (("2023-02-14", "2023-02-17"), 4),
    (("2023-02-14", "2023-03-01"), 12),
    (("2023-02-14", "2023-03-17"), 24)
])
def test_num_workdays_from_until(test_input, expected):
    d1, d2 = test_input
    d_from = datetime.fromisoformat(d1)
    d_to = datetime.fromisoformat(d2)
    assert num_workdays_between(d_from, d_to) == expected
