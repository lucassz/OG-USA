from __future__ import print_function
'''
------------------------------------------------------------------------
Last updated 4/7/2015

Miscellaneous functions for SS.py and TPI.py.

------------------------------------------------------------------------
'''

# Packages
import os
from io import StringIO
import numpy as np
import taxcalc
try:
    import cPickle as pickle
except ImportError:
    import pickle
from pkg_resources import resource_stream, Requirement

EPSILON = 1e-10
PATH_EXISTS_ERRNO = 17

REFORM_DIR = "./OUTPUT_REFORM"
BASELINE_DIR = "./OUTPUT_BASELINE"

# Default year for model runs
DEFAULT_START_YEAR = 2018

# Latest year TaxData extrapolates to
TC_LAST_YEAR = 2027

# Year of data used (e.g. PUF or CPS year)
CPS_START_YEAR = taxcalc.Records.CPSCSV_YEAR
PUF_START_YEAR = taxcalc.Records.PUFCSV_YEAR

# for f in (REFORM_DIR, BASELINE_DIR):
#     if not os.path.exists(f):
#         os.mkdir(f)


def mkdirs(path):
    '''
    Makes directories to save output.

    Inputs:
        path = string, path name for new directory

    Functions called: None

    Objects in function:

    Returns: N/A
    '''

    try:
        os.makedirs(path)
    except OSError as oe:
        if oe.errno == PATH_EXISTS_ERRNO:
            pass


def pct_diff_func(simul, data):
    '''
    Used to calculate the absolute percent difference between data
    moments and model moments.

    Inputs:
        simul = any shape, model moments
        data  = same shape as simul, data moments

    Functions called: None

    Objects in function:
        frac   = same shape as simul, percent difference between data and model moments
        output = same shape as simul, absolute percent difference between data and model moments

    Returns: output
    '''

    frac = (simul - data) / data
    output = np.abs(frac)
    return output


def convex_combo(var1, var2, nu):
    '''
    Takes the convex combination of two variables, where nu is in [0,1].

    Inputs:
        var1 = any shape, variable 1
        var2 = same shape as var1, variable 2
        nu   = scalar, weight on var1 in convex combination

    Functions called: None

    Objects in function:
        combo = same shape as var1, convex combination of var1 and var2

    Returns: combo
    '''

    combo = nu * var1 + (1 - nu) * var2
    return combo




def read_file(path, fname):
    '''
    Read the contents of 'path'. If it does not exist, assume the file
    is installed in a .egg file, and adjust accordingly.

    Inputs:
        path  = string, path name for new directory
        fname = string, filename

    Functions called: None

    Objects in function:
        path_in_egg
        buf
        _bytes

    Returns: file contents
    '''

    if not os.path.exists(os.path.join(path, fname)):
        path_in_egg = os.path.join("ogusa", fname)
        buf = resource_stream(Requirement.parse("ogusa"), path_in_egg)
        _bytes = buf.read()
        return StringIO(_bytes.decode("utf-8"))
    else:
        return open(os.path.join(path, fname))


def pickle_file_compare(fname1, fname2, tol=1e-3, exceptions={}, relative=False):
    '''
    Read two pickle files and unpickle each. We assume that each resulting
    object is a dictionary. The values of each dict are either numpy arrays
    or else types that are comparable with the == operator.

    Inputs:
        fname1  = string, file name of file 1
        fname2  = string, file name of file 2
        tol     = scalar, tolerance
        exceptions = dictionary, exceptions
        relative = boolean,

    Functions called:
        dict_compare

    Objects in function:
        pkl1 =  dictionary, from first pickle file
        pkl2 = dictionary, from second pickle file

    Returns: difference between dictionaries
    '''
    try:
        pkl1 = pickle.load(open(fname1, 'rb'), encoding='latin1')
    except TypeError:
        pkl1 = pickle.load(open(fname1, 'rb'))
    try:
        pkl2 = pickle.load(open(fname2, 'rb'), encoding='latin1')
    except TypeError:
        pkl2 = pickle.load(open(fname2, 'rb'))

    return dict_compare(fname1, pkl1, fname2, pkl2, tol=tol,
                        exceptions=exceptions, relative=relative)


