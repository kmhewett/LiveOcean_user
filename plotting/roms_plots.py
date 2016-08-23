"""
Module of plotting functions.
"""

# imports
#
# because the calling function, pan_plot.py, has already put alpha on the
# path we assume it is on the path here too.
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt

from importlib import reload
import zfun
import zrfun
import matfun
import pfun; reload(pfun)

# module defaults (available inside the methods)

figsize = (18,10)
out_dict = dict()

def P_basic(in_dict):
    # This creates, and optionally saves, a basic plot of surface fields
    # from a ROMS history file.
    # INPUT a dict containing:
    #   fn: text string with the full path name of the history file to plot
    #   fn_out: text string with full path of output file name
    #   in_dict: a tuple with optional information to pass to the plot
    # OUTPUT: either a screen image or a graphics file, and a dict of other
    # information such as axis limits.

    # START
    fig = plt.figure(figsize=figsize)
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    # PLOT CODE
    # panel 1
    t_str = 'Surface Salinity'
    ax = fig.add_subplot(121)
    vn = 'salt'
    cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
            vlims=vlims[vn], cmap='rainbow')
    fig.colorbar(cs)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(t_str)
    pfun.add_info(ax, in_dict['fn'])
    pfun.add_windstress_flower(ax, ds)
    # panel 2
    t_str = 'Surface Temperature'
    ax = fig.add_subplot(122)
    vn = 'temp'
    cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
            vlims=vlims[vn], cmap='bwr')
    fig.colorbar(cs)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')
    pfun.add_velocity_vectors(ax, ds, in_dict['fn'])

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict

def P_carbon(in_dict):
    # START
    fig = plt.figure(figsize=figsize)
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    # PLOT CODE
    # panel 1
    t_str = 'Surface TIC'
    ax = fig.add_subplot(121)
    vn = 'TIC'
    cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
            vlims=vlims[vn], cmap='YlOrBr')
    fig.colorbar(cs)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')
    pfun.add_info(ax, in_dict['fn'])
    pfun.add_windstress_flower(ax, ds)
    # panel 2
    t_str = 'Surface Alkalinity'
    ax = fig.add_subplot(122)
    vn = 'alkalinity'
    cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
            vlims=vlims[vn], cmap='RdYlGn')
    fig.colorbar(cs)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')
    pfun.add_velocity_vectors(ax, ds, in_dict['fn'])

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict

def P_bio(in_dict):
    # START
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    vn_list = ['NO3', 'phytoplankton', 'zooplankton', 'oxygen']
    cmap_list = ['Oranges', 'Greens', 'BuPu', 'Spectral']
    cmap_dict = dict(zip(vn_list, cmap_list))
    NP = len(vn_list)
    if False:
        NR = np.maximum(1, np.ceil(np.sqrt(NP)).astype(int))
        NC = np.ceil(np.sqrt(NP)).astype(int)
        figsize = (16,16)
    else:
        NR = 1
        NC = NP
        figsize=(23, 7)
    fig, axes = plt.subplots(nrows=NR, ncols=NC, figsize=figsize,
                             squeeze=False)
    cc = 0
    for vn in vn_list:
        ir = int(np.floor(cc/NC))
        ic = int(cc - NC*ir)
        # PLOT CODE
        ax = axes[ir, ic]
        t_str = vn
        try:
            vlims[vn]
        except KeyError:
            vlims[vn] = ()
        if vn == 'oxygen':
            cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
                vlims=vlims[vn], cmap=cmap_dict[vn], slev=0)
            ax.text(.95, .04, 'BOTTOM',
                    horizontalalignment='right', transform=ax.transAxes)
        else:
            cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
                vlims=vlims[vn], cmap=cmap_dict[vn])
        fig.colorbar(cs, ax=ax)
        pfun.add_bathy_contours(ax, ds)
        pfun.add_coast(ax)
        ax.axis(pfun.get_aa(ds))
        pfun.dar(ax)
        ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')
        if ir == NR-1:
            ax.set_xlabel('Longitude')
        if ic == 0:
            ax.set_ylabel('Latitude')
        ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')
        if cc == 0:
            pfun.add_info(ax, in_dict['fn'])
        cc += 1

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict

