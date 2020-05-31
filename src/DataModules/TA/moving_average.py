import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import prices
import config
import utils
import tautils as ta

table_filename = "MA.csv"
sma_name = "SMA"
ema_name = "EMA"
sma_graph_filename = sma_name + ".png"
ema_graph_filename = ema_name + ".png"

macd_name = "MACD"
macd_graph_filename = macd_name + ".png"

default_periods = [20, 50, 200]
macd_periods = [9, 12, 26]


def sma(symbol, period, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the simple moving agerage for the given symbol, saves this data in a .csv file, and returns this data
    The SMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int
        backfill : bool, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        dataframe
            A dataframe containing the simple moving agerage for the given symbol
    """

    if not utils.refresh(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), refresh=refresh):
        df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]
    else:
        if utils.refresh(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), refresh=refresh):
            prices.download_data_from_yahoo(symbol, backfill=backfill, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if len(df) < period:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period))

    if (sma_name + str(period)) not in df.columns:
        df[sma_name + str(period)] = df["Close"].rolling(period).mean()
        utils.debug(df[sma_name + str(period)])
        df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))
    return df[sma_name + str(period)]


# TODO: 200 day ema is slightly off. 50 and 20 day emas have no issue. Diverence seems to start around 70
# Data matches 20 and 50 ema from Yahoo Finance, TradingView, and MarketWatch. 200 ema matches TradingView but not the others
def ema(symbol, period, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the exponential moving agerage for the given symbol, saves this data in a .csv file, and returns this data
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int
        backfill : bool, optional
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
            prices.download_data_from_yahoo(symbol, backfill=backfill, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if len(df) < period:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period))

    if (ema_name + str(period)) not in df.columns:
        df[ema_name + str(period)] = df["Close"].ewm(span=period, min_periods=period, adjust=False).mean()
        utils.debug(df[ema_name + str(period)])
        df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))
    return df[ema_name + str(period)]


def plot_sma(symbol, period=default_periods, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the simple moving agerage for each period for the given symbol, saves this data in a .csv file, and plots this data
    The SMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
        backfill : bool, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A subplot containing the simple moving agerage for the given symbol
    """

    if not utils.refresh(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), refresh=refresh):
        df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]
    else:
        if utils.refresh(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), refresh=refresh):
            prices.download_data_from_yahoo(symbol, backfill=backfill, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if isinstance(period, int):
        period = [period]
    period.sort()

    if len(df) < period[-1]:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period))

    fig, ax = plt.subplots(figsize=config.figsize)
    # TODO: replace this with a call to prices.plot_prices?
    ax.plot(df.index, df["Close"], label="Price")
    for p in period:
        column_name = sma_name + str(p)
        if column_name not in df.columns:
            # refresh=False causes this to read from ma file, which means ma numbers are not refreshed
            # refresh=True causes this to refresh 3 times  # harcoded refresh=False in sma to avoid this
            df = df.join(sma(symbol, p, backfill=backfill, refresh=False, start_date=start_date, end_date=end_date))
        if len(df) > p:  # to prevent AttributeError when the column is all None
            ax.plot(df.index, df[column_name], label=column_name)
    utils.prettify_ax(ax, title=symbol + "-".join(str(p) for p in period) + sma_name, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, "-".join(str(p) for p in period) + sma_graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax


def plot_ema(symbol, period=default_periods, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the exponential moving agerage for each period for the given symbol, saves this data in a .csv file, and plots this data
    The EMA is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
        backfill : bool, optional
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
            prices.download_data_from_yahoo(symbol, backfill=backfill, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if isinstance(period, int):
        period = [period]
    period.sort()

    if len(df) < period[-1]:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period))

    fig, ax = plt.subplots(figsize=config.figsize)
    # TODO: replace this with a call to prices.plot_prices?
    ax.plot(df.index, df["Close"], label="Price")
    for p in period:
        column_name = ema_name + str(p)
        if column_name not in df.columns:
            # refresh=False causes this to read from ma file, which means ma numbers are not refreshed
            # refresh=True causes this to refresh 3 times  # harcoded refresh=False in ema to avoid this
            df = df.join(ema(symbol, p, backfill=backfill, refresh=False, start_date=start_date, end_date=end_date))
        if len(df) > p:  # to prevent AttributeError when the column is all None
            ax.plot(df.index, df[column_name], label=column_name)
    utils.prettify_ax(ax, title=symbol + "-".join(str(p) for p in period) + ema_name, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, "-".join(str(p) for p in period) + ema_graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax


def generate_signals(symbol, ma_type=ema_name, period=default_periods, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the moving agerage and buy/sell signals for each period for the given symbol, saves this data in a .csv file, and plots this data. Only uses the first and last periods
    The EMA/SMA is a lagging trend indicator.

    Parameters:
        symbol : str
        ma_type : str
            What function to calculate the moving average with. Valid values are "sma" and "ema"
        period : int or list of int, optional
            What periods to calculate for. Only uses the first and last period
        backfill : bool, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A figure and axes containing the exponential moving agerage for the given symbol
    """

    if len(period) < 2:
        raise ValueError("Requires at least two periods")
    if ma_type != sma_name and ma_type != ema_name:
        raise ValueError("Valid functions are 'sma' and 'ema'")

    if ma_type == sma_name:
        fig, ax = plot_sma(symbol, period=period, backfill=backfill, refresh=refresh, start_date=start_date, end_date=end_date)
        column_name = sma_name
        graph_filename = sma_graph_filename
    if ma_type == ema_name:
        fig, ax = plot_ema(symbol, period=period, backfill=backfill, refresh=refresh, start_date=start_date, end_date=end_date)
        column_name = ema_name
        graph_filename = ema_graph_filename

    df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    period.sort()

    fast_column_name = column_name + str(period[0])
    slow_column_name = column_name + str(period[-1])

    conditions = [
        ((df[fast_column_name].shift(1) < df[slow_column_name].shift(1)) & (df[fast_column_name] > df[slow_column_name])),  # fast line crosses slow line from below; buy signal
        ((df[fast_column_name].shift(1) > df[slow_column_name].shift(1)) & (df[fast_column_name] < df[slow_column_name])),  # fast line crosses slow line from above; sell signal
        ((df[fast_column_name] < df[slow_column_name]) & (df["Close"].shift(1) < df[fast_column_name].shift(1)) & (df["Close"] > df[fast_column_name])),  # price crosses fast line from below, soft buy
        ((df[fast_column_name] > df[slow_column_name]) & (df["Close"].shift(1) > df[fast_column_name].shift(1)) & (df["Close"] < df[fast_column_name]))  # price crosses fast line from above, soft sell
    ]

    column_name = column_name + ta.signal_name + str(period[0]) + "-" + str(period[-1])
    if column_name not in df.columns:
        df[column_name] = np.select(conditions, ta.signals, default=ta.default_signal)
        utils.debug(df[column_name])

    df[ta.signal_name] = df[column_name]
    df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))

    buy_signals = df.loc[df[column_name] == ta.buy_signal]
    ax.scatter(buy_signals.index, df.loc[df.index.isin(buy_signals.index)][fast_column_name], label=ta.buy_signal, color=ta.signal_colors[ta.buy_signal], marker=ta.signal_markers[ta.buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((buy_signals.index, buy_signals.index), (df.loc[df.index.isin(buy_signals.index)][fast_column_name], buy_signals["Close"]), color=ta.signal_colors[ta.buy_signal])

    sell_signals = df.loc[df[column_name] == ta.sell_signal]
    ax.scatter(sell_signals.index, df.loc[df.index.isin(sell_signals.index)][fast_column_name], label=ta.sell_signal, color=ta.signal_colors[ta.sell_signal], marker=ta.signal_markers[ta.sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((sell_signals.index, sell_signals.index), (df.loc[df.index.isin(sell_signals.index)][fast_column_name], sell_signals["Close"]), color=ta.signal_colors[ta.sell_signal])

    soft_buy_signals = df.loc[df[column_name] == ta.soft_buy_signal]
    ax.scatter(soft_buy_signals.index, df.loc[df.index.isin(soft_buy_signals.index)][fast_column_name], label=ta.soft_buy_signal, color=ta.signal_colors[ta.soft_buy_signal], marker=ta.signal_markers[ta.soft_buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((soft_buy_signals.index, soft_buy_signals.index), (df.loc[df.index.isin(soft_buy_signals.index)][fast_column_name], soft_buy_signals["Close"]), color=ta.signal_colors[ta.soft_buy_signal])

    soft_sell_signals = df.loc[df[column_name] == ta.soft_sell_signal]
    ax.scatter(soft_sell_signals.index, df.loc[df.index.isin(soft_sell_signals.index)][fast_column_name], label=ta.soft_sell_signal, color=ta.signal_colors[ta.soft_sell_signal], marker=ta.signal_markers[ta.soft_sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax.plot((soft_sell_signals.index, soft_sell_signals.index), (df.loc[df.index.isin(soft_sell_signals.index)][fast_column_name], soft_sell_signals["Close"]), color=ta.signal_colors[ta.soft_sell_signal])

    utils.prettify_ax(ax, title=symbol + "-".join(str(p) for p in period) + column_name, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, "-".join(str(p) for p in period) + graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax


def plot_macd(symbol, period=macd_periods, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the macd for the given symbol, saves this data in a .csv file, and plots this data
    The MACD is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
            Must contain 3 values. First value is signal line, second is fast line, third is slow line.
        backfill : bool, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A figure and axes containing the macd for the given symbol
    """

    if not utils.refresh(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), refresh=refresh):
        df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]
    else:
        if utils.refresh(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), refresh=refresh):
            prices.download_data_from_yahoo(symbol, backfill=backfill, start_date=start_date, end_date=end_date)
        df = pd.read_csv(utils.get_file_path(config.prices_data_path, prices.price_table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    if len(period) != 3:
        raise ValueError("MACD requires 3 periods")
    if len(df) < period[-1]:
        raise ta.InsufficientDataException("Not enough data to compute a period length of " + str(period))

    fig, ax = plt.subplots(2, figsize=config.figsize)
    # TODO: replace this with a call to prices.plot_prices?
    ax[0].plot(df.index, df["Close"], label="Price")
    utils.prettify_ax(ax[0], title=symbol + prices.price_name, start_date=start_date, end_date=end_date)

    macd_column_name = macd_name + str(period[1]) + "-" + str(period[2])
    if macd_column_name not in df.columns:
        slow_column_name = ema_name + str(period[1])
        if slow_column_name not in df.columns:
            # refresh=False causes this to read from ma file, which means ma numbers are not refreshed
            # refresh=True causes this to refresh 3 times  # harcoded refresh=False in ema to avoid this
            df = df.join(ema(symbol, period[1], backfill=backfill, refresh=False, start_date=start_date, end_date=end_date))
        fast_column_name = ema_name + str(period[2])
        if fast_column_name not in df.columns:
            # refresh=False causes this to read from ma file, which means ma numbers are not refreshed
            # refresh=True causes this to refresh 3 times  # harcoded refresh=False in ema to avoid this
            df = df.join(ema(symbol, period[2], backfill=backfill, refresh=False, start_date=start_date, end_date=end_date))
        df[macd_column_name] = df[slow_column_name] - df[fast_column_name]
    utils.debug(df[macd_column_name])
    if len(df) > period[1] and len(df) > period[2]:
        ax[1].plot(df.index, df[macd_column_name], label="MACD")

    signal_column_name = macd_name + str(period[0])
    if signal_column_name not in df.columns:
        df[signal_column_name] = df[macd_column_name].ewm(span=period[0], min_periods=period[0], adjust=False).mean()
        utils.debug(df[signal_column_name])
        df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))
    if len(df) > period[0]:  # to prevent AttributeError when the column is all None
        ax[1].plot(df.index, df[signal_column_name], label="Signal")
        # TODO Fix histogram - ValueError: incompatible sizes: argument 'height' must be length 3876 or scalar
        # ax[1].bar(df.index, np.histogram(np.isfinite(df[signal_column_name] - df[macd_column_name])), normed=True, alpha=config.alpha)
    utils.prettify_ax(ax[1], title=symbol + macd_name, center=True, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, "-".join(str(p) for p in period) + macd_graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax


def generate_macd_signals(symbol, period=macd_periods, backfill=False, refresh=False, start_date=config.start_date, end_date=config.end_date):
    """Calculates the macd and buy/sell signals for the given symbol, saves this data in a .csv file, and plots this data. Only uses the first and last periods
    The MACD is a lagging trend indicator.

    Parameters:
        symbol : str
        period : int or list of int, optional
            Must contain 3 values. First value is signal line, second is fast line, third is slow line.
        backfill : bool, optional
        refresh : bool, optional
        start_date : date, optional
        end_date : date, optional

    Returns:
        figure, axes
            A figure and axes containing the macd for the given symbol
    """

    if len(period) != 3:
        raise ValueError("MACD requires 3 periods")

    fig, ax = plot_macd(symbol, period=period, backfill=backfill, refresh=refresh, start_date=start_date, end_date=end_date)
    df = pd.read_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol), index_col="Date", parse_dates=["Date"])[start_date:end_date]

    macd_column_name = macd_name + str(period[1]) + "-" + str(period[2])
    signal_column_name = macd_name + str(period[0])

    conditions = [
        ((df[macd_column_name].shift(1) < df[signal_column_name].shift(1)) & (df[macd_column_name] > df[signal_column_name]) & (df[signal_column_name] < 0)),  # macd line crosses signal line from below and the crossover occurs below 0; hard buy signal
        ((df[macd_column_name].shift(1) > df[signal_column_name].shift(1)) & (df[macd_column_name] < df[signal_column_name]) & (df[signal_column_name] > 0)),  # macd line crosses signal line from above and the crossover occurs above 0; hard sell signal
        ((df[macd_column_name].shift(1) < df[signal_column_name].shift(1)) & (df[macd_column_name] > df[signal_column_name])),  # macd line crosses signal line from below; buy signal
        ((df[macd_column_name].shift(1) > df[signal_column_name].shift(1)) & (df[macd_column_name] < df[signal_column_name]))  # macd line crosses signal line from above; sell signal
    ]

    column_name = macd_column_name + signal_column_name + ta.signal_name
    if column_name not in df.columns:
        df[column_name] = np.select(conditions, ta.signals, default=ta.default_signal)
        utils.debug(df[column_name])

    df[ta.signal_name] = df[column_name]
    df.to_csv(utils.get_file_path(config.ta_data_path, table_filename, symbol=symbol))

    buy_signals = df.loc[df[column_name] == ta.buy_signal]
    ax[0].scatter(buy_signals.index, df.loc[df.index.isin(buy_signals.index)]["Close"], label=ta.buy_signal, color=ta.signal_colors[ta.buy_signal], marker=ta.signal_markers[ta.buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax[1].scatter(buy_signals.index, df.loc[df.index.isin(buy_signals.index)][macd_column_name], label=ta.buy_signal, color=ta.signal_colors[ta.buy_signal], marker=ta.signal_markers[ta.buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)

    sell_signals = df.loc[df[column_name] == ta.sell_signal]
    ax[0].scatter(sell_signals.index, df.loc[df.index.isin(sell_signals.index)]["Close"], label=ta.sell_signal, color=ta.signal_colors[ta.sell_signal], marker=ta.signal_markers[ta.sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax[1].scatter(sell_signals.index, df.loc[df.index.isin(sell_signals.index)][macd_column_name], label=ta.sell_signal, color=ta.signal_colors[ta.sell_signal], marker=ta.signal_markers[ta.sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)

    soft_buy_signals = df.loc[df[column_name] == ta.soft_buy_signal]
    ax[0].scatter(soft_buy_signals.index, df.loc[df.index.isin(soft_buy_signals.index)]["Close"], label=ta.soft_buy_signal, color=ta.signal_colors[ta.soft_buy_signal], marker=ta.signal_markers[ta.soft_buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax[1].scatter(soft_buy_signals.index, df.loc[df.index.isin(soft_buy_signals.index)][macd_column_name], label=ta.soft_buy_signal, color=ta.signal_colors[ta.soft_buy_signal], marker=ta.signal_markers[ta.soft_buy_signal], s=config.scatter_size, alpha=config.scatter_alpha)

    soft_sell_signals = df.loc[df[column_name] == ta.soft_sell_signal]
    ax[0].scatter(soft_sell_signals.index, df.loc[df.index.isin(soft_sell_signals.index)]["Close"], label=ta.soft_sell_signal, color=ta.signal_colors[ta.soft_sell_signal], marker=ta.signal_markers[ta.soft_sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)
    ax[1].scatter(soft_sell_signals.index, df.loc[df.index.isin(soft_sell_signals.index)][macd_column_name], label=ta.soft_sell_signal, color=ta.signal_colors[ta.soft_sell_signal], marker=ta.signal_markers[ta.soft_sell_signal], s=config.scatter_size, alpha=config.scatter_alpha)

    utils.prettify_ax(ax[0], title=symbol + prices.price_name, start_date=start_date, end_date=end_date)
    utils.prettify_ax(ax[1], title=symbol + column_name, center=True, start_date=start_date, end_date=end_date)

    utils.prettify_fig(fig)
    fig.savefig(utils.get_file_path(config.ta_graphs_path, "-".join(str(p) for p in period) + macd_graph_filename, symbol=symbol))
    utils.debug(fig)
    return fig, ax

# symbols should be all caps

# TODO: Calls with a more recent date than what was already in the file will delete old data.
# Then, calling for the old date without refresh=True will lack data.
# TODO plot_sma/ema/macd should download data from start_date - period, and pass start_date - period to sma/ema/macd
