
from dash import dcc, html, dash_table, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import backtrader as bt
import backtrader
import pandas as pd
import numpy as np
import joblib
import dash
import ast

max_params = 8
strategy_classes = ['Strategy', 'MetaStrategy', 'SignalStrategy', 'MetaSigStrategy']

dash.register_page(__name__, path = '/', name = 'Home', order = '00')

data = joblib.load('btc.dat')
data_df = data.p.dataname.dropna().round(4)

script_callback_output = [
	Output('alert-dlg', 'is_open', allow_duplicate = True),
	Output('alert-msg', 'children', allow_duplicate = True),
	Output('alert-dlg', 'style', allow_duplicate = True)
] + [
	Output('param-div-{}'.format(i), 'style', allow_duplicate = True) for i in range(max_params)
] + [
	Output('param-label-{}'.format(i), 'children', allow_duplicate = True) for i in range(max_params)
] + [
	Output('param-input-{}'.format(i), 'value', allow_duplicate = True) for i in range(max_params)
] + [
	Output('param-type-{}'.format(i), 'children', allow_duplicate = True) for i in range(max_params)
]

saved_param_info = []
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
	yaxis_tickformat = '~s', yaxis_tickvals = [*range(0, 70000, 10000)],
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
			id = 'main-tab',
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
										dcc.Textarea(id = 'script-input', value = ''),
										html.Div(
											children = [
												html.Button('RESET', id = 'reset-button', n_clicks = 0),
												html.Button('SAVE', id = 'save-button', n_clicks = 0)
											]
										)          								
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
															children = 'Param-{} :'.format(i)
														),
														dcc.Input(
															className = 'param-input',
               												id = 'param-input-{}'.format(i),
															value = '0'
														),
              											html.Label(
                  											className = 'param-type',
															id = 'param-type-{}'.format(i),
															children = 'String'
														)
													]
												) for i in range(max_params)
											]
                      					),
          								html.Button('TEST', id = 'test-button', n_clicks = 0)
									]
								)
							]
                		)
           			]
            	),
				dcc.Tab(label = 'Record', value = 'record', children = [html.Div(id = 'record-div')])
          	],
			value = 'plot'
		),
  		dbc.Alert([html.Label('', id = 'alert-msg')], id = 'alert-dlg', is_open = False, fade = True, duration = 3000)
	],
    className = 'content'
)

def alert_success(msg = '', param_ret = []):
	return [True, msg, {'backgroundColor': '#4CB22C'}] + param_ret

def alert_warning(msg = '', param_ret = 0):
	return [True, msg, {'backgroundColor': '#E98454'}] + param_ret

def alert_error(msg = '', param_ret = 0):
	return [True, msg, {'backgroundColor': '#D35151'}] + param_ret

def alert_hide(param_ret = 0):
	return [False, '', {}] + param_ret

def get_script_param_ret():
	return [{'display': 'none'} for _ in range(max_params)] + [None for _ in range(3 * max_params)]

def is_lower(c):
	return c.isalpha() and c.islower()

def is_upper(c):
    return c.isalpha() and c.isupper()

def titlize(s):
    return s[0].upper() + s[1:].lower()

def render_param_name(name):
	segs, tmp = [], ''
    
	for i in range(len(name) + 1):
		if (
				(
					i > 0 and i < len(name) and
					(
						(is_lower(name[i - 1]) and is_upper(name[i])) or
						(name[i - 1].isdigit() and name[i].isalpha())
					)
				)
				or
				i == len(name)
				or
				name[i] == '_'
			):
			if len(tmp) > 0: segs.append(tmp)
			tmp = ''

		if i < len(name) and name[i] != '_': tmp += name[i]

	return ' '.join([titlize(s) for s in segs])

def compile_script(script):
	param_info = []
	
	try:
		code = compile(script, filename = '<string>', mode = 'exec')		
	except SyntaxError as e:
		return -1, e, None

	tree = ast.parse(script)
	bt_aliases, class_defs, constructor_def = {'backtrader'}, [], None
 
	for node in tree.body:
		if isinstance(node, ast.Import):
			for n in node.names:
				if n.name == 'backtrader': bt_aliases.add(n.asname or n.name)
 
	for node in tree.body:
		if isinstance(node, ast.ClassDef):
			for b in node.bases:		
				if isinstance(b, ast.Attribute) and (b.attr in strategy_classes) and (b.value.id in bt_aliases): class_defs.append(node)				

	if len(class_defs) == 0:
		return -2, None, None
	elif len(class_defs) > 1:
		return -3, len(class_defs), None

	for node in class_defs[0].body:
		if isinstance(node, ast.FunctionDef) and node.name == '__init__':
			constructor_def = node
			break
	
	if constructor_def is not None:
		for param in constructor_def.args.args[1:]:
			param_name = param.arg
			param_type = 'Variant'

			if param.annotation is not None:
				if param.annotation.id == 'str':
					param_type = 'String'
				elif 'float' in param.annotation.id.lower():
					param_type = 'Float'
				elif 'int' in param.annotation.id.lower():
					param_type = 'Integer'
			
			param_info.append([param_name, param_type, ''])

		def_vals = [d.value for d in constructor_def.args.defaults]

		for i in range(len(param_info) - len(def_vals), len(param_info)):
			param_info[i][-1] = def_vals[len(def_vals) - len(param_info) + i]

	return 0, (class_defs[0].name, code), param_info

