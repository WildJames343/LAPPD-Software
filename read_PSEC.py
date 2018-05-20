#!/usr/bin/env python
import os
import datetime
import subprocess
import numpy as np

def read(fname):
    '''takes a PSEC4 log file, reads it and plots it to a bokeh file. 
     <fname> = file to open and read
    Returns: t, samples
     <t> = a numpy array that has the time axis
     <samples> = A dictionary containing the data samples. Each sample is a 
            6x256 numpy array with the data in.'''

    if not os.path.isfile(fname):
        print("ERROR: File not found...")
        return [], {}
    f = open(fname, 'r')

    # Samples is a list, and each sample contains
    #  a set of 6 lists which are the channels readings
    samples = {}
    channels = np.zeros((6,256))
    t = [0.0]

    j = 0
    n = 0
    vmin = 0.
    vmax = 0.
    for line in f:
        # Skip over headers
        if line[0] == '#':
            continue
        else:
            # voltage is stored in Volts, convert to mV.
            line = [float(x)*1000. for x in line.split()]
            
            try:
                # Get the data for each channel into the lists
                for i in range(6):
                    channels[i][j%256] = line[i]
                    if line[i] > vmax:
                        vmax = float(line[i])
                    if line[i] < vmin:
                        vmin = float(line[i])
                j += 1
            except:
                # Catch if the file's line is incomplete
                print("ERROR: bad line")
                print(line)
        # If I detect a header, 
        if j%256 == 0:
            samples[str(n)] = channels.copy()
            channels = np.zeros((6,256))
            n += 1

    f.close()

    # Construct a time array as well
    t = np.arange(0.0, 25.6*n, step=0.1)

    return t, samples