#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import dataclasses
import glob
import cv2
import numpy as np
import pandas as pd
#from scipy.io import loadmat
import h5py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, callback, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import os

g_script_dir = os.path.dirname(os.path.abspath(__file__))

THEMES = {
    "CERULEAN": dbc.themes.CERULEAN,
    "MORPH": dbc.themes.MORPH,
    "QUARTZ": dbc.themes.QUARTZ,
    "SLATE": dbc.themes.SLATE,
    "SOLAR": dbc.themes.SOLAR,
    "SPACELAB": dbc.themes.SPACELAB,
}
default_external_stylesheets = [THEMES["CERULEAN"]]

# THEMES = {
#     name: value
#     for name, value in dbc.themes.__dict__.items()
#     if not name.startswith("_") and isinstance(value, str)
# }

@dataclasses.dataclass
class Config:
    event_list_path:str
    mat_server_dir:str
    avi_dir:str

CONF = Config(
    event_list_path="./event-list.xlsx",
    mat_server_dir=f"{g_script_dir}/server-out",
    avi_dir=f"{g_script_dir}/avi"
)

@dataclasses.dataclass
class AppContext:
    mat_dir:str

g_ac = AppContext(mat_dir=f"{CONF.mat_server_dir}/11000")

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

    fig.update_layout(dragmode=False)

    return fig

g_evlist_df = pd.read_excel(CONF.event_list_path)

def generate_dummy_graph() -> go.Figure:
    df = px.data.iris()
    fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
    return fig
fig = generate_dummy_graph()

def find_avi_from_filename(fname:str) -> str|None:
    stem = os.path.splitext(fname)[0]
    for path in glob.glob(f"{CONF.avi_dir}/*"):
        tmp_fname = os.path.split(path)[1]
        tmp_stem = os.path.splitext(tmp_fname)[0]
        if stem == tmp_stem:
            return path
    return None

def get_dat_min_max_time(h5obj:h5py.File) -> tuple[float,float]:
    max_time = -99999
    min_time = 99999
    for k in h5obj.keys():
        if "time" in h5obj[k]:
            tmp_min_time = h5obj[k]["time"][0]
            tmp_max_time = h5obj[k]["time"][-1]
            min_time = min(tmp_min_time, min_time)
            max_time = max(tmp_max_time, max_time)
    return min_time, max_time

def convert_to_avi_time(ev_dat_time:float, h5obj:h5py.File, avi_path:str) -> float:
    min_time, _ = get_dat_min_max_time(h5obj)
    avi_time = ev_dat_time - min_time
    return avi_time

def extract_still_image_as_ndarray(avi_path:str, avi_time_sec:float) -> np.ndarray:
    cap = cv2.VideoCapture(avi_path)
    if not cap.isOpened():
        print("error1")
        return False

    cap.set(cv2.CAP_PROP_POS_MSEC, avi_time_sec*1000.0)
    ret, frame = cap.read()
    if not ret:
        print("error2")
        return False

    return frame

def extract_still_image_as_base64(avi_path:str, avi_time_sec:float) -> str:
    frame = extract_still_image_as_ndarray(avi_path, avi_time_sec)
    _, buffer = cv2.imencode(".jpg", frame)
    encoded = base64.b64encode(buffer).decode("ascii")
    return "data:image/jpeg;base64," + encoded

def generate_still_image_as_base64(latid:int, h5obj:h5py.File) -> str:
    row = g_evlist_df[g_evlist_df["event_id"] == latid].iloc[0]
    fname = row["file"]
    avi_path = find_avi_from_filename(fname)
    print(f"avi_path: {avi_path}")
    if avi_path is None:
        return
    dat = row["dat"]
    print(avi_path)
    print(type(dat))
    print(dat)

    avi_time_sec = convert_to_avi_time(dat, h5obj, avi_path)
    b64img = extract_still_image_as_base64(avi_path, avi_time_sec)
    return b64img

app = dash.Dash(
    __name__,
    external_stylesheets=default_external_stylesheets,
    suppress_callback_exceptions=True)
