import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plotly.graph_objs.layout import legend

from bobcat_db_interface.communications import db_comms

# Get 1 mas scale sep vs z
mas_sep_vs_z = pd.read_csv("sep.txt", sep="\t", header=None, names=["z", "sep"])

# Get ngVLA and VLA resolutions vs z
ngVLA_res_1 = pd.read_csv("ngVLA_res_1.txt", sep="\t", header=None, names=["z", "res"])
ngVLA_res_2 = pd.read_csv("ngVLA_res_2.txt", sep="\t", header=None, names=["z", "res"])
vla_max = pd.read_csv("vla_max.txt", sep="\t", header=None, names=["z", "res"])

# Database connection
cur, conn = db_comms.db_connect()

# Load data
sep_candidates = pd.read_sql("SELECT candidate_name, seperation FROM binary_model", conn)
z_candidates = pd.read_sql("SELECT name, redshift FROM candidate", conn)

# Merge data
z_sep_candidates = pd.merge(sep_candidates, z_candidates, left_on='candidate_name', right_on='name')

fig = go.Figure()
fig.add_trace(go.Scatter(
    name='Candidates',
    x=z_sep_candidates['redshift'],
    y=z_sep_candidates['seperation'],
    mode='markers',
    customdata=np.column_stack([
        z_sep_candidates['candidate_name'],
        z_sep_candidates['redshift'],
        z_sep_candidates['seperation']
    ]),
    hovertemplate='<b>%{customdata[0]}</b><br>Redshift: %{customdata[1]}<br>Separation: %{customdata[2]} pc<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=mas_sep_vs_z['z'],
    y=mas_sep_vs_z['sep'],
    mode='lines',
    name='1 mas separation',
    line=dict(dash='dash', color='orange')
))
fig.add_trace(go.Scatter(
    x=ngVLA_res_1['z'],
    y=ngVLA_res_1['res'],
    mode='lines',
    name='ngVLA 93 GHz resolution',
    line=dict(dash='dot', color='red')
))
fig.add_trace(go.Scatter(
    x=ngVLA_res_2['z'],
    y=ngVLA_res_2['res'],
    mode='lines',
    name='ngVLA 2.4 GHz resolution',
    line=dict(dash='dot', color='green')
))
fig.add_trace(go.Scatter(
    x=vla_max['z'],
    y=vla_max['res'],
    mode='lines',
    name='VLA max resolution',
    line=dict(dash='dot', color='blue')
))
fig.update_xaxes(
    minorloglabels="complete",
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    showexponent="all",
    exponentformat="power",
    dtick=1
)
fig.update_yaxes(
    minorloglabels="complete",
    showexponent="all",
    exponentformat="power",
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    dtick=1
)
fig.update_layout(
    xaxis_title="Redshift",
    yaxis_title="Separation (pc)",
    xaxis_type="log",
    yaxis_type="log",
    legend=dict(
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
    ),
    font=dict(family="STIXGeneral, Times New Roman, serif")
)
fig.show()
