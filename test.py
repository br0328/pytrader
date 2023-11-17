
import backtrader as bt
import pandas as pd
import joblib

is_local_data = True

class SmaCross(bt.SignalStrategy):
    def __init__(self, x1 : str, x2 : int):
        sma1, sma2 = bt.ind.SMA(period = 10), bt.ind.SMA(period = 30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)
        
        print('Hey! Initialized with x1={} and x2={}'.format(x1, x2))

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

df = pd.DataFrame(columns = ['ID', 'EnterDate', 'Position', 'EnterPrice', 'ExitDate', 'ExitPrice'])
trans_dates = list(transactions.keys())

for i in range(0, len(transactions), 2):
    enter_date, exit_date = trans_dates[i], trans_dates[i + 1]
    
    enter_position, enter_price, _, _, _ = transactions[enter_date][0]
    _, exit_price, _, _, _ = transactions[exit_date][0]
    
    row = {
        'ID': i // 2 + 1,
        'EnterDate': enter_date.strftime('%Y-%m-%d'),
        'Position': 'Long' if enter_position > 0 else 'Short',
        'EnterPrice': '{:.4f}'.format(enter_price),
        'ExitDate': exit_date.strftime('%Y-%m-%d'),
        'ExitPrice': '{:.4f}'.format(exit_price)
    }
    df = pd.concat([df, pd.Series(row).to_frame().T], ignore_index = True)

print(df)
