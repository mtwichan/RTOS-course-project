# Auto PEP8: pip install nb_black
# Loading extension
# %load_ext nb_black

from typing import Union

import plotly.graph_objects as go
import pandas as pd

def generate_init_data() -> Union[list, list]:
    # Create mock dataset for testing
    task_0 = [0, 3, 8, 2, 1]
    task_1 = [1, 3, 10, 1, 1]
    task_2 = [2, 1, 14, 1, 1]
    tasks = [task_0, task_1, task_2]

    # Dash table outputs its property "data" for every row, where key is the column, and value is the value
    task_template = ["Task", "Worst Case", "Period", "Invocation-1", "Invocation-2"]

    table_data = []

    for task in tasks:
        task_tup = tuple(zip(task_template, task))
        task_dict = {key: val for key, val in task_tup}
        table_data.append(task_dict)

    # Dash table outputs its property "column" for every column name, where key is the column_id, and value is the value
    table_col = [
        {
            "name": val,
            "id": val,
            "type": "numeric",
        }
        for val in task_template
    ]
    table_col[0].update({"editable": False})
    return table_data, table_col


table_data, table_col = generate_init_data()

# Cycle conserving EDF algorithim and figure
def fig_edf_data(df_params: pd.DataFrame, fm_all=False, fm_val=1) -> list:
    curr_period = 0
    start_time = []
    end_time = []
    plot_data = []
    deadline = {"state": False, "x": None, "y": None}
    df_params = df_params.sort_values(by=["Period"])
    # Get lists from Pandas
    task_id = df_params["Task"].tolist()
    task_state = df_params["Worst Case"].tolist()
    task_wc = df_params["Worst Case"].tolist()
    task_period = df_params["Period"].tolist()

    # Plotly data templating
    hovertemplate = (
        "<b>Start:</b> %{base:.2f}s<br>"
        + "<b>Finish:</b> %{x:.2f}s<br>"
        + "<b>%{text}</b>"
    )

    for task in task_id:
        fig = {
            "name": "Task-{}".format(task),
            "x": [],
            "y": [],
            "base": [],
            "text": [],
            "orientation": "h",
            "hovertemplate": hovertemplate,
        }
        plot_data.append(fig)

    # Get a list of invocations
    df_invoc = df_params.filter(regex="Invocation")
    task_invoc = [df_invoc[col].tolist() for col in df_invoc.columns]

    # Iterate thru through each invocation of each task
    for inv_num, invocation in enumerate(task_invoc, start=1):
        for task_num in range(len(task_state)):
            # If at start of algo
            if inv_num == 1 and task_num == 0:
                t_start = 0
            # Check if this task has been released
            elif inv_num != 1 and end_time[-1] < (
                curr_period * task_period[task_num]
            ):
                t_start = curr_period * task_period[task_num]
            # Else make last task's end time this task's start time (sequential)
            else:
                t_start = end_time[-1]

            start_time.append(t_start)

            # Set running task T as worst case
            task_state[task_num] = task_wc[task_num]

            # Calculate utility
            util = [
                task_state[idx] / task_period[idx] for idx in range(len(task_state))
            ]

            util = sum(util) * fm_val

            # Round to other util if enabled
            if fm_all:
                if util < 0.5:
                    util = 0.5
                elif util < 0.75:
                    util = 0.75

            if util > 1:
                util = 1

            # Set the current task state to next invocation's execution time
            # for next iteration to use
            task_state[task_num] = invocation[task_num]

            # Calculate t
            t = invocation[task_num] / util

            # If waiting till next period
            if inv_num != 1 and end_time[-1] < (
                curr_period * task_period[task_num]
            ):
                t_end = curr_period * task_period[task_num] + t
            #                 end_time.append(t_end)
            else:
                t_end = t + start_time[-1]

            end_time.append(t_end)

            # Append data to plotly figures
            fig = plot_data[task_num]

            task_number = task_id[task_num]
            fig["x"].append(t_end - t_start)
            fig["y"].append("Task-{}".format(task_number))
            fig["text"].append("Frequency (Fm={}): {:.3f}".format(fm_val, util))
            fig["base"].append(t_start)

            # Check if we past the deadline
            if t_end > (inv_num * task_period[task_num]):
                deadline["state"] = True
                deadline["x"] = inv_num * task_period[task_num]
                deadline["y"] = "Task-{}".format(task_number)

                break

        if deadline["state"]:
            break

        curr_period += 1

    # Generate Plotly figure
    plot_data = [go.Bar(fig) for fig in plot_data]

    return plot_data, deadline



import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objects as go
from jupyter_dash import JupyterDash


