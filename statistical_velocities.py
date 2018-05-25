#!/usr/bin/env python 

###### James Wild, May 2018 ######
# This is a script to analyse PSEC files with laser triggering. It needs to 
# do the following:
#
# - Read in data from the PSEC logfile
# - Channel 5 contains the Laser pulse. The leading edge time should be 
#    found. This can be done with a threshold voltage
# - If the rise time is in the first 10ns, continue. Otherwise discard the
#    sample.
# - Check if any of the other channels observe a signal
# - If they do, integrate the pulse and get its time difference 
# - Calculate the position and the number of incident photons
# - Calculate the QE. This will be the Number of laser signals followed by a 
#    pulse, divided by the total number of laser signals detected in the 
#    initial 10ns

import matplotlib.pyplot as plt

import numpy as np
import os
from Tkinter import *
import tkFileDialog
import tkMessageBox
import bokeh.plotting as bkh
from scipy import optimize
from bokeh.models import Span
from scipy import stats

def gaussian(x, height, center, width):
    return height*np.exp(-(x - center)**2/(2*width**2))

def two_gaussians(x, h1, c1, w1, h2, c2, w2):
    return (gaussian(x, h1, c1, w1) +
        gaussian(x, h2, c2, w2))

def three_gaussians(x, h1, c1, w1, h2, c2, w2, h3, c3, w3):
    return (two_gaussians(x, h1, c1, w1, h2, c2, w2) +
        gaussian(x, h3, c3, w3))

def get_laser_pulse(sample):
    # The laser is on channel 5
    volts = sample[4,:]
    ts = np.arange(0.0, 25.6, 0.1) #ns

    # Threshold crossing, laser pulses are < -60mv
    risetime = np.argmax(volts < -0.100)
    risetime = ts[risetime]

    # If the risetime is within the first 10ns, we want to continue
    if risetime < 5.0 and risetime > 0.0:
        return risetime
    else:
        # print("Laser too late; %.2lf" % risetime)
        return None

# Chisq error function
errfunc = lambda p, x, y: (two_gaussians(x, *p) - y)**2

def analyse(sample, ch):
    # If we don't get any pulse in the sample, return None
    time_difference = None

    ## Fit a double gaussian to the data ##
    volts = sample[ch,:]
    #Make a maller version of ts to use for individual samples
    ts = np.arange(0.0, 25.6, 0.1)

    ## Is there a pulse in this channel?
    # Establish the noise level from channel 4
    zeropoint = np.mean(sample[3])
    # Get the standard deviation of the noise
    scatter = np.std(sample[3])
    # Sum data that are more than 3 sigma from the mean
    lowerlim = zeropoint - (3.5*scatter)

    # Make an array of the values that exceed our computed noise level
    pulse = np.where(volts < lowerlim)

    # If there is a pulse,
    if np.sum(pulse) > 0:
        # Calculate the time delay between peaks

        # Guess the locations of the gaussians
        halfmax_volt = 0.5 * np.amin(volts)
        halfmax_t1 = np.argmax(volts<halfmax_volt)
        halfmax_t1 = ts[halfmax_t1]

        halfmax_t2 = np.argmax(volts[::-1] < halfmax_volt)
        halfmax_t2 = ts[-1*halfmax_t2]

        # Initial solution guesses two peaks at the leading abd trailing edges
               #   h1,   c1,   w1]
        guess = [halfmax_volt, halfmax_t1, 0.1,
                halfmax_volt, halfmax_t2, 0.1,
                # np.mean(sample[2,:])  # y offset
                ]

        # Optimise gaussian with a chisq fit
        optim, success = optimize.leastsq(errfunc, guess[:], args=(ts, volts))

        # Get the time differences
        time_difference = abs(optim[4]-optim[1])*1e-9 # Convert to ns

    return time_difference

# fnames.txt contains a list of all the files to analyse.
fnames = []
with open('fnames.txt', 'r') as f:
    for line in f:
        line = line.strip()
        fnames.append(line)

#Make a maller version of ts to use for individual samples
ts = np.arange(0.0, 25.6, 0.1)

dt = 100e-12 # 100ps time resolution

# List of the delta t
velocities = []
max_velocities = []

y = 0

for fname in fnames:
    velocities = []
    # Open the file and read in a sample at a time
    with open(fname, 'r') as f:
        sample = np.zeros((6, 256))
        # i counts the number of data in the sample
        i = 0
        for line in f:
            if line[0] == '#':
                continue
            if i == 256:
                # Get the time difference of each channel
                for ch in [0,1,2,4,5]:
                    delta_ts = analyse(sample, ch)
                    if delta_ts != None:
                        velocities.append(12e-2/delta_ts)

                # Reset array
                sample = np.zeros((6,256))
                i = 0

            # Read the data into array
            try:
                sample[:,i] = np.array([float(x) for x in line.split()])[:6]
                i += 1
            except:
                break

    if velocities != []:
        # Get the max velocity. Remove values that are too large.
        velocities = np.array(velocities)
        velocities = velocities[velocities < 3e8]
        max_velocities.append(np.max(velocities))

    y += 1
    print("Done %d of %d" % (y, len(fnames)))

# with open('max_velocities.txt', 'r') as f:
#     for line in f:
#         max_velocities.append(float(line))

max_velocities = np.array(max_velocities)

mean = np.mean(max_velocities)
std  = np.std(max_velocities)
standard_error = std/max_velocities.shape[0]

print("Mean Velocity: %.3g" % mean)
print("Standard Deviation: %.3g" % std)
print("Standard error: %.3g" % standard_error)

plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig, ax = plt.subplots(figsize=[10,6])
N, bins, patches = ax.hist(np.log10(max_velocities),
    bins=20, range=[8.0, 9.0],
    facecolor='green', edgecolor='black')
ax.set_xlabel(r'$log_{10}$(Velocity, m/s)')
ax.set_ylabel(r'Frequency')
plt.tight_layout()
plt.show()

with open('max_velocities.txt', 'w') as f:
    for v in max_velocities:
        f.write(str(v)+'\n')
