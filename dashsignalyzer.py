#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#%%
import dataclasses
import numpy as np
import pandas as pd
#from scipy.io import loadmat
import h5py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import os

@dataclasses.dataclass
class Config:
    event_list_path:str

CONF = Config(
    event_list_path="./event-list.xlsx"
)

def get_signal_by_path(d, path:str):
    keys = path.split(".")
    v = d
    for k in keys:
        v = v[k]
    return v

def get_index_range(time:np.ndarray, stime:float, etime:float) -> range:
    sidx = np.searchsorted(time, stime)
    eidx = np.searchsorted(time, etime)
    return range(sidx, eidx)

def generate_empty_figure() -> go.Figure:
    subplot_titles = [
        "port1.dx",
        "port2.c1",
    ]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=subplot_titles, vertical_spacing=0.05)
    return fig

def generate_signal_figure(mat:h5py.File, event_time:float):
    stime = event_time - 3.0
    etime = event_time + 2.0

    port1_time = get_signal_by_path(mat, "port1.time")
    port1_dx = get_signal_by_path(mat, "port1.dx")
    port1_dy = get_signal_by_path(mat, "port1.dy")
    port1_r = get_index_range(port1_time, stime, etime)

    port2_time = get_signal_by_path(mat, "port2.time")
    port2_c0 = get_signal_by_path(mat, "port2.c0")
    port2_c1 = get_signal_by_path(mat, "port2.c1")
    port2_r = get_index_range(port2_time, stime, etime)

    fig = generate_empty_figure()
    row=0; col=0

    col+=1
    row+=1
    fig.add_trace(go.Scatter(x=port1_time[port1_r], y=port1_dx[port1_r], mode="lines+markers"), row=row, col=col)
    fig.add_vline(x=event_time, line_dash="dot", row=row, col=col)

    row+=1
    fig.add_trace(go.Scatter(x=port2_time[port2_r], y=port2_c1[port2_r], mode="lines+markers"), row=row, col=col)
    fig.add_vline(x=event_time, line_dash="dot", row=row, col=col)

    return fig

evlist_df = pd.read_excel(CONF.event_list_path)

#%%
def generate_dummy_graph() -> go.Figure:
    df = px.data.iris()
    fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
    return fig
fig = generate_dummy_graph()

external_stylesheets = [dbc.themes.CERULEAN]
#external_stylesheets = [dbc.themes.SLATE]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True)
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="My Dashboard",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="#")),
            dbc.NavItem(dbc.NavLink("About", href="#")),
        ],
        className="mb-4"
    ),
    dbc.Tabs([
        dbc.Tab(label="Settings", tab_id="tab-settings", children=[
            dbc.Container([
                dbc.Row([
                    html.H2("Settings"),
                    dbc.RadioItems(
                        id="radioitems-mat-folder-selection-method",
                        options=[
                            {"label": "Job Number", "value": "by-job-number"},
                            {"label": "Folder", "value": "by-folder"},
                        ],
                        value="by-job-number",
                        inline=True, # 横並び
                    ),
                    html.Hr(),
                    dbc.Collapse(
                        id="collapse-mat-folder-selection-by-job-number",
                        is_open=True,
                        children=([
                            dbc.InputGroup([
                                dbc.InputGroupText("Job Number: "),
                                dbc.Input(
                                    id="input-text-job-number",
                                    type="text",
                                    placeholder="12345"
                                ),
                            ])
                        ])
                    ),
                    dbc.Collapse(
                        id="collapse-mat-folder-selection-by-folder",
                        is_open=False,
                        children=([
                            dbc.RadioItems(
                                id="radioitems-mat-folder-type",
                                options=[
                                    {"label": "Path in the server", "value": "server-path"},
                                    {"label": "Shared folder path ('\\' characters will be replaced with '/'. 'file://' will be removed.)", "value": "shared"},
                                ],
                                value="server-path",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Input(
                                id="input-text-mat-folder",
                                type="text",
                                className="mb-3"
                            ),
                        ])
                    ),
                    dbc.Button("Apply", id="button-settings-apply", className="w-auto"),
                    html.P(id="debug-message1")
                ])
            ])
        ]),
        dbc.Tab(label="Triggers", tab_id="tab-triggers", children=[
            html.P("hello2")
        ]),
        dbc.Tab(label="Analysis", tab_id="tab-analysis", children=[
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Img(src="hoge.jpg"), width=6, style={"height": "100%"}),
                    dbc.Col(html.Img(src="hoge.jpg"), width=6, style={"height": "100%"}),
                ], style={"height": "20%"}),
                dbc.Row([
                    dcc.Graph(
                        id="graph-signals",
                        #figure=fig,
                        config={"staticPlot": True},
                        style={"height": "800px"}),
                ]),
            ]),
        ]),
    ],
    id="tabs-main",
    active_tab="tab-settings"),
], fluid=True)

# @app.callback(
#     Output("tab-content", "children"),
#     Input("tabs-main", "active_tab"))
# def render_tab_content(active_tab):
#     if active_tab == "tab-settings":
#         return create_settings_tab_content()
#     if active_tab == "tab-1":
#         return html.Div("Tab1 content")
#     elif active_tab == "tab-2":
#         return create_main_tab_content()
#     elif active_tab == "tab-3":
#         return html.Div("Tab3 content")
#     else:
#         return "タブが選択されていません"

