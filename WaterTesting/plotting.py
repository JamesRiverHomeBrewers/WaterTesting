"""

"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
import mpld3
from mpld3 import plugins
#import numpy as np
import sys, os
from PIL import Image, ImageChops

# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, the format matplotlib accepts.
for i in range(len(tableau20)):
    r, g, b = tableau20[i]
    tableau20[i] = (r / 255., g / 255., b / 255.)


class Plot():
    """

    """

    def __init__(self, x, y, labels, ids, title=None):
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

        self.title = title

    def plot(self):
        """ Dummy function needs to be implemented. """
        pass

    def _trim(self, path):
        im = Image.open(path)

        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            im.save(path)


class StackedArea(Plot):
    """

    """

    def _plot(self):
        fig, ax  = plt.subplots()



class LinePlot(Plot):
    """ Class to implement the _plot function of Plot class. Makes stacked
        area line charts.
    """

    def plot(self, path, legend=True):
        fontP = FontProperties()
        fontP.set_size('xx-small')
        color_select = tableau20[:len(self.y)]

        fig = plt.figure(figsize=(700/96, 500/96), dpi=96)
        ax = fig.add_subplot(111)

        handle_list = []
        for idx, series in enumerate(self.y):
            #labels = ['{}: {}'.format(self.labels[idx], y) for y in series]
            #targets = ['<a href="url">{}</a>'.format(id) for id in self.ids]
            ax.plot(self.x, series, color=color_select[idx], marker='o')
            handle_list.append(mpatches.Patch(
                color=color_select[idx],
                label=self.labels[idx])
            )

        ax.grid(color='lightgray', alpha=0.7)

        if legend:
            ax.legend(
                handles=handle_list,
                title='',
                loc='upper center',
                bbox_to_anchor=(0.5, 1.1),
                ncol=len(self.y),
                prop = fontP
            )

        ax.figure.autofmt_xdate()
        # Generate the plot HTML
        html = mpld3.fig_to_html(fig)
        #html = None

        # Save png image
        img_file = '{}.png'.format(self.title)
        plt.savefig(os.path.join(path, img_file), bbox_inches='tight')
        self._trim(os.path.join(path, img_file))

        plt.close()

        return img_file, html