def P_layer(in_dict):
    # START
    fig = plt.figure(figsize=figsize)
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    # PLOT CODE
    zfull = pfun.get_zfull(ds, in_dict['fn'], 'rho')
    # panel 1
    t_str = 'Salinity'
    ax = fig.add_subplot(121)
    vn = 'salt'
    laym = pfun.get_laym(ds, zfull, ds['mask_rho'][:], vn, in_dict['z_level'])
    if len(vlims[vn]) == 0:
        vlims[vn] = pfun.auto_lims(laym)
    out_dict['vlims'][vn] = vlims[vn]
    cs = ax.pcolormesh(ds['lon_psi'][:], ds['lat_psi'][:], laym[1:-1,1:-1],
                       vmin=vlims[vn][0], vmax=vlims[vn][1], cmap='rainbow')
    cb = fig.colorbar(cs)
    cb.formatter.set_useOffset(False)
    cb.update_ticks()
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(t_str + ' on Z = ' + str(in_dict['z_level']) + ' m')
    pfun.add_info(ax, in_dict['fn'])
    pfun.add_windstress_flower(ax, ds)
    # panel 2
    t_str = 'Temperature'
    ax = fig.add_subplot(122)
    vn = 'temp'
    laym = pfun.get_laym(ds, zfull, ds['mask_rho'][:], vn, in_dict['z_level'])
    if len(vlims[vn]) == 0:
        vlims[vn] = pfun.auto_lims(laym)
    out_dict['vlims'][vn] = vlims[vn]
    cs = ax.pcolormesh(ds['lon_psi'][:], ds['lat_psi'][:], laym[1:-1,1:-1],
                       vmin=vlims[vn][0], vmax=vlims[vn][1], cmap='bwr')
    cb = fig.colorbar(cs)
    cb.formatter.set_useOffset(False)
    cb.update_ticks()
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_title(t_str + ' (' + pfun.get_units(ds, vn) + ')')

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict

def P_nest_plot(in_dict):
    # plots a field nested inside the corresponding HYCOM field
    # - currently only works for salt and temp -

    # START
    fig = plt.figure(figsize=figsize)
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    # PLOT CODE
    # ** choose the variable to plot **
    which_var = 'temp'
    # need to get Ldir, which means unpacking gtagex
    fn = in_dict['fn']
    gtagex = fn.split('/')[-3]
    gtx_list = gtagex.split('_')
    import Lfun
    Ldir = Lfun.Lstart(gtx_list[0], gtx_list[1])
    # Get HYCOM field
    hyvar_dict = {'temp':'t3d', 'salt':'s3d'}
    hvar = hyvar_dict[which_var]
    f_string = fn.split('/')[-2]
    fnhy = (Ldir['LOo'] + Ldir['gtag'] + '/' + f_string +
        '/ocn/Data/' + hvar + '.nc')
    ds = nc.Dataset(fnhy)
    lon = ds.variables['lon'][:]
    lat = ds.variables['lat'][:]
    z = ds.variables['z'][:]
    # make sure zlev is in the HYCOM z
    zlev = zfun.find_nearest(z, in_dict['z_level'])
    nz = list(z).index(zlev)
    laym_hy = ds.variables[hvar + '_filt'][0,nz,:,:].squeeze()
    vlims = pfun.auto_lims(laym_hy)
    ds.close()
    aa = [lon.min(), lon.max(), lat.min(), lat.max()]
    # Get ROMS field
    ds = nc.Dataset(fn)
    zfull = pfun.get_zfull(ds, fn, 'rho')
    laym = pfun.get_laym(ds, zfull, ds['mask_rho'][:], which_var, zlev)

    # PLOTTING
    cmap = plt.get_cmap(name='gist_ncar')
    plt.close()
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=figsize, squeeze=False)
    # panel 1
    ax = axes[0,0]
    ax.set_title('HYCOM: z=' + str(zlev) + 'm, var=' + which_var)
    cs = ax.pcolormesh(lon, lat, laym_hy,
                       vmin=vlims[0], vmax=vlims[1], cmap = cmap)
    ax.axis(aa)
    fig.colorbar(cs, ax=ax)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    # panel 2
    ax = axes[0,1]
    ax.set_title('HYCOM + ROMS')
    cs = ax.pcolormesh(lon, lat, laym_hy,
                       vmin=vlims[0], vmax=vlims[1], cmap = cmap)
    ax.axis(aa)
    laymd = laym.data
    laymd[laym.mask] = 1e6
    ax.pcolormesh(ds['lon_psi'][:], ds['lat_psi'][:], laymd[1:-1,1:-1],
                  vmin=vlims[0], vmax=vlims[1], cmap = cmap)
    fig.colorbar(cs, ax=ax)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    pfun.dar(ax)
    ax.set_xlabel('Longitude')

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict

