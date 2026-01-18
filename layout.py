#!/usr/bin/env python

import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Vehicle ECU Dashboard"

# Generate dummy data
np.random.seed(42)

def generate_dummy_graph_data():
    """Generate dummy data for graphs"""
    x = np.linspace(0, 10, 50)
    y = np.sin(x) + np.random.normal(0, 0.1, 50)
    return x, y

def create_dummy_graph(title):
    """Create a dummy plotly graph"""
    x, y = generate_dummy_graph_data()
    fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers'))
    fig.update_layout(
        title=title,
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Sample mat file names
mat_files = [
    "001.mat", "002.mat", "005.mat", "007.mat", 
    "010.mat", "012.mat", "015.mat", "020.mat"
]

# Navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Settings", href="#")),
        dbc.NavItem(dbc.NavLink("Help", href="#")),
    ],
    brand="My Dashboard",
    brand_href="#",
    color="primary",
    dark=True,
    fluid=True,
    style={"padding": "0.1rem 1rem"}
)

# Sidebar with toggle functionality
sidebar = html.Div(
    [
        # Toggle button (always visible)
        dbc.Button(
            ">",
            id="sidebar-toggle",
            size="sm",
            color="secondary",
            className="mb-2",
            style={"position": "fixed", "left": "10px", "bottom": "20px", "z-index": "1000", "width": "30px", "height": "30px"}
        ),

        # Collapsible sidebar content
        dbc.Collapse(
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H6("File Selection", className="mb-3"),
                        ]
                    ),
                    dbc.Select(
                        id="file-select",
                        options=[{"label": f, "value": f} for f in mat_files],
                        value="005.mat",
                        className="mb-3"
                    ),
                    html.Div(
                        [html.P(f, className="small text-muted") for f in mat_files],
                        style={"max-height": "400px", "overflow-y": "auto"}
                    )
                ],
                width=2,
                className="bg-light p-3",
                style={"min-height": "100vh", "position": "fixed", "left": "0", "top": "56px", "z-index": "1050", "border-right": "1px solid #dee2e6"}
            ),
            id="sidebar-collapse",
            is_open=True
        ),

        # Close button for sidebar (separate from sidebar content)
        dbc.Button(
            "<",
            id="sidebar-close",
            size="sm",
            color="secondary",
            style={"position": "fixed", "left": "10px", "bottom": "20px", "width": "30px", "height": "30px", "z-index": "1051", "display": "block"}
        ),

        # Store component to keep track of sidebar state
        dcc.Store(id="sidebar-state", data={"is_open": True}),

        # Hidden input for keyboard shortcuts
        dcc.Input(
            id="keyboard-input",
            style={"position": "absolute", "left": "-9999px", "opacity": 0},
            autoFocus=True
        ),
        dcc.Store(id="keyboard-trigger", data=0)
    ]
)

# Main content area
main_content = html.Div(
    id="main-content",
    children=[
        # Header row with file info and timestamp
        dbc.Row(
            [
                dbc.Col(
                    html.P(id="current-file-info", children="005.mat 140.230 00:02:20.230", className="mb-0"),
                    width=12,
                    className="mb-2 p-2 bg-white border"
                )
            ]
        ),

        # Content row
        dbc.Row(
            [
                # Left column with camera image and BEV
                dbc.Col(
                    [
                        # Camera image section
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    html.Img(
                                        src="/assets/sample1.jpg",
                                        style={
                                            "width": "640px",
                                            "height": "auto",
                                            "max-width": "100%"
                                        },
                                        className="img-fluid"
                                    )
                                ),
                                dbc.CardFooter(
                                    dbc.Select(
                                        options=[
                                            {"label": "Time Sync", "value": "time"},
                                            {"label": "Frame Sync", "value": "frame"},
                                            {"label": "Manual Sync", "value": "manual"}
                                        ],
                                        value="time",
                                        size="sm"
                                    ),
                                    className="p-2"
                                )
                            ],
                            className="mb-3"
                        ),

                        # BEV Canvas section
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    html.Canvas(
                                        id="bev-canvas",
                                        width="640",
                                        height="480",
                                        style={
                                            "border": "1px solid #ddd",
                                            "background-color": "#f8f9fa",
                                            "width": "100%",
                                            "max-width": "640px"
                                        }
                                    )
                                )
                            ]
                        )
                    ],
                    width=4
                ),

                # Right column with graphs (2x4 grid)
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id=f"graph-{i}",
                                        figure=create_dummy_graph(f"Graph {i}")
                                    ),
                                    width=6,
                                    className="mb-3"
                                ) for i in range(1, 3)
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id=f"graph-{i}",
                                        figure=create_dummy_graph(f"Graph {i}")
                                    ),
                                    width=6,
                                    className="mb-3"
                                ) for i in range(3, 5)
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id=f"graph-{i}",
                                        figure=create_dummy_graph(f"Graph {i}")
                                    ),
                                    width=6,
                                    className="mb-3"
                                ) for i in range(5, 7)
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id=f"graph-{i}",
                                        figure=create_dummy_graph(f"Graph {i}")
                                    ),
                                    width=6,
                                    className="mb-3"
                                ) for i in range(7, 9)
                            ]
                        )
                    ],
                    width=8
                )
            ]
        )
    ],
    style={"padding": "20px"}
)

