#!/usr/bin/env python
import matplotlib.pyplot as plt
import bokeh.plotting as bkh
from bokeh.models import Range1d
from bokeh.models import HoverTool
from bokeh.models import Span
import os
import datetime
import subprocess
import read_PSEC
import numpy as np

def plot_PSEC(fname, oname=''):
	# takes a PSEC4 log file, reads it and plots it to a bokeh file. 
	#  <fname> = file to open and read. Include .txt extension.
	#  <oname> = filename to write to. will be appended with '.html'
	# Returns:
	#  <p>     = bokeh plot object for further manipulation, if desired.
	if oname == '':
		oname = fname[:-4]

	# Read in the data
	t, samples = read_PSEC.read(fname)

	#recover the user inputted name so it can be applied to graphs
	stamp = oname.split('/')[-1]
	oname = oname

	# output graph to a static HTML file
	print "saving to %s" % (oname)
	bkh.output_file(oname, title=stamp)

	#create plot object
	p = bkh.figure(plot_width=1000, title=stamp, x_axis_label='t-t0, ns', 
			y_axis_label='Voltage, mV')

	# Read the channels from each sample into long lists for plotting
	channels = np.zeros((6, 0))
	for S in samples:
		channels = np.concatenate((channels, samples[S]), axis=1)

	print 'Plotting...'
	# Plot the data
	cols = ['red', 'blue', 'orange', 'green', 'purple', 'black']
	i = 0
	#add data to the plot object
	for i in range(6):
		# Plot the lines for each channel
		p.line(
				y = channels[i],
				x = t,
				line_width = 2,
				legend=("Channel "+str(i+1)),
				line_color = cols[i],
				# alpha = 0.3
				)

	vlines = []
	for i in range(len(samples)):
		vlines.append(Span(location=25.6*i,
							dimension='height',
							line_color='cyan',
							line_width=2,
							line_alpha=0.3
							))
	p.renderers.extend(vlines)

	# Make data toggleable
	p.legend.location = "top_left"
	p.legend.click_policy="hide"

	# set ranges
	vmin = np.amin(channels)
	vmax = np.amax(channels)
	p.y_range = Range1d(1.1*vmin, 1.1*vmax)

	return p
