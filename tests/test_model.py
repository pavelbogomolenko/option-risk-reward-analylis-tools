import pytest
from unittest.mock import patch

from dateutil.parser import parse
from optionrra.model import ContractType, OptionContract, OptionType, Position, StockContract


@pytest.mark.parametrize("test_input, expected", [(100, False), (95, True), (90, False)])
def test_call_option_is_at_money(test_input, expected):
    call_option = OptionContract(1, ContractType.LONG, 1.25, OptionType.CALL, 95.0)
    assert call_option.is_at_money(test_input) == expected


@pytest.mark.parametrize("test_input, expected", [
    (OptionType.CALL, OptionType.CALL.value),
    (OptionType.PUT, OptionType.PUT.value)
])
def test_option_get_option_type_value(test_input, expected):
    call_option = OptionContract(1, ContractType.LONG, 1.25, test_input, 95.0)
    assert call_option.get_option_type_value() == expected


@pytest.mark.parametrize("test_input", ["+1 95 put 6.25", "-1 105 call 9.25"])
def test_build_option_contract_from_string(test_input):
    o = OptionContract.from_str(test_input)
    c, s, ot, p = test_input.split(" ")
    assert o.count == abs(int(c))
    assert o.strike_price == float(s)
    assert o.premium == float(p)
    assert o.option_type == OptionType[ot.upper()]


def test_not_a_valid_option_string():
    with pytest.raises(ValueError):
        OptionContract.from_str("+1 95 put")


@pytest.mark.parametrize("test_input", ["+1 95 put 6.25 2023-03-15", "-1 105 call 9.25 2024-03-15", "+1 110 call 8.0"])
def test_build_option_contract_from_string_with_optional_expiration_date(test_input):
    o = OptionContract.from_str(test_input)
    params = test_input.split(" ")
    count = int(params[0])
    contract_type = ContractType.LONG if int(count) > 0 else ContractType.SHORT
    strike = float(params[1])
    option_type = OptionType[params[2].upper()]
    premium = float(params[3])
    exp_date = parse(params[4]) if len(params) > 4 else None

    assert o.count == abs(count)
    assert o.type == contract_type
    assert o.strike_price == strike
    assert o.premium == premium
    assert o.option_type == option_type
    assert o.expiration_date() == exp_date


@pytest.mark.parametrize("test_input", ["+1 stock 95", "-1 stock 100"])
def test_build_stock_contract_from_string(test_input):
    c = StockContract.from_str(test_input)
    count, _, p = test_input.split(" ")
    assert c.count == abs(int(count))
    assert c.type == ContractType.LONG if int(count) > 0 else ContractType.SHORT
    assert c.get_price() == float(p)
    assert c.expiration_date() is None


@pytest.mark.parametrize("test_input, expected", [
    (("+1 95 put 6.25", 90), True),
    (("+1 95 put 6.25", 95), False),
    (("+1 95 call 6.25", 95), False),
    (("+1 95 call 6.25", 100), True),
    (("+1 95 call 6.25", 80), False),
])
def test_option_contract_is_in_money(test_input, expected):
    o, current_price = test_input
    c = OptionContract.from_str(o)
    assert c.is_in_money(current_price) == expected


@pytest.mark.parametrize("test_input, expected", [
    (("+1 stock 95", 90), True),
    (("+1 stock 95", 100), True),
    (("-1 stock 95", 95), True),
    (("-1 stock 95", 90), True),
    (("-1 stock 95", 0), False),
])
def test_stock_contract_is_in_money(test_input, expected):
    o, current_price = test_input
    c = StockContract.from_str(o)
    assert c.is_in_money(current_price) == expected


@pytest.mark.parametrize("test_input, expected", [
    (("+1 95 call 6.25", 90), -6.25),
    (("+1 95 call 6.25", 95), -6.25),
    (("+1 95 call 6.25", 101.25), 0),
    (("+1 95 call 6.25", 98), -3.25),
    (("+1 95 call 6.25", 105), 3.75),
    (("-1 95 call 2.25", 90), 2.25),
    (("-2 95 call 2.25", 90), 2 * 2.25),
    (("-1 100 call 2.25", 90), 2.25),
    (("-1 105 put 7.75", 140.5), 7.75),
    (("-1 105 put 7.75", 95), -2.25),
    (("-2 105 put 7.75", 95), -2 * 2.25),
    (("-1 105 put 5.0", 80), -20.0),
    (("+1 95 put 6.25", 90), -1.25),
    (("+1 95 put 5", 80.0), 10),
    (("+1 95 put 6.25", 88.75), 0),
    (("+1 95 put 5", 100.0), -5),
])
def test_option_contract_pl(test_input, expected):
    o, current_price = test_input
    c = OptionContract.from_str(o)
    assert c.pl(current_price) == expected


@pytest.mark.parametrize("test_input, expected", [
    (("+1 stock 95", 90), 5),
    (("+1 stock 90", 90), 0),
    (("+1 stock 90", 95), -5),
    (("+2 stock 90", 95), -2 * 5),
])
def test_stock_contract_pl(test_input, expected):
    o, current_price = test_input
    c = StockContract.from_str(o)
    assert c.pl(current_price) == expected


