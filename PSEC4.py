import matplotlib.pyplot as plt
import os
import datetime
import subprocess

### FILEPATH TO PSEC4 CODE DIRECTORY!!! SET THIS!!!!!! ###
DIR = '/home/wizenedchimp/Documents/LAPPD-Project/run-psec4-master'


oname = raw_input('Please enter a filename (blank for automatic):')
if oname == '':
	t = datetime.datetime.now()
	oname = 'sample_'+str(t.year)+'-'+str(t.month)+'-'+str(t.day)+'_'+str(t.hour)+'h'+str(t.minute)+'m'
oname = DIR+'/DATA/'+oname

print 'Writing to %s.txt' % oname
N = raw_input('Please enter the number of samples you want to take: ')
N = int(N)

command = [DIR+'/bin/LogData', str(oname), str(N), '0']
print command
psec = subprocess.Popen(command)
psec.wait()


# Samples is a list, and each sample contains
#  a set of 6 lists which are the channels readings

samples = []
channels = [[],[],[],[],[],[],[]]
j = 0
with open(oname+'.txt', 'r') as f:
	for line in f:
		if line[0] == '#':
			continue
		else:
			line = line.split()
			for i in range(6):
				channels[i+1].append(line[i])
			channels[0].append(j)
			j += 1
		if j%256 == 0:
			samples.append(channels)
			channels = [[],[],[],[],[],[],[]]
print 'Read out %d samples, in %d lines' % (len(samples), j)

fig, ax = plt.subplots()

fig.canvas.set_window_title(oname.split('/')[-1])
ax.set_xlabel('data index')
ax.set_ylabel('Readout Voltage')

i = 0
col = ['black', 'red']
for sample in samples:
	plt.plot(sample[0], sample[1], color=col[i%2])
	i += 1

plt.show()