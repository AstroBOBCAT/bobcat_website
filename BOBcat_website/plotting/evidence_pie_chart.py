import plotly.graph_objects as go
import pandas as pd
import numpy as np
from bobcat_db_interface.communications import db_comms

# Database connection
cur, conn = db_comms.db_connect()

# Load data
evidence_df = pd.read_sql("SELECT evid1_type, evid2_type, evid3_type, evid4_type FROM binary_model GROUP BY evid1_type, evid2_type, evid3_type, evid4_type", conn)
evidence_series = evidence_df.stack().reset_index()
evidence_series = evidence_series[evidence_series[0] != 'NaN']
evidence_types = evidence_series[0].unique()
counts = []
for evid_type in evidence_types:
    count = np.sum(evidence_series[0] == evid_type)
    counts.append(count)

# Create pie chart
fig = go.Figure(data=[go.Pie(labels=evidence_types, values=counts)])
fig.update_layout(
    title="Evidence Types",
    font=dict(family="STIXGeneral, Times New Roman, serif")
)
fig.show()