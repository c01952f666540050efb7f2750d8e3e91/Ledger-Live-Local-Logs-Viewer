# Imports
import pandas as pd
from dash import html, dcc, dash_table
from app import app
from dash.dependencies import Input, Output, State
from datetime import datetime
import json
from base64 import b64decode
import codecs

# DEBUG - Test settings to visualise entire Pandas dataframe
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Static Data
df_col = ['timestamp', 'level', 'pname', 'message', 'raw_content']

# Drop Box for Files
drop_box = html.Div([
    dcc.Upload(
        id='json_data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Click here to Select a File')
        ]),
        # Style
        style= {
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Multiple Files
        multiple = False
    )
])

# DEBUG - recursive function to print nested dictionary
def dict_print(input_dict, level):
    for key in input_dict.keys():
        if type(input_dict[key]) is dict:
            print('\t'*level, end='')
            print(f'{key} //')
            dict_print(input_dict[key], level+1)
        else:
            print('\t'*level, end='')
            print(f'{key} // {input_dict[key]}')


# Function to parse JSON contents
def parse_contents(filename, contents):

    # Variable definition
    output = {
        'error': False,
        'error_msg': '',
        'raw_data': {}
    }

    try: # Try
        if 'json' in filename:
            # Assume file is JSON - decode base64 and then decode to utf-8
            raw_data = b64decode(contents.split(',')[1]).decode('utf-8')

            # Debug print to separate uploads
            print(f'Attempting parsing of file: {filename}')

            # Parse data
            raw_data = json.loads(raw_data)
            output['raw_data'] = raw_data

            for idx in range(20):
                # DEBUG - print
                print(f'\n------ {idx} ------')
                dict_print(raw_data[idx], 0)

            # Check all lines - Most likely very slow
            for idx in range(len(raw_data)):

                # Extract Metadata
                if raw_data[idx]['message'] == 'exportLogsMeta':
                    # raw_data[idx]['raw_content'] = str(raw_data[idx].copy())
                    raw_data[idx]['raw_content'] = codecs.decode(
                        str(raw_data[idx].copy()), 'unicode_escape'
                    )

                    # Get Release
                    output['release'] = raw_data[idx]['release']

                    # git_commit
                    output['git_commit'] = raw_data[idx]['git_commit']

                    # Get user Env
                    output['userAgent'] = raw_data[idx]['userAgent']

                elif 'stack' in raw_data[idx]:
                    # raw_data[idx]['raw_content'] = str(raw_data[idx].copy())
                    raw_data[idx]['raw_content'] = codecs.decode(
                        str(raw_data[idx].copy()), 'unicode_escape'
                    )

            # Export into DataFrame
            output['df'] = pd.DataFrame(
                raw_data,
                columns=df_col
            )
            print(output['df'].head())

        else:
            # This does not seem like a JSON file
            output['error_msg'] = 'This does not seem like a JSON file!'
            print(output['error_msg'])
            err_bool = True

    except Exception as e: # Except
        # If not JSON - Print exception
        print('Something Went Wrong!')
        print(e)


    # Return all the information required to display (df included)
    return output

# Callback to update output Div
@app.callback(Output('datatable', 'children'),
              Input('json_data', 'contents'),
              State('json_data', 'filename'),
              State('json_data', 'last_modified'))
def update_output(contents, name, last_modified):
    if contents is not None:

        # Parse contents to be provided to datatable
        output = parse_contents(name, contents)

        # Table + Information
        return html.Div(children=[
            f'Ledger Live release version: {output["release"]}',
            f' / git commit {output["git_commit"]}',
            html.Br(),
            f'User Agent: {output["userAgent"]}',
            html.Br(),
            'BTC xpub: ',
            html.Br(),
            # f'ETH Addresses: {output["AccountsIds"]}',
            html.Br(),
            dash_table.DataTable(
                output['df'].to_dict('records'),
                [{"name": i, "id": i} for i in output['df'].columns],
                style_cell={'textAlign': 'left'},
                filter_action='native',
                style_data={
                    'maxWidth': '450px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px'
                    }
                )
            ]
        )
    else:
        return ''

# Callback for last modified
@app.callback(Output('datetime-print', 'children'),
              Input('json_data', 'contents'),
              State('json_data', 'filename'),
              State('json_data', 'last_modified'))
def update_last_modified(contents, name, last_modified):
    if contents is not None:
        ts = int(last_modified)
        dt_str = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        return f'Last modified - UTC: {last_modified} / Datetime: {dt_str}'
    else:
        return f'Last modified - UTC: None / Datetime: None'

# Callback for filename
@app.callback(Output('filename', 'children'),
              Input('json_data', 'contents'),
              State('json_data', 'filename'),
              State('json_data', 'last_modified'))
def update_filename(contents, name, last_modified):
    if contents is not None:
        return f'Currently viewing file: {name}'
    else:
        return f'Currently viewing file: None'
