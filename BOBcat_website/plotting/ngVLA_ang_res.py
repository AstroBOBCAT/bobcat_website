import numpy as np
import pandas as pd
import plotly.graph_objects as go
from bobcat_db_interface.communications import db_comms
from gw_utils.calc import cosmo_calc

# Database connection
cur, conn = db_comms.db_connect()

# Load data
sep_candidates = pd.read_sql("SELECT candidate_name, seperation FROM binary_model", conn)
z_candidates = pd.read_sql("SELECT name, redshift FROM candidate", conn)

# Merge data
z_sep_candidates = pd.merge(sep_candidates, z_candidates, left_on='candidate_name', right_on='name')

# Compute angular separation
z_sep_candidates['angular_separation'] = np.nan
for i in range(len(z_sep_candidates['redshift'])):
    z_sep_candidates.loc[i, 'angular_separation'] = z_sep_candidates['seperation'].iloc[i] * cosmo_calc(z_sep_candidates['redshift'].iloc[i])[2]# / 1000

# Create Plotly figure
fig = go.Figure()

# Scatter plot
fig.add_trace(go.Scatter(
    x=z_sep_candidates['redshift'],
    y=z_sep_candidates['angular_separation'],
    mode='markers',
    name='Candidates',
    text=z_sep_candidates['name'],
    hovertemplate='%{text}<br>Redshift: %{x}<br>Angular Separation: %{y}<extra></extra>'
))

# Horizontal lines
hline_values = [
    (0.0645e3, "VLA Max Resolution", "blue"),
    (2.97, "ngVLA 2.4 GHz Resolution", "green"),
    (1, "1 mas", "orange"),
    (0.08, "ngVLA 93 GHz Resolution", "red")
]

for y_val, label, color in hline_values:
    fig.add_trace(go.Scatter(
        x=[z_sep_candidates['redshift'].min()/2, z_sep_candidates['redshift'].max()*2],
        y=[y_val, y_val],
        mode='lines',
        line=dict(dash='dash', color=color),
        name=label
    ))

# Log scales
fig.update_xaxes(
    type="log",
    title_text="Redshift",
    showexponent="all",
    exponentformat="power",
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    minorloglabels="complete",
    dtick=1
)
fig.update_yaxes(
    type="log",
    title_text="Separation (mas)",
    showexponent="all",
    exponentformat="power",
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    minorloglabels="complete"
)

# Layout
fig.update_layout(
    title="Redshift vs Angular Separation",
    legend=dict(title="Resolution Lines"),
    font=dict(family="STIXGeneral, Times New Roman, serif")
)

fig.show()