# Main layout
app.layout = dbc.Container(
    [
        navbar,
        sidebar,
        main_content
    ],
    fluid=True,
    className="p-0"
)

# Clientside callback for keyboard shortcuts
app.clientside_callback(
    """
    function(pathname) {
        document.addEventListener('keydown', function(event) {
            if (event.key === 's' || event.key === 'S') {
                event.preventDefault();
                // Trigger sidebar toggle by simulating button click
                const toggleBtn = document.getElementById('sidebar-toggle');
                const closeBtn = document.getElementById('sidebar-close');

                if (toggleBtn && toggleBtn.style.display !== 'none') {
                    toggleBtn.click();
                } else if (closeBtn) {
                    closeBtn.click();
                }
            }
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("keyboard-trigger", "data"),
    Input("keyboard-input", "value")
)

# Callback to toggle sidebar
@callback(
    [Output("sidebar-collapse", "is_open"),
     Output("sidebar-state", "data"),
     Output("main-content", "style"),
     Output("sidebar-toggle", "children"),
     Output("sidebar-toggle", "style"),
     Output("sidebar-close", "style")],
    [Input("sidebar-toggle", "n_clicks"),
     Input("sidebar-close", "n_clicks")],
    [State("sidebar-state", "data")]
)
def toggle_sidebar(toggle_clicks, close_clicks, current_state):
    ctx = dash.callback_context

    if not ctx.triggered:
        # Initial load - sidebar is open, hide toggle button, show close button
        return True, {"is_open": True}, {"padding": "20px"}, ">", {"position": "fixed", "left": "10px", "bottom": "20px", "z-index": "1000", "width": "30px", "height": "30px", "display": "none"}, {"position": "fixed", "left": "10px", "bottom": "20px", "width": "30px", "height": "30px", "z-index": "1051", "display": "block"}

    # Check if sidebar is currently open
    is_open = current_state.get("is_open", True)

    # Toggle the sidebar state
    new_is_open = not is_open

    # Update styles based on new state
    if new_is_open:
        main_style = {"padding": "20px"}
        toggle_icon = ">"
        toggle_style = {"position": "fixed", "left": "10px", "bottom": "20px", "z-index": "1000", "width": "30px", "height": "30px", "display": "none"}
        close_style = {"position": "fixed", "left": "10px", "bottom": "20px", "width": "30px", "height": "30px", "z-index": "1051", "display": "block"}
    else:
        main_style = {"padding": "20px"}
        toggle_icon = ">"
        toggle_style = {"position": "fixed", "left": "10px", "bottom": "20px", "z-index": "1000", "width": "30px", "height": "30px", "display": "block"}
        close_style = {"position": "fixed", "left": "10px", "bottom": "20px", "width": "30px", "height": "30px", "z-index": "1051", "display": "none"}

    return new_is_open, {"is_open": new_is_open}, main_style, toggle_icon, toggle_style, close_style

# Callback to update file info when selection changes
@callback(
    Output("current-file-info", "children"),
    Input("file-select", "value")
)
def update_file_info(selected_file):
    # Generate dummy timestamp and values
    base_time = datetime.now()
    timestamp = base_time.strftime("%H:%M:%S.%f")[:-3]  # Format: HH:MM:SS.mmm
    dummy_value = np.random.randint(100, 200)
    dummy_decimal = np.random.randint(100, 999)

    return f"{selected_file} {dummy_value}.{dummy_decimal} {timestamp}"

if __name__ == "__main__":
    app.run(debug=True)
