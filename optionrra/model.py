from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from dataclasses import dataclass
from dateutil.parser import parse
from datetime import datetime
from typing import List


class ContractType(Enum):
    SHORT = 'short'
    LONG = 'long'


class ContractSubtype(Enum):
    pass


@dataclass
class Contract(metaclass=ABCMeta):
    PRICE_SIGN_MAP = {
        "long": -1,
        "short": +1
    }
    count: int
    type: ContractType

    @abstractmethod
    def get_price(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_value(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def expiration_date(self) -> datetime:
        raise NotImplementedError

    @property
    @abstractmethod
    def subtype(self) -> ContractSubtype:
        raise NotImplementedError

    @property
    @abstractmethod
    def in_money_slope(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_in_money(self, price_at_exp: float) -> bool:
        raise NotImplementedError

    @abstractmethod
    def pl(self, current_price: float) -> float:
        raise NotImplementedError

    @staticmethod
    def from_str(s: str) -> Contract:
        raise NotImplementedError

    def get_type_value(self):
        return ContractType(self.type).value

    def is_in_money_between(self, lo: float, hi: float) -> bool:
        return self.is_in_money(lo) or self.is_in_money(hi)

    def price_sign(self):
        return self.PRICE_SIGN_MAP[self.get_type_value()]

    def __str__(self):
        return f"+{self.count}" if self.type == ContractType.LONG else f"-{self.count}"

    def __hash__(self):
        return hash(self.__str__())


@dataclass
class StockContract(Contract):
    price: float

    @staticmethod
    def from_str(s: str) -> Contract:
        try:
            count, _, price = s.split(" ")
            c = int(count)
            c_type = ContractType.LONG if c > 0 else ContractType.SHORT
            return StockContract(abs(c), c_type, float(price))
        except Exception as e:
            raise ValueError(f"Cant build an OptionContract object from input {s}. Error {e}")

    def get_price(self):
        return self.price

    def get_value(self):
        return self.price

    def is_in_money(self, price_at_exp: float) -> bool:
        # you always "in money" in case price_at_exp is greater than 0
        return price_at_exp > 0

    def in_money_slope(self) -> int:
        return -1 if self.type == ContractType.SHORT else +1

    def pl(self, current_price: float) -> float:
        return self.count * (self.price - current_price)

    def subtype(self):
        # There is no subtype of StockContract
        return None

    def expiration_date(self) -> datetime:
        # There is no expiration date of StockContract
        return None

    def __str__(self):
        s = super().__str__()
        return f"{s} stock {self.price}"

    def __hash__(self):
        return hash(self.__str__())


class OptionType(ContractSubtype):
    CALL = 'call'
    PUT = 'put'


@dataclass
class OptionContract(Contract):
    IN_MONEY_SLOPE_MAP = {
        "long_call": +1,
        "short_call": -1,
        "long_put": -1,
        "short_put": +1,
    }
    premium: float
    option_type: OptionType
    strike_price: float
    exp_date: datetime = None

    def get_price(self) -> float:
        return self.strike_price

    def get_value(self):
        return self.premium

    def subtype(self):
        return self.option_type

    def expiration_date(self) -> datetime:
        return self.exp_date

    def is_in_money(self, underlying_price: float) -> bool:
        if self.option_type == OptionType.CALL:
            return underlying_price > self.strike_price
        return underlying_price < self.strike_price

    def is_at_money(self, underlying_price: float) -> bool:
        return self.strike_price == underlying_price

    def in_money_slope(self) -> int:
        key = f"{self.get_type_value()}_{self.get_option_type_value()}"
        return self.IN_MONEY_SLOPE_MAP[key]

    def pl(self, current_price: float) -> float:
        contract_value = self.premium
        sign = self.price_sign()
        if self.is_in_money(current_price):
            sign = ~self.in_money_slope() + 1
            if self.type == ContractType.LONG \
                    and self.option_type == OptionType.CALL:
                sign = 1
            contract_value = abs(self.strike_price - current_price) - contract_value
        return self.count * sign * contract_value

    def get_option_type_value(self):
        return OptionType(self.option_type).value

    @staticmethod
    def from_str(s: str) -> OptionContract:
        try:
            params = s.split(" ")
            if len(params) < 4:
                raise ValueError("Not a valid option contract string")
            count = int(params[0])
            strike = float(params[1])
            option_type = OptionType[params[2].upper()]
            premium = float(params[3])
            contract_type = ContractType.LONG if int(count) > 0 else ContractType.SHORT
            exp_date = parse(params[4]) if len(params) > 4 else None
            return OptionContract(abs(count), contract_type, premium, option_type, strike, exp_date)
        except Exception as e:
            raise ValueError(f"Cant build an OptionContract object from input {s}. Error {e}")

    def __str__(self):
        s = super().__str__()
        return f"{s} {self.strike_price} {self.get_option_type_value()} {self.premium}"

    def __hash__(self):
        return hash(self.__str__())


class Position:

    def __init__(self, contracts: List[Contract]):
        self.contracts = sorted(set(contracts), key=lambda c: c.get_price())
        self.all_strikes = self.__get_all_strikes()
        self.min_strike = min(self.all_strikes)
        self.max_strike = max(self.all_strikes)
        self.pl_at_strike = {}
        for price in self.all_strikes:
            self.pl_at_strike[price] = self.pl_at_expiration(price)

        min_exp_date = parse("2199-01-01")
        max_exp_date = parse("1970-01-01")
        for c in self.contracts:
            exp_date = c.expiration_date()
            if exp_date is None:
                continue

            if exp_date < min_exp_date:
                min_exp_date = exp_date

            if exp_date > max_exp_date:
                max_exp_date = exp_date

        self.min_expiration_date = min_exp_date
        self.max_expiration_date = max_exp_date

    @staticmethod
    def from_str_list(str_contracts: List[str]) -> Position:
        contracts = []
        for s in str_contracts:
            if s.find("stock") >= 0:
                contracts.append(StockContract.from_str(s))
            else:
                contracts.append(OptionContract.from_str(s))
        return Position(contracts)

    def to_str_list(self):
        return [str(c) for c in self.contracts]

    def __get_all_strikes(self):
        prices = []
        prev_price = -1
        for i, c in enumerate(self.contracts):
            price = c.get_price()
            if i == 0:
                prices.append(price)
            else:
                if prev_price != price:
                    prices.append(price)
            prev_price = price
        return prices

    def pl_at_expiration(self, exp_price: float):
        total_pl = 0
        for c in self.contracts:
            total_pl += c.pl(exp_price)
        return round(total_pl, 2)

    def entry_cost(self):
        total_cost = 0
        for c in self.contracts:
            total_cost += c.price_sign() * c.count * c.get_value()
        return total_cost