def P_roms_sect(in_dict):
    # plots a section (distance, z)

    # START
    fig = plt.figure(figsize=(20,8))
    ds = nc.Dataset(in_dict['fn'])
    vlims = in_dict['vlims'].copy()
    out_dict['vlims'] = vlims

    # PLOT CODE

    # GET DATA
    G, S, T = zrfun.get_basic_info(in_dict['fn'])
    h = G['h']
    zeta = ds['zeta'][:].squeeze()
    zr = zrfun.get_z(h, zeta, S, only_rho=True)

    varname = 'salt'
    try:
        vlims[varname]
    except KeyError:
        vlims[varname] = ()

    sectvar = ds[varname][:].squeeze()

    L = G['L']
    M = G['M']
    N = S['N']

    lon = G['lon_rho']
    lat = G['lat_rho']
    mask = G['mask_rho']
    maskr = mask.reshape(1, M, L).copy()
    mask3 = np.tile(maskr, [N, 1, 1])
    zbot = -h # don't need .copy() because of the minus operation

    # make sure fields are masked
    zeta[mask==False] = np.nan
    zbot[mask==False] = np.nan
    sectvar[mask3==False] = np.nan

    # CREATE THE SECTION
    # create track by hand
    if False:
        x = np.linspace(lon.min(), -124, 500)
        y = 47 * np.ones(x.shape)
    # or read one in
    else:
        import Lfun
        Ldir = Lfun.Lstart()
        tracks_path = Ldir['data'] + 'tracks/'
        which_track = 'jdf2psTrack'
        # get the track to interpolate onto
        mat = matfun.loadmat(tracks_path + which_track + '.mat')
        x = mat['x']
        y = mat['y']

    # create dist
    earth_rad = zfun.earth_rad(np.mean(lat[:,0])) # m
    xrad = np.pi * x /180
    yrad = np.pi * y / 180
    dx = earth_rad * np.cos(yrad[1:]) * np.diff(xrad)
    dy = earth_rad * np.diff(yrad)
    ddist = np.sqrt(dx**2 + dy**2)
    dist = np.zeros(len(x))
    dist[1:] = ddist.cumsum()/1000 # km
    # find the index of zero
    i0, i1, fr = zfun.get_interpolant(np.zeros(1), dist)
    idist0 = i0
    distr = dist.reshape(1, len(dist)).copy()
    dista = np.tile(distr, [N, 1]) # array
    # pack fields to process in dicts
    d2 = dict()
    d2['zbot'] = zbot
    d2['zeta'] = zeta
    d2['lon'] = lon
    d2['lat'] = lat
    d3 = dict()
    d3['zr'] = zr
    d3['sectvar'] = sectvar
    # get vectors describing the (plaid) grid
    xx = lon[1,:]
    yy = lat[:,1]
    col0, col1, colf = zfun.get_interpolant(x, xx)
    row0, row1, rowf = zfun.get_interpolant(y, yy)
    # and prepare them to do the bilinear interpolation
    colff = 1 - colf
    rowff = 1 - rowf
    # now actually do the interpolation
    # 2-D fields
    v2 = dict()
    for fname in d2.keys():
        fld = d2[fname]
        fldi = (rowff*(colff*fld[row0, col0] + colf*fld[row0, col1])
        + rowf*(colff*fld[row1, col0] + colf*fld[row1, col1]))
        if type(fldi) == np.ma.core.MaskedArray:
            fldi = fldi.data # just the data, not the mask
        v2[fname] = fldi
    # 3-D fields
    v3 = dict()
    for fname in d3.keys():
        fld = d3[fname]
        fldi = (rowff*(colff*fld[:, row0, col0] + colf*fld[:, row0, col1])
        + rowf*(colff*fld[:, row1, col0] + colf*fld[:, row1, col1]))
        if type(fldi) == np.ma.core.MaskedArray:
            fldid = fldi.data # just the data, not the mask
            fldid[fldi.mask == True] = np.nan
        v3[fname] = fldidlobio1
    v3['dist'] = dista # distance in km
    # make "full" fields by padding top and bottom
    nana = np.nan * np.ones((N + 2, len(dist))) # blank array
    v3['zrf'] = nana.copy()
    v3['zrf'][0,:] = v2['zbot']
    v3['zrf'][1:-1,:] = v3['zr']
    v3['zrf'][-1,:] = v2['zeta']
    #
    v3['sectvarf'] = nana.copy()
    v3['sectvarf'][0,:] = v3['sectvar'][0,:]
    v3['sectvarf'][1:-1,:] = v3['sectvar']
    v3['sectvarf'][-1,:] = v3['sectvar'][-1,:]
    #
    v3['distf'] = nana.copy()
    v3['distf'][0,:] = v3['dist'][0,:]
    v3['distf'][1:-1,:] = v3['dist']
    v3['distf'][-1,:] = v3['dist'][-1,:]
    # NOTE: should make this a function
    # (but note that it is specific to each variable)

    # PLOTTING

    # panel 1
    ax = fig.add_subplot(1, 3, 1)
    vn = varname
    cs, out_dict['vlims'][vn] = pfun.add_map_field(ax, ds, vn,
            vlims=vlims[vn], cmap='rainbow')
    fig.colorbar(cs)
    pfun.add_bathy_contours(ax, ds)
    pfun.add_coast(ax)
    ax.axis(pfun.get_aa(ds))
    pfun.dar(ax)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Bathymetry and Section Track')
    pfun.add_info(ax, in_dict['fn'])
    pfun.add_windstress_flower(ax, ds)
    ax.plot(x, y, '-r', linewidth=2)
    ax.plot(x[idist0], y[idist0], 'or', markersize=10, markerfacecolor='w',
    markeredgecolor='r', markeredgewidth=2)

    # section
    ax = fig.add_subplot(1, 3, (2, 3))
    ax.plot(dist, v2['zbot'], '-k', linewidth=2)
    ax.plot(dist, v2['zeta'], '-b', linewidth=1)
    ax.set_xlim(dist.min(), dist.max())
    ax.set_ylim(in_dict['z_level'], 5)
    vlims = pfun.auto_lims(v3['sectvarf'])
    cs = ax.pcolormesh(v3['distf'], v3['zrf'], v3['sectvarf'],
                       vmin=vlims[0],
                       vmax=vlims[1],
                       cmap='rainbow')
    fig.colorbar(cs)
    cs = ax.contour(v3['distf'], v3['zrf'], v3['sectvarf'],
        np.linspace(np.floor(vlims[0]), np.ceil(vlims[1]), 20), colors='k')
    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Z (m)')
    ax.set_title(varname)

    # FINISH
    ds.close()
    if len(in_dict['fn_out']) > 0:
        plt.savefig(in_dict['fn_out'])
        plt.close()
    else:
        plt.show()
    return out_dict
