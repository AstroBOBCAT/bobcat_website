import pandas as pd
import healpy as hp
import numpy as np
from gw_utils import calc
from bobcat_db_interface.communications import db_comms
import matplotlib.pyplot as plt

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
coords['dec_deg'] = coords['dec_deg']
coords['ra_deg'] = coords['ra_deg']
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
#strain_calc_params.dropna(inplace=True)
strain_calc_params.reset_index(drop=True, inplace=True)
strains = pd.DataFrame(strain_calc_params['name'])
h = pd.DataFrame()
h['h'] = pd.DataFrame([calc.strain_calc(strain_calc_params.loc[i,'mc'],strain_calc_params.loc[i,'Dl_Mpc'],strain_calc_params.loc[i,'f_grav']) for i in range(len(strain_calc_params))])
logh = np.log10(h['h'])
strains = strains.merge(h, left_index=True, right_index=True)
strains['logh'] = logh
coords_rad_strains = coords_rad.merge(strains, left_on='name', right_on='name')

# Generate the background strain upper limit map:
NPIX = strain_limit_skies.shape[1]
NSIDE = hp.npix2nside(NPIX)
hp.mollview(h_lim, title="Sky Map of Sensitivity w/ Candidates", unit='Strain', badcolor='grey', flip='astro', coord='C', norm='log')
hp.graticule(dpar=30,dmer=30,coord='C')

# Generate the map of candidates
NSIDE = 64
m = coords_rad_strains['h'].values
candidate_pixels = hp.ang2pix(NSIDE, coords_rad['theta'], coords_rad['phi'])
#for obj in coords_rad_strains.iterrows():
#    pixel = hp.ang2pix(NSIDE, obj[1]['theta'], obj[1]['phi'])
#    m[pixel] = obj[1]['h']
m_masked = np.ma.masked_invalid(m)
cmap = plt.cm.Reds.copy()
hp.projscatter(coords_rad_strains['phi'], coords_rad_strains['theta'], c='grey', cmap=cmap, norm='log', rot=(0,0,180))
sc = hp.projscatter(coords_rad_strains['phi'], coords_rad_strains['theta'], c=m_masked, cmap=cmap, norm='log', rot=(0,0,180))
cbar2 = plt.colorbar(
    sc,
    orientation='horizontal',
    pad=0.08,
    fraction=0.05
)
plt.show()