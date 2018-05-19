"""
Functions for adding CTD data to an extrapolation.
"""

import os
import sys
import pickle
import netCDF4 as nc
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import Ofun

pth = os.path.abspath('../../alpha')
if pth not in sys.path:
    sys.path.append(pth)
import zfun

def get_casts(Ldir, year=2017, this_mo=1):
    # +++ load ecology CTD cast data +++

    dir0 = Ldir['parent'] + 'ptools_data/ecology/'
    # load processed station info and data
    sta_df = pd.read_pickle(dir0 + 'sta_df.p')

    # limit the stations used, if desired
    sta_list = [s for s in sta_df.index]# if ('WPA' not in s) and ('GYS' not in s)]
    # keep only certain columns
    sta_df = sta_df.loc[sta_list,['Max_Depth', 'Latitude', 'Longitude']]

    # +++ load the Ecology cast data +++

    Casts = pd.read_pickle(dir0 + 'Casts_' + str(year) + '.p')

    # start a dict to store one cast per station (it is has data in the year)
    Cast_dict = dict()

    for station in sta_list:
        casts = Casts[Casts['Station'] == station]
        casts = casts.set_index('Date')
        casts = casts.loc[:,['Salinity', 'Temperature','Z']] # keep only selected columns
        # identify a single cast by its date
        alldates = casts.index
        castdates = alldates.unique() # a short list of unique dates (1 per cast)
    
        # get the CTD cast data for this station, in the nearest month
        cdv = castdates.month.values # all the months with casts
        if len(cdv) > 0:
            # get the cast closest to the selected month
            imo = zfun.find_nearest_ind(cdv, this_mo)
            new_mo = cdv[imo]
            cast = casts[casts.index==castdates[imo]]
            Cast = cast.set_index('Z') # reorganize so that the index is Z
            Cast = Cast.dropna() # clean up
            # store cast in a dict
            Cast_dict[station] = Cast
            # save the month, just so we know
            sta_df.loc[station,'Month'] = new_mo
        else:
            print(station + ': no data')
        
    # at this point Cast_dict.keys() is the "official" list of stations
    # to loop over
    
    return Cast_dict, sta_df
    
def get_orig(Cast_dict, sta_df, X, Y, fld, lon, lat, zz, vn):
    
    #  make vectors or 1- or 2-column arrays (*) of the good points to feed to cKDTree
    xyorig = np.array((X[~fld.mask],Y[~fld.mask])).T
    fldorig = fld[~fld.mask]

    #========================================================================

    # +++ append good points from CTD data to our arrays (*) +++

    goodcount = 0

    for station in Cast_dict.keys():
    
        Cast = Cast_dict[station]
        cz = Cast.index.values
        izc = zfun.find_nearest_ind(cz, zz)
    
        # only take data from this cast if its bottom depth is at or above
        # the chosen hycom level
        czbot = -sta_df.loc[station,'Max_Depth']
        if czbot <= zz:
            # becasue we used find_nearest above we should always
            # get data in the steps below
            if vn == 't3d':
                this_fld = Cast.iloc[izc]['Temperature']
            elif vn == 's3d':
                this_fld = Cast.iloc[izc]['Salinity']
            # and store in sta_df (to align with lat, lon)
            sta_df.loc[station,'fld'] = this_fld
            goodcount += 1
        else:
            pass
        
    if goodcount >= 1:
    
        # drop stations that don't have T and s values at this depth
        sta_df = sta_df.dropna()
        # and for later convenience make a new list of stations
        sta_list = list(sta_df.index)
    
        # if we got any good points then append them
        print('goodcount = ' + str(goodcount) + ' =?')
        print('len(sta_df) = ' + str(len(sta_df)))
    
        # append CTD values to the good points from HYCOM
        x_sta = sta_df['Longitude'].values
        y_sta = sta_df['Latitude'].values
        xx_sta, yy_sta = zfun.ll2xy(x_sta, y_sta, lon.mean(), lat.mean())
        xy_sta = np.stack((xx_sta,yy_sta), axis=1)
        xyorig = np.concatenate((xyorig, xy_sta))
    
        fld_arr = sta_df['fld'].values
        fldorig = np.concatenate((fldorig, np.array(fld_arr,ndmin=1)))
    
    else:
        print('No points added')
    
    return xyorig, fldorig
    
def extrap_nearest_to_masked_CTD(X,Y,fld,xyorig=[],fldorig=[],fld0=0):
    if np.ma.is_masked(fld):
        if fld.all() is np.ma.masked:
            print('  filling with ' + str(fld0))
            fldf = fld0 * np.ones(fld.data.shape)
            fldd = fldf.data
            Ofun.checknan(fldd)
            return fldd
        else:
            fldf = fld.copy()
            # array of the missing points that we want to fill
            xynew = np.array((X[fld.mask],Y[fld.mask])).T
            # array of indices for points nearest to the missing points
            a = cKDTree(xyorig).query(xynew)
            aa = a[1]

            # use those indices to fill in using the good data
            fldf[fld.mask] = fldorig[aa]
                
            fldd = fldf.data
            Ofun.checknan(fldd)
            return fldd
    else:
        Ofun.checknan(fld)
        return fld
