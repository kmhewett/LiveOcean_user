"""
Functions for particle tracking.
"""
# setup
import numpy as np
import os
import sys
alp = os.path.abspath('../../LiveOcean/alpha')
if alp not in sys.path:sys.path.append(alp)
import zfun
import netCDF4 as nc4
from datetime import datetime, timedelta

def get_tracks(fn_list, plon0, plat0, pcs0, dir_tag,
               method, surface, ndiv, windage):

    plonA = plon0.copy()
    platA = plat0.copy()
    pcsA = pcs0.copy()

    # get basic info
    G, S = zfun.get_basic_info(fn_list[0], getT=False)

    # get time vector of history files
    NT = len(fn_list)
    rot = np.nan * np.ones(NT)
    counter = 0
    for fn in fn_list:
        ds = nc4.Dataset(fn)
        rot[counter] = ds.variables['ocean_time'][:].squeeze()
        counter += 1
        ds.close

    delta_t = rot[1] - rot[0] # second between saves

    # this is how we track backwards in time
    if dir_tag == 'reverse':
        delta_t = -delta_t
        fn_list = fn_list[::-1]

    # make vectors to feed to interpolant maker
    R = dict()
    R['rlonr'] = G['lon_rho'][0,:].squeeze()
    R['rlatr'] = G['lat_rho'][:,0].squeeze()
    R['rlonu'] = G['lon_u'][0,:].squeeze()
    R['rlatu'] = G['lat_u'][:,0].squeeze()
    R['rlonv'] = G['lon_v'][0,:].squeeze()
    R['rlatv'] = G['lat_v'][:,0].squeeze()
    R['rcsr'] = S['Cs_r'][:]
    R['rcsw'] = S['Cs_w'][:]

    # these lists are used internally to get other variables as needed
    vn_list_vel = ['u','v','w']
    vn_list_wind = ['Uwind','Vwind']
    vn_list_zh = ['zeta','h']
    vn_list_other = ['salt', 'temp', 'zeta', 'h', 'u', 'v', 'w',
                     'Uwind', 'Vwind']

    # Step through times.
    #
    counter = 0
    nrot = len(rot)
    for pot in rot[:-1]:

        if np.mod(counter,24) == 0:
            print(' - time %d out of %d' % (counter, nrot))

        # get time indices
        it0, it1, frt = zfun.get_interpolant(np.array(pot), rot, extrap_nan=False)
#        iot = zfun.get_interpolant(np.array(pot), rot)
#        it0 = iot[0,0].astype(int)
#        it1 = iot[0,1].astype(int)
        #print('it0=%d it1=%d' % (it0,it1))

        # get the velocity zeta, and h at all points
        ds0 = nc4.Dataset(fn_list[it0[0]])
        ds1 = nc4.Dataset(fn_list[it1[0]])

        if counter == 0:

            # remove points on land
            SALT = get_V(['salt'], ds0, plonA, platA, pcsA, R)
            SALT = SALT.flatten()
            plon = plonA[~np.isnan(SALT)].copy()
            plat = platA[~np.isnan(SALT)].copy()
            pcs = pcsA[~np.isnan(SALT)].copy()

            # create result arrays
            NP = len(plon)
            P = dict()
            # plist main is what ends up written to output
            plist_main = ['lon', 'lat', 'cs', 'ot', 'z', 'zeta', 'zbot',
                          'salt', 'temp', 'u', 'v', 'w', 'Uwind', 'Vwind', 'h']
            for vn in plist_main:
                P[vn] = np.nan * np.ones((NT,NP))

            # write positions to the results arrays
            P['lon'][it0,:] = plon
            P['lat'][it0,:] = plat
            if surface == True:
                pcs[:] = S['Cs_r'][-1]
            P['cs'][it0,:] = pcs

            P = get_properties(vn_list_other, ds0, it0, P, plon, plat, pcs, R)

        delt = delta_t/ndiv

        for nd in range(ndiv):

            fr0 = nd/ndiv
            fr1 = (nd + 1)/ndiv
            frmid = (fr0 + fr1)/2

            if method == 'rk4':
                # RK4 integration

                V0, ZH0 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon, plat, pcs, R, fr0)

                plon1, plat1, pcs1 = update_position(V0, ZH0, S, delt/2,
                                                     plon, plat, pcs, surface)
                V1, ZH1 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon1, plat1, pcs1, R, frmid)

                plon2, plat2, pcs2 = update_position(V1, ZH1, S, delt/2,
                                                     plon, plat, pcs, surface)
                V2, ZH2 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon2, plat2, pcs2, R, frmid)

                plon3, plat3, pcs3 = update_position(V2, ZH2, S, delt,
                                                     plon, plat, pcs, surface)
                V3, ZH3 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon3, plat3, pcs3, R, fr1)

                # add windage, calculated from the middle time
                if (surface == True) and (windage > 0):
                    Vwind = get_wind(vn_list_wind, ds0, ds1, plon, plat, pcs, R, frmid)
                    Vwind3 = np.concatenate((windage*Vwind,np.zeros((NP,1))),axis=1)
                else:
                    Vwind3 = np.zeros((NP,3))

                plon, plat, pcs = update_position((V0 + 2*V1 + 2*V2 + V3)/6 + Vwind3,
                                                  (ZH0 + 2*ZH1 + 2*ZH2 + ZH3)/6,
                                                  S, delt,
                                                  plon, plat, pcs, surface)
            elif method == 'rk2':
                # RK2 integration
                V0, ZH0 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon, plat, pcs, R, fr0)

                plon1, plat1, pcs1 = update_position(V0, ZH0, S, delt/2,
                                                     plon, plat, pcs, surface)
                V1, ZH1 = get_vel(vn_list_vel, vn_list_zh,
                                           ds0, ds1, plon1, plat1, pcs1, R,frmid)

                # add windage, calculated from the middle time
                if (surface == True) and (windage > 0):
                    Vwind = get_wind(vn_list_wind, ds0, ds1, plon, plat, pcs, R, frmid)
                    Vwind3 = np.concatenate((windage*Vwind,np.zeros((NP,1))),axis=1)
                else:
                    Vwind3 = np.zeros((NP,3))

                plon, plat, pcs = update_position(V1 + Vwind3, ZH1, S, delt,
                                                  plon, plat, pcs, surface)

        # write positions to the results arrays
        P['lon'][it1,:] = plon
        P['lat'][it1,:] = plat
        if surface == True:
            pcs[:] = S['Cs_r'][-1]
        P['cs'][it1,:] = pcs
        P = get_properties(vn_list_other, ds1, it1, P, plon, plat, pcs, R)

        ds0.close()
        ds1.close()

        counter += 1

    # by doing this the points are going forward in time
    if dir_tag == 'reverse':
        for vn in plist_main:
            P[vn] = P[vn][::-1,:]

    # and save the time vector (seconds in whatever the model reports)
    P['ot'] = rot

    return P, G, S

