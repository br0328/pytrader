
from dash import dcc, html, callback, Output, Input, State
import plotly.graph_objects as go
import backtrader as bt
import pandas as pd
import numpy as np
import joblib
import dash

dash.register_page(__name__, path = '/', name = 'Home', order = '00')

data = joblib.load('btc.dat')
data_df = data.p.dataname.dropna().round(4)

fig = go.Figure()

fig.add_trace(go.Candlestick(
		x = data_df.index,
		open = data_df['Open'], high = data_df['High'], low = data_df['Low'], close = data_df['Close'],
		increasing_line_color = 'green', decreasing_line_color = 'red'
	)
)
fig.update_xaxes(
	rangeslider_visible = False,
	range = [data_df.index[0], data_df.index[-1]]
)
fig.update_yaxes(type = 'log')

fig.update_layout(
	yaxis_tickformat = "~s", yaxis_tickvals = [*range(0, 70000, 10000)],
	height = 640,
	margin = dict(t = 40, b = 40, r = 100),
	showlegend = False
)

layout = html.Div(
    [
		html.Div(
			[
				html.H1('PEMBE BACKTRADER'),
				html.H2('Proof of Concept')
			],
			className = 'header'
		),
		dcc.Tabs(
			className = 'main_tab',
			children = [
				dcc.Tab(label = 'Plot', value = 'plot', children = [dcc.Graph(figure = fig, className = 'plot-graph')]),
				dcc.Tab(label = 'Script', value = 'script', children =
            		[
        				html.Div(
							className = 'tab-script',
							children = [
								html.Div(
									className = 'left-div',
									children = [
										dcc.Textarea(id = 'script-input', value = 'Hello!'),
          								html.Button('SAVE', id = 'save-button', n_clicks = 0)
									]
								),
        						html.Div(
									className = 'right-div',
									children = [
										html.Div(
              								className = 'setting-panel',
											children = [
												html.Div(
													className = 'param-div',
													id = 'param-div-{}'.format(i),
													children = [
														html.Label(
                  											className = 'param-label',
															id = 'param-label-{}'.format(i),
															children = 'Param-{}'.format(i)
														)
													]
												) for i in range(7)
											]
                      					),
          								html.Button('TEST', id = 'test-button', n_clicks = 0)
									]
								)
							]
                		)
           			]
            	),
				dcc.Tab(label = 'Record', value = 'record', children = [html.Div(className = 'tab-record')])
          	],
			value = 'script'
		)
	],
    className = 'content'
)
