"""
Code for particle tracking, designed for ROMS output.  This new version
makes extensive use of nearest-neighbor KDTree algorithms for interpolation.
This results is significantly (36x) faster runtimes compared with tracker/tracker_1.py.

NOTE: You have to have run make_KDTrees.py for the grid (e.g. cas6) before running.

NOTE: There is some issue, perhaps with garbage collection, which causes
the loading of NetCDF files to happen slower after running a few times
interactively from ipython.  It appears that this can be avoided by running
from the terminal as: python tracker.py [args].

This program is a driver where you specify:
- an experiment (ROMS run + release locations + other choices)
- a release or set of releases within that experiment (start day, etc.)

The main argument you provide is -exp, which is the experiment name, and
is used by experiments.get_exp_info() and .get_ic() to get the gtagex and initial particle
locations.  Other possible commmand line arguments and their defaults
are explained in the argparse section below.

NOTE: To improve usefulness for people other than me, this driver will
first look for:
- LiveOcean_user/tracker2/user_experiments.py and
- LiveOcean_user/tracker2/user_trackfun.py
before loading my versions.
This allows you to create yout own experiments, and modifications
to the tracking (e.g. for diurnal depth behavior) while still being able
to use git pull to update the main code.

It can be run on its own, or with command line arguments to facilitate
large, automated jobs, for example in python:
    
[examples under construction]

"""

# setup
from datetime import datetime, timedelta
import time
import argparse
import numpy as np

import os; import sys
sys.path.append(os.path.abspath('../alpha'))
import Lfun
Ldir = Lfun.Lstart()

from importlib import reload

if os.path.isfile(Ldir['LOu'] + 'tracker2/user_experiments.py'):
    sys.path.append(os.path.abspath(Ldir['LOu'] + 'tracker2'))
    import user_experiments as exp
else:
    import experiments as exp
reload(exp)

import trackfun_nc as tfnc

# The import of trackfun or user_trackfun is done later in this program,
# about 100 lines down.

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def boolean_string(s):
    if s not in ['False', 'True']:
        raise ValueError('Not a valid boolean string')
    return s == 'True' # note use of ==
    
# optional command line arguments, can be input in any order
parser = argparse.ArgumentParser()

# Set the experiment name
# (details set in experiments.py, or, if it exists, user_experiments.py)
parser.add_argument('-exp', '--exp_name', default='fast0', type=str)
parser.add_argument('-clb', '--clobber', default=False, type=boolean_string)
# overwrite existing output folder if clobber == True

# These are False unless the flags are used with the argument True
# so if you do NOT use these flags the run will be:
# - trapped to the surface
# - no vertical turbulent diffusion
parser.add_argument('-3d', default=False, type=boolean_string) # do 3d tracking
parser.add_argument('-laminar', default=False, type=boolean_string) # no turbulence

# windage = a small number: 0 <= windage << 1 (e.g. 0.03)
# fraction of windspeed added to advection, only for 3d=False
parser.add_argument('-wnd', '--windage', default=0, type=float)

# set the starting day
parser.add_argument('-ds', '--ds_first_day', default='2019.07.04', type=str)

# You can make multiple releases using:
# number_of_start_days > 1 & days_between_starts
parser.add_argument('-nsd', '--number_of_start_days', default=1, type=int)
parser.add_argument('-dbs', '--days_between_starts', default=1, type=int)
parser.add_argument('-dtt', '--days_to_track', default=1, type=int)

# number of divisions to make between saves for the integration
# e.g. if ndiv = 12 and we have hourly saves, we use a 300 sec step
# for the integration. 300 s seems like a good default value,
# based on Banas et al. (2009, CSR RISE paper).
parser.add_argument('-ndiv', default=12, type=int)
parser.add_argument('-sph', default=1, type=int)
# sph = saves per hour, a new argument to allow more frequent writing of output.

# set which roms output directory to look in (refers to Ldir['roms'] or Ldir['roms2'])
parser.add_argument('-rd', '--roms_dir', default='roms', type=str)
# valid arguments to pass are: roms, roms2

args = parser.parse_args()
TR = args.__dict__ 
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# set dependent and default fields

TR['turb'] = False

# make sure sph is no greater than ndiv
TR['sph'] = np.min((TR['sph'],TR['ndiv']))

# overrides
if TR['3d']:
    TR['windage'] = 0
    TR['turb'] = True # default is that 3d is always turbulent
    
if TR['laminar']:
    TR['turb'] = False

# get experiment info, including initial condition
EI = exp.get_exp_info(TR['exp_name'])
TR['gtagex'] = EI['gtagex']
TR['gridname'] = EI['gridname']
TR['ic_name'] = EI['ic_name']

