
import pandas as pd
import healpy as hp
import numpy as np
from gw_utils import calc
from bobcat_db_interface.communications import db_comms
import matplotlib
import matplotlib.pyplot as plt
import h5py
import healpy as hp
import scipy.constants as sc
import emcee

# Finding strain of each candidate
# Connect to the database
cur, conn = db_comms.db_connect()

# Get the strain calculation parameters
strain_calc_params = pd.read_sql("SELECT candidate_name, mc, orb_freq FROM binary_model", conn)
z = pd.read_sql("SELECT name, redshift FROM candidate", conn)
strain_calc_params = strain_calc_params.merge(z, left_on='candidate_name', right_on='name', how='left')

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
strains = strains.merge(strain_calc_params[['name','f_grav']], left_on='name', right_on='name', how='left')

# Sensitivity Plot (copied from https://github.com/nanograv/15yr_cw_analysis/blob/main/UL_analysis.ipynb)

hdf_file = "15yr_quickCW_UL.h5"

#specify how much of the first samples to discard
#(no need to discard any for provided samples as that has already been done)
#and how much more to thin the samples in addition to what we already thinned when we saved the samples
#burnin = 100_000
burnin = 0
extra_thin = 1

with h5py.File(hdf_file, 'r') as f:
    # Only load the columns we need (indices 3 and 4 for f_grav and h)
    samples_cold = f['samples_cold'][0,burnin::extra_thin,3:5]

#define function to calculate upper limits

def get_UL_vs_freq(log10_fgws, log10_hs, f_bounds, n_bins):
    f_min = f_bounds[0]
    f_max = f_bounds[1]
    
    f_bins = np.logspace(np.log10(f_min), np.log10(f_max), n_bins+1)#100)

    f_bincenters = []
    for i in range(f_bins.size-1):
        f_bincenters.append((f_bins[i+1]+f_bins[i])/2)
    f_bincenters = np.array(f_bincenters)

    #make bin centers
    bincenters = []
    h, xedges, yedges, _ = plt.hist2d(log10_fgws, log10_hs, bins=[np.log10(f_bins), np.linspace(-25, -15, 100)])
    for i in range(xedges.size-1):
        bincenters.append((xedges[i+1]+xedges[i])/2)
    bincenters = np.array(bincenters)

    freq_idx = np.digitize(log10_fgws, xedges)

    UL_freq = np.zeros(bincenters.size)
    UL_sigma = np.zeros(bincenters.size)
    for i in range(bincenters.size):

        hs = 10**log10_hs[np.where(freq_idx==i+1)]
        if hs.size==0:
            UL_freq[i] = 0.0
            continue

        #normal UL
        UL_freq[i] = np.percentile(hs, 95)

        cc = emcee.autocorr.integrated_time(hs, c=10, quiet=True)[0]
        N_eff = hs.size/cc

        h_bins = np.linspace(0, np.max(hs), 100)
        hist, bin_edges = np.histogram(hs, bins=h_bins, density=True)
        ul_idx = np.where(UL_freq[i]<bin_edges)[0][0]-1
        UL_sigma[i] = np.sqrt(0.95*(1-0.95)/N_eff)/hist[ul_idx]
            
    return UL_freq, UL_sigma, bincenters, xedges

#uniform prior
plt.rcParams.update({'font.size': 18})

burnin = 0
thin=1

log10_fgws = samples_cold[burnin::thin,0]
log10_hs = samples_cold[burnin::thin,1]


f_min = 1e-9
f_max = 3e-7

n_bins=37

UL_freq, UL_sigma, bincenters, xedges = get_UL_vs_freq(log10_fgws, log10_hs, [f_min,f_max], n_bins)

matplotlib.rcParams.update({'font.size': 25})

plt.figure(figsize=(10,7))

plt.gca().axvline((365.25*86400)**-1, color='black', ls='--', lw=2, label='1/yr')
plt.gca().axvline(10**-8.704, color='gray', ls='--', lw=2, label=r'$1/T_{\rm obs}$')

plt.errorbar(10**bincenters, UL_freq, yerr=UL_sigma,
             ls='', lw=2, marker='', alpha=1.0, color="xkcd:red")

plt.step(10**xedges, np.concatenate((UL_freq, [0.0,])), where='post',
             ls='-', lw=2, marker='', alpha=1.0, color="xkcd:red", label="15-year")

plt.scatter(strains['f_grav'], strains['h'], color='black', s=50, label='Candidates')

plt.xscale('log')
plt.yscale('log')
#plt.ylim(6e-15,4e-12)
#plt.xlim(1e-9, 3e-7)
plt.xlabel(r"$f_{\rm GW}$ [Hz]")
plt.ylabel(r"GW Strain Upper Limit")
plt.legend(bbox_to_anchor=(0.06,1), loc="upper left")
plt.grid(which='both', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()