import numpy as np
from scipy.stats import norm


def __d1(s: float, k: float, r: float, sigma: float, t_days: int) -> float:
    """
    Standardized distance between the current stock price and the option's strike price,
    adjusted for the risk-free interest rate and the stock's volatility.
    It measures the distance between the current stock price and the option's strike price,
    relative to the risk-free interest rate and the stock's volatility.

    expected_return_on_stock is essentially a `d1` coefficient in Black-Scholes formula

    :param s: stock price or underlying contract price
    :param k: strike price
    :param r: risk-free rate
    :param sigma: standard deviation of stock or underlying contract
    :param t_days: time to maturity in days
    :return: float
    """
    t = t_days / 365
    return (np.log(s / k) + (r + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))


def __d2(d1: float, sigma: float, t_days: int) -> float:
    """
    Standardized distance between the mean and the option's strike,
    adjusted for the risk-free interest rate and the time to expiration.
    It measures the degree of uncertainty about the stock's future price at the time of expiration.

    expected_volatility_of_stock is essentially a `d2` coefficient in Black-Scholes formula

    :param d1: expected return on the stock. d1` coefficient in Black-Scholes formula
    :param sigma: standard deviation of stock or underlying contract
    :param t_days: time to maturity in days
    :return: float
    """
    t = t_days / 365
    return d1 - sigma * np.sqrt(t)


def call_option_value(s: float, k: float, r: float, sigma: float, t_days: int) -> float:
    """
    Estimates theoretical value of european call option

    P = S * N(-d1) - K * exp(-rT) * N(-d2)

    :param s: stock price or underlying contract price
    :param k: strike price
    :param r: risk-free rate
    :param sigma: standard deviation of stock or underlying contract
    :param t_days: time to maturity in days
    :return: float
    """
    if t_days <= 0:
        return max(s - k, 0)

    d1 = __d1(s, k, r, sigma, t_days)
    d2 = __d2(d1, sigma, t_days)

    t = t_days / 365
    return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)


def put_option_value(s: float, k: float, r: float, sigma: float, t_days: int) -> float:
    """
    Estimates theoretical value of european put option

    P = K * exp(-rT) * N(-d2) - S * N(-d1)

    :param s: stock price or underlying contract price
    :param k: strike price
    :param r: risk-free rate
    :param sigma: standard deviation of stock or underlying contract
    :param t_days: time to maturity in days
    :return: float
    """
    if t_days <= 0:
        return abs(min(s - k, 0))

    d1 = __d1(s, k, r, sigma, t_days)
    d2 = __d2(d1, sigma, t_days)

    t = t_days / 365
    return k * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)


def option_value(s: float, k: float, r: float, sigma: float, t_days: int, option_type: str = "c") -> float:
    """
    Estimates theoretical value of european option

    :param s: stock price or underlying contract price
    :param k: strike price
    :param r: risk-free rate
    :param sigma: standard deviation of stock or underlying contract
    :param t_days: time to maturity in days
    :param option_type: "c" stands for call or "p" stands for put option respectively
    :return: float
    """
    if option_type not in ["c", "p"]:
        raise ValueError("Not a valid option_type")

    if option_type == "c":
        return call_option_value(s, k, r, sigma, t_days)
    elif option_type == "p":
        return put_option_value(s, k, r, sigma, t_days)
