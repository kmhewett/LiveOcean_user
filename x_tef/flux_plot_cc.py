"""
Plot the results of the flux age engine.

"""

# imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os; import sys
sys.path.append(os.path.abspath('../alpha'))
import Lfun
Ldir = Lfun.Lstart(gridname='cas6', tag='v3')
import zfun

import tef_fun
import flux_fun

# select the indir
indir0 = Ldir['LOo'] + 'tef/'
indir = indir0 + 'flux_engine/cas6_v3_lo8b/'
voldir = indir0 + 'volumes_' + Ldir['gridname'] + '/'

outdir = Ldir['LOo'] + 'tef/cc_plots/'
Lfun.make_dir(outdir)

ilist_raw = os.listdir(indir)
ilist_raw.sort()
ilist = [item for item in ilist_raw if 'S_' in item]
ilist = [item for item in ilist if 'AGE' in item]

for infile in ilist:
    
    print(infile)

    # load the DataFrame of results of flux_engine.py
    #infile = Lfun.choose_item(indir, tag='AGE', itext='Choose flux engine output file:')
    cc = pd.read_pickle(indir + infile)
    cc.loc[:,'age'] = 365*cc.loc[:,'ca']/cc.loc[:,'c']

    # load a Series of the volumes of each segment, created by flux_get_vol.py
    v_df = pd.read_pickle(voldir + 'volumes.p')
    
    plt.close('all')
    fig = plt.figure(figsize=(13,8))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    fs = 16
    lw = 3
    log_plot = False

    Dist_dict = {}
    for ch in flux_fun.channel_dict.keys():
        seg_list = flux_fun.seg_dict[ch]
        dist = flux_fun.make_dist(v_df.loc[seg_list,'lon'],v_df.loc[seg_list,'lat'])
        Dist = pd.Series(dist, index=seg_list)
        Dist_dict[ch] = Dist
    # hand edits
    Dist_dict['Admiralty Inlet to South Sound'] += Dist_dict['Juan de Fuca to Strait of Georgia']['J4']
    Dist_dict['Hood Canal'] += Dist_dict['Admiralty Inlet to South Sound']['A3']
    Dist_dict['Whidbey Basin'] += Dist_dict['Admiralty Inlet to South Sound']['M1']

    ch_counter = 0
    for ch in flux_fun.channel_dict.keys():
        dist = Dist_dict[ch]
        seg_list = flux_fun.seg_dict[ch]

        vs = [s + '_s' for s in seg_list]
        vf = [s + '_f' for s in seg_list]

        color = flux_fun.clist[ch_counter]
        if log_plot:
            ax1.plot(dist, np.log10(cc.loc[vs,'c'].values),'-',color=color, linewidth=lw)
            ax1.plot(dist, np.log10(cc.loc[vf,'c'].values),'--',color=color, linewidth=lw)
        else:
            ax1.plot(dist, 100*cc.loc[vs,'c'].values,'-',color=color, linewidth=lw)
            ax1.plot(dist, 100*cc.loc[vf,'c'].values,'--',color=color, linewidth=lw)
        # for ii in range(len(dist)):
        #     ax1.text(dist[ii],np.log10(cc.loc[vs[ii],'c']), seg_list[ii],color=color)
        
        ax2.plot(dist, cc.loc[vs,'age'].values,'-',color=color, linewidth=lw)
        ax2.plot(dist, cc.loc[vf,'age'].values,'--',color=color, linewidth=lw)
        # for ii in range(len(dist)):
        #     ax2.text(dist[ii], cc.loc[vs[ii],'age'], seg_list[ii], color=color,
        #     horizontalalignment='center', verticalalignment='bottom', fontsize=fs-3)
        
        ax1.text(.05, .75-ch_counter*.05, ch, color=color,
            transform=ax1.transAxes, fontsize=fs, fontweight='bold',
            bbox=dict(facecolor='w',edgecolor='w', alpha=0.8))
    
        ch_counter += 1
    
    if 'S_Ocean' in infile:
        ax1.set_ylim(75,102)
    else:
        ax1.set_ylim(0,35)
    ax2.set_ylim(0, 800)

    ax1.set_xlim(-10,410)
    ax2.set_xlim(-10,410)

    ax1.grid(True)
    ax2.grid(True)

    if log_plot:
        ax1.text(.05,.9,'(a) log10(Concentration)', size=fs, weight='bold', transform=ax1.transAxes)
    else:
        ax1.text(.05,.9,'(a) Concentration [%]', size=fs, weight='bold', transform=ax1.transAxes)
        
    ax2.text(.05,.9,'(b) Age [days]', size=fs, weight='bold', transform=ax2.transAxes)
        
    ax1.set_xlabel('Distance from Mouth of JdF (km)', fontsize=fs)
    ax2.set_xlabel('Distance from Mouth of JdF (km)', fontsize=fs)

    ax1.tick_params(labelsize=fs-2) 
    ax2.tick_params(labelsize=fs-2)

    ax2.text(.95,.05,'Dashed line = Upper layer', size=fs, transform=ax2.transAxes,
        style='italic', ha='right')

    ttext = infile.replace('S_','').replace('.p','').replace('AGE','').replace('_',' ')
    ax1.text(.05,.85,'Source: ' + ttext, size=.8*fs, style='italic', transform=ax1.transAxes)

    #plt.show()
    
    plt.savefig(outdir + infile.replace('.p','').replace('_AGE','') + '.png')