app.layout = dbc.Container([
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("My Dashboard", className="ms-0"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Home", href="#")),
                dbc.DropdownMenu(
                    label="Settings",
                    nav=True,
                    in_navbar=True,
                    children=[
                        dbc.DropdownMenuItem("Application Settings", header=True),
                        html.Div([
                            html.Label("Theme:", className="dropdown-header px-3 py-2"),
                            dbc.Select(
                                id="navbar-theme-selector",
                                options=[{"label": k, "value": v} for k, v in THEMES.items()],
                                value=default_external_stylesheets[0],
                            ),
                        ])
                    ],
                ),
                dbc.NavItem(dbc.NavLink("About", href="#")),
            ]),
        ], fluid=True),
    ),
    html.Link(id="navbar-theme-css", rel="stylesheet", href=default_external_stylesheets[0]),
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
                        inline=True,
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
            ], fluid=True),
            dbc.Modal([
                dbc.ModalHeader([
                    html.I(className="fas fa-spinner fa-spin me-2 text-primary"),
                    "Processing"
                ], className="theme-mordal-header", style={"border-bottom": "1px solid var(--bs-border-color)"}),
                dbc.ModalBody([
                    html.Div([
                        dcc.Loading(id="loading-settings-apply", type="circle", color="var(--bs-primary)", children=html.Div("Checking mat folder...", className="text-center mt-3")),
                    ], className="text-center")
                ], className="theme-mordal-body", style={"padding": "30px"}),
            ], id="modal-settings-apply-processing", is_open=False, backdrop="static", keyboard=False, centered=True),
            dbc.Modal([
                dbc.ModalHeader([
                    html.I(className="fas fa-check-circle me-2 text-success"),
                    "Success"
                ], className="theme-mordal-header", style={"border-bottom": "1px solid var(--bs-border-color)"}),
                dbc.ModalBody([
                    html.Div([
                        html.I(className="fas fa-check-circle text-success", style={"font-size": "48px", "margin-bottom": "15px"}),
                        html.Div("Loaded the mat folder")
                    ], className="text-center")
                ], className="theme-mordal-body", style={"padding": "30px"}),
                dbc.ModalFooter(
                    dbc.Button("Close", id="button-settings-apply-success-modal-close", color="success", className="ms-auto"),
                    className="theme-mordal-footer"),
            ], id="modal-settings-apply-success", is_open=False, centered=True),
            dbc.Modal([
                dbc.ModalHeader([
                    html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                    "Error"
                ], className="theme-mordal-header", style={"border-bottom": "1px solid var(--bs-border-color)"}),
                dbc.ModalBody([
                    html.Div([
                        html.I(className="fas fa-times-circle text-danger", style={"font-size": "48px", "margin-bottom": "15px"}),
                        html.Div([
                            html.P("Failed to load the mat folder", className="mb-3"),
                            html.Div(id="modal-settings-apply-error-body", children="An error occurred", className="text-muted")
                        ])
                    ], className="text-center")
                ], className="theme-mordal-body", style={"padding": "30px"}),
                dbc.ModalFooter(
                    dbc.Button("Close", id="button-settings-apply-error-modal-close", color="danger", className="ms-auto"),
                    className="theme-mordal-footer"),
            ], id="modal-settings-apply-error", is_open=False, centered=True),
            dcc.Store(id="store-settings-apply-process-started"),
            dcc.Store(id="store-settings-apply-process-result"),
        ]),
        dbc.Tab(label="Triggers", tab_id="tab-triggers", children=[
            dash_table.DataTable(g_evlist_df.to_dict("records")),
        ]),
        dbc.Tab(label="Analysis", tab_id="tab-analysis", children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="table-analysis-id-selection",
                                style_table={
                                    "height": "calc(100vh)",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"state": "selected"},
                                        "background-color": "#cce5ff",
                                        "border": "lightgray",
                                    }
                                ],
                                data=g_evlist_df[["event_id"]].to_dict("records"),
                            )
                        ])
                    ], style={"height": "calc(100vh - 250px)"}),
                ], width=1),
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.P("12345  sample-001  1234.5  HH:MM:SS.DD", id="p-analysis-trigger-info", className="card-text mb-0", style={"font-weight": "bold"})
                                ]),
                            ]),
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Img(
                                        id="img-analysis-webcam",
                                        src="https://via.placeholder.com/400x200/007bff/ffffff?text=Image+1",
                                        className="img-fluid",
                                        style={"width": "100%", "height": "100%", "object-fit": "cover"}
                                    )
                                ])
                            ], className="mb-3", style={"flex": "1"}),
                            dbc.Card([
                                dbc.CardBody([
                                    html.Img(
                                        id="img-analysis-bev",
                                        src="https://via.placeholder.com/400x200/007bff/ffffff?text=Image+1",
                                        className="img-fluid",
                                        style={"width": "100%", "height": "100%", "object-fit": "cover"}
                                    )
                                ])
                            ], className="mb-3", style={"flex": "1"}),
                        ], width=4, style={
                            "height": "calc(100vh - 240px)",  # Adjusted for tabs
                            "display": "flex",
                            "flex-direction": "column"
                        }),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Graph(
                                        id="graph-analysis-signals",
                                        config={
                                            #"staticPlot": True,
                                            "displayModeBar": False,
                                            "scrollZoom": False,
                                            "doubleClick": False,
                                            "showTips": True,
                                            "editable": False,
                                        },
                                        style={"height": "calc(100vh - 300px"}
                                    )
                                ])
                            ])
                        ], width=8)
                    ]),
                ], width=11),
            ])
        ]),
    ],
    id="tabs-main",
    active_tab="tab-settings"),
], fluid=True)

