"""
Google API example: https://developers.google.com/sheets/api/quickstart/python


"""
# %%
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pandas as pd
from datetime import datetime as dt
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html

# %%

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# %%

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1dWwo0B9tLKLXh-NNOiNVgQUdS02978h0E-o6YqzrnOk' # google forms
# old data '1zu3U5va_QaxtU5yVGvyumtR0A747O5C-7kYTMEhxQzE' # old data 
RANGE = 'data!A:E'

# def main():
"""Shows basic usage of the Sheets API.
Prints values from a sample spreadsheet.
"""
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)

# %%
# Call the Sheets API
sheet = service.spreadsheets()

result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()

values = result.get('values', [])

# %%
# new col names
col_names = ['timestamp','island','price','time_of_day', 'date_replacement']

# import values to pandas
data = pd.DataFrame(values[1:], columns=col_names)

# clean data

date = []
# replace timestamp with date, if applicable
for t,tod,d in zip(data['timestamp'], data['time_of_day'], data['date_replacement']):
    if d is not None:
        if tod == 'Morning':
            date.append(dt.strptime(d + ' ' + '9:00',  '%m/%d/%Y %H:%M'))
        elif tod == 'Afternoon':
            date.append(dt.strptime(d + ' ' + '15:00',  '%m/%d/%Y %H:%M'))
    elif d is None:
        temp = dt.strptime(t, '%m/%d/%Y %H:%M:%S')
        if tod == 'Morning':
            date.append(dt.strptime(str(temp.strftime('%m/%d/%Y')) + ' ' + '9:00', '%m/%d/%Y %H:%M'))
        elif tod == 'Afternoon':
            date.append(dt.strptime(str(temp.strftime('%m/%d/%Y')) + ' ' + '15:00',  '%m/%d/%Y %H:%M'))

data['date']=date

# sort on new column date  


# strip white space off island names
islands = [ str.strip(i) for i in data['island']]

data['island'] = islands

# %% 
# create the rectangles to go behind every other date - maybe every even date to simplify things?


# %%
# seperate data into the different island groups
# create a list of island data
island_data = []
islands = data['island'].unique() # maybe sort alphabetically?
# trim extra spaces

for i in islands:
    island_data.append(data[data['island']==i])

# %%
# create a plotly 
fig = go.Figure()

for i,name in zip(island_data, islands):
    fig.add_trace(go.Scatter(x=i['date'], y=i['price'],  name=name))
 
fig.update_layout(
    title = "Sow Joan's Stalk Market Tracking",
    xaxis_title='date / time of day',
    yaxis_title='turnip sale price'
)

# fig.update_layout(shapes=rect_dicts)



# highlight every other day witht he background block thing that I did in the sleep chart (should be even easier tbh)

# fig.show()

# %%
# do the dash and figure how to pop it on my website

# select date ranges

app = dash.Dash(__name__)

server = app.server # the Flask app

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(children=[
    dcc.Markdown(children=
    '''
    # Animal Crossing Stalk Market Tracking

    A vizualization of several islands' turnip prices over time.

    To add data to this chart, please use this Google Form: https://forms.gle/mmzoGqMHumFbgzUd7 (right click to open in new tab - apparently MD doesn't want to have a feature for that)
    
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)