# Build App
table_data, table_cols = generate_init_data()

app = JupyterDash(__name__)
app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.H1("ENGR 467 - Cycle Conserving EDF Algorithim"),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        dt.DataTable(
                            id="fm-table",
                            columns=table_cols,
                            data=table_data,
                            editable=True,
                            row_deletable=True,
                        )
                    ],
                    style={"margin": "1.5% 0%"},
                    className="row",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Select Fm"),
                                dcc.Dropdown(
                                    id="fm-dropdown",
                                    options=[
                                        {
                                            "label": "Fm (All Frequencies)",
                                            "value": 0,
                                        },
                                        {
                                            "label": "Fm, 0.75Fm, & 0.5Fm",
                                            "value": 1,
                                        },
                                    ],
                                    value=0,
                                ),
                            ],
                            className="three columns",
                        ),
                        html.Div(
                            [
                                html.Br(),
                                html.Button(
                                    "Add Invocation",
                                    id="invocation-button",
                                    n_clicks=0,
                                    style={"width": "100%"},
                                ),
                            ],
                            className="three columns",
                        ),
                        html.Div(
                            [
                                html.Br(),
                                html.Button(
                                    "Add Task",
                                    id="rows-button",
                                    n_clicks=0,
                                    style={"width": "100%"},
                                ),
                            ],
                            className="two columns",
                        ),
                        html.Div(
                            [
                                html.Br(),
                                html.Button(
                                    "Run",
                                    id="run-button",
                                    style={"float": "right", "width": "40%"},
                                ),
                            ],
                            className="four columns",
                        ),
                    ],
                    style={"margin": "1.5% 0%"},
                    className="row",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                dcc.Graph(id="fm-graph"),
            ],
        ),
        dcc.Store(id="invocation-store", data=2),
    ],
    style={"margin": "0% 1%"},
)

# Update graph with algorithim
@app.callback(
    Output("fm-graph", "figure"),
    [Input("run-button", "n_clicks")],
    [
        State("fm-table", "columns"),
        State("fm-table", "data"),
        State("fm-dropdown", "value"),
    ],
)
def update_figure(run_button, table_cols, table_data, fm_all):
    df_params = pd.DataFrame(table_data)
    data, deadline = fig_edf_data(df_params, fm_all=fm_all, fm_val=1)
    fig = go.Figure(data=data)

    # Draw deadline
    if deadline["state"]:
        title = "EDF Graph:  Schedulable?  No!"
        fig.add_annotation(
            x=deadline["x"],
            y=deadline["y"],
            text="Deadline Missed!",
            showarrow=True,
            arrowhead=1,
        )
    else:
        title = "EDF Graph:  Schedulable?  Yes!"

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Task",
        xaxis=dict(tickmode="linear", tick0=0.5, dtick=0.5, fixedrange=True),
        yaxis=dict(fixedrange=True),
        barmode="stack",
    )

    # Draw periods on figure
    df_invoc = df_params.filter(regex="Invocation")
    num_cols = len(df_invoc.columns)
    for invoc in range(num_cols):
        for task_idx, period in enumerate(df_params["Period"]):
            fig.add_shape(
                type="line",
                ysizemode="pixel",
                yanchor="Task-{}".format(task_idx),
                x0=period * (invoc + 1),
                y0=20,
                x1=period * (invoc + 1),
                y1=-20,
                line=dict(
                    color="black",
                    width=3,
                ),
            )
    return fig


# Add invocation table column
@app.callback(
    [
        Output("invocation-store", "data"),
        Output("fm-table", "columns"),
    ],
    [Input("invocation-button", "n_clicks")],
    [
        State("fm-table", "columns"),
        State("fm-table", "data"),
        State("invocation-store", "data"),
    ],
)
def add_table_col(invocation_button, table_cols, table_data, invoc_num):
    if invocation_button > 0:
        invoc_num += 1
        invoc_name = "Invocation-{}".format(invoc_num)
        table_cols.append(
            {"id": invoc_name, "name": invoc_name, "deletable": True, "type": "numeric"}
        )
    return invoc_num, table_cols


# Add rows to table
@app.callback(
    Output("fm-table", "data"),
    [Input("rows-button", "n_clicks")],
    [State("fm-table", "data"), State("fm-table", "columns")],
)
def add_rows(rows_button, table_rows, table_cols):
    if rows_button > 0:
        row_default_data = {c["id"]: None for c in table_cols}
        row_default_data[table_cols[0]["id"]] = len(table_rows)
        table_rows.append(row_default_data)
    return table_rows


app.run_server(mode="external")