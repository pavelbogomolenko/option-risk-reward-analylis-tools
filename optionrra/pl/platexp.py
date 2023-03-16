from sys import maxsize

from optionrra.model import OptionType, Position


class PositionPLAtExpiration:
    LAST_PRICE_INTERVAL_MULTIPLIER = 1.1

    def __init__(self, position: Position):
        # we assume contracts in a position are sorted
        self.position = position
        self.price_intervals = self.__price_intervals()
        self.slopes = self.__slopes()
        self.adj_price_intervals = self.__adjusted_price_intervals()
        self.adj_slopes = self.__adjusted_slopes()
        self.pl_points = self.__pl_points()

    def __price_intervals(self):
        prev_price = self.position.contracts[0].get_price()
        intervals = [(0, prev_price)]

        for c in self.position.contracts[1:]:
            price = round(c.get_price(), 2)
            if prev_price == price:
                continue
            interval = (prev_price, price)
            intervals.append(interval)
            prev_price = price

        last_price = round(prev_price * self.LAST_PRICE_INTERVAL_MULTIPLIER, 2)
        intervals.append((prev_price, last_price))
        return intervals

    def __slope_between_interval(self, lo: float, hi: float):
        total_slope = 0
        for c in self.position.contracts:
            if c.is_in_money_between(lo, hi):
                slope = c.in_money_slope()
                total_slope += slope * c.count
        return total_slope

    def __slopes(self):
        d = {}
        for lo, hi in self.price_intervals:
            d[f"{lo}-{hi}"] = self.__slope_between_interval(lo, hi)
        return d

    def __adjusted_slopes(self):
        d = {}
        for lo, hi in self.adj_price_intervals:
            d[f"{lo}-{hi}"] = self.__slope_between_interval(lo, hi)
        return d

    def __adjusted_price_intervals(self):
        slope_direction_count = 0
        prev_slope = maxsize
        intervals = []
        int_count = len(self.price_intervals)
        for i, interval in enumerate(self.price_intervals):
            lo, hi = interval
            slope = 1
            if self.slopes.get(f"{lo}-{hi}") < 0:
                slope = -1
            elif self.slopes.get(f"{lo}-{hi}") == 0:
                slope = 0

            if i == 0:
                intervals.append(interval)
                slope_direction_count = 1
            else:
                # we need to have at least 3 intervals, unless it is straddle or strangle
                if i == int_count - 1 and len(intervals) == 2:
                    intervals.append(interval)
                    continue

                if slope_direction_count < 1 and slope == prev_slope:
                    intervals.append(interval)
                    slope_direction_count += 1

                elif slope_direction_count >= 1 and slope == prev_slope:
                    lo_prev, hi_prev = intervals[-1]
                    intervals[i - slope_direction_count] = (lo_prev, hi)
                    slope_direction_count += 1

                if slope != prev_slope:
                    intervals.append(interval)
                    slope_direction_count = 1

            prev_slope = slope

        return intervals

    @staticmethod
    def __is_slope_changed(s1, s2):
        if s1 == 0 or s2 == 0:
            return s1 != s2
        return (s1 ^ s2) < 0

    def __pl_points(self):
        points = []
        position_num = len(self.position.contracts)
        pl = self.position.pl_at_strike[self.position.all_strikes[0]]
        int_len = len(self.adj_price_intervals)
        slope_key = f"{self.adj_price_intervals[0][0]}-{self.adj_price_intervals[0][1]}"
        first_slope = self.adj_slopes.get(slope_key)
        if first_slope is None:
            raise ValueError("not a valid slope")

        prev_slope = ~first_slope + 1
        for i, interval in enumerate(self.adj_price_intervals):
            lo, hi = interval
            slope = self.adj_slopes.get(f"{lo}-{hi}")

            if slope == 0:
                if len(points) > 0:
                    prev_x, prev_y = points[-1]
                    points.append((hi, prev_y))
                else:
                    points.append((lo, pl))
                    points.append((hi, pl))

                prev_slope = slope
                continue

            # start with finding first point
            if i == 0:
                points.append((hi, pl))

            # find a breakeven if slope has changed
            x_br = 0
            if self.__is_slope_changed(slope, prev_slope):
                # A special case for straddle and strangle
                if position_num == 1:
                    x = lo if lo > 0 else hi
                    # since there is only 1 contract, take the first one
                    contract_subtype = self.position.contracts[0].subtype()
                    sl = abs(pl / slope)
                    x_br = x + sl if contract_subtype != OptionType.PUT else x - sl
                    points = [(x_br, 0)] + points
                else:
                    if slope < 0 and int_len == 2:
                        x_hi = hi if i != int_len - 1 else lo
                        x_br = x_hi + abs(pl) / slope
                        points.append((x_br, 0))
                    else:
                        x = lo if lo > 0 else hi
                        x_br = x + abs(pl / slope)
                        points.append((x_br, 0))

            if 0 < i < int_len - 1:
                pl = round((hi - x_br) / slope, 2)
                points.append((hi, pl))

            prev_slope = slope

        return points
