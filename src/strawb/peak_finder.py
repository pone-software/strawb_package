import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

import strawb.tools


class PMTPeak:

    def __init__(self, rate, time):

        """The general idea behind this class is to search for different kinds of peaks
        within the inputed (and interpolated) rate and times, and then output important parameters of those peaks
        This class is expandable as different kinds of peaks are searched for """

        self.rate = rate
        self.time = time

        self.alphas = None
        self.timestamps = None

        '''This finder searches for peaks that rise linearly very quickly 
        and then decay exponentially, which seems to be the most common 
        bioluminscent flash type. This finder may be replaced by a gamma
        distribution finder'''

    def ExpoPeakFinder(self):

        # Want to collect the decay rate (alpha) and timestamps of our found peaks

        self.alphas = []
        self.timestamps = []

        # Here we define the power law for the exponential decay, and a line to fit the intial linear rise

        def expo_decay(x, a, alpha):
            y = a * np.exp(-alpha * x)
            return y

        def line(x, a, c):
            y = (a * x) + c
            return y

        # Searches for peaks with high prominence (TODO: Make peak finder parameters adjustable)

        peaks, __ = find_peaks(self.rate, prominence=4e4)

        '''The basic idea of the following loop is to scan backwards and forwards from the peak 
        to find the appropriate limits of the peak. The limits are defined by when the slope of 
        the peak has flattened sufficiently'''

        backLimits = []
        frontLimits = []
        backLimitFound = False
        frontLimitFound = False

        for peak in peaks:

            # Calculates slope for the back limit

            for i in np.arange(len(self.rate)):
                if not backLimitFound:
                    rate1 = self.rate[peak - i - 1]
                    rate2 = self.rate[peak - i]

                    slope = (rate2 - rate1)

                    '''The peaks we're looking for have a very sharp rise initially
                    and we only want to include the sharp rise within our boundaries 
                    and hence the slope limit is high'''

                    if i > 0 and slope < 20000:
                        backLimits.append(peak - i)
                        backLimitFound = True

                # Calculating slope for front limit

                if not frontLimitFound:

                    try:
                        rate1 = self.rate[peak + i + 1]
                        rate2 = self.rate[peak + i]
                    except IndexError:
                        frontLimits.append(peak + i)
                        frontLimitFound = True

                    slope = (rate2 - rate1)

                    '''We want to include a significant part of the exponential decay within our boundaries
                    hence the slope limit is relatively low'''

                    if slope < 100:
                        frontLimits.append(peak + i)
                        frontLimitFound = True

                # Once we've found the boundaries we exit the loop

                if frontLimitFound and backLimitFound:
                    frontLimitFound = False
                    backLimitFound = False
                    break

        # Now we test how well our peaks fit a linear function before the peak and an exponential decay after the peak

        for i in np.arange(len(frontLimits)):

            y = self.rate[peaks[i]:frontLimits[i]]

            if len(y) > 1:

                seconds = self.time[frontLimits[i]] - self.time[peaks[i]]

                if type(seconds) == np.timedelta64:
                    seconds = seconds / np.timedelta64(1, 's')

                # Here we curve fit to an exponential decay
                fit, _ = curve_fit(expo_decay, np.linspace(0, seconds, len(y)), y, [np.max(y), 1], maxfev=50000)
                y_fit = expo_decay(np.linspace(0, seconds, len(y)), fit[0], fit[1])

                # Here is calculate the goodness of fit

                ss_res = np.sum((y - y_fit) ** 2)

                ss_tot = np.sum((y - np.mean(y)) ** 2)

                r2 = 1 - (ss_res / ss_tot)

                # If it passes the goodness of fit limit, then we move on the fitting the linear rise

                if r2 > 0.90:
                    z = self.rate[backLimits[i]:peaks[i] + 1]

                    if len(z) > 1:

                        linefit, _ = curve_fit(line, np.arange(backLimits[i], peaks[i] + 1), z, maxfev=50000)
                        z_fit = line(np.arange(backLimits[i], peaks[i] + 1), linefit[0], linefit[1])

                        ss_res = np.sum((z - z_fit) ** 2)

                        ss_tot = np.sum((z - np.mean(z)) ** 2)

                        r2 = 1 - (ss_res / ss_tot)

                        # If it passes the goodness of fit limit again and is sufficiently steep,
                        # then we save the peak's parameters

                        if r2 > 0.78 and linefit[0] > 100000:
                            self.alphas.append(fit[1])

                            if type(self.time[peaks[i]]) != np.datetime64:
                                self.timestamps.append(strawb.tools.asdatetime(self.time[peaks[i]]))
                            else:
                                self.timestamps.append(self.time[peaks[i]])

    # Here you can access the list of decay parameters from found peaks

    def ExpoDecayParam(self):
        if self.alphas is None:
            print("Run ExpoPeakFinder to collect decay parameters")
            return None
        else:
            return self.alphas

            # Here you can access the list of timestamps from found peaks

    def ExpoTimestamps(self):
        if self.timestamps is None:
            print("Run ExpoPeakFinder to collect timestamps")
            return None
        else:
            return self.timestamps
