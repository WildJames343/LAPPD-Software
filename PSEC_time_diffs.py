#!/usr/bin/env python
import matplotlib.pyplot as plt
import read_PSEC as psec
import os
from Tkinter import *
import tkFileDialog
import tkMessageBox
import numpy as np

#  This script will take a PSEC logfile, with two channels connected to
# either end of an anode. 
#  The script will integrate the voltage to get the number of photoelectrons.
#  The script will then construct a new array, where 1 indicates a signal,
# and 0 indicates no signal. This will be done on a threshold basis, 
# calibrated from channel 6.

cwd = os.getcwd()
# Get the data file from a dialogue box and open it. Also store the filename.
root = Tk()
root.withdraw()
root.update()
f = tkFileDialog.askopenfile(mode='rb', 
    initialfile=cwd, 
    title='Select a file', 
    filetypes = (("txt Files", "*.txt"),("all files","*.*")))
root.destroy()
try:
    fname = f.name
except:
    print("No file selected")
    exit()
f.close()

voltage = float(raw_input("Please enter the applied voltage to the MCP-PMT: "))
# Use the gain prescription we measured
gain    = (15400. * voltage) - 34097909.
print("Voltage: %.2lf\nGain: %.2lf" % (voltage, gain))

# Read in the data
t, samples = psec.read(fname)
dt = (t[1]-t[0]) * 1e-9
N_samples = len(samples)

# Get the sample keys
keys = samples.keys()

# Get the arrival times
signals = {}

# Integrate the voltages. Construct an array indicating the number of P.E.
sums = np.zeros((6, N_samples))

# Loop over the data
for k in keys:
    sample = samples[k]

    # Establish the noise level from channel 6
    zeropoint = np.mean(sample[-2])
    # Get the standard deviation of the noise
    scatter = np.std(sample[-2])
    # Sum data that are more than 3.5 sigma from the mean
    lowerlim = zeropoint - (3*scatter)

    # i is the channel number
    i = 0
    # l is datapoint index
    l = 0
    # Voltage sum
    Vsum = 0.0
    # Initialise signal array
    signals[k] = np.zeros((6, 256))
    # Loop over channels
    for channel in sample:
        # Reset datapoint idex counter
        l = 0
        # Loop over datapoints in the channel
        for point in channel:
            if point < lowerlim:
                # Divide by 1000 to convert back from mV to V
                Vsum += point*dt/1000
                # If above threshold, flag the signal
                signals[k][i][l] = 1
            l += 1
        sums[i][int(k)] = Vsum
        i += 1
        Vsum = 0.0
# Sum the channels to get the total charge detected
sums = np.sum(sums, axis=0)

# Use the gain relation to get the number of photoelectrons
photoelectrons = sums / (-1.6e-19* 50 * gain)

def first_nonzero(arr, axis, invalid_val=-1):
    mask = arr!=0
    return np.where(mask.any(axis=axis), mask.argmax(axis=axis), invalid_val)

def last_nonzero(arr, axis, invalid_val=-1):
    mask = arr!=0
    val = arr.shape[axis] - np.flip(mask, axis=axis).argmax(axis=axis) - 1
    return np.where(mask.any(axis=axis), val, invalid_val)

# Crawl over <signals> and get the arrival time differences between each
#  pulse
for k in keys:
    sample = samples[k]
    signal = signals[k]


    # Get first non-zero signals for each channel
    arrivals = first_nonzero(signal, 1, invalid_val=None)
    print ("\nFor sample %s, the arrivals were as follows:" % (k))
    print(arrivals)

    plt.plot(sample[0])
    plt.plot(signal[0])
    plt.show()

    exit()
