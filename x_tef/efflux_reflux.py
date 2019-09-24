"""
Calculate efflux-reflux coefficients.
"""

# imports
import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as la
import pickle
import pandas as pd
from datetime import datetime, timedelta

import os
import sys
alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun
Ldir = Lfun.Lstart(gridname='cas6', tag='v3')


pth = os.path.abspath(Ldir['LO'] + 'plotting')
if pth not in sys.path:
    sys.path.append(pth)
import pfun

import tef_fun
from importlib import reload
reload(tef_fun)

# get the DataFrame of all sections
sect_df = tef_fun.get_sect_df()

# select input file
if False:
    indir0 = Ldir['LOo'] + 'tef/'
    # choose the tef extraction to plot
    item = Lfun.choose_item(indir0)
    indir = indir0 + item + '/'
else:
    indir = '/Users/pm7/Documents/LiveOcean_output/tef/cas6_v3_lo8b_2017.01.01_2017.12.31/'

df = pd.read_pickle(indir + 'two_layer/TwoLayer.p')

# get river flow from the model run
fnr = Ldir['gtag'] + '_2017.01.01_2018.12.31.p'
fn = Ldir['LOo'] + 'river/' + fnr
dfr = pd.read_pickle(fn)
dt0 = datetime(2017,1,1)
dt1 = datetime(2017,12,31)
dfrr = dfr.loc[dt0:dt1,:]
rmean = dfrr.mean() # a series


# segment definitions, assembled by looking at the figure
# created by plot_thalweg_mean.py
segs = {
        'J1':{'S':[], 'N':[], 'W':['jdf1'], 'E':['jdf2'], 'R':['sanjuan', 'hoko']},
        'J2':{'S':[], 'N':[], 'W':['jdf2'], 'E':['jdf3'], 'R':[]},
        'J3':{'S':[], 'N':[], 'W':['jdf3'], 'E':['jdf4'], 'R':['elwha']},
        'J4':{'S':[], 'N':['sji1'], 'W':['jdf4'], 'E':['ai1','dp'], 'R':['dungeness']},
        'G1':{'S':['sji1'], 'N':['sji2'], 'W':[], 'E':[], 'R':['samish']},
        'G2':{'S':['sji2'], 'N':['sog1'], 'W':[], 'E':[], 'R':['nooksack', 'cowichan']},
        'G3':{'S':['sog1'], 'N':['sog2'], 'W':[], 'E':[], 'R':['nanaimo', 'fraser']},
        'G4':{'S':['sog2'], 'N':[], 'W':['sog3'], 'E':[], 'R':['clowhom', 'squamish']},
        'G5':{'S':[], 'N':['sog4'], 'W':[], 'E':['sog3'], 'R':['englishman', 'tsolum', 'oyster']},
        'G6':{'S':['sog4'], 'N':['sog5'], 'W':[], 'E':[], 'R':[]},
        
        #'##':{'S':[], 'N':[], 'W':[], 'E':[], 'R':[]},
        }

