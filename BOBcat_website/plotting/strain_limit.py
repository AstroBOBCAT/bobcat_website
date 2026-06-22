import pandas as pd
import healpy as hp
import numpy as np
from gw_utils import calc
from bobcat_db_interface.communications import db_comms
import h5py
import scipy.constants as sc
import emcee

import plotly.graph_objects as go

# ============================================================
# Finding strain of each candidate
# ============================================================

cur, conn = db_comms.db_connect()

strain_calc_params = pd.read_sql(
    "SELECT candidate_name, mc, orb_freq FROM binary_model",
    conn
)

z = pd.read_sql(
    "SELECT name, redshift FROM candidate",
    conn
)

strain_calc_params = strain_calc_params.merge(
    z,
    left_on='candidate_name',
    right_on='name',
    how='left'
)

strain_calc_params['mc'] = 10**strain_calc_params['mc']
strain_calc_params['f_grav'] = 2 * strain_calc_params['orb_freq']

strain_calc_params['Dl_Mpc'] = np.empty(
    len(strain_calc_params['redshift'])
)

strain_calc_params.reset_index(drop=True, inplace=True)

for i in range(len(strain_calc_params['redshift'])):
    strain_calc_params.loc[i, 'Dl_Mpc'] = calc.cosmo_calc(
        strain_calc_params.loc[i, 'redshift']
    )[0]

strain_calc_params.dropna(inplace=True)
strain_calc_params.reset_index(drop=True, inplace=True)

# Compute strains
h = pd.DataFrame()
h['h'] = pd.DataFrame([
    calc.strain_calc(
        strain_calc_params.loc[i, 'mc'],
        strain_calc_params.loc[i, 'Dl_Mpc'],
        strain_calc_params.loc[i, 'f_grav']
    )
    for i in range(len(strain_calc_params))
])

logh = np.log10(h['h'])

strains = pd.DataFrame(strain_calc_params['name'])
strains = strains.merge(h, left_index=True, right_index=True)

strains['logh'] = logh

strains = strains.merge(
    strain_calc_params[['name', 'f_grav']],
    left_on='name',
    right_on='name',
    how='left'
)

# ============================================================
# Sensitivity curve
# ============================================================

hdf_file = "15yr_quickCW_UL.h5"

burnin = 0
extra_thin = 1

with h5py.File(hdf_file, 'r') as f:
    samples_cold = f['samples_cold'][0, burnin::extra_thin, 3:5]

# ============================================================
# Upper-limit calculation
# ============================================================

def get_UL_vs_freq(log10_fgws, log10_hs, f_bounds, n_bins):

    f_min = f_bounds[0]
    f_max = f_bounds[1]

    f_bins = np.logspace(
        np.log10(f_min),
        np.log10(f_max),
        n_bins + 1
    )

    f_bincenters = []

    for i in range(f_bins.size - 1):
        f_bincenters.append(
            (f_bins[i + 1] + f_bins[i]) / 2
        )

    f_bincenters = np.array(f_bincenters)

    h, xedges, yedges = np.histogram2d(
        log10_fgws,
        log10_hs,
        bins=[np.log10(f_bins), np.linspace(-25, -15, 100)]
    )

    bincenters = []

    for i in range(xedges.size - 1):
        bincenters.append(
            (xedges[i + 1] + xedges[i]) / 2
        )

    bincenters = np.array(bincenters)

    freq_idx = np.digitize(log10_fgws, xedges)

    UL_freq = np.zeros(bincenters.size)
    UL_sigma = np.zeros(bincenters.size)

    for i in range(bincenters.size):

        hs = 10**log10_hs[np.where(freq_idx == i + 1)]

        if hs.size == 0:
            UL_freq[i] = 0.0
            continue

        UL_freq[i] = np.percentile(hs, 95)

        cc = emcee.autocorr.integrated_time(
            hs,
            c=10,
            quiet=True
        )[0]

        N_eff = hs.size / cc

        h_bins = np.linspace(0, np.max(hs), 100)

        hist, bin_edges = np.histogram(
            hs,
            bins=h_bins,
            density=True
        )

        ul_idx = np.where(UL_freq[i] < bin_edges)[0][0] - 1

        UL_sigma[i] = (
            np.sqrt(0.95 * (1 - 0.95) / N_eff)
            / hist[ul_idx]
        )

    return UL_freq, UL_sigma, bincenters, xedges