# get the full path to a valid history file
fn00 = Ldir['roms'] + 'output/' + TR['gtagex'] + '/f' + TR['ds_first_day'] + '/ocean_his_0001.nc'
TR['fn00'] = fn00

# pass some info to Ldir
Ldir['gtagex'] = TR['gtagex']
Ldir['roms'] = Ldir[TR['roms_dir']]

# set the name of the output folder
out_name = TR['exp_name']
out_name += '_ndiv' + str(TR['ndiv'])
# modify the output folder name, based on other choices
if TR['3d']:
    out_name += '_3d'
elif not TR['3d']:
    out_name += '_surf'
if TR['laminar']:
    out_name += '_laminar'
if TR['windage'] > 0:
    out_name += '_wind' + str(int(100*TR['windage']))

# make the list of start days (datetimes) for separate releases
idt_list = []
dt = datetime.strptime(TR['ds_first_day'], '%Y.%m.%d')
for nic in range(TR['number_of_start_days']):
    idt_list.append(dt)
    dt = dt + timedelta(TR['days_between_starts'])

# make sure the output parent directory "tracks2" exists
outdir00 = Ldir['LOo']
Lfun.make_dir(outdir00)
outdir0 = Ldir['LOo'] + 'tracks2/'
Lfun.make_dir(outdir0)

# make the output directory (empty)
outdir1 = out_name + '/'
outdir = outdir0 + outdir1
if os.path.isdir(outdir):
    if args.clobber:
        pass # continue and overwrite if clobber is True
    else:
        print('Warning: output directory exists - rename if you want to keep it!!')
        sys.exit()
Lfun.make_dir(outdir, clean=True)
print(50*'*' + '\nWriting to ' + outdir)
sys.stdout.flush()

# and write some info to outdir0 for use by trackfun.py
Lfun.dict_to_csv(TR,outdir0 + 'exp_info.csv')
# and write the same info to outdir
Lfun.dict_to_csv(TR, outdir + 'exp_info.csv')

# Load the trackfun module.
# NOTE: we have to load this module AFTER we write [outdir0]/exp_info.csv
# because it uses that information to decide which KDTrees to load.  Crude.
if os.path.isfile(Ldir['LOu'] + 'tracker2/user_trackfun.py'):
    sys.path.append(os.path.abspath(Ldir['LOu'] + 'tracker2'))
    import user_trackfun as tfun
else:
    import trackfun as tfun
reload(tfun)

# get the initial particle location vectors
plon00, plat00, pcs00 = exp.get_ic(TR['ic_name'], fn00)

# calculate total number of times per release for NetCDF output
NT_full = (TR['sph']*24*TR['days_to_track']) + 1

# step through the releases, one for each start day
write_grid = True
for idt0 in idt_list:
    tt0 = time.time() # monitor integration time
    
    # name the release file by start day
    idt0_str = datetime.strftime(idt0,'%Y.%m.%d')
    outname = ('release_' + idt0_str + '.nc')
    print('-- ' + outname)
    sys.stdout.flush()
    out_fn = outdir + outname
    
    # we do the calculation in one-day segments, but write complete
    # output for a release to a single NetCDF file.
    for nd in range(TR['days_to_track']):
        
        # get or replace the history file list for this day
        idt = idt0 + timedelta(days=nd)
        idt_str = datetime.strftime(idt,'%Y.%m.%d')
        print(' - working on ' + idt_str)
        sys.stdout.flush()
        fn_list = tfun.get_fn_list(idt, Ldir)
        
        # write the grid file (once per experiment) for plotting
        if write_grid == True:
            g_infile = fn_list[0]
            g_outfile = outdir + 'grid.nc'
            tfnc.write_grid(g_infile, g_outfile)
            write_grid = False
           
        # DO THE TRACKING
        if nd == 0: # first day
            # set IC
            plon0 = plon00.copy()
            plat0 = plat00.copy()
            pcs0 = pcs00.copy()
            # do the tracking
            P = tfun.get_tracks(fn_list, plon0, plat0, pcs0, TR, trim_loc=True)
            it0 = 0
            it1 = TR['sph']*24 + 1
            # save the results to NetCDF
            tfnc.start_outfile(out_fn, P, NT_full, it0, it1)
        else: # subsequent days
            # set IC
            plon0 = P['lon'][-1,:]
            plat0 = P['lat'][-1,:]
            pcs0 = P['cs'][-1,:]
            # do the tracking
            P = tfun.get_tracks(fn_list, plon0, plat0, pcs0, TR)
            it0 = TR['sph']*24*nd
            it1 = it0 +  TR['sph']*24 + 1
            tfnc.append_to_outfile(out_fn, P, it0, it1)
            
    print(' - Took %0.1f sec for %s day(s)' %
            (time.time() - tt0, str(TR['days_to_track'])))
    print(50*'=')
