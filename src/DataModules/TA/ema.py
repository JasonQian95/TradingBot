import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import prices
import config
import utils
import tautils as ta


table_filename = "EMA.csv"
graph_filename = ".png"

default_periods = [50, 200]


# TODO: 200 day ema is slightly off. 50 and 20 day emas have no issue. Diverence seems to start around 70
# Data matches 20 and 50 ema from Yahoo Finance, TradingView, and MarketWatch. 200 ema matches TradingView but not the others
def ema(symbol, period, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the exponential moving agerage for the given symbol, saves this data in a .csv file, and returns this data
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        dataframe
            A dataframe containing the exponential moving agerage for the given symbol
    """

    if not utils.refresh(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), refresh=refresh):
        df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]
    else:
        if utils.refresh(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), refresh=refresh):
            prices.download_data_from_yahoo(symbol, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), usecols=["Date", "Close"], index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if ("EMA" + str(period)) not in df.columns:
        df["EMA" + str(period)] = df["Close"].ewm(span=period, min_periods=period, adjust=False).mean()
        utils.debug(df["EMA" + str(period)])
        df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))
    return df["EMA" + str(period)]


def plot_ema(symbol, period=default_periods, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the exponential moving agerage for each period for the given symbol, saves this data in a .csv file, and plots this data
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A figure and axes containing the exponential moving agerage for the given symbol
    """

    if not utils.refresh(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), refresh=refresh):
        df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]
    else:
        if utils.refresh(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), refresh=refresh):
            prices.download_data_from_yahoo(symbol, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), usecols=["Date", "Close"], index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if isinstance(period, int):
        period = [period]
    period.sort()

    if len(df) < period[-1]:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period[-1]))

    fig, ax = plt.subplots(figsize=config.figsize)
    ax.plot(df.index, df["Close"], label="Price")
    for p in period:
        column_name = "EMA" + str(p)
        if column_name not in df.columns:
            df = df.join(ema(symbol, p, refresh=False, start_date=start_date, end_date=end_date))
        # if len(df) > p:  # to prevent AttributeError when the column is all None
        ax.plot(df.index, df[column_name], label=column_name)

    utils.prettify_ax(ax, title=symbol + "EMA" + "-".join(str(p) for p in period), start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, get_signal_name(period) + graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax


def generate_signals(symbol, period=default_periods, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the exponential moving agerage buy/sell signals for each period for the given symbol, saves this data in a .csv file, and plots this data.
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
            What periods to calculate for. Only uses the first two periods
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        dataframe
            A dataframe containing the exponential moving agerage signals for the given symbol
    """

    if len(period) != 2:
        raise ValueError("Requires at two periods")
    period.sort()

    # Why did I do this differently in plot?
    for p in period:
        ema(symbol, p, refresh=False, start_date=start_date, end_date=end_date)
    df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    signal_column_name = get_signal_name(period=period)
    if signal_column_name not in df.columns:
        fast_column_name = "EMA" + str(period[0])
        slow_column_name = "EMA" + str(period[1])

        conditions = [
            ((df[fast_column_name].shift(1) < df[slow_column_name].shift(1)) & (df[fast_column_name] > df[slow_column_name])),  # fast line crosses slow line from below; buy signal
            ((df[fast_column_name].shift(1) > df[slow_column_name].shift(1)) & (df[fast_column_name] < df[slow_column_name])),  # fast line crosses slow line from above; sell signal
            ((df[fast_column_name] < df[slow_column_name]) & (df["Close"].shift(1) < df[fast_column_name].shift(1)) & (df["Close"] > df[fast_column_name])),  # price crosses fast line from below, soft buy
            ((df[fast_column_name] > df[slow_column_name]) & (df["Close"].shift(1) > df[fast_column_name].shift(1)) & (df["Close"] < df[fast_column_name]))  # price crosses fast line from above, soft sell
        ]

        df[signal_column_name] = np.select(conditions, ta.signals, default=ta.default_signal)
        utils.debug(df[signal_column_name])
        df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))

    return df[signal_column_name]


def plot_signals(symbol, period=default_periods, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Plots the exponential moving agerage buy/sell signals for each period for the given symbol, saves this data in a .csv file, and plots this data.
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
            What periods to calculate for. Only uses the first two periods
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A figure and axes containing the exponential moving agerage signals for the given symbol
    """

    if len(period) != 2:
        raise ValueError("Requires at two periods")
    period.sort()

    generate_signals(symbol, period=period, refresh=refresh, start_date=start_date, end_date=end_date)
    fig, ax = plot_ema(symbol, period=period, refresh=refresh, start_date=start_date, end_date=end_date)
    df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    fast_column_name = "EMA" + str(period[0])
    slow_column_name = "EMA" + str(period[1])  # can use either column since I'm plotting crossovers
    signal_column_name = get_signal_name(period=period)

    buy_signals = df.loc[df[signal_column_name] == ta.buy_signal]
    ax.scatter(buy_signals.index, df.loc[df.index.isin(buy_signals.index)][fast_column_name], label=ta.buy_signal, color=ta.signal_colors[ta.buy_signal], marker=ta.signal_markers[ta.buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((buy_signals.index, buy_signals.index), (df.loc[df.index.isin(buy_signals.index)][fast_column_name], buy_signals["Close"]), color=ta.signal_colors[ta.buy_signal])

    sell_signals = df.loc[df[signal_column_name] == ta.sell_signal]
    ax.scatter(sell_signals.index, df.loc[df.index.isin(sell_signals.index)][fast_column_name], label=ta.sell_signal, color=ta.signal_colors[ta.sell_signal], marker=ta.signal_markers[ta.sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((sell_signals.index, sell_signals.index), (df.loc[df.index.isin(sell_signals.index)][fast_column_name], sell_signals["Close"]), color=ta.signal_colors[ta.sell_signal])

    soft_buy_signals = df.loc[df[signal_column_name] == ta.soft_buy_signal]
    ax.scatter(soft_buy_signals.index, df.loc[df.index.isin(soft_buy_signals.index)][fast_column_name], label=ta.soft_buy_signal, color=ta.signal_colors[ta.soft_buy_signal], marker=ta.signal_markers[ta.soft_buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((soft_buy_signals.index, soft_buy_signals.index), (df.loc[df.index.isin(soft_buy_signals.index)][fast_column_name], soft_buy_signals["Close"]), color=ta.signal_colors[ta.soft_buy_signal])

    soft_sell_signals = df.loc[df[signal_column_name] == ta.soft_sell_signal]
    ax.scatter(soft_sell_signals.index, df.loc[df.index.isin(soft_sell_signals.index)][fast_column_name], label=ta.soft_sell_signal, color=ta.signal_colors[ta.soft_sell_signal], marker=ta.signal_markers[ta.soft_sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((soft_sell_signals.index, soft_sell_signals.index), (df.loc[df.index.isin(soft_sell_signals.index)][fast_column_name], soft_sell_signals["Close"]), color=ta.signal_colors[ta.soft_sell_signal])

    utils.prettify_ax(ax, title=symbol + signal_column_name, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, get_signal_name(period) + graph_filename, symbol=symbol))
    utils.debug(fig)

    return fig, ax


def get_signal_name(period=default_periods):
    return "EMA" + "Signal" + "-".join(str(p) for p in period)
