#!/usr/bin/env python
# Fit a double gaussian to a PSEC logfile

import matplotlib.pyplot as plt
import read_PSEC as psec

import numpy as np
import os
from Tkinter import *
import tkFileDialog
import tkMessageBox
import bokeh.plotting as bkh
from scipy import optimize
from bokeh.models import Span

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

def gaussian(x, height, center, width):
    return height*np.exp(-(x - center)**2/(2*width**2))

def two_gaussians(x, h1, c1, w1, h2, c2, w2, offset=0):
    return (gaussian(x, h1, c1, w1) +
        gaussian(x, h2, c2, w2) + offset)

cwd = os.getcwd()
# Get the data file from a dialogue box and open it. Also store the filename.
root = Tk()
root.withdraw()
root.update()
f = tkFileDialog.askopenfile(mode='rb', 
    initialfile=cwd, 
    title='Select a file', 
    filetypes = (("TXT Files", "*.txt"),("all files","*.*")))
root.destroy()
try:
    fname = f.name
except:
    print("No file selected")
    exit()
f.close()


#Make a maller version of ts to use for individual samples
ts = np.arange(0.0, 25.6, 0.1)

ch = raw_input("What channel on the PSEC? (1-6): ")
ch = int(ch)-1
# position = float(raw_input("What position on the tile are we at (cm): "))/100
electronVelocity = 6e7
dt = 100e-12 # 100ps time resolution

# Initialise data storage
positions = []
gains = []
measurements = {}

def analyse(sample):
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

    return time_difference, gain, position

with open(fname, 'r') as f:
    sample = np.zeros((6, 256))
    i = 0
    for line in f:
        if line[0] == '#':
            continue
        if i == 256:
            # Get the analysis
            time_difference, gain, position = analyse(sample)
            # If its a signal, store it
            if position > 0.0 and position < 0.058:
                positions.append(position)
                gains.append(gain)
            # Reset array
            sample = np.zeros((6,256))
            i = 0

        # Read the data into array
        sample[:,i] = np.array([float(x) for x in line.split()])[:6]
        i += 1



plt.hist(positions, facecolor='green', edgecolor='black', bins=24)
plt.title("Positions of signals")
plt.ylabel('Frequency')
plt.xlabel('Position, cm')
plt.savefig(fname[:-4]+'_pos')
plt.clf()

plt.hist(np.array(gains)/1e6, facecolor='green', edgecolor='black', bins=24)
plt.title("Gains of signals")
plt.ylabel('Frequency')
plt.xlabel('Gain, 10^6')
plt.savefig(fname[:-4]+'_gains')
plt.clf()

oname = fname[:-4]+'_gains.txt'
with open(oname, 'w') as f:
    for position, gain in zip(positions, gains):
        f.write("%lf, %lf\n" % (position, gain))


# Smooth the gain data with a moving average, with a window 1/10th the 
#  number of data since our position resolution is only actually accurate to 
#  1cm on a 6cm tile.
window_len = int(len(gains)/5)

# Ordered lists of gain and position
positions, gains = zip(*sorted(zip(positions, gains)))

# Get a cumulative sum, so each cell is the sum of all that came before it
gains = np.cumsum(gains, dtype=float)
# subtract the other side of the window to isolate the sum of JUST the window
gains[window_len:] = gains[window_len:] - gains[:-window_len]

# divide by the window size, so that it's a mean.
gains = gains[window_len-1:]/window_len

# The same for position
positions = np.cumsum(positions, dtype=float)
positions[window_len:] = positions[window_len:] - positions[:-window_len]
positions = positions[window_len-1:]/window_len

plt.plot(positions, gains/1e6, color='green')
plt.title('Gain as a function of position')
plt.xlabel("Position, cm")
plt.ylabel("Gain, 10^6")
plt.savefig(fname[:-4]+'_gainPos')
plt.clf()

