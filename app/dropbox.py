# Imports
import pandas as pd
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
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
df_col = ['timestamp', 'type', 'level', 'pname', 'message', 'raw_content']


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

# Parse the cmd.NEXT Logs - already
def parse_cmdnext(contents, **kwargs):
    # Can return multiple account types
    id_str = contents['id'].split(':')
    if id_str[2] == 'bitcoin':
        return {
            'add_type': 'BTC',
            'balance': contents['balance'],
            'addresstype': id_str[-1],
            'name': contents['name'],
            'address': contents['freshAddress'],
            'xpub': id_str[-2],
            'path': contents['freshAddressPath']
        }
    elif id_str[2] == 'ethereum':
        return  {
            'add_type': 'ETH',
            'balance': contents['balance'],
            # 'addresstype': id_str[-1], Not required
            'name': contents['name'],
            'address': id_str[-2],
            # 'xpub': id_str[-2] Note Required
            'path': contents['freshAddressPath']
        }
    else:
        return None

def update_address_matrix(matrix, candidate):
        if candidate['add_type'] == 'BTC':
            if not any([True for elem in matrix['BTC'] if candidate['xpub'] in elem.values()]):
                matrix['BTC'].append({
                    'name': candidate['name'],
                    'addresstype': candidate['addresstype'],
                    'xpub': candidate['xpub'],
                    'path': candidate['path'],
                    'balance': candidate['balance']
                })
        elif candidate['add_type'] == 'ETH':
            if not any([True for elem in matrix['ETH'] if candidate['address'] in elem.values()]):
                matrix['ETH'].append({
                    'name': candidate['name'],
                    'address': candidate['address'],
                    'path': candidate['path'],
                    'balance': candidate['balance']
                })

# Main Parse function to parse JSON contents
def parse_contents(filename, contents):

    # Variable definition
    output = {
        'error': False,
        'error_msg': '',
        'address_matrix': {
            'BTC': [],
            'ETH': []
        },
        'modelId': None,
        'deviceVersion': None,
    }


    if 'json' in filename:
        # Assume file is JSON - decode base64 and then decode to utf-8
        raw_data = b64decode(contents.split(',')[1]).decode('utf-8')

        # Debug print to separate uploads
        print(f'Attempting parsing of file: {filename}')

        # Parse data
        raw_data = json.loads(raw_data)
        # output['raw_data'] = raw_data

        # DEBUG - print
        # for idx in range(740,750):
        #    print(f'\n------ {idx} ------')
        #    dict_print(raw_data[idx], 0)

        # Check all lines - Most likely very slow --------
        for idx in range(len(raw_data)):

            # Always extract raw data
            raw_data[idx]['raw_content'] = codecs.decode(
                str(raw_data[idx].copy()), 'unicode_escape'
            )

            # Extract Metadata
            if 'message' in raw_data[idx] and \
            raw_data[idx]['message'] == 'exportLogsMeta':

                # raw_data[idx]['raw_content'] = str(raw_data[idx].copy())

                # Get Release
                output['release'] = raw_data[idx]['release']

                # git_commit
                output['git_commit'] = raw_data[idx]['git_commit']

                # Get user Env
                output['userAgent'] = raw_data[idx]['userAgent']

                # Experimental way to get addresses
                output['accountsIds'] = raw_data[idx]['accountsIds']

            elif 'stack' in raw_data[idx]:
                pass
            elif 'type' in raw_data[idx] and \
            raw_data[idx]['type'] == 'cmd.NEXT' and \
            'data' in raw_data[idx] and raw_data[idx]['data'] is not None:
                if 'type' in raw_data[idx]['data'] and \
                raw_data[idx]['data']['type'] == 'discovered':
                    # DEBUG print
                    # raw_address_data = raw_data[idx]['data']['account']
                    # print(raw_address_data)
                    # print('--'*25)

                    # Get addresses / xpub
                    add_dat = parse_cmdnext(raw_data[idx]['data']['account'])

                    if add_dat is not None:
                        # Debug print
                        print(add_dat)

                        # update matrix
                        update_address_matrix(
                            output['address_matrix'],
                            add_dat
                        )
            elif 'type' in raw_data[idx] and \
            raw_data[idx]['type'] == 'analytics':
                output['modelId'] = raw_data[idx]['data']['modelId']
                output['deviceVersion'] = raw_data[idx]['data']['deviceVersion']

        # Export into DataFrame
        output['df'] = pd.DataFrame(
            raw_data,
            columns=df_col
        )

        # Debug print
        # print(output['df'].head())

    else:
        # This does not seem like a JSON file
        output['error_msg'] = 'This does not seem like a JSON file!'
        print(output['error_msg'])
        err_bool = True



    # Return all the information required to display (df included)
    return output

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

# Callback to update output Div
@app.callback(Output('datatable', 'children'),
              Input('json_data', 'contents'),
              State('json_data', 'filename'),
              State('json_data', 'last_modified'))
def update_output(contents, name, last_modified):
    if contents is not None:

        # Parse contents to be provided to datatable
        output = parse_contents(name, contents)
        # html.Ul([html.Li(x) for x in my_list])
        if 'accountsIds' in output:
            account_ids = html.Ul([html.Li(x) for x in output['accountsIds']])

        btc_table = dbc.Table.from_dataframe(
            pd.DataFrame(output['address_matrix']['BTC']),
            striped=True,
            bordered=True,
            hover=True,
            index=False
        )
        eth_table = dbc.Table.from_dataframe(
            pd.DataFrame(output['address_matrix']['ETH']),
            striped=True,
            bordered=True,
            hover=True,
            index=False
        )
        if 'release' in output:
            release_ver = f'Ledger Live release version: {output["release"]}'
        else:
            release_ver = 'Ledger Live release version: N/A'
        if 'git_commit' in output:
            git_ver = f' / git commit: {output["git_commit"]}'
        else:
            git_ver = ' / git commit: N/A'


        # Table + Information
        return html.Div(children=[
            f'{release_ver}{git_ver}',
            html.Br(),
            f'User Agent: {output["userAgent"]}', html.Br(),
            f'Modeld: {output["modelId"]}', html.Br(),
            f'Device Version: {output["deviceVersion"]}', html.Br(),
            html.Br(),
            'Accounts IDs', html.Br(),
            account_ids,
            html.Br(),
            'BTC Paths', html.Br(),
            btc_table,
            html.Br(),
            'ETH Paths', html.Br(),
            eth_table,
            html.Br(),
            dash_table.DataTable(
                output['df'].to_dict('records'),
                [{"name": i, "id": i} for i in output['df'].columns],
                style_cell={'textAlign': 'left'},
                filter_action='native',
                style_data={
                    'maxWidth': '350px',
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
