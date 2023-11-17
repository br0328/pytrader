
from dash import dcc, html, dash_table, callback, Output, Input, page_container
import dash_bootstrap_components as dbc
import pandas as pd
import dash
import os

app = dash.Dash(__name__, use_pages = True, external_stylesheets = [dbc.themes.SANDSTONE])

app.title = 'PEMBE POC'
app.layout = html.Div([
    page_container
])

app.run(debug = False, host = 'localhost', port = 1123)
