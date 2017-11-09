
import matplotlib.pyplot as plt
import bokeh.plotting as bkh
from bokeh.models import Range1d
import os
import datetime
import subprocess
import tkFileDialog
import tkMessageBox

cwd = os.getcwd()
f = tkFileDialog.askopenfile(mode='rb', initialfile=cwd, title='Select a file', filetypes = (("Text Files","*.txt"),("all files","*.*")))
oname = f.name

# Samples is a list, and each sample contains
#  a set of 6 lists which are the channels readings
samples = []
channels = [[],[],[],[],[],[],[]]

j = 0
vmin = 0.
vmax = 0.
for line in f:
	if line[0] == '#':
		continue
	else:
		line = [float(x) for x in line.split()]
		for i in range(6):
			channels[i+1].append(line[i])
			if line[i] > vmax:
				vmax = float(line[i])
			if line[i] < vmin:
				vmin = float(line[i])
		channels[0].append(j)
		j += 1
	if j%256 == 0:
		samples.append(channels)
		channels = [[],[],[],[],[],[],[]]
f.close()
print 'Read out %d samples, in %d lines' % (len(samples), j)

#recover the user inputted name so it can be applied to graphs and whatever
stamp = oname.split('/')[-1].strip('.txt')

# output graph to a static HTML file
bkh.output_file(stamp+'.html')

#create plot object
p = bkh.figure(plot_width=1000, title=stamp, x_axis_label='N', y_axis_label='Voltage, V')

# Read the channels from each sample into long lists for plotting
channels = [[],[],[],[],[],[]]
for sample in samples:
	for i in range(6):
		for data in sample[i]:
			channels[i].append(data)
j = range(len(channels[0]))

# Plot the data
col = ['red', 'blue', 'orange', 'green', 'purple', 'black']
i = 1
#add data to the plot object
for channel in channels:
	p.line(j, channel, legend='Channel '+str(i), line_width=1, line_color=col[i-1])
	i += 1

# set ranges
p.y_range = Range1d(1.1*vmin, 1.1*vmax)

bkh.save(p)
# bkh.show(p)