def update_position(V, ZH, S, delta_t, plon, plat, pcs, surface):
    # find the new position
    Plon = plon.copy()
    Plat = plat.copy()
    Pcs = pcs.copy()
    dX_m = V*delta_t
    per_m = zfun.earth_rad(Plat)
    clat = np.cos(np.pi*Plat/180.)
    pdx_deg = (180./np.pi)*dX_m[:,0]/(per_m*clat)
    pdy_deg = (180./np.pi)*dX_m[:,1]/per_m
    H = ZH.sum(axis=1)
    pdz_s = dX_m[:,2]/H
    Plon += pdx_deg
    Plat += pdy_deg
    if surface == False:
        Pcs_orig = Pcs.copy()
        Pcs += pdz_s
        # enforce limits on cs
        mask = np.isnan(Pcs)
        Pcs[mask] = Pcs_orig[mask]
        Pcs[pcs < S['Cs_r'][0]] = S['Cs_r'][0]
        Pcs[pcs > S['Cs_r'][-1]] = S['Cs_r'][-1]
    else:
        Pcs[:] = S['Cs_r'][-1]

    return Plon, Plat, Pcs

def get_vel(vn_list_vel, vn_list_zh, ds0, ds1, plon, plat, pcs, R, frac):
    # get the velocity, zeta, and h at all points, at an arbitrary
    # time between two saves
    # "frac" is the fraction of the way between the times of ds0 and ds1
    # 0 <= frac <= 1
    V0 = get_V(vn_list_vel, ds0, plon, plat, pcs, R)
    V1 = get_V(vn_list_vel, ds1, plon, plat, pcs, R)
    V0[np.isnan(V0)] = 0.0
    V1[np.isnan(V1)] = 0.0
    ZH0 = get_V(vn_list_zh, ds0, plon, plat, pcs, R)
    ZH1 = get_V(vn_list_zh, ds1, plon, plat, pcs, R)
    V = (1 - frac)*V0 + frac*V1
    ZH = (1 - frac)*ZH0 + frac*ZH1

    return V, ZH

def get_wind(vn_list_wind, ds0, ds1, plon, plat, pcs, R, frac):
    # get the wind velocity at an arbitrary
    # time between two saves
    # "frac" is the fraction of the way between the times of ds0 and ds1
    # 0 <= frac <= 1
    V0 = get_V(vn_list_wind, ds0, plon, plat, pcs, R)
    V1 = get_V(vn_list_wind, ds1, plon, plat, pcs, R)
    V0[np.isnan(V0)] = 0.0
    V1[np.isnan(V1)] = 0.0
    V = (1 - frac)*V0 + frac*V1

    return V

