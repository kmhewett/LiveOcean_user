# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 07:14:06 2016

@author: PM5

Code to look at the ocn files on a given day.

Only set up to work on mac.

"""

gridname='cas4'
tag='v2'
date_string = '2018.12.25'
#date_string = '2017.01.10'

# setup

import os
import sys
alp = os.path.abspath('../../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun
Ldir = Lfun.Lstart(gridname=gridname, tag=tag)
import zfun
import zrfun

pth = os.path.abspath('../../plotting')
if pth not in sys.path:
    sys.path.append(pth)
import pfun

import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
import pickle

# get files

grid_fn = Ldir['grid'] + 'grid.nc'
dsg = nc.Dataset(grid_fn)

lonr = dsg['lon_rho'][:]
latr = dsg['lat_rho'][:]
maskr = dsg['mask_rho'][:]

lonu = dsg['lon_u'][:]
latu = dsg['lat_u'][:]
masku = dsg['mask_u'][:]

lonv = dsg['lon_v'][:]
latv = dsg['lat_v'][:]
maskv = dsg['mask_v'][:]

dsg.close()

indir = Ldir['LOo'] + Ldir['gtag'] +'/f' + date_string + '/ocn3/'
in_fn = (indir + 'ocean_ini.nc')
try:
    ds = nc.Dataset(in_fn)
except OSError:
    pass
    
in_fn_coords = (indir + 'Data/coord_dict.p')
in_fn_fh = (indir + 'Data/fh' + date_string + '.p')
in_fn_xfh = (indir + 'Data/xfh' + date_string + '.p')
#
coord_dict = pickle.load(open(in_fn_coords, 'rb'))
lon = coord_dict['lon']
lat = coord_dict['lat']
#
fh = pickle.load(open(in_fn_fh, 'rb'))
xfh = pickle.load(open(in_fn_xfh, 'rb'))

#%% plotting

plt.close()


def set_box(ax):
    ax.set_xlim(-127.5, -122)
    ax.set_ylim(42.5,50.5)

fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15,7), squeeze=False)

vn = 'v' # roms variable name to plot
cmap = 'bwr' # default colormap

if vn == 'salt':
    hvn = 's3d'
    vmin = 15
    vmax = 34
elif vn == 'temp':
    hvn = 't3d'
    vmin = 5
    vmax = 12
elif vn == 'zeta':
    hvn = 'ssh'
    vmin = 0
    vmax = .4
elif vn == 'ubar':
    hvn = 'ubar'
    vmin = -.5
    vmax = .5
elif vn == 'vbar':
    hvn = 'vbar'
    vmin = -.1
    vmax = .1
elif vn == 'u':
    hvn = 'u3d'
    vmin = -.5
    vmax = .5
elif vn == 'v':
    hvn = 'v3d'
    vmin = -.5
    vmax = .5

# extract variables to plot
if vn in ['zeta', 'ubar', 'vbar']:
    # 2D
    vxfh = xfh[hvn][:,:]
    try:
        vfh = fh[hvn][:,:]
    except KeyError: # no vbar in fh; it is created during extrapolation
        vfh = 0 * vxfh
    vroms = ds[vn][0, :, :]
else:
    # 3D
    vfh = fh[hvn][-1,:,:]
    vxfh = xfh[hvn][-1,:,:]
    vroms = ds[vn][0, -1, :, :]
    
ax = axes[0,0]
cs = ax.pcolormesh(lon, lat, vfh, cmap=cmap, vmin=vmin, vmax=vmax)
pfun.dar(ax)
pfun.add_coast(ax)
set_box(ax)
ax.set_title('HYCOM original: ' + hvn)

ax = axes[0,1]
cs = ax.pcolormesh(lon, lat, vxfh, cmap=cmap, vmin=vmin, vmax=vmax)
pfun.dar(ax)
pfun.add_coast(ax)
set_box(ax)
ax.set_title('HYCOM extrapolated: ' + hvn)

ax = axes[0,2]

if vn in ['u', 'ubar']:
    Lon = lonu; Lat = latu; Mask = masku
elif vn in ['v', 'vbar']:
    Lon = lonv; Lat = latv; Mask = maskv
else:
    Lon = lonr; Lat = latr; Mask = maskr
vroms[Mask==0] = np.nan

cs = ax.pcolormesh(Lon, Lat, vroms, cmap=cmap, vmin=vmin, vmax=vmax)
fig.colorbar(cs)
pfun.dar(ax)
pfun.add_coast(ax)
ax.text(.95, .05, date_string,
    horizontalalignment='right', transform=ax.transAxes,
    fontweight='bold')
set_box(ax)
ax.set_title('ROMS ' + Ldir['gtag'] + ': ' + vn)

plt.show()

