from re import X
import pandas as pd
import healpy as hp
import numpy as np
from gw_utils import calc
from bobcat_db_interface.communications import db_comms
import matplotlib.pyplot as plt
from PIL import Image
import plotly.graph_objects as go

# Get strain upper limits as per https://github.com/nanograv/15yr_cw_analysis/blob/main/limits_freq_sky.ipynb
#first we need to load in the data file containing the limits
npzfile = np.load("15yr_cw_3d_limits_v4.npz")

#this is the 2D array containing the luminosity distance limits in Mpc as a function of frequency bin and sky pixel
#dist_limit_skies = npzfile["dist_UL_skies"]
#this is a 2D array containing 1-sigma statistical errors on the distance limits in Mpc
#dist_limit_sky_sigmas = npzfile["dist_UL_sky_sigmas"]

#this is the 2D array containing the strain upper limits as a function of frequency bin and sky pixel
strain_limit_skies = npzfile["UL_skies"]
#this is a 2D array containing 1-sigma statistical errors on the strain upper limits
#strain_limit_sky_sigmas = npzfile["UL_sky_sigmas"]

#this array defines the edges of the GW frequency bins
F_edges = npzfile["F_edges"]

f = 6e-9 # Hz
f_idx = np.argmin(f>np.array(F_edges))-1

h_lim = strain_limit_skies[f_idx]

# Connect to the database
cur, conn = db_comms.db_connect()

# Get the coordinates and strain calculation parameters
coords = pd.read_sql("SELECT name, ra_deg, dec_deg FROM candidate", conn)
strain_calc_params = pd.read_sql("SELECT candidate_name, mc, orb_freq FROM binary_model", conn)
z = pd.read_sql("SELECT name, redshift FROM candidate", conn)
strain_calc_params = strain_calc_params.merge(z, left_on='candidate_name', right_on='name', how='left')

# Reformat coordinates
vals = np.ones(len(coords))
coords_rad = pd.DataFrame()
coords_rad['phi'] = np.radians(coords['ra_deg'])
coords_rad['theta'] = np.radians(coords['dec_deg']) + np.pi/2 # Needs to be positive for ang2pix to work
coords_rad['name'] = coords['name']

# Calculate the strain for each candidate where it is calculable
strain_calc_params['mc'] = 10**strain_calc_params['mc']
strain_calc_params['f_grav'] = 2*strain_calc_params['orb_freq']
strain_calc_params['Dl_Mpc'] = np.empty(len(strain_calc_params['redshift']))
strain_calc_params.reset_index(drop=True, inplace=True)
for i in range(len(strain_calc_params['redshift'])):
    strain_calc_params.loc[i,'Dl_Mpc'] = calc.cosmo_calc(strain_calc_params.loc[i,'redshift'])[0]
strain_calc_params.reset_index(drop=True, inplace=True)
strains = pd.DataFrame(strain_calc_params['name'])
h = pd.DataFrame()
h['h'] = pd.DataFrame([calc.strain_calc(strain_calc_params.loc[i,'mc'],strain_calc_params.loc[i,'Dl_Mpc'],strain_calc_params.loc[i,'f_grav']) for i in range(len(strain_calc_params))])
logh = np.log10(h['h'])
strains = strains.merge(h, left_index=True, right_index=True)
strains['logh'] = logh
coords_rad_strains = coords_rad.merge(strains, left_on='name', right_on='name')
coords_deg_strains = coords.merge(strains, left_on='name', right_on='name')

import healpy as hp
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import numpy as np

# ------------------------------------------------------------
# Create and save the healpy background map
# ------------------------------------------------------------

hp.mollview(
    h_lim,
    title=None,#"Sky Map of Sensitivity w/ Candidates",
    unit="Strain",
    badcolor="grey",
    flip="astro",
    coord="C",
    norm="log",
    cbar=False,
    notext=True
)

hp.graticule(
    dpar=30,
    dmer=30,
    coord="C"
)

background_file = "sensitivity_background.png"

plt.savefig(
    background_file,
    dpi=600,
    bbox_inches="tight",
    pad_inches=0
)

plt.close()

# ------------------------------------------------------------
# Create Plotly figure
# ------------------------------------------------------------

fig = go.Figure()
width=1200
height=545

# Background image
img = Image.open(background_file)

fig.add_layout_image(
    dict(
        source=img,
        xref="paper",
        yref="paper",

        x=0,
        y=1,

        sizex=1,
        sizey=1,

        sizing="stretch",
        layer="below"
    )
)

# Interactive candidates
fig.add_trace(
    go.Scattergeo(
        lon=coords_deg_strains["ra_deg"],
        lat=coords_deg_strains["dec_deg"],

        mode="markers",

        customdata=np.column_stack([
            coords_deg_strains["name"],
            coords_deg_strains["ra_deg"],
            coords_deg_strains["dec_deg"],
            coords_deg_strains["h"]
        ]),

        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "RA: %{customdata[1]}<br>"
            "Dec: %{customdata[2]}<br>"
            "h: %{customdata[3]}"
            "<extra></extra>"
        ),

        marker=dict(
            size=9,
            color=coords_deg_strains["logh"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(
                title="log<sub>10</sub>(h)",
                dtick=1
            )
        ),
        showlegend=False
    )
)

# Second trace with no points for virdis colorbar
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        
        mode="markers",
        
        marker=dict(
            size=0,
            color=np.log10([min(h_lim), max(h_lim)]),
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(
                title="log<sub>10</sub>(h<sub>UL</sub>)",
                x=1.1,
                dtick=0.25
            )
        ),
        showlegend=False
    )
)
# ------------------------------------------------------------
# Formatting
# ------------------------------------------------------------

fig.update_xaxes(
    visible=False,
#    range=[-np.pi, np.pi]
)

fig.update_yaxes(
    visible=False,
    scaleanchor="x",
#    range=[-np.pi/2, np.pi/2]
)

fig.update_layout(
    width=width,
    height=height,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="STIXGeneral, Times New Roman, serif"),
    geo=dict(
        bgcolor="rgba(0,0,0,0)",
        showlakes=False,
        showland=False,
        showcoastlines=False,
        showcountries=False,
        showocean=False,
        showframe=False,
        projection=dict(
            type="mollweide"
        ),
    ),

    template="simple_white",

    margin=dict(
        l=0,
        r=0,
        t=30,
        b=0
    ),

    title="Sky Map of Sensitivity with Candidates"
)

fig.show(config={
    "scrollZoom": False,
    "displayModeBar": False,
})