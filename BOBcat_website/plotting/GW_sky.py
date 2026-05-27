import pandas as pd
import healpy as hp
import numpy as np
from gw_utils import calc
from bobcat_db_interface.communications import db_comms
import matplotlib.pyplot as plt


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
strain_calc_params.dropna(inplace=True)
strain_calc_params.reset_index(drop=True, inplace=True)
strains = pd.DataFrame(strain_calc_params['name'])
h = pd.DataFrame()
h['h'] = pd.DataFrame([calc.strain_calc(strain_calc_params.loc[i,'mc'],strain_calc_params.loc[i,'Dl_Mpc'],strain_calc_params.loc[i,'f_grav']) for i in range(len(strain_calc_params))])
logh = np.log10(h['h'])
strains = strains.merge(h, left_index=True, right_index=True)
strains['logh'] = logh
coords_rad_strains = coords_rad.merge(strains, left_on='name', right_on='name')

# Generate the sky map
NSIDE = 128
NPIX = hp.nside2npix(NSIDE)
m = np.ones(NPIX)*min(strains['h'])/10
candidate_pixels = hp.ang2pix(NSIDE, coords_rad['theta'], coords_rad['phi'])
for pixel in candidate_pixels:
    m[pixel] = np.nan
for obj in coords_rad_strains.iterrows():
    pixel = hp.ang2pix(NSIDE, obj[1]['theta'], obj[1]['phi'])
    m[pixel] = obj[1]['h']
hp.mollview(m, title="Sky Map of Candidates", unit='strain', badcolor='red', flip='astro', coord='C', norm='log', rot=(0,0,180))
hp.graticule(dpar=30,dmer=30,coord='C')
plt.show()