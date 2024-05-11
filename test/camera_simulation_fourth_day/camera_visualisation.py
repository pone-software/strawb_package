
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib
import cv2

from scipy.ndimage import convolve

import strawb
import strawb.calibration
 


 
class CameraVisualisation():
    def __init__(self, positions, intensity, cam_device_code, cam_pos_x, cam_pos_y, cam_pos_z):
        self.x, self.y, self.z = positions
        self.initial_intensity = intensity
        self.device_code = cam_device_code
        self.cam = strawb.Camera(device_code=cam_device_code)

        self.cam_pos_x = cam_pos_x
        self.cam_pos_y = cam_pos_y
        self.cam_pos_z = cam_pos_z

        self.color_grid = np.zeros((1280, 960))  # 0 is green
        self.color_grid[0::2, 0::2] = 1 # 1 is blue
        self.color_grid[1::2, 1::2] = 2  # 2 is red

    

    def dist_to_cam(self):
        """ Get the distance between the organism and the camera at each timestep. """
        dist = np.linalg.norm([self.x, self.y, self.z], axis=0)

        return dist



    def pix_cam(self):
        """
        Turn the 3d coordinates of the emitting organisms into 2d pixel coordinates of the camera.
        """
        pix_x = []
        pix_y = []

        # x and y coordinates with the camera positioned in (0,0)
        x_cam = self.x - self.cam_pos_x
        y_cam = self.y - self.cam_pos_y
        z_cam = self.z - self.cam_pos_z

        for i in range(len(self.x)):
            points_cam = np.array(self.cam.tc.real2camera(np.array((np.array(x_cam[i]).flatten(), 
                                                                    np.array(y_cam[i]).flatten(), 
                                                                    np.array(z_cam[i]).flatten()))))
            pixel = self.cam.projection.vec2pixel(points_cam[0], points_cam[1], points_cam[2])
            pix_x.append([int(i) for i in pixel[0]])
            pix_y.append([int(i) for i in pixel[1]])

        return np.array([pix_x, pix_y])



    def pixel_intensity(self, wavelength=np.linspace(260, 900, 500), *args, **kwargs):
        """ 

        """
        # preassure glass housing with a thickness of 12mm
        bk7 = strawb.calibration.BK7(thickness=.012)
        # Camera
        filter_dict = {c_i: strawb.calibration.CameraRGB(color=c_i) for c_i in ['blue', 'green', 'red']}
        # water absorption for a thickness in meter
        water = strawb.calibration.Water(thickness=5, 
                                         publication='hale73')

        # pixel conversion 
        x_pix, y_pix = self.pix_cam()

        all_int = []  # the actual intensities
        # x and y values of the intensity values
        x_int = []  
        y_int = []

        for position in range(len(self.x)):
            if (x_pix[position] < self.color_grid.shape[1]) and (y_pix[position] < self.color_grid.shape[0]):
                x_int.append(int(x_pix[position]))
                y_int.append(int(y_pix[position]))

                # color of the pixel the 3d coordinate is converted to
                c = int(self.color_grid[int(y_pix[position])][int(x_pix[position])])
                color = ['green', 'blue', 'red'][c]

                int_pixel = self.initial_intensity[position] * bk7.transmittance(wavelength, *args, **kwargs) 
                int_pixel = int_pixel * water.transmittance(wavelength, thickness=self.dist_to_cam()[position], *args, **kwargs)
                int_pixel = int_pixel * filter_dict[color].transmittance(wavelength, *args, **kwargs)  

                # take the sum of intensities over all wavelengths
                all_int.append(np.sum(int_pixel))

        return np.array([x_int, y_int]), np.array(all_int)
    


    def get_intensity_grid(self):
        """
        """
        pix_ints, ints = self.pixel_intensity()

        # create intensity grid
        grid = np.zeros_like(self.color_grid)
        for i in range(len(ints)):
            grid[pix_ints[1][i]][pix_ints[0][i]] = ints[i]

        grid[grid < 0] = 0

        return grid



    def generate_image_rgb(self, figsize=(4,6), x_lim=[0, 960], y_lim=[0, 1280], cable_points=None, 
                           colorbar=False, fov=False, legend=False):
        """ 
        """

        grid = self.get_intensity_grid()

        red = np.ma.masked_array(grid, np.where(self.color_grid == 2, False, True))
        blue = np.ma.masked_array(grid, np.where(self.color_grid == 1, False, True))
        green = np.ma.masked_array(grid, np.where(self.color_grid == 0, False, True))

        cmap_red = matplotlib.colors.LinearSegmentedColormap.from_list('red', ['black', 'tab:red'])
        cmap_blue = matplotlib.colors.LinearSegmentedColormap.from_list('blue', ['black', 'tab:blue'])
        cmap_green = matplotlib.colors.LinearSegmentedColormap.from_list('green', ['black', 'tab:green'])

        fig, ax = plt.subplots(figsize = figsize)
        plot_red = ax.imshow(red/np.sum(grid),interpolation='nearest',cmap=cmap_red)
        plot_blau = ax.imshow(blue/np.sum(grid),interpolation='nearest',cmap=cmap_blue)
        plot_green = ax.imshow(green/np.sum(grid), interpolation='nearest', cmap=cmap_green)

        if colorbar == True:
            plt.colorbar(plot_red)
            plt.colorbar(plot_blau)
            plt.colorbar(plot_green)


        plt.ylim(y_lim[0], y_lim[1])
        plt.xlim(x_lim[0], x_lim[1])

        plt.xlabel('x [pixel]')
        plt.ylabel('y [pixel]')

        if cable_points != None:
            cable_points_cam = self.cam.tc.real2camera(np.array((np.array(cable_points[0])-3.2, 
                                                                           np.array(cable_points[1])-7.5, 
                                                                           np.array(cable_points[2]))))
            cable_pixel = self.cam.projection.vec2pixel(cable_points_cam[0], cable_points_cam[1], cable_points_cam[2])
            plt.plot([int(i) for i in cable_pixel[0]], [int(i) for i in cable_pixel[1]], c='tab:orange', linewidth=.8, label='Cable')
        
        if fov == True:
            mask = strawb.sensors.camera.Config(device_code=self.device_code).mask_mounting
            polygons, hierarchy = strawb.camera.tools.get_contours(mask)
            ax.plot(polygons[0][:,0], polygons[0][:,1], c='dimgray', 
                    label='Field of View from Module', linewidth=1)
            
        if legend == True:
            plt.legend()

        plt.show()

    

    #def get_solution_image(self, image):
    #    """
    #    Parameters
    #    ----------
    #    image: ndarray
