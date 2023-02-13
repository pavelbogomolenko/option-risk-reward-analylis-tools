from sys import maxsize

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import numpy as np


def line_slope(y2, y1, x2, x1):
    return (y2 - y1) / (x2 - x1)


class PositionPlGraph:
    HEAD_TAIL_MULT = 0.15

    def __init__(self, title: str, points: list):
        self.title = title
        self.points = points

    def __get_x_mult(self, sorted_points: list):
        x_tail, _ = sorted_points[0]
        x_next_tail, _ = sorted_points[1]
        return x_tail * self.HEAD_TAIL_MULT if x_tail > 0 \
            else x_next_tail * self.HEAD_TAIL_MULT

    def __calc_tail_and_head_points(self, sorted_points: list):
        x_tail, y_tail = sorted_points[0]
        x_tail_next, y_tail_next = sorted_points[1]
        x_mult = self.__get_x_mult(sorted_points)
        tail_slope = line_slope(y_tail_next, y_tail, x_tail_next, x_tail)
        tail_points = (x_tail_next - x_mult / 2, y_tail)
        if tail_slope != 0:
            x_tail_new = x_tail - x_mult
            y_tail_new = tail_slope * (x_tail_new - x_tail)
            tail_points = (x_tail_new, y_tail_new)

        x_head, y_head = sorted_points[-1]
        x_head_prev, y_head_prev = sorted_points[-2]
        head_slope = line_slope(y_head_prev, y_head, x_head_prev, x_head)
        head_points = ()
        if head_slope != 0:
            x_head_new = x_head + x_mult
            y_head_new = head_slope * (x_head_new - x_head)
            head_points = (x_head_new, y_head_new)

        return tail_points, head_points

    def draw(self):
        plt.ylabel('P&L at expiration')

        plt.title(self.title)

        # Draw a hline at y=0 that spans the xrange
        plt.axhline(color='#000000', linestyle="dotted")

        all_prices = []
        all_x = []
        all_y = []
        sorted_points = sorted(self.points, key=lambda point: point[0])

        tail, head = self.__calc_tail_and_head_points(sorted_points)
        if len(tail) == 2:
            sorted_points = [tail] + sorted_points

        if len(head) == 2:
            sorted_points = sorted_points + [head]

        print(sorted_points)

        points_len = len(sorted_points)
        lowest_y = maxsize
        highest_y = -maxsize
        for i, p in enumerate(sorted_points):
            x, y = p
            if 0 < i < points_len - 1:
                plt.axvline(x=x, color='#000000', linestyle="dotted")
            all_x.append(x)
            all_y.append(y)
            if y < lowest_y:
                lowest_y = y

            if y > highest_y:
                highest_y = y
            all_prices.append(x)
        plt.plot(all_x, all_y, label='Position PL')

        # fill losses
        x_losses = np.array([p[0] for p in sorted_points if p[1] <= 0])
        y1_losses = np.array([p[1] for p in sorted_points if p[1] <= 0])
        y2_losses = np.zeros(len(y1_losses))
        plt.fill_between(x_losses, y1_losses, y2_losses,
                         where=(y2_losses > y1_losses), color='r', alpha=0.3,
                         interpolate=True)

        # fill profits
        x_profits = np.array([p[0] for p in sorted_points if p[1] >= 0])
        y1_profits = np.array([p[1] for p in sorted_points if p[1] >= 0])
        y2_profits = np.zeros(len(y1_profits))
        plt.fill_between(x_profits, y1_profits, y2_profits,
                         where=(y2_profits <= y1_profits), color='g', alpha=0.3,
                         interpolate=True)

        yticks = all_y[1:-1]
        plt.yticks(yticks)
        xticks = all_prices[1:]
        plt.xticks(xticks)

        plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        min_price = all_prices[1] if all_prices[0] == 0 else all_prices[0]
        max_price = all_prices[-1]

        max_y = max(abs(lowest_y), abs(highest_y)) + 2

        # axis
        plt.axis([min_price, max_price, -max_y, max_y])

        # tick params
        plt.tick_params(labeltop=True, labelbottom=False, bottom=False, labelright=True)

        plt.show()
