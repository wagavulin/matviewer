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
from dash import html, dcc, callback, Input, Output, State, callback_context
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
            ]),
            dbc.Modal([
                dbc.ModalHeader("Processing"),
                dbc.ModalBody(dcc.Loading(id="loading-settings-apply", type="circle", children=html.Div("loading..."))),
            ], id="modal-settings-apply-processing", is_open=False, backdrop="static", keyboard=False),
            dbc.Modal([
                dbc.ModalHeader("Success"),
                dbc.ModalBody("Loaded the mat folder"),
                dbc.ModalFooter(dbc.Button("Close", id="button-settings-apply-success-modal-close", className="ms-auto")),
            ], id="modal-settings-apply-success", is_open=False),
            dbc.Modal([
                dbc.ModalHeader("Error"),
                dbc.ModalBody("Failed to load the mat folder"),
                dbc.ModalFooter(dbc.Button("Close", id="button-settings-apply-error-modal-close", className="ms-auto")),
            ], id="modal-settings-apply-error", is_open=False),
            dcc.Store(id="store-settings-apply-process-started"),
            dcc.Store(id="store-settings-apply-process-result"),
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

def do_io_task():
    import time
    time.sleep(5)
    # Return True for success, False for failure
    # For demonstration, randomly return True or False
    import random
    return random.choice([True, False])

@app.callback(
    Output("modal-settings-apply-processing", "is_open"),
    Output("modal-settings-apply-success", "is_open"),
    Output("modal-settings-apply-error", "is_open"),
    Input("button-settings-apply", "n_clicks"),
    Input("button-settings-apply-success-modal-close", "n_clicks"),
    Input("button-settings-apply-error-modal-close", "n_clicks"),
    State("modal-settings-apply-processing", "is_open"),
    State("modal-settings-apply-success", "is_open"),
    State("modal-settings-apply-error", "is_open"),
    prevent_initial_call=True)
def handle_settings_apply_button(apply_n_clicks, success_close_n_clicks, error_close_n_clicks, processing_is_open, success_is_open, error_is_open):
    triggered = callback_context.triggered_id
    if triggered == "button-settings-apply":
        # Show processing modal first
        return True, False, False
    elif triggered == "button-settings-apply-success-modal-close":
        # Close success modal
        return False, False, error_is_open
    elif triggered == "button-settings-apply-error-modal-close":
        # Close error modal
        return False, success_is_open, False
    return processing_is_open, success_is_open, error_is_open

@app.callback(
    Output("store-settings-apply-process-result", "data"),
    Input("modal-settings-apply-processing", "is_open"),
    prevent_initial_call=True)
def trigger_check_mat_folder(processing_is_open):
    if processing_is_open:
        # Execute the IO task
        result = do_io_task()
        return {"success": result}
    return dash.no_update

@app.callback(
    Output("modal-settings-apply-processing", "is_open", allow_duplicate=True),
    Output("modal-settings-apply-success", "is_open", allow_duplicate=True),
    Output("modal-settings-apply-error", "is_open", allow_duplicate=True),
    Input("store-settings-apply-process-result", "data"),
    prevent_initial_call=True)
def handle_check_mat_folder_result(result_data):
    if result_data and "success" in result_data:
        if result_data["success"]:
            # Success: close processing modal, show success modal
            return False, True, False
        else:
            # Failure: close processing modal, show error modal
            return False, False, True
    return dash.no_update, dash.no_update, dash.no_update

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

app.run(host="0.0.0.0", debug=True)
