# Imports
from app import app
from dash import html, dcc

# Page Components
from app.dropbox import *

# Version
version = '0.00b'
title = f'Ledger Live Local Logs Viewer {version}'

# Application set up
app.title = title

# search_bar = 'None'

# Application Layout
app.layout = html.Div([
    html.H1(title),
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
