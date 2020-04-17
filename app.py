"""
Google API example: https://developers.google.com/sheets/api/quickstart/python


"""
# %%
import support
import support_v2

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

def serve_layout():
    values = support.pull_data()

    data, dates = support.clean_data(values)

    islands, island_data = support.seperate_islands(data)

    rect_dict = support.generate_rects(data)

    all_chart = support.all_chart(islands, island_data, rect_dict)

    minis = support.chart_island_minis(islands, island_data)

    table = support.daily_table(islands, island_data, dates)

    return html.Div(children=[
                dcc.Markdown(children=
                '''
                    # Animal Crossing Stalk Market Tracking

                    A vizualization of several islands' turnip prices over time.

                    To add data to this chart, please use this Google Form: https://forms.gle/mmzoGqMHumFbgzUd7 (right click to open in new tab - apparently MD doesn't want to have a feature for that)
                    
                '''),

                dcc.Graph(
                    id='all-chart',
                    figure=all_chart
                ),

                dcc.Graph(
                    id='minis',
                    figure=minis
                ),

                dcc.Graph(
                    id='table',
                    figure=table
                ),


    ])

# %%
app = dash.Dash(__name__)

server = app.server # the Flask app

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)