def get_properties(vn_list_other, ds, it, P, plon, plat, pcs, R):
    # find properties at a position
    OTH = get_V(vn_list_other, ds, plon, plat, pcs, R)
    for vn in vn_list_other:
        P[vn][it,:] = OTH[:,vn_list_other.index(vn)]
    this_zeta = OTH[:, vn_list_other.index('zeta')]
    this_h = OTH[:, vn_list_other.index('h')]
    full_depth = this_zeta + this_h
    P['z'][it,:] = pcs * full_depth
    P['zbot'][it,:] = -this_h

    return P

def fix_masked_old(V, mask_val):
    try:
        if V.mask.any():
            if mask_val == 99: # used for salt and temp
                vm = np.array(~V.mask, dtype=bool).flatten()
                vf = V.flatten()
                vgood = vf[vm].mean()
                if V.mask.all():
                    V[V.mask] = np.nan
                else:
                    V[V.mask] = vgood
            else: # used for velocity with mask_val = 0
                #V[V.mask] = mask_val
                V = mask_val # this stops particles near the coast?
            V = V.data
    except AttributeError:
            # raised when V is not a masked array
            pass
    return V

def fix_masked(V, mask_val):
    try:
        if V.mask.any():
            if mask_val == 99: # used for salt and temp
                vm = np.array(~V.mask, dtype=bool).flatten()
                vf = V.flatten()
                vgood = vf[vm].mean()
                if V.mask.all():
                    V[V.mask] = np.nan
                else:
                    V[V.mask] = vgood
            else: # used for velocity with mask_val = 0
                V[V.mask] = mask_val
                #V = mask_val # this stops particles near the coast?
            V = V.data
    except AttributeError:
            # raised when V is not a masked array
            pass
    return V