# def create_settings_tab_content():
#     return dbc.Container([
#         dbc.Row([
#             html.H2("Settings"),
#             dbc.RadioItems(
#                 id="radioitems-mat-folder-selection-method",
#                 options=[
#                     {"label": "Job Number", "value": "by-job-number"},
#                     {"label": "Folder", "value": "by-folder"},
#                 ],
#                 value="by-job-number",
#                 inline=True, # 横並び
#             ),
#             html.Hr(),
#             dbc.Collapse(
#                 id="collapse-mat-folder-selection-by-job-number",
#                 is_open=True,
#                 children=([
#                     dbc.InputGroup([
#                         dbc.InputGroupText("Job Number: "),
#                         dbc.Input(
#                             id="input-text-job-number",
#                             type="text",
#                             placeholder="12345"
#                         ),
#                     ])
#                 ])
#             ),
#             dbc.Collapse(
#                 id="collapse-mat-folder-selection-by-folder",
#                 is_open=False,
#                 children=([
#                     dbc.RadioItems(
#                         id="radioitems-mat-folder-type",
#                         options=[
#                             {"label": "Path in the server", "value": "server-path"},
#                             {"label": "Shared folder path ('\\' characters will be replaced with '/'. 'file://' will be removed.)", "value": "shared"},
#                         ],
#                         value="server-path",
#                         inline=False,
#                         className="mb-3"
#                     ),
#                     dbc.Input(
#                         id="input-text-mat-folder",
#                         type="text",
#                         className="mb-3"
#                     ),
#                 ])
#             ),
#             dbc.Button("Apply", id="button-settings-apply", className="w-auto"),
#             html.P(id="debug-message1")
#         ])
#     ])

@app.callback(
    Output("collapse-mat-folder-selection-by-job-number", "is_open"),
    Output("collapse-mat-folder-selection-by-folder", "is_open"),
    Input("radioitems-mat-folder-selection-method", "value"))
def toggle_main_tab(value):
    return (value == "by-job-number", value == "by-folder")

@app.callback(
    Output("input-text-mat-folder", "placeholder"),
    Input("radioitems-mat-folder-type", "value"))
def toggle_mat_path_inputs(selected):
    if selected == "server-path":
        return "e.g. \\\\mnt\\dfs\\xxx\\yyy"
    elif selected == "shared":
        return ".e.g. //server//aaa/bbb"
    return "invalid"

@app.callback(
    Output("debug-message1", "children"),
    Input("button-settings-apply", "n_clicks"))
def button_settings_apply(n_clicks):
    if not n_clicks:
        return ""
    return f"clicked {n_clicks}"

def create_main_tab_content():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.Img(src="hoge.jpg"), width=6, style={"height": "100%"}),
            dbc.Col(html.Img(src="hoge.jpg"), width=6, style={"height": "100%"}),
        ], style={"height": "20%"}),
        dbc.Row([
            dcc.Graph(
                id="graph-signals",
                #figure=fig,
                config={"staticPlot": True},
                style={"height": "800px"}),
        ]),
    ])

# app.layout = dbc.Container([
#     dbc.NavbarSimple(
#         brand="My Dashboard",
#         color="primary",
#         dark=True,
#         children=[
#             dbc.NavItem(dbc.NavLink("Home", href="#")),
#             dbc.NavItem(dbc.NavLink("About", href="#")),
#         ],
#         className="mb-4"
#     ),
#     dbc.Row([
#         dbc.Col(
#             dbc.Card(
#                 dbc.CardBody([
#                     html.H4("サイト情報", className="cart-title"),
#                     html.P("ここに説明文"),
#                     dbc.Button("アクション", color="primary"),
#                 ]),
#                 className="mb-4"),
#             xs=12, md=4, lg=3),
#         dbc.Col(
#             dbc.Card(
#                 dbc.CardBody([
#                     html.H4("グラフ", className="card-title"),
#                     dcc.Graph(figure=fig)
#                 ])
#             ),
#             xs=12, md=8, lg=9),
#     ]),
# ])

# app.layout = html.Div([
#     html.H1("DashSignalyzer", style={"textAlign": "center"}),
#     dcc.Dropdown(
#         id="dropdown-event-id",
#         options=evlist_df["event_id"],
#         style={"width": "600px"},
#     ),
#     html.Table([
#         html.Tbody([
#             html.Tr([
#                 html.Td("File"),
#                 html.Td("", id="text-file"),
#             ]),
#             html.Tr([
#                 html.Td("DAT"),
#                 html.Td("", id="text-dat")
#             ]),
#             html.Tr([
#                 html.Td("Event Time"),
#                 html.Td("", id="text-event-time")
#             ]),
#         ]),
#     ], style={
#         "width": "600px",
#         #"border": "1px solid black",
#         #"borderCollapse": "collapse",
#     }),
#     dcc.Graph(
#         id="graph-signals",
#         #figure=fig,
#         config={"staticPlot": True},
#         style={"height": "800px"}),
#     html.Div("", id="text-message", style={"width": "600px", "border": "1px solid gray", "padding": "5px"})
# ])

# @app.callback(
#     Output("text-file", "children"),
#     Output("text-dat", "children"),
#     Output("text-event-time", "children"),
#     Output("graph-signals", "figure"),
#     Output("text-message", "children"),
#     Input("dropdown-event-id", "value"))
# def dropdown_event_id_updated(value):
#     try:
#         if not value:
#             fig = generate_empty_figure()
#             return "", "", "", fig, ""
#         df = evlist_df[evlist_df["event_id"] == value]
#         if not len(df) == 1:
#             raise ValueError("length is not 1")
#         file = df["file"].values[0]
#         mat_path = f"{file}.mat"
#         dat = df["dat"].values[0]
#         event_time = dat + 0.8
#         mat = h5py.File(mat_path)
#         fig = generate_signal_figure(mat, event_time)
#         msg = ""
#         return file, f"{dat:.2f}", f"{event_time:.2f}", fig, msg
#     except Exception as e:
#         fig = generate_empty_figure()
#         return "", "", "", fig, str(e)

app.run(host="0.0.0.0", debug=True)
