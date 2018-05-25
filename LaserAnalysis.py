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


# Toggle plotting
plot = 1

def chisquare(fobs, fgen):
    chi = 0.0
    k = 0.
    for obs, gen in zip(fobs, fgen):
        if obs == 0 or gen == 0:
            continue
        chi += (float(obs)-float(gen))**2/float(abs(obs))
        k += 1.
    return chi/k


#Fit a double gaussian to the TTS data
def gaussian(x, height, center, width):
    return height*np.exp(-(x - center)**2/(2*width**2))

def two_gaussians(x, h1, c1, w1, h2, c2, w2):
    return (gaussian(x, h1, c1, w1) +
        gaussian(x, h2, c2, w2))

def three_gaussians(x, h1, c1, w1, h2, c2, w2, h3, c3, w3):
    return (two_gaussians(x, h1, c1, w1, h2, c2, w2) +
        gaussian(x, h3, c3, w3))

# Chisq error function
errfunc = lambda p, x, y: (two_gaussians(x, *p) - y)**2
errfunc = lambda p, x, y: (gaussian(x, *p) - y)**2

# Guess the locations of the gaussians
       #   h1,   c1,   w1]
guess = [1750, 17.1, 0.1,
        # 500, 18.8, 0.2,
        # 250, 17.7, 1.5,
]


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

def analyse(sample, ch):
    ## Fit a double gaussian to the data ##
    volts = sample[ch,:]
    #Make a maller version of ts to use for individual samples
    ts = np.arange(0.0, 25.6, 0.1)

    # Chisq error function
    errfunc = lambda p, x, y: (two_gaussians(x, *p) - y)**2

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
            np.mean(sample[2,:]) ] # y offset

    # Optimise gaussian fit
    optim, success = optimize.leastsq(errfunc, guess[:], args=(ts, volts))

    chisq = chisquare(volts, two_gaussians(ts, *optim))
    
    # Pulse arrival time
    arrival_time = min([optim[4], optim[1]])

    # Get the time differences
    time_difference = abs(optim[4]-optim[1])*1e-9 # Convert to ns

    # Calculate the position
    position = 0.06 - (.5*time_difference * electronVelocity)

    ## Integrate the pulse, where it crosses the threshold
    # Establish the noise level from channel 6
    zeropoint = np.mean(sample[-1])
    # Get the standard deviation of the noise
    scatter = np.std(sample[-1])
    # Sum data that are more than 3 sigma from the mean
    lowerlim = zeropoint - (3.5*scatter)

    # Make an array of the values that exceed our computed noise level
    pulse = np.where(volts < lowerlim)
    pulse = volts[pulse]

    # Sum that array
    integrated_voltage = np.sum(pulse)*dt

    # Calculate the gain, assuming a single PE. 
    #  (integrated V)/(electron charge * resistance)
    gain = integrated_voltage / (-1.6e-19 * 50)

    return arrival_time, time_difference, gain, position

fnames = ['20ksamples2.5kV.txt']
# fnames = ['sample.txt']

#Make a maller version of ts to use for individual samples
ts = np.arange(0.0, 25.6, 0.1)

# position = float(raw_input("What position on the tile are we at (cm): "))/100
electronVelocity = 6e7
dt = 100e-12 # 100ps time resolution
# Detection threshold
threshold = -0.007

# Initialise data storage
transit_times = [[],[],[],[],[],[]]
positions = [[],[],[],[],[],[]]
gains = [[],[],[],[],[],[]]

y = 0
d = 0
flag = 0

for fname in fnames:
    # Open the file and read in a sample at a time
    with open(fname, 'r') as f:
        sample = np.zeros((6, 256))
        i = 0
        for line in f:
            if line[0] == '#':
                continue
            if i == 256:
                # Where is the laser pulse?
                laser_time = get_laser_pulse(sample)
                if laser_time != None:
                    y += 1
                    flag = 0
                    for ch in [0,1,2,3,4,5]:
                        # Get if/when the pulse crosses the threshold
                        arrival_time = np.argmax(sample[ch,:] < threshold)
                        # Returns 0 if the threshold isnt reached
                        if arrival_time > 0:
                            # Get timestamp
                            arrival_time = ts[arrival_time]
                            # Get delat between laser and pulse
                            tts = arrival_time - laser_time

                            if tts > 0:
                                if flag == 0:
                                    flag = 1
                                    d += 1
                                transit_times[ch].append(tts)


                # Reset array
                sample = np.zeros((6,256))
                i = 0

            # Read the data into array
            sample[:,i] = np.array([float(x) for x in line.split()])[:6]
            i += 1



junctions = [
    'J31',
    'J29',
    'J27',
    'J25'
    ]

fig, axs = plt.subplots(4, 1, sharex=True, figsize=[8.27, 11.69])

for ch, ax in zip([0,1,2,3], axs.reshape(-1)):
    # Get the channel
    if len(transit_times[ch]) > 0:
        tts = np.array(transit_times[ch])
    else:
        tts = np.array([0])
    xmin, xmax = np.min(tts), np.max(tts)

    # Plot the observations
    N, bins, patches = ax.hist(tts, range=[15, 20.], facecolor='green', 
        edgecolor='black', bins=50, label='Data')
    ax.set_ylabel('Frequency')

    # Optimise gaussian fit
    bins = np.array(bins[:-1]) + 0.05
    optim, success = optimize.leastsq(errfunc, guess[:], args=(bins, N))

    print("For %s" % (junctions[ch]))
    print("First gaussian:\nHeight - %d\nCentre - %.3lf\nWidth - %.3lf\n" % 
        (optim[0], optim[1], optim[2]))

    # Plot the fit
    # ax.plot(bins, two_gaussians(bins, *optim), color='black', label='Normal Distribution')
    ax.plot(bins, gaussian(bins, *optim), color='black', label='Normal Distribution')


    ax.set_xlim(15, 20)
    ax.set_title("%s. Mean: %.3lf, Standard deviation: %.3lf" % 
        (junctions[ch], optim[1], optim[2]))


axs[-1].set_xlabel('Transit time, ns')
plt.tight_layout()
plt.savefig('TTS_for_each_channel')
plt.show()