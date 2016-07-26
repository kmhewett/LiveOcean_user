# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 08:20:32 2016

@author: PM5
"""

"""
Plot results of tracker focusing on surface trapped drifters.

Motivated by the Dead Birds project with Tim Jones and Julia Parrish.
"""
import pickle
import matplotlib.pyplot as plt
import numpy as np

import os
import sys
alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
from importlib import reload
import Lfun
import zfun
reload(zfun)
import matfun

Ldir = Lfun.Lstart()
indir = Ldir['LOo'] + 'tracks/'
fn_coast = Ldir['data'] + 'coast/pnw_coast_combined.mat'

# choose file to plot
print('\n%s\n' % '** Choose tracker file to plot **')
m_list_raw = os.listdir(indir)
m_list = []
for m in m_list_raw:
    if m[-2:] == '.p':
        m_list.append(m)
Npt = len(m_list)
m_dict = dict(zip(range(Npt), m_list))
for npt in range(Npt):
    print(str(npt) + ': ' + m_list[npt])
my_npt = int(input('-- Input number -- '))
inname = m_dict[my_npt]
  
P, G, S, PLdir = pickle.load( open( indir + inname, 'rb' ) )

NT, NP = P['lon'].shape

# mask for beaching
u = P['u']
v = P['v']
s = u**2 + v**2
d = s==0
dd = d.astype(int)
ii = np.argmax(d,axis=0)
jj = dd.max(axis=0)
for vn in P.keys():
    if P[vn].ndim == 2:
        for ip in range(NP):
            if jj[ip] == 1:
                P[vn][np.min([NT-1,ii[ip]+1]):,ip] = np.nan    

lonr = G['lon_rho']
latr = G['lat_rho']
if 'jdf' in inname:
    aa = [-126, -123.5, 47, 49]
elif 'cr' in inname:
    aa = [-125, -122.5, 45, 48]
elif 'test' in inname:
    aa = [-125.6, -124.6, 46.6, 47.4]
else:
    aa = [lonr.min(), lonr.max(), latr.min(), latr.max()]   
depth_levs = [100, 200, 500, 1000, 2000, 3000]
    
# get coastline
cmat = matfun.loadmat(fn_coast)
    
# PLOTTING

plt.close()
fig = plt.figure(figsize=(17,10))

# MAP OF TRACKS
   
ax = fig.add_subplot(121)
ax.contour(lonr, latr, G['h'], depth_levs, colors='g')        
ax.plot(cmat['lon'],cmat['lat'], '-k', linewidth=.5) # coastline       
ax.axis(aa)
zfun.dar(ax)
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# plot tracks

ax.plot(P['lon'],P['lat'])
for ip in range(NP):
    if jj[ip] == 1:
        ax.plot(P['lon'][ii[ip]:,ip],P['lat'][ii[ip]:,ip],'*k')

ax.grid()    

  
ax.set_title(PLdir['date_string0'] + ' ' + str(PLdir['days_to_track']))

ax.text(.95, .25, 'Run Info', horizontalalignment='right', weight='bold',
        transform=ax.transAxes, color='g')
info_list = ['gtagex', 'ic_name', 'method', 'ndiv', 'dir_tag', 'surface',
             'windage']
dd = 1
for vn in info_list:
    vn_str = vn + ' = ' + str(PLdir[vn])
    ax.text(.95, .25 - .03*dd, vn_str, horizontalalignment='right',
            transform=ax.transAxes, color='g')
    dd += 1

# TIME SERIES
tdays = (P['ot'] - P['ot'][0])/86400.
TD = tdays.reshape((NT,1)) * np.ones((NT,NP))

ts_list = ['salt', 'temp', 'u']
row_list = [2, 4, 6]



counter = 0
for vn in ts_list:
    ax = fig.add_subplot(3,2,row_list[counter])   
    ax.plot(tdays, P[vn])
    ax.set_title(vn)
    counter += 1