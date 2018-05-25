import matplotlib.pyplot as plt
import numpy as np

fnames = [
'FullMap/Trial1Channel1_gains.txt',
'FullMap/Trial1Channel2_gains.txt',
'FullMap/Trial1Channel3_gains.txt',
'FullMap/Trial1Channel5_gains.txt',
'FullMap/Trial1Channel6_gains.txt',
'FullMap/Trial2Channel1_gains.txt',
'FullMap/Trial2Channel2_gains.txt',
'FullMap/Trial2Channel3_gains.txt',
'FullMap/Trial2Channel5_gains.txt',
        ]

labels = [
'J35',
'J33',
'J31',
'J29',
'J27',
'J25',
'J23',
'J21',
'J19'
    ]

i = 0
lanes = [1,2,3,4,5]

gains = []
x = []
y = []

gains = []

for fname in fnames:
    x.append([])
    y.append([])
    gains.append([])
    try:
        with open(fname, 'r') as f:
            for data in f:
                data = [float(d) for d in data.split(',')]
                if data[1] > 1e5:
                    x[i].append(data[0]*100)
                    y[i].append(i)
                    gains[i].append(data[1])
    except:
        pass
    i += 1


for i in range(len(fnames)):
    x_row = x[i]
    gain_row = gains[i]

    step = 0.2
    xout    = np.arange(0, 6, step)
    gainout = np.zeros(xout.shape)
    Ns      = np.zeros(xout.shape)

    for xi, gi in zip(x_row, gain_row):
        xi = np.floor(xi/step)*step
        gainout[np.where(xout==xi)] += gi
        Ns[np.where(xout==xi)] += 1
    for j in range(len(xout)):
        if Ns[j]:
            gainout[j]/= Ns[j]*1e6
        else:
            gainout[j] = None

    x[i] = xout[:-1]
    gains[i] = gainout[:-1]

x_init = x
gains_init = gains

fig, axs = plt.subplots(nrows=len(x_init), sharex=True)
colormap = 'viridis'


for i in range(len(x_init)):

    x = np.array(x_init[i])
    y = np.array(gains_init[i])

    extent = [x[0]-(x[1]-x[0])/2., x[-1]+(x[1]-x[0])/2.,0,1]
    im = axs[i].imshow(y[np.newaxis,:], cmap=colormap, aspect="auto", 
        extent=extent, interpolation='hanning')
    axs[i].set_yticks([])
    h = axs[i].set_ylabel(labels[i])
    axs[i].set_xlim(extent[0], extent[1])

axs[0].set_xlabel("Anode Position, cm")
axs[0].xaxis.tick_top()
axs[0].xaxis.set_label_position('top')

fig.text(0.03, 0.53, 'Anode Strip', ha='center', va='center', rotation='vertical')

plt.tight_layout()

fig.subplots_adjust(left=0.08, bottom=0.25, hspace=0.0)
cbar_ax = fig.add_axes([0.08, 0.1, 0.9, 0.05])
fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
cbar_ax.set_xlabel('Gain, 1e6')


plt.show()