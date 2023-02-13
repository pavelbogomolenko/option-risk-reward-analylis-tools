import pytest

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


@pytest.mark.parametrize("test_input", ["+1 stock 95", "-1 stock 100"])
def test_build_stock_contract_from_string(test_input):
    o = StockContract.from_str(test_input)
    c, _, p = test_input.split(" ")
    assert o.count == abs(int(c))
    assert o.type == ContractType.LONG if int(c) > 0 else ContractType.SHORT
    assert o.get_price() == float(p)


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