@pytest.mark.parametrize("test_input, expected", [
    (
            ["+1 95 call 6.25", "-1 105 call 1.75", "-2 105 put 7.75", "-2 stock 98"],
            {95: -3.0, 98: 0, 105: 7.0}
    ),
    (["-1 95 call 6.25"], {95: 6.25}),
    (
            ["+1 95 call 6.25", "+1 100 call 4.5", "+1 105 call 2.5", "+1 102 call 3.5"],
            {95.0: -16.75, 100.0: -11.75, 102.0: -7.75, 105.0: 1.25}
    ),
])
def test_position_pl(test_input, expected):
    position = Position.from_str_list(test_input)
    assert position.pl_at_strike == expected


def test_position_to_str_list():
    long_95_call = OptionContract(1, ContractType.LONG, 6.25, OptionType.CALL, 95)
    short_105_call = OptionContract(1, ContractType.SHORT, 1.75, OptionType.CALL, 105)
    long_90_put = OptionContract(2, ContractType.LONG, 2.25, OptionType.PUT, 90)
    short_90_put = OptionContract(2, ContractType.SHORT, 7.25, OptionType.PUT, 90)
    short_stock_95 = StockContract(1, ContractType.SHORT, 95)
    pos = Position([long_95_call, short_105_call, long_90_put, short_90_put, short_stock_95])

    actual = sorted(pos.to_str_list())
    expected = sorted(["+2 90 put 2.25", "-2 90 put 7.25", "+1 95 call 6.25", "-1 stock 95", "-1 105 call 1.75"])

    assert actual == expected


def test_position_contracts_are_sorted_by_price():
    contracts = ["+1 90 call 9.5", "+1 85 call 5.5", "+1 80 call 3.5"]
    position = Position.from_str_list(contracts)
    expected_contracts = ["+1 80.0 call 3.5", "+1 85.0 call 5.5", "+1 90.0 call 9.5"]
    assert position.to_str_list() == expected_contracts


def test_position_min_strike():
    contracts = ["+1 90 put 9.5", "+1 85 call 5.5", "+1 80 call 3.5"]
    pos = Position.from_str_list(contracts)
    assert pos.min_strike == 80


def test_position_max_strike():
    contracts = ["+1 90 put 9.5", "+1 85 call 5.5", "+1 80 call 3.5"]
    pos = Position.from_str_list(contracts)
    assert pos.max_strike == 90


def test_position_min_expiration_date():
    contracts = ["+1 90 put 9.5 2023-06-15", "+1 85 call 5.5 2023-05-15", "+1 80 call 3.5 2023-05-10"]
    pos = Position.from_str_list(contracts)
    assert pos.min_expiration_date == parse("2023-05-10")


def test_position_max_expiration_date():
    contracts = ["+1 90 put 9.5 2023-06-15", "+1 85 call 5.5 2023-05-15", "+1 80 call 3.5 2023-05-10"]
    pos = Position.from_str_list(contracts)
    assert pos.max_expiration_date == parse("2023-06-15")


@pytest.mark.parametrize("test_input, expected", [
    (
            ["+1 95 call 6.25", "-1 105 call 1.75", "-2 105 put 7.75"],
            -6.25+1.75+2*7.75
    ),
    (
            ["+1 95 call 6.25", "-1 105 call 1.75", "-2 105 put 7.75", "-2 stock 98"],
            -6.25+1.75+2*7.75+2*98
    ),
    (
            ["+2 35.0 put 9.5", "-2 50.0 put 12.5"],
            2*(-9.5)+2*12.5
    ),
    (
            ["+2 19.00 call 1.8 2023-04-15", "-1 19.00 put 1.8 2023-06-15"],
            2*(-1.8)+1.8
    ),
])
def test_position_entry_cost(test_input, expected):
    pos = Position.from_str_list(test_input)
    assert pos.entry_cost() == expected


@pytest.mark.parametrize("test_input, expected", [
    (
            (["+1 95 call 6.25"], 100),
            0
    ),
    (
            (["+1 95 put 6.25"], 96),
            0
    ),
    (
            (["+1 stock 98.0"], 100),
            2.0
    ),
    (
            (["+2 stock 98.0"], 100),
            4.0
    ),
])
def test_position_theoretical_value_with_no_expiration_value(test_input, expected):
    pos = Position.from_str_list(test_input[0])
    assert pos.theoretical_value(test_input[1], 0.4) == expected


@pytest.mark.parametrize("test_input, expected", [
    (
            (["+1 70 call 7.9 2023-05-15"], 100, 0.4, 0.05),
            1.8
    ),
    (
            (["+2 70 put 7.9 2023-05-15"], 100, 0.4, 0.05),
            2 * 1.8
    ),
])
def test_position_theoretical_value_with_expiration_value(test_input, expected):
    num_days = 30
    theor_value = 1.8
    sigma = test_input[2]
    r = test_input[3]
    with patch("optionrra.model.num_workdays_until", return_value=num_days):
        with patch("optionrra.model.option_value", return_value=theor_value) as option_value_mock:
            pos = Position.from_str_list(test_input[0])
            count = pos.contracts[0].count
            assert pos.theoretical_value(test_input[1], sigma, r) == count * theor_value
            for c in pos.contracts:
                option_type = c.subtype().value[0]
                option_value_mock.assert_called_with(test_input[1], c.get_price(),
                                                     r, sigma,
                                                     num_days + 1,
                                                     option_type)
