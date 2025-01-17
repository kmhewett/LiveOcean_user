"""
Calculate efflux-reflux coefficients, and then create
the transport matrix used in flux_engine.py.

Note: to see specific row values use:
pd.set_option('display.max_rows',78)
q_df.loc['W3_f',:] # shows columns for this row
q_df['W3_f'] # shows columns for this column
"""

# imports
import numpy as np
import numpy.linalg as la
import pickle
import pandas as pd
from datetime import datetime, timedelta

import os
import sys
sys.path.append(os.path.abspath('../alpha'))
import Lfun
Ldir = Lfun.Lstart(gridname='cas6', tag='v3')

import tef_fun
import flux_fun

testing = False

verbose = False

# this makes it easier to see things during inspection
pd.set_option('display.max_rows',100)

# Input directory
indir0 = Ldir['LOo'] + 'tef/'

# Get segment definitions, assembled by looking at the figure
# created by plot_thalweg_mean.py.
segs = flux_fun.segs
# Create list of all segments to work on.
seg_name_list = list(segs.keys())

if testing:
    year_list = [2017]
    season_list = ['full']
    verbose_list = ['G4','W4','M1']
    #verbose_list = seg_name_list
else:
    year_list = [2017, 2018, 2019]
    season_list = flux_fun.season_list
    verbose_list = seg_name_list

