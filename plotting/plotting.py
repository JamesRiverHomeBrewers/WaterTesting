"""

"""

import matplotlib.pyplot as plt
import mpld3
from mpld3 import plugins
import numpy as np
import sys

# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(tableau20)):
    r, g, b = tableau20[i]
    tableau20[i] = (r / 255., g / 255., b / 255.)


class Plot():
    """

    """

    def __init__(self, x, y, labels, ids):
        self.x = x
        if isinstance(y, list):
            self.y = []
            for s in y:
                self.y.append(s.tolist())
        else:
            self.y = [y.tolist()]

        self.labels = labels

        self.ids = []
        for id in ids:
            self.ids.append(str(id))

        self._plot()

    def _plot(self):
        pass


class LinePlot(Plot):
    """

    """

    def _plot(self):
        fig, ax  = plt.subplots()



class StackedArea(Plot):
    """

    """

    def _plot(self):
        color_select = tableau20[:len(self.y)]

        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)

        plot_list = []
        for idx, series in enumerate(self.y):
            labels = ['{}: {}'.format(self.labels[idx], y) for y in series]
            targets = ['<a href="url">{}</a>'.format(id) for id in self.ids]

            plot = ax.plot(self.x, series, color=color_select[idx], marker='o')
            plot_list.append(plot)

            print(labels, file=sys.stderr)
            print(targets, file=sys.stderr)


        ax.legend(plot_list, self.labels)

        print(mpld3.fig_to_html(fig))

        plt.close()
