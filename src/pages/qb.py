import dash
from dash import Dash, html, dcc, dash_table, callback, Output, Input
import plotly.express as px
import pandas as pd
from dash.dash_table import DataTable
from dash.dash_table.Format import Format, Scheme, Trim
import plotly.graph_objects as go
import numpy as np

import nfl_data_py as nfl
import dash_bootstrap_components as dbc

# bring in nfl play data for the previous seasons
player_stats = nfl.import_weekly_data(years=[2019,2020,2021,2022,2023], columns=['player_display_name', 'position', 'season_type', 'season', 'week', 'recent_team', 'opponent_team'
                                                                           , 'completions', 'attempts', 'passing_yards', 'passing_tds', 'interceptions', 'sacks', 'fantasy_points', 'fantasy_points_ppr'],
                                                                           downcast=True)

player_stats = player_stats.loc[(player_stats['position'] == 'QB') & (player_stats['season_type'] == 'REG')]

# join the season stats data and the player info data
player_stats['new_week'] = player_stats['week'].astype(str)
player_stats['new_week'] = np.where(player_stats['new_week'].str.len()==1, '0' + player_stats['new_week'], player_stats['new_week'])
player_stats['games'] = 1
player_stats['season_sort_order'] = player_stats['season'].astype(str) + '.' + player_stats['new_week'].astype(str)


player_stats = player_stats.sort_values(['player_display_name', 'season_sort_order'])

# delete the previous dataframes to keep memory down

dfr = player_stats.pivot_table(index=['player_display_name', 'position', 'season', 'season_type'], values=['games', 'completions', 'attempts', 'passing_yards', 'passing_tds', 'interceptions', 'sacks', 'fantasy_points', 'fantasy_points_ppr'],
                               aggfunc='sum')

dfr = dfr.dropna()
dfr.reset_index(inplace=True)

dfr = dfr[dfr['attempts'] >= 100]
# unpivot the data in order to render graph axis with selected categories
dfr = dfr.melt(id_vars=['season', 'player_display_name', 'position'],
                                 var_name='Category',
                                 value_vars=['games', 'completions', 'attempts',
                                    'passing_yards', 'passing_tds', 'interceptions', 'sacks','fantasy_points', 'fantasy_points_ppr'])

player_stats = player_stats.melt(id_vars=['season', 'week', 'player_display_name', 'position', 'recent_team', 'opponent_team', 'season_sort_order'],
                                 var_name='Category',
                                 value_vars=['completions', 'attempts', 'passing_yards', 'passing_tds',
                                             'interceptions', 'sacks','fantasy_points', 'fantasy_points_ppr'])

column_order = ['season', 'player_display_name', 'position', 'games', 'completions', 'attempts',
                                    'passing_yards', 'passing_tds', 'interceptions', 'sacks','fantasy_points', 'fantasy_points_ppr']
 
dash.register_page(__name__, name = 'Quarterbacks', order = 1)
# app = Dash(__name__)
# server = app.server

layout = dbc.Container([html.H1("Fantasy Football POC"), html.P("Proof of concept to visualize player stats dynamically"),
                    html.H2("Skill Players' Stats"), 
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'completions',
                            id='qb-crossfilter-xaxis-column'
                        ), html.P("x-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'passing_tds',
                            id='qb-crossfilter-yaxis-column'
                        ), html.P("y-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'fantasy_points_ppr',
                            id='qb-crossfilter-zaxis-column'
                        ), html.P("z-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div(dcc.Graph(
                          id='qb-crossfilter-indicator-scatter',
                          hoverData={'points':[{'customdata': 'Patrick Mahomes'}]}
                            ),
                            style={'width': '49%', 'height':'100%', 'display': 'inline-block', 'padding': '0 20'}),
                    html.Div([dcc.Graph(id='qb-x-time-series'),
                            dcc.Graph(id='qb-y-time-series'),
                            dcc.Graph(id='qb-z-time-series')],
                            style={'display': 'inline-block', 'width': '49%'})
                    ,
                    html.Br(),
                    html.Div([html.P("Season"),
                            dcc.Slider(
                                    dfr['season'].min(),
                                    dfr['season'].max(),
                                    step=1,
                                    id='qb-crossfilter-year-slider',
                                    value=dfr['season'].max(),
                                    marks={str(year): str(year) for year in dfr['season'].unique()}
                                )], style={'width': '49%', 'padding': '0px 20px 20px 20px'}
                            ),
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            player_stats['player_display_name'].unique(),
                                'Patrick Mahomes',
                                id='qb-select-player-list'
                                )
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Br(),
                    html.Div(id='qb-display-player-stats'),
                    html.Br(),
                    html.Footer("**Github.com - NFLVerse")
                ]
            )
          
 

# callbacks are used to update the graphs and datatable, based on the user's selection
# callbacks are used to update the graphs and datatable, based on the user's selection
@callback(
    Output('qb-crossfilter-indicator-scatter', 'figure'),
    Input('qb-crossfilter-xaxis-column', 'value'),
    Input('qb-crossfilter-yaxis-column', 'value'),
    Input('qb-crossfilter-zaxis-column', 'value'),
    Input('qb-crossfilter-year-slider', 'value'))
