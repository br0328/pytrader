
import backtrader as bt
import pandas as pd
import joblib

is_local_data = True
            
class SmaCross(bt.Strategy):
    def __init__(self, x1 : str, x2 : int = 0):
        sma1, sma2 = bt.ind.SMA(period = 10), bt.ind.SMA(period = 30)
        self.crossover = bt.ind.CrossOver(sma1, sma2)
        
        print('Hey! Initialized with x1={} and x2={}'.format(x1, x2))
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(signal = 'Long')
            elif self.crossover < 0:
                self.sell(signal = 'Short')
            else:
                self.buy(signal = 'Semi-Long')
        elif self.position.size > 0:
            if self.crossover < 0:
                self.close(signal = 'Short')
            elif self.crossover == 0:
                self.close(signal = 'Semi-Short')
        elif self.position.size < 0:
            if self.crossover > 0:
                self.close(signal = 'Long')
            elif self.crossover == 0:
                self.close(signal = 'Semi-Long')

cerebro = bt.Cerebro()

kwargs = {'x1': 'ABC', 'x2': 33}
cerebro.addstrategy(SmaCross, **kwargs)

if not is_local_data:
    import yfinance as yf
    
    data = bt.feeds.PandasData(dataname = yf.download('MSFT', '2015-07-06', '2021-07-01', auto_adjust = True))
    joblib.dump(data, 'msft.dat')
else:
    data = joblib.load('msft.dat')

cerebro.adddata(data)
cerebro.addanalyzer(bt.analyzers.Transactions, _name = "trans")

result = cerebro.run()

transactions = result[0].analyzers.trans.get_analysis()
if len(transactions) % 2 != 0: transactions.popitem()

df = pd.DataFrame(columns = ['ID', 'EnterDate', 'Position', 'EnterPrice', 'EnterSignal', 'ExitDate', 'ExitPrice', 'ExitSignal'])
trans_dates = list(transactions.keys())

for i in range(0, len(transactions), 2):
    enter_date, exit_date = trans_dates[i], trans_dates[i + 1]
    
    enter_position, enter_price, _, _, _, enter_info = transactions[enter_date][0]
    _, exit_price, _, _, _, exit_info = transactions[exit_date][0]
    
    row = {
        'ID': i // 2 + 1,
        'EnterDate': enter_date.strftime('%Y-%m-%d'),
        'Position': 'Long' if enter_position > 0 else 'Short',
        'EnterPrice': '{:.4f}'.format(enter_price),
        'EnterSignal': enter_info['signal'],
        'ExitDate': exit_date.strftime('%Y-%m-%d'),
        'ExitPrice': '{:.4f}'.format(exit_price),
        'ExitSignal': exit_info['signal']
    }
    df = pd.concat([df, pd.Series(row).to_frame().T], ignore_index = True)

df.to_csv('record.csv', index = False)
print(df)
