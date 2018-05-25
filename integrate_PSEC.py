#!/usr/bin/env python
import matplotlib.pyplot as plt
import read_PSEC as psec
import os
from Tkinter import *
import tkFileDialog
import tkMessageBox
import numpy as np

#       James Wild, April 2018
#  This script will take a PSEC logfile, and assume that the following has 
# happened:
#  - Channel 5 is purely noise
#  - one or two of the other channels are attached to the LAPPD. If two, 
#     they are both attached to the same anode. 
#  - The signal present has been produced by dark noise.
# The script then calculates the gain of the device, and reports this as a 
# mean and a histogram.

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

t, samples = psec.read(fname)
dt = (t[1]-t[0]) * 1e-9


# For each sample, integrate the voltage while it's above the noise
#   background.
keys = samples.keys()


sums = np.zeros((6, len(samples)))
for k in keys:
    sample = samples[k]

    # Establish the noise level from channel 5
    zeropoint = np.mean(sample[3])
    # Get the standard deviation of the noise
    scatter = np.std(sample[3])
    # Sum data that are more than 3.5 sigma from the mean
    lowerlim = zeropoint - (3*scatter)

    # i is the channel number
    i = 0
    Vsum = 0.0

    # Integrate the voltages in all samples that rise above the threshold. 
    for channel in sample:
    #     plt.plot(np.arange(0.0, 25.6, 0.1), channel, color='red')
    #     plt.plot(np.arange(0.0, 25.6, 0.1), sample[-2], color='black')
    #     plt.axhline(lowerlim, color='blue', alpha=0.5)
    #     plt.axhline(zeropoint, color='green')
        for point in channel:
            if point < lowerlim:
                # Divide by 1000 to convert back from mV to V
                Vsum += point*dt/1000
        sums[i][int(k)] = Vsum
        i += 1
        Vsum = 0.0

# Sum the total recieved voltage in each sample
sums = np.sum(sums, axis=0)
print("Filename: %s" % fname.split('/')[-1])
print("The mean integrated voltage from this file is %.2g Vs" % 
    np.mean(sums))

# For each sum, calculate the gain assuming the event was from a single 
#  photoelectron
gains = sums / (-1.6e-19 * 50)

gains = gains[np.where(gains < 2e7)]

# Assume gains is one half of a normal distribution?
dev = np.std(gains)

print("The mean gain from this file is %.4g +/- %.4g" %
        (np.mean(gains), dev))

plt.hist(gains/1e6, facecolor='green', edgecolor='black', bins=25)
plt.xlabel("Gain, 1e6")
plt.ylabel("Frequency")
# plt.title("The distribution of gains for test\n%s" % fname.split('/')[-1])
plt.tight_layout()
plt.show()