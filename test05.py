#!/usr/bin/env python

import os
import h5py
import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

g_mat_path = "../server-out/11000/sample-001.mat"
g_mat = h5py.File(g_mat_path)
g_event_time = 1152.45
g_range_before = 3.0
g_range_after = 2.0

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

def get_value_at_time(time:np.ndarray, signal:np.ndarray, target_time:float) -> float:
    """指定時刻以前の最新の値を取得"""
    idx = np.searchsorted(time, target_time, side='right') - 1
    if idx < 0:
        return float('nan')
    return float(signal[idx])

def generate_empty_figure() -> go.Figure:
    subplot_titles = [
        "port1.dx",
        "port2.c1",
    ]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=subplot_titles, vertical_spacing=0.05)
    return fig

def generate_signal_figure(mat:h5py.File, event_time:float):
    stime = event_time - g_range_before
    etime = event_time + g_range_after

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
    fig.add_vline(x=event_time, line_dash="solid", row=row, col=col)

    row+=1
    fig.add_trace(go.Scatter(x=port2_time[port2_r], y=port2_c1[port2_r], mode="lines+markers"), row=row, col=col)
    fig.add_vline(x=event_time, line_dash="solid", row=row, col=col)

    fig.update_layout(dragmode=False, height=600)

    return fig

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
app.layout = dbc.Container([
    dbc.Row([
        html.H3("Hello"),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Event Time Adjustment"),
            dcc.Slider(
                id="time-slider",
                min=-g_range_before,
                max=g_range_after,
                step=0.05,
                value=0,
                marks={i: f"{i:+.1f}" for i in [-3, -2, -1, 0, 1, 2]},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # 値表示とグラフを横並びに配置
                    dbc.Row([
                        # 左側：値表示エリア
                        dbc.Col([
                            # port1.dxの値表示
                            html.Div([
                                html.H6("port1.dx", className="mb-1 text-muted"),
                                html.H4(id="value-port1-dx", children="--", className="text-primary mb-3")
                            ], className="text-center p-3 border rounded mb-3"),
                            # port2.c1の値表示
                            html.Div([
                                html.H6("port2.c1", className="mb-1 text-muted"),
                                html.H4(id="value-port2-c1", children="--", className="text-primary")
                            ], className="text-center p-3 border rounded")
                        ], width=2),
                        # 右側：グラフ
                        dbc.Col([
                            dcc.Graph(
                                id="graph1",
                                figure=generate_signal_figure(g_mat, g_event_time),
                                style={'height': '600px'}
                            ),
                        ], width=10)
                    ])
                ])
            ])
        ])
    ])
], fluid=True)

# コールバック関数：ボタンが押された時の処理（サーバーサイド）
# @app.callback(
#     Output("graph1", "figure"),
#     [Input("btn-minus-2-0", "n_clicks"),
#      Input("btn-minus-1-5", "n_clicks"),
#      Input("btn-minus-1-0", "n_clicks"),
#      Input("btn-minus-0-8", "n_clicks"),
#      Input("btn-minus-0-5", "n_clicks"),
#      Input("btn-minus-0-4", "n_clicks"),
#      Input("btn-minus-0-3", "n_clicks"),
#      Input("btn-minus-0-2", "n_clicks"),
#      Input("btn-minus-0-1", "n_clicks"),
#      Input("btn-0", "n_clicks"),
#      Input("btn-plus-0-5", "n_clicks"),
#      Input("btn-plus-1-0", "n_clicks"),
#      Input("time-slider", "value")],
#     prevent_initial_call=False
# )
# def update_graph_on_button_click(*args):
#     # どのボタンが押されたかを判定
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         # 初回読み込み時はスライダーの値を使用
#         time_offset = args[-1]  # 最後の引数はスライダーの値
#     else:
#         trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
#         # ボタンIDから時間オフセットを取得
#         button_offsets = {
#             "btn-minus-2-0": -2.0,
#             "btn-minus-1-5": -1.5,
#             "btn-minus-1-0": -1.0,
#             "btn-minus-0-8": -0.8,
#             "btn-minus-0-5": -0.5,
#             "btn-minus-0-4": -0.4,
#             "btn-minus-0-3": -0.3,
#             "btn-minus-0-2": -0.2,
#             "btn-minus-0-1": -0.1,
#             "btn-0": 0.0,
#             "btn-plus-0-5": 0.5,
#             "btn-plus-1-0": 1.0,
#             "time-slider": args[-1]  # スライダーの場合は値を取得
#         }
#         time_offset = button_offsets.get(trigger_id, 0.0)
#     
#     # マーカーラインの位置を計算
#     marker_time = g_event_time + time_offset
#     
#     # グラフを生成
#     fig = generate_signal_figure(g_mat, g_event_time)
#     
#     # マーカーラインを追加（点線）
#     for i in range(1, 3):  # 2つのサブプロットに対して
#         fig.add_vline(x=marker_time, line_dash="dot", line_color="red", row=i, col=1)
#     
#     return fig

# サーバーサイドコールバック：値表示の更新
# @app.callback(
#     [Output("value-port1-dx", "children"),
#      Output("value-port2-c1", "children")],
#     [Input("time-slider", "value")],
#     prevent_initial_call=False
# )
# def update_values(time_offset):
#     target_time = g_event_time + time_offset
    