def comp_array(name, a, b, tol, unequal, exceptions={}, relative=False):
    '''
    Compare two arrays in the L inifinity norm
    Return True if | a - b | < tol, False otherwise
    If not equal, add items to the unequal list
    name: the name of the value being compared

    Inputs:


    Functions called:


    Objects in function:


    Returns: Boolean


    '''

    if name in exceptions:
        tol = exceptions[name]

    if not a.shape == b.shape:
        print("unequal shpaes for {0} comparison ".format(str(name)))
        unequal.append((str(name), a, b))
        return False

    else:

        if np.all(a < EPSILON) and np.all(b < EPSILON):
            return True

        if relative:
            err = abs(a - b)
            mn = np.mean(b)
            err = np.max(err / mn)
        else:
            err = np.max(abs(a - b))

        if not err < tol:
            print("diff for {0} is {1} which is NOT OK".format(str(name), err))
            unequal.append((str(name), a, b))
            return False
        else:
            print("err is {0} which is OK".format(err))
            return True


def comp_scalar(name, a, b, tol, unequal, exceptions={}, relative=False):
    '''
    Compare two scalars in the L inifinity norm
    Return True if abs(a - b) < tol, False otherwise
    If not equal, add items to the unequal list
    '''

    if name in exceptions:
        tol = exceptions[name]

    if (a < EPSILON) and (b < EPSILON):
        return True

    if relative:
        err = float(abs(a - b)) / float(b)
    else:
        err = abs(a - b)

    if not err < tol:
        print("err for {0} is {1} which is NOT OK".format(str(name), err))
        unequal.append((str(name), str(a), str(b)))
        return False
    else:
        print("err is {0} which is OK".format(err))
        return True


def dict_compare(fname1, pkl1, fname2, pkl2, tol, verbose=False,
                 exceptions={}, relative=False):
    '''
    Compare two dictionaries. The values of each dict are either
    numpy arrays
    or else types that are comparable with the == operator.
    For arrays, they are considered the same if |x - y| < tol in
    the L_inf norm.
    For scalars, they are considered the same if x - y < tol
    '''

    keys1 = set(pkl1.keys())
    keys2 = set(pkl2.keys())
    check = True
    if keys1 != keys2:
        if len(keys1) == len(keys2):
            extra1 = keys1 - keys2
            extra2 = keys2 - keys1
            msg1 = "extra items in {0}: {1}"
            print(msg1.format(fname1, extra1))
            print(msg1.format(fname2, extra2))
            return False
        elif len(keys1) > len(keys2):
            bigger = keys1
            bigger_file = fname1
            smaller = keys2
        else:
            bigger = keys2
            bigger_file = fname2
            smaller = keys1
        res = bigger - smaller
        msg = "more items in {0}: {1}"
        print(msg.format(bigger_file, res))
        return False
    else:
        unequal_items = []
        for k, v in pkl1.items():
            if type(v) == np.ndarray:
                check &= comp_array(k, v, pkl2[k], tol, unequal_items,
                                    exceptions=exceptions, relative=relative)
            else:
                try:
                    check &= comp_scalar(k, v, pkl2[k], tol, unequal_items,
                                         exceptions=exceptions, relative=relative)
                except TypeError:
                    check &= comp_array(k, np.array(v), np.array(pkl2[k]), tol,
                                        unequal_items, exceptions=exceptions,
                                        relative=relative)

        if verbose and unequal_items:
            frmt = "Name {0}"
            res = [frmt.format(x[0]) for x in unequal_items]
            print("Different arrays: ", res)
            return False

    return check


def safe_read_pickle(file_path):
    '''
    This function reads a pickle from Python 2 into Python 2 or Python 3
    '''
    with open(file_path, 'rb') as f:
        try:
            obj = pickle.load(f, encoding='latin1')
        except TypeError:
            obj = pickle.load(f)
    return obj
