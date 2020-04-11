import pickle
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pandas as pd
import numpy as np

from datetime import datetime as dt
from datetime import timedelta

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html

# %%
def pull_data():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = '1dWwo0B9tLKLXh-NNOiNVgQUdS02978h0E-o6YqzrnOk' # google forms
    # old data '1zu3U5va_QaxtU5yVGvyumtR0A747O5C-7kYTMEhxQzE' # old data 
    RANGE = 'data!A:E'

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

    # Call the Sheets API
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()

    return result.get('values', [])

def clean_data(values):
    # in the future, can we determine which data is new?

    # new col names
    col_names = ['timestamp','island','price','tod', 'date_replacement']

    # import values to pandas
    data = pd.DataFrame(values[1:], columns=col_names)

    # clean dates
    date = []
    # replace timestamp with date, if applicable
    for t,tod,d in zip(data['timestamp'], data['tod'], data['date_replacement']):
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

    # new date column for the viz
    data['date']=date

    # strip white space off island names
    islands = [ str.strip(i) for i in data['island']]

    # reassign cleaned islands
    data['island'] = islands

    return data

def seperate_islands(data):
    # seperate data into the different island groups
    # create a list of island data
    island_data = []
    islands = np.sort(data['island'].unique())
    # islands = islands.sort()
    # maybe sort alphabetically?

    for i in islands:
        island_data.append(data[data['island']==i])

    return islands, island_data
    
def generate_rects(data):
    # create the rectangles to go behind every other date - maybe every even date to simplify things?
    rect_dict = []

    date_only = [ d.date() for d in data['date'] ]

    dates = pd.DataFrame(date_only)[0].unique()
    dates = np.append(dates, [dates[-1] + timedelta(days=1)])
    dates = pd.DataFrame(dates)

    for i in range(len(dates[0])-1):
        if dates[0].iloc[i].day % 2 == 0:
            rect_dict.append({
                'type':"rect",
                # x-reference is assigned to the x-values
                'xref':"x",
                # y-reference is assigned to the plot paper [0,1]
                'yref':"paper",
                'x0':dates[0].iloc[i] + timedelta(hours=0, minutes=0),
                'y0':0,
                'x1':dates[0].iloc[i+1] + timedelta(hours=0, minutes=0),
                'y1':1,
                'fillcolor':'rgba(208, 208, 208, 1)',
                'opacity':0.5,
                'layer':"below",
                'line_width':0,
            })
        else:
            rect_dict.append({
                'type':"rect",
                # x-reference is assigned to the x-values
                'xref':"x",
                # y-reference is assigned to the plot paper [0,1]
                'yref':"paper",
                'x0':dates[0].iloc[i] + timedelta(hours=0, minutes=0),
                'y0':0,
                'x1':dates[0].iloc[i+1] + timedelta(hours=0, minutes=0),
                'y1':1,
                'fillcolor':'rgba(230, 230, 230, 1)',#'rgba(43, 176, 233, 1)',
                'opacity':0.5,
                'layer':"below",
                'line_width':0,
            })
    return rect_dict

def all_chart(islands, island_data, rect_dict):
    # create a plotly 
    fig = go.Figure()

    for i,name in zip(island_data, islands):
        fig.add_trace(go.Scatter(x=i['date'], y=i['price'],  name=name))
    
    fig.update_layout(
        title = "Sow Joan's Stalk Market Tracking",
        xaxis_title='date / time of day',
        yaxis_title='turnip sale price'
    )

    fig.update_layout(
        shapes=rect_dict, 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def chart_island_minis(islands, island_data):

    rows = 2
    cols = 3

    titles = islands

    fig = make_subplots(
            rows=rows, 
            cols=cols,
            # shared_xaxes=True,
            # shared_yaxes=True,
            subplot_titles=titles)

    # for loop. figure out subplots again
    r=1
    c=1
    for i,d in zip(islands, island_data):
        #add a sub plot
        add_plot(fig,i,d,r,c)
        c=c+1
        if c % 4==0:
            r=r+1
            c=1

    
    fig.update_layout(
        showlegend=False,
        # xaxis_rangeslider_visible=False,
        # height=1000
        )
    
    return fig

def add_plot(fig,island,data,row,col):
    fig.add_trace(bar_chart(island, data), row=row, col=col)

def bar_chart(island, data):
    temp_data = data.copy()
    date_only = [ d.date() for d in temp_data['date'] ]
    temp_data['date_only'] = date_only 
    dates = temp_data['date_only'].unique()

    # ensure open and close are the same length
    for d in dates:
        temp = temp_data.loc[temp_data['date_only']==d]

        if temp.shape[0] < 2 and temp.shape[0] > 0:
            if temp['tod'].iloc[0] == 'Morning':
                temp_data = temp_data.append(dict(date=d, tod='Afternoon',price=temp['price'].iloc[0]), ignore_index=True)
            elif temp['tod'].iloc[0] == 'Afternoon':
                temp_data = temp_data.append(dict(date=d, tod='Morning',price=temp['price'].iloc[0]), ignore_index=True)
    # add missing date / tod / price = None

    temp_data = temp_data.sort_values(by='date')

    open_data = temp_data.loc[temp_data['tod'] == 'Morning', 'price']
    close_data = temp_data.loc[temp_data['tod'] == 'Afternoon', 'price']

    high_data = [ max(o, c) for o,c in zip(open_data, close_data) ]
    low_data = [ min(o, c) for o,c in zip(open_data, close_data) ]

    fig = go.Box(
                x=temp_data['date_only'],
                y=temp_data['price']
            )

    # fig = go.Candlestick(
    #             x=temp_data['date_only'],
    #             open=open_data,
    #             high=high_data,
    #             low=low_data,
    #             close=close_data
    #         )

    #titles, island name
    #axis titles

    return fig