#     # port1.dxの値を取得
#     port1_time = get_signal_by_path(g_mat, "port1.time")
#     port1_dx = get_signal_by_path(g_mat, "port1.dx")
#     port1_value = get_value_at_time(port1_time, port1_dx, target_time)
    
#     # port2.c1の値を取得
#     port2_time = get_signal_by_path(g_mat, "port2.time")
#     port2_c1 = get_signal_by_path(g_mat, "port2.c1")
#     port2_value = get_value_at_time(port2_time, port2_c1, target_time)
    
#     # 値をフォーマット
#     port1_text = f"{port1_value:.3f}" if not np.isnan(port1_value) else "--"
#     port2_text = f"{port2_value:.3f}" if not np.isnan(port2_value) else "--"
    
#     return port1_text, port2_text

# クライアントサイドコールバック（JavaScript）：スライダーのみ
app.clientside_callback(
    """
    function(slider_value, figure) {
        
        if (!window.dash_clientside) {
            return window.dash_clientside.no_update;
        }
        
        // イベント時間（Pythonから取得）
        const event_time = 1152.45;
        const time_offset = slider_value;
        const marker_time = event_time + time_offset;
        
        function decodePlotlyBinary(data) {
            if (Array.isArray(data)) {
                return data;
            }
            if (!data || !data.bdata) {
                return [];
            }

            const binaryString = window.atob(data.bdata);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const buffer = bytes.buffer;
            if (data.dtype === "float64" || data.dtype === "f8") return new Float64Array(buffer);
            if (data.dtype === "float32" || data.dtype === "f4") return new Float32Array(buffer);
            if (data.dtype === "int64" || data.dtype === "i8") return new BigInt64Array(buffer);
            if (data.dtype === "int32" || data.dtype === "i4") return new Int32Array(buffer);
            if (data.dtype === "u1") return new Uint8Array(buffer);
            return Array.from(bytes);
        }

        /*
        if (figure && figure.data) {
            const trace = figure.data[0];
            console.log("trace: ", trace);
            const xs = decodePlotlyBinary(trace.x);
            console.log("xs0: ", xs[0]);
        }
        */
        
        // 既存の図をコピー
        const new_figure = JSON.parse(JSON.stringify(figure));
        
        // 既存のマーカーライン（黒い点線）を削除
        if (new_figure.layout.shapes) {
            new_figure.layout.shapes = new_figure.layout.shapes.filter(shape => 
                !(shape.line && shape.line.color === 'black' && shape.line.dash === 'dot')
            );
        } else {
            new_figure.layout.shapes = [];
        }
        
        // 新しいマーカーライン（黒い点線）を追加
        // subplot 1
        new_figure.layout.shapes.push({
            type: 'line',
            x0: marker_time,
            x1: marker_time,
            y0: 0,
            y1: 1,
            yref: 'y1 domain',
            xref: 'x1',
            line: {
                color: 'black',
                width: 2,
                dash: 'dot'
            }
        });
        
        // subplot 2
        new_figure.layout.shapes.push({
            type: 'line',
            x0: marker_time,
            x1: marker_time,
            y0: 0,
            y1: 1,
            yref: 'y2 domain',
            xref: 'x2',
            line: {
                color: 'black',
                width: 2,
                dash: 'dot'
            }
        });
        
        if (!new_figure.layout.annotations) {
            new_figure.layout.annotations = [];
        }

        function searchsorted(arr, value, side="left") {
            let lo = 0;
            let hi = arr.length;

            while (lo < hi) {
                const mid = (lo + hi) >> 1;  // 2分探索
                if (side === "left") {
                    if (arr[mid] < value) lo = mid + 1;
                    else hi = mid;
                } else {  // side === "right"
                    if (arr[mid] <= value) lo = mid + 1;
                    else hi = mid;
                }
            }
            return lo;
        }

        for (let i = 0; i < new_figure.data.length; i++) {
            const trace = new_figure.data[i];
            const xs = decodePlotlyBinary(trace.x);
            const ys = decodePlotlyBinary(trace.y);
            selected_idx = searchsorted(xs, marker_time) - 1;
            if (selected_idx === -1) {
                selected_idx = 0;
            }
            const y_value = ys[selected_idx];
            console.log("y_value: ", y_value);
        }

        for (const key in new_figure.layout) {
            if (key.startsWith("yaxis")) {
                const axis = new_figure.layout[key];
                if (!axis.domain) {
                    continue;
                }
                const dom = axis.domain; // [y0, y1]
                const y_top = dom[1] - 0.04;

                let idx = key.replace("yaxis", "");
                if (idx === "") {
                    idx = "1";
                }
                new_figure.layout.annotations.push({
                    text: "Subplot" + idx,
                    xref: "paper",
                    yref: "paper",
                    x: 0.07,
                    y: y_top,
                    xanchor: "right",
                    showarrow: false,
                    bgcolor: "rgba(220, 235, 255, 0.5)",
                    bordercolor: "rgba(80, 120, 200, 0.9)",
                    borderwidth: 1.5,
                    borderpad: 1
                });
            }
        }

        return new_figure;
    }
    """,
    Output("graph1", "figure"),
    [Input("time-slider", "value"),
     State("graph1", "figure")]
)

if __name__ == "__main__":
    app.run(debug=True)

