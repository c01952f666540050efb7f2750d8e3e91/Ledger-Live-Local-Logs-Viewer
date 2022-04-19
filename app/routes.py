# Imports
from app import app
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
# from dash_bootstrap_templates import ThemeSwitchAIO

# Page Components
from app.dropbox import *

# Version
version = '0.00c'
title = f'Ledger Live Local Logs Viewer {version}'

# Application set up
app.title = title

# Theme data
url_theme1 = dbc.themes.FLATLY
url_theme2 = dbc.themes.DARKLY

# Application Layout
app.layout = html.Div([
    html.H1(title),
    #ThemeSwitchAIO(aio_id="theme", themes=[url_theme1, url_theme2],),
    drop_box,
    html.Br(),
    html.Div(children=[
        # Current File
        html.P(id='filename', children=[]),
        # Last Modified
        html.P(id='datetime-print', children=[]),
        html.Br(),
        # Table
        html.Div(
            id='datatable',
            children=[]
        )
    ])
])