#
    #    
    #    Returns
    #    -------
#
    #    """
    #    masks = dict((color, np.zeros(image.shape)) for color in 'RGB')
    #    masks['R'][1::2, 0::2] = 1
    #    masks['G'][0::2, 0::2] = 1
    #    masks['G'][1::2, 1::2] = 1
    #    masks['B'][0::2, 1::2] = 1
#
    #    for color in 'RGB':
    #        masks[color] = masks[color].astype(bool)
#
    #    # color kernels for the convolution
    #    kernel_G = np.asarray(
    #        [[0, 1, 0],
    #         [1, 4, 1],
    #         [0, 1, 0]]) / 4  
    #    kernel_RB = np.asarray(
    #        [[1, 2, 1],
    #         [2, 4, 2],
    #         [1, 2, 1]]) / 4 
#
    #    R = convolve(image * masks['R'], kernel_RB, mode='constant', cval=0)
    #    G = convolve(image * masks['G'], kernel_G, mode='constant', cval=0)
    #    B = convolve(image * masks['B'], kernel_RB, mode='constant', cval=0)
    #    return np.stack([R, G, B],axis=2)



    def generate_image(self, figsize=(4,6), amplification=1, x_lim=[0, 960], y_lim=[0, 1280], cable_points=None, 
                        colorbar=False, fov=False, legend=False):
        """
        """
        grid = self.get_intensity_grid()
        if (grid.any() != 0) == False:
            print('Organism not visible on camera.')
        elif np.min(grid[grid != 0]) < 1:
            ampl = math.floor(np.log10(np.min(grid[grid != 0])))
            grid = grid * 10**abs(ampl)
        elif 1 <= np.min(grid[grid != 0]) < 10:
            ampl = math.ceil(np.log10(np.min(grid[grid != 0])))
            grid = grid * 10**ampl

        bayer_pattern = cv2.COLOR_BAYER_BG2BGR_EA        
        bgr = cv2.cvtColor(grid.astype(np.uint16), bayer_pattern)  # cv2 exports BGR

        fig, ax = plt.subplots(figsize = figsize)
        ax.imshow(bgr)

        plt.ylim(y_lim[0], y_lim[1])
        plt.xlim(x_lim[0], x_lim[1])

        plt.xlabel('x [pixel]') 
        plt.ylabel('y [pixel]')

        if colorbar == True:
            plt.colorbar()

        if cable_points != None:
            cable_points_cam = self.cam.tc.real2camera(np.array((np.array(cable_points[0])-3.2, 
                                                                           np.array(cable_points[1])-7.5, 
                                                                           np.array(cable_points[2]))))
            cable_pixel = self.cam.projection.vec2pixel(cable_points_cam[0], cable_points_cam[1], cable_points_cam[2])
            plt.plot([int(i) for i in cable_pixel[0]], [int(i) for i in cable_pixel[1]], c='tab:orange', linewidth=.8, label='Cable')
        
        if fov == True:
            mask = strawb.sensors.camera.Config(device_code=self.device_code).mask_mounting
            polygons, hierarchy = strawb.camera.tools.get_contours(mask)
            ax.plot(polygons[0][:,0], polygons[0][:,1], c='dimgray', 
                    label='Field of View from Module', linewidth=1)

        if legend == True:
            plt.legend()
            
        plt.show()