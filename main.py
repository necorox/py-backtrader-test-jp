from datetime import datetime, timedelta

import backtrader as bt
import pandas_datareader as web


class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


class SmaCrossStrategy(bt.Strategy):
    params = (('pfast', 10), ('pslow', 30),)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataClose = self.datas[0].close
        self.order = None
        self.size = 100

        sma1 = bt.ind.SMA(period=self.params.pfast)
        sma2 = bt.ind.SMA(period=self.params.pslow)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                cost = self.size * self.dataClose[0]
                self.log(
                    f'BUY CREATE, Cash: {self.broker.getvalue():.2f}, Price: {self.dataClose[0]:.2f}, Size: {self.size}, Cost: {cost:.2f}')
                self.buy(size=self.size)  # enter long
        elif self.crossover < 0:
            self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            self.log('Order Submitted/Accepted')
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')


if __name__ == "__main__":
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(10000000.0)

    # 銘柄を指定する
    # 9433.JP: KDDI
    code = '9433.JP'

    # データを取得する
    data = web.get_data_stooq(code, start=datetime.now() - timedelta(days=365), end=datetime.now())

    # datafeedを作成する
    datafeed = bt.feeds.PandasData(dataname=data)

    # cerebroにdatafeedを追加する
    cerebro.adddata(datafeed)

    # 戦略を追加する
    cerebro.addstrategy(SmaCrossStrategy)

    # テストを実行する
    cerebro.run()

    # 結果を表示する
    cerebro.plot(style='candlestick')
