# Imports
from dash import Dash

import dash_bootstrap_components as dbc

# Application
app = Dash(__name__)

# Routes
from app import routes