# ============================================================
# Prepare data
# ============================================================

thin = 1

log10_fgws = samples_cold[burnin::thin, 0]
log10_hs = samples_cold[burnin::thin, 1]

f_min = 1e-9
f_max = 3e-7

n_bins = 37

UL_freq, UL_sigma, bincenters, xedges = get_UL_vs_freq(
    log10_fgws,
    log10_hs,
    [f_min, f_max],
    n_bins
)

# ============================================================
# Plotly Figure
# ============================================================

fig = go.Figure()

# ------------------------------------------------------------
# Vertical reference lines
# ------------------------------------------------------------

fig.add_trace(go.Scatter(
    x=[(365.25 * 86400)**-1, (365.25 * 86400)**-1],
    y=[min(strains['h'])/10, max(UL_freq)*10],

    mode='lines',
    line=dict(color='black', dash='dash'),
    name='$1/\mathrm{yr}$',

    hoverinfo='skip'
))

fig.add_trace(go.Scatter(
    x=[10**-8.704, 10**-8.704],
    y=[min(strains['h'])/10, max(UL_freq)*10],

    mode='lines',
    line=dict(color='gray', dash='dash'),
    name='$1/T_{obs}$',

    hoverinfo='skip'
))

# ------------------------------------------------------------
# Error bars
# ------------------------------------------------------------
#
#fig.add_trace(go.Scatter(
#    x=10**bincenters,
#    y=UL_freq,
#
#    error_y=dict(
#        type='data',
#        array=UL_sigma,
#        visible=True
#    ),
#
#    mode='markers',
#    marker=dict(color='red'),
#
#    name='UL Error'
#))

# ------------------------------------------------------------
# Step sensitivity curve
# ------------------------------------------------------------

fig.add_trace(go.Scatter(
    x=10**xedges,
    y=np.concatenate((UL_freq, [0.0])),

    mode='lines',

    line=dict(
        color='red',
        width=3
    ),

    line_shape='hv',

    name='NANOGrav $15$-year Upper Limit'
))

# ------------------------------------------------------------
# Candidate strains
# ------------------------------------------------------------

fig.add_trace(go.Scatter(
    x=strains['f_grav'],
    y=strains['h'],

    mode='markers',

    marker=dict(
        color='black',
        size=9
    ),

    name='Candidates',

    text=strains['name'],

    hovertemplate=(
        r"f_GW = %{x:.2e} Hz<br>" +
        r"h = %{y:.2e}<br>" +
        "<extra></extra>"
    )
))

# ============================================================
# Layout / formatting
# ============================================================

fig.update_xaxes(
    type='log',
    title_text='$f_{GW}$ [Hz]',
    exponentformat='power',
    showexponent='all',
    minorloglabels="complete",
    dtick=1,
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    fixedrange=True
)

fig.update_yaxes(
    type='log',
    title_text='GW Strain Upper Limit',
    exponentformat='power',
    showexponent='all',
    showline=True,
    linewidth=1,
    linecolor='black',
    mirror=True,
    range=[np.log10(min(strains['h'])/10), np.log10(max(UL_freq)*10)]
)

fig.update_layout(
    title="Detectability of Gravitational Waves from Candidates",
    xaxis_range=[np.log10(min(strains['f_grav'])-0.2), max(xedges)-0.01],
    legend=dict(
        x=0.06,
        y=1.0,
        bgcolor='rgba(255,255,255,0.8)'
    ),

    font=dict(family="STIXGeneral, Times New Roman, serif")
)
fig.show()