def qb_update_graph(xaxis_column_name, yaxis_column_name,zaxis_column_name,
                 year_value):
    
    dff = dfr[dfr['season'] == year_value] 
                        
    fig = px.scatter_3d(x=dff[dff['Category'] == xaxis_column_name]['value'],
            y=dff[dff['Category'] == yaxis_column_name]['value'],
            z=dff[dff['Category'] == zaxis_column_name]['value'],
            hover_name=dff[dff['Category'] == yaxis_column_name]['player_display_name']
            )
    
    fig.update_scenes(xaxis_title=xaxis_column_name,
                      yaxis_title=yaxis_column_name,
                      zaxis_title=zaxis_column_name) 
    
    fig.update_traces(customdata=dff[dff['Category'] == yaxis_column_name]['player_display_name'], marker_size=5)

 
    fig.update_layout(height = 675, margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest', showlegend=False)
    fig.update_layout(showlegend = False)
 
    return fig
 
 
def qb_create_time_series(dff, title):
 
    fig = px.line(dff, x='week', y='value', color='season')
 
    fig.update_traces(mode='lines+markers')
 
    fig.update_xaxes(showgrid=False)
 
    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)
 
    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})
 
    return fig
 
 
@callback(
    Output('qb-x-time-series', 'figure', allow_duplicate=True),
    Input('qb-crossfilter-indicator-scatter', 'hoverData'),
    Input('qb-crossfilter-xaxis-column', 'value'),
    prevent_initial_call=True)
def qb_update_x_timeseries_from_plot(hoverData, xaxis_column_name):
    player_name = hoverData['points'][0]['customdata']
    dff = player_stats[player_stats['player_display_name'] == player_name]
    dff = dff[dff['Category'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(player_name, xaxis_column_name)
    return qb_create_time_series(dff, title)

 
@callback(
    Output('qb-y-time-series', 'figure', allow_duplicate=True),
    Input('qb-crossfilter-indicator-scatter', 'hoverData'),
    Input('qb-crossfilter-yaxis-column', 'value'),
    prevent_initial_call=True)
def qb_pdate_y_timeseries_from_plot(hoverData, yaxis_column_name):
    dff = player_stats[player_stats['player_display_name'] == hoverData['points'][0]['customdata']]
    dff = dff[dff['Category'] == yaxis_column_name]
    return qb_create_time_series(dff, yaxis_column_name)

@callback(
    Output('qb-z-time-series', 'figure', allow_duplicate=True),
    Input('qb-crossfilter-indicator-scatter', 'hoverData'),
    Input('qb-crossfilter-zaxis-column', 'value'),
    prevent_initial_call=True)
def qb_update_z_timeseries_from_plot(hoverData, zaxis_column_name):
    dff = player_stats[player_stats['player_display_name'] == hoverData['points'][0]['customdata']]
    dff = dff[dff['Category'] == zaxis_column_name]
    return qb_create_time_series(dff, zaxis_column_name)

@callback(
    Output('qb-display-player-stats', 'children', allow_duplicate=True),
    Output('qb-select-player-list', 'value', allow_duplicate=True),
    Input('qb-crossfilter-indicator-scatter', 'hoverData'),
    prevent_initial_call = True
 )
def qb_show_player_stats_from_plot(hoverData):
    player_name = hoverData['points'][0]['customdata']
    dfs = dfr[dfr['player_display_name'] == player_name]
    dfs = dfs.pivot(index=['season', 'player_display_name', 'position'], columns='Category')
    dfs = dfs.sort_values('season')
    dfs = dfs['value'].reset_index()
    dfs = dfs[column_order]
    return dash_table.DataTable(data=dfs.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in dfs.columns],
                fixed_columns={'headers': True, 'data': 2},
                style_table={'minWidth': '100%'},
                style_cell={
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                }), player_name
                
@callback(
    Output('qb-display-player-stats', 'children'),
    Input('qb-select-player-list', 'value')
 )
def qb_show_player_stats(player_name):
    df = dfr[dfr['player_display_name'] == player_name]
    df = df.pivot(index=['season', 'player_display_name', 'position'], columns='Category')
    df = df.sort_values('season')
    df = df['value'].reset_index()
    df = df[column_order]
    return dash_table.DataTable(data=df.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in df.columns],
                fixed_columns={'headers': True, 'data': 2},
                style_table={'minWidth': '100%'},
                style_cell={
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                })

@callback(
    Output('qb-x-time-series', 'figure'),
    Input('qb-select-player-list', 'value'),
    Input('qb-crossfilter-xaxis-column', 'value'))
def qb_update_x_timeseries(hoverData, xaxis_column_name):
    player_name = hoverData
    dff = player_stats[player_stats['player_display_name'] == player_name]
    dff = dff[dff['Category'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(player_name, xaxis_column_name)
    return qb_create_time_series(dff, title)

 
@callback(
    Output('qb-y-time-series', 'figure'),
    Input('qb-select-player-list', 'value'),
    Input('qb-crossfilter-yaxis-column', 'value'))
def update_y_timeseries(hoverData, yaxis_column_name):
    dff = player_stats[player_stats['player_display_name'] == hoverData]
    dff = dff[dff['Category'] == yaxis_column_name]
    return qb_create_time_series(dff, yaxis_column_name)

@callback(
    Output('qb-z-time-series', 'figure'),
    Input('qb-select-player-list', 'value'),
    Input('qb-crossfilter-zaxis-column', 'value'))
def qb_update_z_timeseries(hoverData, zaxis_column_name):
    dff = player_stats[player_stats['player_display_name'] == hoverData]
    dff = dff[dff['Category'] == zaxis_column_name]
    return qb_create_time_series(dff, zaxis_column_name)


# if __name__ == "__main__":
#     app.run_server(debug=True)