for seg_name in segs.keys():
    
    seg = segs[seg_name]
    has_riv = False

    # find number of sections for this segment
    N = 0
    for side in list('SNWE'):
        s = seg[side]
        N += len(s) # count up the TEF sections
    if len(seg['R']) > 0:
        N += 1 # the sum of all rivers counts as a single section
        
    # initialize result arrays
    # - inflows
    q = np.nan * np.ones(N)
    f = np.nan * np.ones(N)
    # - outflows
    Q = np.nan * np.ones(N)
    # Qf is a modified version of Q, non-zero only in the fresher of two layers
    Qf = np.zeros(N)
    F = np.nan * np.ones(N)
    
    
    # initialize arrays
    counter = 0
    for side in list('SNWER'):
    #for side in list('WESNR'):
        s = seg[side]
        if len(s) > 0:
            if side in ['W', 'S']:
                for sect in s:
                    q_s, q_f, f_s, f_f, s_s, s_f = df.loc[sect,:]
                    
                    # debugging
                    # print(sect)
                    # np.set_printoptions(precision=3, suppress=True)
                    # print(np.array([q_s, q_f, f_s, f_f, s_s, s_f]))
                    
                    if q_s > 0:
                        q[counter] = q_s
                        Q[counter] = -q_f
                        Qf[counter] = -q_f
                        f[counter] = f_s
                        F[counter] = -f_f
                    elif q_s < 0:
                        q[counter] = q_f
                        Q[counter] = -q_s
                        f[counter] = f_f
                        F[counter] = -f_s
                    counter += 1
            elif side in ['E', 'N']:
                for sect in s:
                    q_s, q_f, f_s, f_f, s_s, s_f = df.loc[sect,:]
                    
                    # debugging
                    # print(sect)
                    # np.set_printoptions(precision=3, suppress=True)
                    # print(np.array([q_s, q_f, f_s, f_f, s_s, s_f]))
                    
                    if q_s > 0:
                        q[counter] =-q_f
                        Q[counter] = q_s
                        f[counter] = -f_f
                        F[counter] = f_s
                    elif q_s < 0:
                        q[counter] = -q_s
                        Q[counter] = q_f
                        Qf[counter] = q_f
                        f[counter] = -f_s
                        F[counter] = f_f
                    counter += 1
            elif side=='R':
                has_riv = True
                Qr = rmean[s].sum()
                q[counter] = Qr
                Q[counter] = 0
                f[counter] = 0
                F[counter] = 0
                
    # make adjustments to enforce volume and salt conservation
    if has_riv:
        # if there are rivers only adjust the non-river fluxes
        dq = q.sum() - Q.sum()
        q[:-1] -= 0.5*dq/(N-1)
        Q[:-1] += 0.5*dq/(N-1)
        dqs = f.sum() - F.sum()
        f[:-1] -= 0.5*dqs/(N-1)
        F[:-1] += 0.5*dqs/(N-1)
    else:
        # if there are no rivers adjust all fluxes
        dq = q.sum() - Q.sum()
        q[:] -= 0.5*dq/N
        Q[:] += 0.5*dq/N
        dqs = f.sum() - F.sum()
        f[:] -= 0.5*dqs/N
        F[:] += 0.5*dqs/N
    print('\n' + seg_name + ':')
    print(' - Volume Flux adjustment = %0.5f' % (dq/Q.sum()))
    print(' -   Salt Flux adjustment = %0.5f' % (dqs/F.sum()))

    # The linear system of equations we will solve looks like
    # C * x = y => x = C-1 * y
    # where x is the vector of exchange fractions we are solving for,
    # C is the matrix of incoming fluxes,
    # and y is the vector of outgoing fluxes
    
    # initialize the system matrices
    C = np.zeros((2*N, 2*N))
    x = np.nan * np.ones(2*N)
    y = np.nan * np.ones(2*N)
    A = np.nan * np.ones((N,N))
    # A is a matrix form of the elements in x, organized as
    # A[incoming section number, outgoing section number], and
    # the vector x is A[:2,:].flatten(order='F')
    
    # fill the elements of C
    Cqf = np.array([ [q[0],q[1]],[f[0],f[1]] ])
    for ii in range(N):
        C[2*ii:2*ii+2, 2*ii:2*ii+2] = Cqf
        
    # make guesses for A
    for cc in range(N):
        A[:N-1,cc] = Q[cc]/Q.sum()
        A[-1,cc] = Qf[cc]/Qf.sum()
        
    # hand edits
    if seg_name == 'G4':
        A[-1,:] = np.array([1,0,0])
        
    # for a20 in np.linspace(0,1,21):
    #
    #     if seg_name == 'G5':
    #         A[-1,:] = np.array([a20, 1-a20, 0])
        
    
    # fill the elements of y:
    for rr in range(N):
        y[2*rr] = Q[rr] - np.sum(A[2:,rr]*q[2:])
        y[2*rr + 1] = F[rr] - np.sum(A[2:,rr]*f[2:])

    # and find the solution
    x = la.tensorsolve(C,y)
    # iCC = la.inv(CC); xalt = iCC.dot(y) # is the same

    # fill in the A matrix with the correct values
    if N > 2:
        A[:2,:] = x.reshape((2,N), order='F')
    else:
        A[:] = x.reshape((N,N), order='F')

    print('Solution matrix A:')
    np.set_printoptions(precision=3, suppress=True)
    print(A)
    
    # cvec = 'rbgmc'
    # plt.close('all')
    # fig = plt.figure(figsize=(10,7))
    #
    #
    # plt.show()
    

