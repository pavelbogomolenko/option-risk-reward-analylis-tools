from optionrra.model import ContractType, OptionContract, OptionType, OptionContract, Position
from optionrra.pl.platexp import PositionPLAtExpiration
from optionrra.pl.platexpgraph import PLAtExpirationGraph

if __name__ == "__main__":

    # some basic positions
    # long_95_call = OptionContract(1, ContractType.LONG, 6.25, OptionType.CALL, 95)
    # position = Position([long_95_call])

    # short_95_call = OptionContract(1, ContractType.SHORT, 6.25, OptionType.CALL, 95)
    # position = Position([short_95_call])

    # long_35_put = OptionContract(1, ContractType.LONG, 9.25, OptionType.PUT, 35)
    # position = Position([long_35_put])

    # short_35_put = OptionContract(1, ContractType.SHORT, 9.25, OptionType.PUT, 35)
    # position = Position([short_35_put])

    #+1 95 c and -1 105 c
    # long_95_call = OptionContract(1, ContractType.LONG, 6.25, OptionType.CALL, 95)
    # short_105_call = OptionContract(1, ContractType.SHORT, 1.75, OptionType.CALL, 105)
    # position = Position([short_105_call, long_95_call])

    # +1 95 p and -1 80 p
    # long_95_put = OptionContract(1, ContractType.LONG, 9.5, OptionType.PUT, 95)
    # short_80_put = OptionContract(1, ContractType.SHORT, 5.0, OptionType.PUT, 80)
    # position = Position([long_95_put, short_80_put])

    # +1 95 c and -2 105 p ( syntactic stock)
    # long_95_call = OptionContract(1, ContractType.LONG, 6.25, OptionType.CALL, 95)
    # short_105_put = OptionContract(2, ContractType.SHORT, 7.00, OptionType.PUT, 105)
    # position = Position([short_105_put, long_95_call])

    # using str list input
    # contracts = ["+1 95 call 6.25", "+1 100 call 4.5", "+1 105 call 2.5", "+1 102 call 3.5"]
    # contracts = ["+1 97 put 9.15", "+1 97 call 6.7"]
    # contracts = ["-1 100 put 3.20", "-1 100 call 3.30"]
    contracts = ["+1 95 call 6.25", "-1 105 call 1.75", "-2 105 put 7.75", "-2 stock 98"]
    position = Position.from_str_list(contracts)

    title = "\n".join(position.to_str_list())
    pos_interval = PositionPLAtExpiration(position)
    g = PLAtExpirationGraph(title, pos_interval.pl_points)
    g.draw()