for year in year_list:
    year_str = str(year)
    item = 'cas6_v3_lo8b_'+year_str+'.01.01_'+year_str+'.12.31'
    indir = indir0 + item + '/flux/'
    indir2 = indir0 + 'flux_engine/'
    
    # Get river flow from the model run, and average over a specified time range.
    fnr = Ldir['gtag'] + '_' + year_str + '.01.01_' + year_str + '.12.31.p'
    fn = Ldir['LOo'] + 'river/' + fnr
    dfr = pd.read_pickle(fn)

    # get desired time ranges of the seasons
    dtr = flux_fun.get_dtr(year)
    
    for season in season_list:
        
        Atyp_list = [] # place to stor segments where Atyp is used
    
        print(60*'=')
        print('Year = %d, Season = %s' % (year,season))
    
        # get TEF transports
        df = pd.read_pickle(indir + 'two_layer_' + season + '.p')

        # get mean river transports
        dt0 = dtr[season][0] - timedelta(days=.5)
        dt1 = dtr[season][1] - timedelta(days=.5)
        dfrr = dfr.loc[dt0:dt1,:]
        rmean = dfrr.mean() # a series of mean river transports

        # Initialize a DataFrame to store the fluxes "q" used to drive the flux engine
        sl2 = []
        # Each segment has a salty layer (_s) beneath a fresh layer (_f).
        for sn in seg_name_list:
            sl2.append(sn + '_s')
            sl2.append(sn + '_f')
        sl2or = ['ocean_s', 'ocean_f'] + ['river_s', 'river_f'] + sl2
        # The rows of the flux DataFrame are just the chosen segments (both layers)
        # The columns of the flux DataFrame are all of the segments (both layers)
        # as well as ocean and river "segments".
        q_df = pd.DataFrame(0, index = sl2, columns = sl2or)
        # The way q_df is used in the flux_engine is that the row denotes where net transports are
        # ending up, and the columns denote where the transports are coming from.  Each entry in
        # q_df is a transport (m3/s).  Hence when we multiply a row by the tracer concentrations
        # in each segment and then sum along that row, we get the net flux of tracer into or out of
        # the segment specified by that row.

        for seg_name in seg_name_list:

            if verbose and seg_name in verbose_list:
                print('')
                print(seg_name.center(40, '-'))

            seg = segs[seg_name]
            # seg is a dictionary with info on which TEF sections are on
            # each boundary, and which rivers enter the segment,
            # e.g. segs['J1'] returns:
            # {'S': [], 'N': [], 'W': ['jdf1'], 'E': ['jdf2'], 'R': ['sanjuan', 'hoko']}

            # initialize a flag to tell if the segment has river(s)
            has_riv = False

            # find number of sections for this segment
            N = 0
            for side in list('SNWE'):
                sect_list = seg[side]
                N += len(sect_list) # count up the TEF sections
            if len(seg['R']) > 0:
                N += 1 # the sum of all rivers counts as a single section

            # initialize result arrays
            # - inflows
            q = np.nan * np.ones(N)
            f = np.nan * np.ones(N)
            s = np.nan * np.ones(N)
            # - outflows
            Q = np.nan * np.ones(N)
            # Qf is a modified version of Q, non-zero only in the fresher of two layers
            Qf = np.zeros(N)
            F = np.nan * np.ones(N)
            S = np.nan * np.ones(N)

            # initialize a list of whether inflow is salt or fresh
            q_sal = list(N*'x')
            # initialize a list of whether outflow is salt or fresh
            Q_sal = list(N*'x')
            # initialize a list of section names (snl = "section name list")
            snl = list(N*'x') # the 'x' is just a placeholder

            # Initialize arrays.
            #
            # Note that the TEF transports in "df" have been pre-processed
            # in flux_two_layer.py so that they are always positive to the
            # East or North.
            #
            # For the arrays here (like q and Q) the sign convention is
            # that ALL transports are positive, and we keep track of direction based
            # on whether they are loaded into q (inflows) or Q (outflows)
            counter = 0 # "counter" indexes which section
            for side in list('SNWER'):
                sect_list = seg[side]
                if len(sect_list) > 0:
                    if side in ['W', 'S']:
                        for sect in sect_list:
                            snl[counter] = sect
                            q_s, q_f, f_s, f_f, s_s, s_f, lon, lat = df.loc[sect,:]
                            if q_s >= 0:
                                # inflow is salty
                                q[counter] = q_s
                                Q[counter] = -q_f
                                q_sal[counter] = 's'
                                Q_sal[counter] = 'f'
                                Qf[counter] = -q_f
                                f[counter] = f_s
                                F[counter] = -f_f
                                s[counter] = s_s
                                S[counter] = s_f
                            elif q_s < 0:
                                # inflow is fresh
                                q[counter] = q_f
                                Q[counter] = -q_s
                                q_sal[counter] = 'f'
                                Q_sal[counter] = 's'
                                f[counter] = f_f
                                F[counter] = -f_s
                                s[counter] = s_f
                                S[counter] = s_s
                            counter += 1
                    elif side in ['E', 'N']:
                        for sect in sect_list:
                            snl[counter] = sect
                            q_s, q_f, f_s, f_f, s_s, s_f, lon, lat = df.loc[sect,:]
                            if q_s >= 0:
                                # outflow is salty
                                q[counter] =-q_f
                                Q[counter] = q_s
                                q_sal[counter] = 'f'
                                Q_sal[counter] = 's'
                                f[counter] = -f_f
                                F[counter] = f_s
                                s[counter] = s_f
                                S[counter] = s_s
                            elif q_s < 0:
                                # outflow is fresh
                                q[counter] = -q_s
                                Q[counter] = q_f
                                q_sal[counter] = 's'
                                Q_sal[counter] = 'f'
                                Qf[counter] = q_f
                                f[counter] = -f_s
                                F[counter] = f_f
                                s[counter] = s_s
                                S[counter] = s_f
                            counter += 1
                    elif side=='R':
                        has_riv = True
                        Qr = rmean[sect_list].sum()
                        q[counter] = Qr
                        Q[counter] = 0
                        q_sal[counter] = 'f'
                        Q_sal[counter] = 'x' # indicate there is no outflow from a river
                        f[counter] = 0
                        F[counter] = 0
                        snl[counter]='river'
                        if verbose and seg_name in verbose_list:
                            print(' - has rivers')
                            print('   ' + str(sect_list))
                            print('   Qr = ' + str(int(Qr)))

            # make adjustments to enforce volume and salt conservation
            dq = q.sum() - Q.sum()
            dqs = f.sum() - F.sum()
            if has_riv:
                # if there are rivers only adjust the non-river fluxes
                q[:-1] -= 0.5*dq/(N-1)
                Q[:-1] += 0.5*dq/(N-1)
                f[:-1] -= 0.5*dqs/(N-1)
                F[:-1] += 0.5*dqs/(N-1)
            else:
                # if there are no rivers adjust all fluxes
                q[:] -= 0.5*dq/N
                Q[:] += 0.5*dq/N
                f[:] -= 0.5*dqs/N
                F[:] += 0.5*dqs/N
            # then adjust the salinities to match
            s = f/q
            if has_riv:
                S = np.zeros(N)
                S[:-1] = F[:-1]/Q[:-1]
            else:
                S = F/Q
            if verbose and seg_name in verbose_list:
                print(' - Volume Flux adjustment = %0.5f' % (dq/Q.sum()))
                print(' -   Salt Flux adjustment = %0.5f' % (dqs/F.sum()))

            # The linear system of equations we will solve looks like
            # C * x = y => x = C-1 * y
            # where x is the vector of exchange fractions we are solving for,
            # C is the matrix of incoming fluxes,
            # and y is the vector of outgoing fluxes

            def print_A(A, snl, q_sal):
                print(' - Solution matrix A:')
                for ii in range(N):
                    print((' %6s (%1s): |' % (snl[ii], q_sal[ii]))
                        + (N*'%6.2f' % (tuple(A[ii,:]))) + ' |')

            def get_A(N, q, Q, f, F, y, A):
                # fill the elements of y:
                for rr in range(N):
                    y[2*rr] = Q[rr] - np.sum(A[2:,rr]*q[2:])
                    y[2*rr + 1] = F[rr] - np.sum(A[2:,rr]*f[2:])
                # and find the solution
                x = la.tensorsolve(C,y)
                # iCC = la.inv(CC); xalt = iCC.dot(y) # is the same as tensorsolve
                # fill in the A matrix with the correct values
                if N > 2:
                    A[:2,:] = x.reshape((2,N), order='F')
                else:
                    A[:] = x.reshape((N,N), order='F')
                return A

            if N == 1: # H8 case, only a single section, no rivers
                A = np.array([0], ndmin=2)

            else:
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
                    if has_riv:
                        A[-1,cc] = Qf[cc]/Qf.sum()
                    else:
                        A[-1,cc] = Q[cc]/Q.sum()

                yorig = y.copy()

                def get_Atyp(N, has_riv):
                    # generate a reasonable guess for cases where we have no
                    # consistent solutions
                    f_diag = .1
                    # value of A along the diagonal (this is all that is used by flux_engine)
                    if verbose and seg_name in verbose_list:
                        print('   <using Atyp> f_diag = %0.2f' % (f_diag))
                    if has_riv:
                        Atyp = np.ones((N,N))*(1-f_diag)/(N-2)
                    else:
                        Atyp = np.ones((N,N))*(1-f_diag)/(N-1)
                    for ii in range(N):
                        Atyp[ii,ii] = f_diag
                    if has_riv:
                        Atyp[:,-1] = 0
                    return Atyp

                if (N == 3):# and has_riv:
                    # iterative method to scan over all possible river distributions
                    # (or section 3 distributions in the case of M4 (do I mean M1?))
                    # and then return the average of all valid A's.
                    NN = 41 # number of guesses
                    AA = np.nan * np.ones((NN,N,N))
                    count = 0
                    for a20 in np.linspace(0,1,NN):
                        A[-1,:] = np.array([a20, 1-a20, 0])
                        AA[count,:,:] = get_A(N, q, Q, f, F, yorig, A)
                        count += 1

                    good_guess = []
                    for gg in range(NN):
                        if (AA[gg,:,:]>=0).all():
                            good_guess.append(gg)
                    if verbose and seg_name in verbose_list:
                        print('   good guess list = ' + str(good_guess))
                    if len(good_guess) > 0:
                        A = AA[good_guess,:,:].mean(axis=0)
                    else: # G5 had no valid solutions
                        Atyp_list.append(seg_name)
                        A = get_Atyp(N, has_riv)
                else:
                    A = get_A(N, q, Q, f, F, yorig, A)

                if (N == 2) and (not has_riv):
                    # check for bad solutions and force them to have set mixing
                    if (A < 0).any():
                        if verbose and seg_name in verbose_list:
                            print('Bad value for N=2 segment ' + seg_name)
                            print_A(A, snl, q_sal)
                        Atyp_list.append(seg_name)
                        A = get_Atyp(N, has_riv)

                if (N == 2) and has_riv:
                    # why can't I set this to be [[1,0],[1,0]]??
                    A = np.array([[0,0],[1,0]])
                                    
            if verbose and seg_name in verbose_list:
                print_A(A, snl, q_sal)
                
            # HAND OVERRIDES --------------------------------------------------
                                                
            if True and seg_name=='A1':
                print('   ** A1 override **')
                A[0,0] = .1; A[0,1] = 1 - A[0,0]
                A[1,1] = .6; A[1,0] = 1 - A[1,1]
                if verbose and seg_name in verbose_list:
                    print_A(A, snl, q_sal)
                # RESULT: this really helps! 2019.10.29
                # A[0,0] = .1; A[0,1] = 1 - A[0,0]
                # A[1,1] = .6; A[1,0] = 1 - A[1,1]
                
            if False and 'W4' in seg_name:
                print('   ** W4 override **')
                A = get_Atyp(N, has_riv)
                if verbose and seg_name in verbose_list:
                    print_A(A, snl, q_sal)
                                        
            # -----------------------------------------------------------------

            # *****************************************************************

            # store results in the DataFrame of fluxes used for the flux engine
            def update_q(q_df, q_sal, seg_name, Seg_name, q, Q, sss):
                # transport in from adjoining segment
                # and vertical transport up from below or down from above
                if q_sal[sss] == 's':
                    q_df.loc[seg_name+'_s',Seg_name+'_s'] += q[sss]*(1-A[sss,sss])
                    q_df.loc[seg_name+'_f',seg_name+'_s'] += q[sss] * A[sss,sss]
                elif q_sal[sss] == 'f':
                    q_df.loc[seg_name+'_f',Seg_name+'_f'] += q[sss]*(1-A[sss,sss])
                    q_df.loc[seg_name+'_s',seg_name+'_f'] += q[sss] * A[sss,sss]
                # transport out to adjoining segment
                # in this case the column (where tracer comes from) is the segment itself
                if Q_sal[sss] == 's':
                    q_df.loc[seg_name+'_s',seg_name+'_s'] -=  Q[sss]
                elif Q_sal[sss] == 'f':
                    q_df.loc[seg_name+'_f',seg_name+'_f'] -= Q[sss]
                return q_df

            sss = 0
            for sect in snl:
                if (seg_name=='J1' and sect=='jdf1') or (seg_name=='G6' and sect=='sog5'):
                    Seg_name = 'ocean'
                    if verbose and seg_name in verbose_list:
                        print(' -- Adjoining segment = ' + Seg_name + ' for ' + sect)
                    q_df = update_q(q_df, q_sal, seg_name, Seg_name, q, Q, sss)
                elif sect == 'river':
                    q_df.loc[seg_name+'_f','river_f'] = q[sss]
                else:
                    # find which segment each section connects to
                    for Seg_name in segs.keys():
                        Seg = segs[Seg_name]
                        for side in list('SNWE'):
                            sect_list = Seg[side]
                            if sect in sect_list and Seg_name != seg_name:
                                if verbose and seg_name in verbose_list:
                                    print(' -- Adjoining segment = ' + Seg_name + ' for ' + sect)
                                q_df = update_q(q_df, q_sal, seg_name, Seg_name, q, Q, sss)
                sss += 1

            # add net vertical advection in the section
            qx_s = q_df.loc[seg_name+'_s',:].sum() # sum a row
            qx_f = q_df.loc[seg_name+'_f',:].sum()
            qxm_s = q_df.loc[seg_name+'_s',:].abs().max()
            qxm_f = q_df.loc[seg_name+'_f',:].abs().max()
            if np.abs(qx_s + qx_f) > 1:
                print('   @@@@@@@@@@@@ qx warning @@@@@@@@@@@@@@@')
            if qx_s > 0:
                # upward transport
                if verbose and seg_name in verbose_list:
                    print('adding upward transport %0.1f (%0.1f pct)' % (qx_s, 100*qx_s/qxm_s))
                q_df.loc[seg_name+'_s',seg_name+'_s'] -=  qx_s
                q_df.loc[seg_name+'_f',seg_name+'_s'] +=  qx_s
            elif qx_s <= 0:
                # downward transport
                if verbose and seg_name in verbose_list:
                    print('adding downward transport %0.1f (%0.1f pct)' % (qx_s, 100*qx_s/qxm_s))
                q_df.loc[seg_name+'_f',seg_name+'_f'] +=  qx_s
                q_df.loc[seg_name+'_s',seg_name+'_f'] -=  qx_s
            # check again
            qx_s = q_df.loc[seg_name+'_s',:].sum() # this use of .loc returns a series
            qx_f = q_df.loc[seg_name+'_f',:].sum()
            if np.abs(qx_s + qx_f) > 1:
                print('   @@@@@@@@@@@@ qx warning @@@@@@@@@@@@@@@')

        if verbose:
            print('\nAtyp list:')
            print(Atyp_list)
            
        # save results
        q_df.to_pickle(indir + 'q_df_' + season + '.p')
        

