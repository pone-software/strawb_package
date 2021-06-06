import numpy as np
from scipy.optimize import least_squares
from inspect import getfullargspec


# this class use least square method to fit a general exposure time and temperature dependent
# dark count function. Then subtract the dark value from known spectrum, return the calibrated value

# other note: for simplification, this version only use the "fit_loop_pixel" method from Kilian's version

class DarkCountFit:
    # need in put from device_handler
    def __init__(self,fit_data_obj):

        # number of opt_parameter in f(dt, temp, *opt_parameter), [dt, temp] aren't opt_parameter
        # -> -len([dt, temp]) = -2
        self.len_opt_parameter = len(getfullargspec(self.darkcounts_fit_function).args) - 2

        # default starting parameters for fits. see darkcounts_fit_function
        self.opt_00 = np.zeros(self.len_opt_parameter)
        self.opt_00[0] = 1887.  # y_0: arbitrary constant
        self.opt_00[1] = -9.9  # dt_m: dark count rate per exposure_time
        self.opt_00[2] = 44.  # A:multi factor of exponential part
        self.opt_00[3] = 0.12  # temp_m:

        #generate zero array to store opt parameters for each pixel,each device has 288 pixel
        #saved when 'fit_loop_pixel' or 'fit_pixel_allin1' is executed
        self.opt = np.zeros((self.len_opt_parameter, 288))

        # maximum possible value of tdc_counts, from Imma's measurement
        self.adc_count_max = 16000
        self.fit_obj = fit_data_obj


    #some auxiliary definitions
    @staticmethod
    def darkcounts_fit_function(dt, temp, y_0, dt_m, a, temp_m):
        """dt: exposure_time -> dark_counts ~ dt_m*dt
        temp: gain -> dark_counts ~expand as exponential function -> temp_m*temp + temp_m2*temp**2"""
        return y_0 + dt_m * dt + a * dt * np.exp(temp_m * temp) # the dark count value


    def func_min_singlepixel(self, opt, dt, temp, data):
        """function to minimize for fit_loop_pixel
        i: index of measurements
        pix: index pixel, i.e. [0,..,287]
        function for least_squares: func_min(opt, dt, temp, data)
        opt: optimisation parameters, shape()=[j]
        dt: exposure_time, shape()=[i,1]
        temp: gain, shape()=[i,1]
        data: tdc_counts, shape()=[i,288]
        return: ( f(dt,temp,*opt)-data ).flatten() , shape()"""
        y = self.darkcounts_fit_function(dt, temp, *opt.reshape(self.len_opt_parameter, -1)) - data
        y /= np.sqrt(data)
        y[data >= self.adc_count_max] = 0.  # mask/exclude saturated
        return y.flatten()

    # the core method start here

    def fit_loop_pixel(self, *args, **kwargs):
        """Fits the data from the device to the f_dark_counts() for each pixel.
        The fit is implemented as a loop over all single pixels - way faster as fit_pixel_allin1

        For each pixel f_dark_counts(x,y,*opt-parameters) is fitted against the device.measurements data to determine
        the opt-parameters. Therefore scipy.optimize.least_squares minimises the _func_min_singlepixel() which is using
        the f_dark_counts() as fit-function.

        device: member of Device
        *args, **kwargs: are passed to scipy.optimize.least_squares
        """

        # import dark measurement
        adc_counts_all = self.fit_obj.ADC_counts
        exposure_time_arr = self.fit_obj.exposure_time
        temperature_arr = self.fit_obj.temperature_after

        # initialise fit parameter
        opt = []
        opt_0 = self.opt_00

        # number of last entries (pixels) in opt to average over for the new opt_0
        # value 10 gave in first trials in ave. fastest results
        # function to determine, see end of this file
        # min: 1, max: 288
        opt_0_average = 10

        for i in np.arange(np.shape(adc_counts_all)[1]):
            # select data of one pixel
            adc_counts_i = adc_counts_all[:, i]

            res_i = least_squares(self.func_min_singlepixel,
                                  opt_0.flatten(),
                                  method='lm',
                                  args=(exposure_time_arr,
                                        temperature_arr,
                                        adc_counts_i),
                                  *args,
                                  **kwargs)

            opt.append(res_i.x.reshape(self.len_opt_parameter, -1))

            # take previous parameters as opt_0
            # opt[-5:] worked best in a first try
            opt_0 = np.mean(opt[-opt_0_average:], axis=0)

        # list->np.array
        opt = np.array(opt)

        # adjust style, after transpose:
        # opt_0[0,:] = [pix_0,...,pix_n] : y_0
        # opt_0[1,:] = [pix_0,...,pix_n] : dt_m
        # opt_0[2,:] = [pix_0,...,pix_n] : A
        # opt_0[3,:] = [pix_0,...,pix_n] : temp_m

        self.opt = opt.reshape(-1, 4).transpose()
        return self.opt