def get_V(vn_list, ds, plon, plat, pcs, R):

    # get interpolant arrays
    i0lon_d = dict()
    i1lon_d = dict()
    frlon_d = dict()
    i0lat_d = dict()
    i1lat_d = dict()
    frlat_d = dict()
    for gg in ['r', 'u', 'v']:
        exn = False
        i0lon_d[gg], i1lon_d[gg], frlon_d[gg] = zfun.get_interpolant(plon, R['rlon'+gg], extrap_nan=exn)
        i0lat_d[gg], i1lat_d[gg], frlat_d[gg] = zfun.get_interpolant(plat, R['rlat'+gg], extrap_nan=exn)
    i0csr, i1csr, frcsr = zfun.get_interpolant(pcs, R['rcsr'], extrap_nan=exn)
    i0csw, i1csw, frcsw = zfun.get_interpolant(pcs, R['rcsw'], extrap_nan=exn)

    NV = len(vn_list)
    NP = len(plon)

    # get interpolated values
    V = np.nan * np.ones((NP,NV))

    if NP < 100:
        ## SLOW VERSION ##
        for ip in range(NP):
            vcount = 0
            for vn in vn_list:

                if vn in ['w']:
                    i0cs = i0csw[ip]
                    i1cs = i1csw[ip]
                    frcs = frcsw[ip]
                else:
                    i0cs = i0csr[ip]
                    i1cs = i1csr[ip]
                    frcs = frcsr[ip]

                if vn in ['salt','temp','zeta','h','Uwind','Vwind', 'w']:
                    gg = 'r'
                elif vn in ['u']:
                    gg = 'u'
                elif vn in ['v']:
                    gg = 'v'

                i0lat = i0lat_d[gg][ip]
                i1lat = i1lat_d[gg][ip]
                frlat = frlat_d[gg][ip]
                i0lon = i0lon_d[gg][ip]
                i1lon = i1lon_d[gg][ip]
                frlon = frlon_d[gg][ip]

                sly = slice(i0lat, i1lat+1)
                slx = slice(i0lon, i1lon+1)
                slz = slice(i0cs, i1cs+1)

                if vn in ['salt','temp','u','v','w']:
                    box0 = ds.variables[vn][0, slz, sly, slx].squeeze()
                    if vn in ['u', 'v', 'w']:
                        box0 = fix_masked_old(box0, 0.0)
                    elif vn in ['salt','temp']:
                        box0 = fix_masked_old(box0, 99)
                    az = np.array([1-frcs, frcs])
                    ay = np.array([1-frlat, frlat]).reshape((1,2))
                    ax = np.array([1-frlon, frlon]).reshape((1,1,2))
                    V[ip,vcount] = (az*( ( ay*((ax*box0).sum(-1)) ).sum(-1) )).sum()
                elif vn in ['zeta','Uwind','Vwind']:
                    box0 = ds.variables[vn][0, sly, slx].squeeze()
                    az = 1.
                    ay = np.array([1-frlat, frlat]).reshape((1,2))
                    ax = np.array([1-frlon, frlon]).reshape((1,1,2))
                    V[ip,vcount] = (az*( ( ay*((ax*box0).sum(-1)) ).sum(-1) )).sum()
                elif vn in ['h']:
                    box0 = ds.variables[vn][sly, slx].squeeze()
                    az = 1.
                    ay = np.array([1-frlat, frlat]).reshape((1,2))
                    ax = np.array([1-frlon, frlon]).reshape((1,1,2))
                    V[ip,vcount] = (az*( ( ay*((ax*box0).sum(-1)) ).sum(-1) )).sum()
                vcount += 1
        ## END SLOW VERSION ##

    else:
        ## FAST VERSION ##
        vcount = 0
        for vn in vn_list:

            if vn in ['w']:
                i0cs = i0csw
                i1cs = i1csw
                frcs = frcsw
            else:
                i0cs = i0csr
                i1cs = i1csr
                frcs = frcsr

            if vn in ['salt','temp','zeta','h','Uwind','Vwind', 'w']:
                gg = 'r'
            elif vn in ['u']:
                gg = 'u'
            elif vn in ['v']:
                gg = 'v'

            i0lat = i0lat_d[gg]
            i1lat = i1lat_d[gg]
            frlat = frlat_d[gg]
            i0lon = i0lon_d[gg]
            i1lon = i1lon_d[gg]
            frlon = frlon_d[gg]

            vv = ds.variables[vn][:].squeeze()
            if vn in ['salt','temp','u','v','w']:
                vl = ( (1-frlat)*((1-frlon)*vv[i0cs, i0lat, i0lon] + frlon*vv[i0cs, i0lat, i1lon])
                    + frlat*((1-frlon)*vv[i0cs, i1lat, i0lon] + frlon*vv[i0cs, i1lat, i1lon]) )
                vu = ( (1-frlat)*((1-frlon)*vv[i1cs, i0lat, i0lon] + frlon*vv[i1cs, i0lat, i1lon])
                    + frlat*((1-frlon)*vv[i1cs, i1lat, i0lon] + frlon*vv[i1cs, i1lat, i1lon]) )
                vv = (1-frcs)*vl + frcs*vu
                if vn in ['u', 'v', 'w']:
                    vv = fix_masked(vv, 0.0)
                elif vn in ['salt','temp']:
                    vv = fix_masked(vv, 99)
                V[:,vcount] = vv
            elif vn in ['zeta','Uwind','Vwind', 'h']:
                vv = ( (1-frlat)*((1-frlon)*vv[i0lat, i0lon] + frlon*vv[i0lat, i1lon])
                    + frlat*((1-frlon)*vv[i1lat, i0lon] + frlon*vv[i1lat, i1lon]) )
                V[:,vcount] = vv
            vcount += 1
        ## END FAST VERSION ##


    return V

def get_fn_list(idt, Ldir):

    if Ldir['gtagex'] in ['cascadia1_base_lo1', 'cascadia1_base_lobio1']:
        # LiveOcean version
        #Ldir['gtagex'] = 'cascadia1_base_lo1'
        # make the list of input history files
        date_list = []
        for nday in range(Ldir['days_to_track']):
            fdt = idt + timedelta(nday)
            date_list.append(fdt.strftime('%Y.%m.%d'))
        fn_list = []
        for dd in date_list:
            indir = (Ldir['roms'] + 'output/' + Ldir['gtagex'] +
                    '/f' + dd + '/')
            for hh in range(2,26):
                hhhh = ('0000' + str(hh))[-4:]
                fn_list.append(indir + 'ocean_his_' + hhhh + '.nc')

    elif Ldir['gtagex'] == 'D2005_his':
        # Other ROMS runs version
        indir = '/Users/PM5/Documents/roms/output/' + Ldir['gtagex'] + '/'
        save_num_list = range(1,365*24)
        save_dt_list = []
        dt00 = datetime(2005,1,1)
        save_dt_list.append(dt00)
        for sn in save_num_list:
            save_dt_list.append(dt00 + timedelta(hours=sn))
        # keys of this dict are datetimes, and values are history numbers
        save_dt_num_dict = dict(zip(save_dt_list,save_num_list))
        fn_list = []
        for hh in range(Ldir['days_to_track']*24 + 1):
            hh = save_dt_num_dict[idt + timedelta(hours=hh)]
            hhhh = ('0000' + str(hh))[-4:]
            fn_list.append(indir + 'ocean_his_' + hhhh + '.nc')

    return fn_list