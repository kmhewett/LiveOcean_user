"""
Plot the mean of many TEF extractions on a thalweg section.

q2, s2 = upper layer

q1, s1 = lower layer (as determined by higher salinity)

"""

# imports
import matplotlib.pyplot as plt
import pickle
import netCDF4 as nc
import pandas as pd
import numpy as np

import os
import sys
alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun

gridname = 'cas6'
tag = 'v3'
Ldir = Lfun.Lstart(gridname, tag)

pth = os.path.abspath(Ldir['LO'] + 'plotting')
if pth not in sys.path:
    sys.path.append(pth)
import pfun

pth = os.path.abspath(Ldir['parent'] + 'ptools/pgrid')
if pth not in sys.path:
    sys.path.append(pth)
import gfun
import gfun_plotting as gfp
Gr = gfun.gstart(gridname=gridname)

import tef_fun
from importlib import reload
reload(tef_fun)

# get the DataFrame of all sections
sect_df = tef_fun.get_sect_df()

# select input file
indir0 = Ldir['LOo'] + 'tef/'
# choose the tef extraction to plot
item = Lfun.choose_item(indir0)
indir = indir0 + item + '/thalweg/'

ThalMean = pickle.load(open(indir + 'ThalMean.p', 'rb'))

def plotit(ax, sect_df, sect_list, lcol, qsign):
    counter = 0
    for sn in sect_list:
        # some information about direction
        x0, x1, y0, y1, landward = sect_df.loc[sn,:]
        ax.plot([x0,x1], [y0,y1], '-', color=lcol, linewidth=3)
        
        xx = (x0+x1)/2
        yy = (y0+y1)/2
        
        # add a mark showing which direction the deep flow is going
        clat = np.cos(np.pi*yy/180)
        if (x0==x1) and (y0!=y1):
            sdir = 'NS'
            dd = qsign[counter] * 0.05 / clat
            ww = dd/8
            if landward == 1:
                ax.fill([xx, xx+dd, xx], [yy-ww, yy, yy+ww], color=lcol)
                dir_str = 'Eastward'
            elif landward == -1:
                ax.fill([xx, xx-dd, xx], [yy-ww, yy, yy+ww], color=lcol)
                dir_str = 'Westward'
        elif (x0!=x1) and (y0==y1):
            sdir = 'EW'
            dd = qsign[counter] * 0.05
            ww = dd/(8*clat)
            if landward == 1:
                ax.fill([xx-ww, xx, xx+ww], [yy, yy+dd, yy], color=lcol)
                dir_str = 'Northward'
            elif landward == -1:
                ax.fill([xx-ww, xx, xx+ww], [yy, yy-dd, yy], color=lcol)
                dir_str = 'Southward'
        counter += 1

# plotting

#plt.close('all')
lw=2
fs=16
distmax = 420
fig = plt.figure(figsize=(20,12))
ax1 = fig.add_subplot(221)
ax2 = fig.add_subplot(223)
ax3 = fig.add_subplot(122) # map

lcol_dict = dict(zip(list(ThalMean.keys()), ['olive', 'blue', 'orange', 'red']))

do_plot_extras = True
for ch_str in lcol_dict.keys():
    sect_list, q1, q2, qs1, qs2, s1, s2, dist = ThalMean[ch_str]
    
    # get the sign of q1
    qsign = np.sign(q1)
    
    lcol = lcol_dict[ch_str]
    ax1.plot(dist,np.abs(q1),'-o', color=lcol,linewidth=lw, label=ch_str)
    ax1.plot(dist,np.abs(q2),'-', color=lcol,linewidth=lw-1, label=ch_str)
    ax1.set_xlim(-20,distmax)
    ax1.grid(True)
    ax1.set_ylabel('Q1 (thick), Q2 (1000 m3/s)', fontsize=fs)
    ax1.legend()

    counter = 0
    for sn in sect_list:
        sn = sn.upper()
        ax1.text(dist[counter], np.abs(q1[counter]), sn, rotation=45, fontsize=8)
        counter += 1
        
    #ax2.fill_between(dist, s1, y2=s2, color=lcol, alpha=.8)
    ax2.plot(dist, s1, color=lcol, linewidth=lw)
    ax2.plot(dist, s2, color=lcol, linewidth=lw-1)
    ax2.set_xlim(0,distmax)
    ax2.grid(True)
    ax2.set_xlabel('Distance from Mouth (km)', fontsize=fs)
    ax2.set_ylabel('S1 (thick), S2 (g/kg)', fontsize=fs)
    #ax2.legend()
    
    if do_plot_extras:
        aa = [-125.5, -122, 46.7, 50.4]
        pfun.add_coast(ax3)
        pfun.dar(ax3)
        ax3.axis(aa)
        ax3.grid(True)
        
        for sn in sect_df.index:
            x0, x1, y0, y1, landward = sect_df.loc[sn,:]
            xx = (x0+x1)/2
            yy = (y0+y1)/2
            ax3.text(xx,yy, sn, rotation=45, fontsize=8)
        
            ax3.set_title('Section Locations, and direction of Q1 (deep inflow)')
        do_plot_extras = False
        
    plotit(ax3, sect_df, sect_list, lcol, qsign)

# add rivers
ri_fn = Gr['ri_dir'] + 'river_info.csv'
df = pd.read_csv(ri_fn, index_col='rname')
for rn in df.index:
    try:
        fn_tr = Gr['ri_dir'] + 'tracks/' + rn + '.csv'
        df_tr = pd.read_csv(fn_tr, index_col='ind')
        x = df_tr['lon'].values
        y = df_tr['lat'].values
        ax3.plot(x, y, '-',color='purple', linewidth=2, alpha=.4)
        ax3.plot(x[-1], y[-1], '*r', alpha=.4)
        ax3.text(x[-1]+.01, y[-1]+.01, rn, alpha=.4)
    except FileNotFoundError:
        pass
        


plt.show()
    