def compare_param_info(param_info):
    global saved_param_info
    
    if len(saved_param_info) != len(param_info): return False
    
    for p1, p2 in list(zip(saved_param_info, param_info)):
        if p1[0] != p2[0]: return False
        if p1[1] != p2[1]: return False
    
    return True

@callback(
	script_callback_output,
	Input('save-button', 'n_clicks'),
	[State('script-input', 'value')],
	prevent_initial_call = True
)
def on_save_clicked(n_clicks, script):
	global saved_param_info

	param_ret =  get_script_param_ret()
	if n_clicks == 0: return alert_hide(param_ret)
	
	err, res, pi = compile_script(script)
	saved_param_info.clear()
	
	if err == 0:
		saved_param_info.extend(pi)

		for i in range(len(pi)):
			param_ret[i] = {'display': 'block'}
			param_ret[max_params + i] = render_param_name(pi[i][0]) + ' :'
			param_ret[2 * max_params + i] = pi[i][2]
			param_ret[3 * max_params + i] = '(' + pi[i][1] + ')'

		return alert_success('Saved Successfully.', param_ret)
	elif err == -1:
		return alert_error('Compilation failed: {}'.format(res), param_ret)
	elif err == -2:
		return alert_error('Strategy class definition not found.', param_ret)
	elif err == -3:
		return alert_error('Expected only one strategy class definition but got {} definitions.'.format(res), param_ret)

@callback(
	script_callback_output + [Output('script-input', 'value')],
	Input('reset-button', 'n_clicks'),
	prevent_initial_call = True
)
def on_reset_clicked(n_clicks):
	param_ret =  get_script_param_ret() + ['']
	if n_clicks == 0: return alert_hide(param_ret)

	with open('code.txt', 'r') as fp:
		script = fp.read()

	return on_save_clicked(n_clicks, script) + [script]

@callback(
    [
		Output('alert-dlg', 'is_open', allow_duplicate = True),
		Output('alert-msg', 'children', allow_duplicate = True),
		Output('alert-dlg', 'style', allow_duplicate = True),
		Output('main-tab', 'value', allow_duplicate = True),
		Output('record-div', 'children')
	],
	Input('test-button', 'n_clicks'),
	[
		State('script-input', 'value')
	] + [
		State('param-input-{}'.format(i), 'value') for i in range(max_params)
	],
	prevent_initial_call = True
)
def on_test_clicked(n_clicks, script, *args):
	param_ret =  ['script', None]
	if n_clicks == 0: return alert_hide(param_ret)

	err, res, pi = compile_script(script)

	if err != 0:
		return alert_error('Error found in the script. Save and retry.', param_ret)
	elif not compare_param_info(pi):
		return alert_error('The script has been changed. Save and retry.', param_ret)

	clsname, code = res
	exec(code)

	cerebro = bt.Cerebro()
	kwargs = {}
 
	for i, p in enumerate(saved_param_info):
		kwargs[p[0]] = args[i]

	cerebro.addstrategy(locals()[clsname], **kwargs)
	cerebro.adddata(data)
	cerebro.addanalyzer(bt.analyzers.Transactions, _name = 'trans')

	try:
		result = cerebro.run()
	except Exception as e:
		return alert_error('Runtime error: {}'.format(e), param_ret)

	transactions = result[0].analyzers.trans.get_analysis()
	if len(transactions) % 2 != 0: transactions.popitem()

	df = pd.DataFrame(columns = ['ID', 'Type', 'Signal', 'Date', 'Price'])
	trans_dates = list(transactions.keys())

	for i in range(0, len(transactions), 2):
		enter_date, exit_date = trans_dates[i], trans_dates[i + 1]
		
		enter_position, enter_price, _, _, _, enter_info = transactions[enter_date][0]
		_, exit_price, _, _, _, exit_info = transactions[exit_date][0]
		
		enter_signal = enter_info['signal'] if len(enter_info['signal']) > 0 else 'Long' if enter_position > 0 else 'Short'
		exit_signal = exit_info['signal'] if len(exit_info['signal']) > 0 else 'Long' if enter_position < 0 else 'Short'
  
		row = {
			'ID': i // 2 + 1,
			'Type': 'Enter Long' if enter_position > 0 else 'Enter Short',
			'Signal': enter_signal,
			'Date': enter_date.strftime('%Y-%m-%d'),			
			'Price': '{:.4f}'.format(enter_price)
		}
		df = pd.concat([df, pd.Series(row).to_frame().T], ignore_index = True)

		row = {
			'ID': '',
			'Type': 'Exit Long' if enter_position > 0 else 'Exit Short',
			'Signal': exit_signal,
			'Date': exit_date.strftime('%Y-%m-%d'),			
			'Price': '{:.4f}'.format(exit_price)
		}
		df = pd.concat([df, pd.Series(row).to_frame().T], ignore_index = True)
	
	table = dash_table.DataTable(
		df.to_dict('records'), [{'name': i, 'id': i} for i in df.columns],
		fixed_rows = dict(headers = True),
		style_table = {
			'height': '600px',
			'max-height': '600px',
			'width': '1000px'
		},
		style_data_conditional = [{
			'if': {
                'row_index': [x for x in range(len(df)) if x % 4 > 1]
            },
			'backgroundColor': 'rgb(230, 230, 230)',
		}],
		style_cell_conditional = [
			{
				'if': {'column_id': c},
				'textAlign': 'right'
			} for c in ['Price']
		],
		style_header = {
			'fontWeight': 'bold',
			'textAlign': 'center'
		}
	)
	return alert_success('Backtest finished.', ['record', table])