@app.callback(
    Output("navbar-theme-css", "href"),
    Input("navbar-theme-selector", "value"))
def update_theme_css(theme_url):
    return theme_url

@app.callback(
    Output("collapse-mat-folder-selection-by-job-number", "is_open"),
    Output("collapse-mat-folder-selection-by-folder", "is_open"),
    Input("radioitems-mat-folder-selection-method", "value"))
def toggle_main_tab(value):
    return (value == "by-job-number", value == "by-folder")

@app.callback(
    Output("button-settings-apply", "disabled"),
    Input("radioitems-mat-folder-selection-method", "value"),
    Input("input-text-job-number", "value"),
    Input("input-text-mat-folder", "value"))
def disable_apply_button(selection_method, job_number, folder_path):
    if selection_method == "by-job-number":
        # When job number is selected -> job_number must be set
        return not job_number or job_number.strip() == ""
    elif selection_method == "by-folder":
        # When folder is selected -> folder_path must be set
        return not folder_path or folder_path.strip() == ""
    return True  # Otherwise -> disabled

@app.callback(
    Output("input-text-mat-folder", "placeholder"),
    Input("radioitems-mat-folder-type", "value"))
def toggle_mat_path_inputs(selected):
    if selected == "server-path":
        return "e.g. \\\\mnt\\dfs\\xxx\\yyy"
    elif selected == "shared":
        return ".e.g. //server//aaa/bbb"
    return "invalid"

def check_mat_folder(selection_method:str, job_number:str, folder_type:str, folder_path:str):
    print(f"Selection method: {selection_method}")
    print(f"Job number: {job_number}")
    print(f"Folder type: {folder_type}")
    print(f"Folder path: {folder_path}")

    import time
    time.sleep(0.5)

    mat_dir = None
    if selection_method == "by-job-number":
        if not job_number or job_number.strip() == "":
            return {"success": False, "error": "Job number is empty"}
        # Process with Job number
        mat_dir = f"{CONF.mat_server_dir}/{job_number}"
    elif selection_method == "by-folder":
        if not folder_path or folder_path.strip() == "":
            return {"success": False, "error": "Folder path is empty"}
        # Process with Folder path
        # Clean up path format
        if folder_path.startswith("file://"):
            folder_path = folder_path[7:]  # Remove file:// prefix
        mat_dir = folder_path.replace("\\", "/")
    else:
        return {"success": False, "error": f"Unknown selection method: {selection_method}"}

    # Check if directory exists
    if not os.path.exists(mat_dir):
        return {"success": False, "error": f"Directory does not exist: {mat_dir}"}

    # Check if it's actually a directory
    if not os.path.isdir(mat_dir):
        return {"success": False, "error": f"Path is not a directory: {mat_dir}"}

    # Check if directory is readable
    if not os.access(mat_dir, os.R_OK):
        return {"success": False, "error": f"Directory is not readable: {mat_dir}"}

    # Check if directory contains .mat files
    mat_files = [f for f in os.listdir(mat_dir) if f.endswith('.mat')]
    if not mat_files:
        return {"success": False, "error": f"No .mat files found in directory: {mat_dir}"}

    # Check if .mat files are readable
    for mat_file in mat_files[:5]:  # Check first 5 files only
        mat_path = os.path.join(mat_dir, mat_file)
        try:
            with h5py.File(mat_path, 'r') as f:
                # Try to access basic structure
                if 'port1' not in f or 'port2' not in f:
                    return {"success": False, "error": f"Invalid .mat file structure in: {mat_file}"}
        except Exception as e:
            return {"success": False, "error": f"Cannot read .mat file {mat_file}: {str(e)}"}

    g_ac.mat_dir = mat_dir

    return {"success": True, "error": None, "mat_dir": mat_dir, "mat_files": len(mat_files)}

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
    State("radioitems-mat-folder-selection-method", "value"),
    State("input-text-job-number", "value"),
    State("radioitems-mat-folder-type", "value"),
    State("input-text-mat-folder", "value"),
    prevent_initial_call=True)
def trigger_check_mat_folder(processing_is_open, selection_method, job_number, folder_type, folder_path):
    if processing_is_open:
        # Execute the IO task with UI values
        result = check_mat_folder(selection_method, job_number, folder_type, folder_path)
        return result
    return dash.no_update

@app.callback(
    Output("modal-settings-apply-processing", "is_open", allow_duplicate=True),
    Output("modal-settings-apply-success", "is_open", allow_duplicate=True),
    Output("modal-settings-apply-error", "is_open", allow_duplicate=True),
    Output("modal-settings-apply-error-body", "children"),
    Input("store-settings-apply-process-result", "data"),
    prevent_initial_call=True)
def handle_check_mat_folder_result(result_data):
    if result_data and "success" in result_data:
        if result_data["success"]:
            # Success: close processing modal, show success modal
            success_msg = f"Successfully loaded mat folder with {result_data.get('mat_files', 0)} .mat files"
            return False, True, False, success_msg
        else:
            # Failure: close processing modal, show error modal
            error_msg = result_data.get("error", "Unknown error occurred")
            return False, False, True, error_msg
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output("p-analysis-trigger-info", "children"),
    Output("img-analysis-webcam", "src"),
    Output("graph-analysis-signals", "figure"),
    #Input("dropdown-analysis-latid", "value"),
    Input("table-analysis-id-selection", "active_cell"),
    prevent_initial_call=True)
def latid_updated(active):
    if active is None:
        return dash.no_update, dash.no_update, dash.no_update
    row = active["row"]
    col = active["column_id"]
    latid = int(g_evlist_df.iloc[row][col])
    row = g_evlist_df[g_evlist_df["event_id"] == latid].iloc[0]
    info_text = f'{latid}  {row["file"]}  {row["dat"]}'

    stem = os.path.splitext(row["file"])[0]
    mat_fname = f"{stem}.mat"
    mat_path = f"{g_ac.mat_dir}/{mat_fname}"
    h5obj = h5py.File(mat_path)
    dat = row["dat"]
    fig = generate_signal_figure(h5obj, dat)
    b64img = generate_still_image_as_base64(latid, h5obj)
    return info_text, b64img, fig

app.run(host="0.0.0.0", debug=True)
