
import numpy as np
import random
import scipy
 



class Organism():
    def __init__(self, species, radius, positions, mean_emission, sd_mean_emission, intensity):
        """
        Parameters
        ----------
        species : str
            Name of the organism.
        radius : float
            Spatial extension of the organism.
        positions : 3darray
            x-, y- and z-coordinates of the organism depending on the time.
        mean_emission : float
            Wavelength of the mean emission of the organism in nm. The emission spectrum follows a
            gamma distribution.
        sd_mean_emission : float
            Standard deviation of the mean emission.
        intensity : ndarray
            Array of the same length as the three spatial coordinates. Number of photons emitted by the
            organism at each position.
        """
        self.species = species
        self.radius = radius  
        self.x, self.y, self.z = positions
        self.mean_emission = mean_emission  # wavelength in nm
        self.sd_mean_emission = sd_mean_emission  # in nm
        self.intensity = intensity  # number of photons
        


    def intensity_pdf(self, n_times):
        """
        Get the pdf of the emission intensity for the organism through the histogram of emitted photons
        per timestep. And create n_times new timesteps following this pdf.
        """
        # intensity pdf from photon histogram
        rv_hist = scipy.stats.rv_histogram((self.intensity, 
                                            np.linspace(0, len(self.intensity), len(self.intensity)+1)))

        # create n_times new timesteps distributed following the intensity pdf
        times = rv_hist.rvs(size=n_times)
        times.sort()

        return rv_hist, times



    def random_point_on_circle(self, radius):
        """
        Select a random point on a circle in the xy-plane with center (0,0,0) and radius r.
        """ 
        theta = random.uniform(0, 2*np.pi)
        x = radius * np.cos(theta) 
        y = radius * np.sin(theta) 

        return np.array([x, y])
    


    def rotate_coordinates(self, x, y, z, angle_xy, angle_yz=None):
        """ 
        Transform coordinates to new system with xy-plane rotatet by angle_xy and yz-plane rotated by angle_yz.
        """
        if angle_yz != None:
            x_new = x*np.cos(angle_yz)*np.cos(angle_xy)-y*np.cos(angle_yz)*np.sin(angle_xy)+z*np.sin(angle_yz)
            y_new = x*np.sin(angle_xy) + y*np.cos(angle_xy)
            z_new = x*np.sin(angle_yz)*np.cos(angle_xy) - y*np.sin(angle_yz)*np.sin(angle_xy)+z*np.cos(angle_yz)
        else:
            x_new = x*np.cos(angle_xy) - y*np.sin(angle_xy)
            y_new = x*np.sin(angle_xy) + y*np.cos(angle_xy)
            z_new = z

        return (x_new, y_new, z_new)
    
 

    def points_along_trajectory(self, times):
        """ 
        Interpolate a trajectory of few points and create n_points new points along that trajectory
        distributed in the same way the photon intensity is distributed over time.

        Parameters
        ----------
        times : np.array
            Array with the timesteps for which a new points should be created on the trajectory.

        Returns
        -------
        new_points : np.array
            3d array with the x-, y-, and z-values of the new points.
        trajectroy_interp_xy : interpolation object
            Interpolation of the organism trajectory in the xy-plane.
        trajectroy_interp_xz : interpolation object
            Interpolation of the organism trajectory in the xz-plane.
        """
        # interpolate x over time
        x_interp = scipy.interpolate.CubicSpline(np.linspace(0, len(self.intensity)-1, len(self.intensity)), 
                                                 self.x)
        # generate x-values distributed like the intensity
        new_x = x_interp(times)

        x_sorted = self.x.copy()
        x_sorted.sort()
        # interpolate trajectory of organism in xz-plane
        trajectory_interp_xz = scipy.interpolate.CubicSpline(x_sorted, self.z)

        # interpolate trajectory of organism in xy-plane
        trajectory_interp_xy = scipy.interpolate.CubicSpline(x_sorted, self.y)
        # y and z values for the new_x
        new_y = trajectory_interp_xy(new_x)
        new_z = trajectory_interp_xz(new_x)

        new_points = np.array([new_x, new_y, new_z])

        return new_points, trajectory_interp_xy, trajectory_interp_xz
    


    def points_along_trajectory_on_organism_surface(self, points, trajectory_interp_xy, trajectory_interp_xz):
        """ 
        Create for each original point a new one on the circumference of a circle with the size of the 
        organism as the radius around the original point.

        Parameters
        ----------
        points : np.array
            3d array with the x-, y-, and z-values of the original points.
        trajectroy_interp_xy : interpolation object
            Interpolation of the organism trajectory in the xy-plane.
        trajectroy_interp_xz : interpolation object
            Interpolation of the organism trajectory in the xz-plane.

        Returns 
        -------
        new_points : list of tuples
            List with the coordinates of the new points. Every element is a tuple with the three
            coordinates of one new point.
        """
        
        # derivative of the interpolation in the xy-plane
        trajectory_interp_xy_der = trajectory_interp_xy.derivative()
        
        # derivative of the interpolation in the xz-plane
        trajectory_interp_xz_der = trajectory_interp_xz.derivative()

        # for each point, get 3d point on circle around the point with radius of the organism turned
        # to be perpendicular to the slope of the trajectory of the organism in 3d at that point

        # slope in y and z for the point
        der_y = trajectory_interp_xy_der(points[0])
        der_z = trajectory_interp_xz_der(points[0])

        new_points = []
        for i in range(len(points[0])):
            y_circ, z_circ = self.random_point_on_circle(radius=self.radius)
            x, y, z = self.rotate_coordinates(x=0, y=y_circ, z=z_circ, angle_xy=np.arctan(der_y[i]), angle_yz=np.arctan(der_z[i]))
            new_points.append((points[0][i]+x, points[1][i]+y, points[2][i]+z))

        return new_points



    def intensity_at_timestep(self, times):
        """
        Get the emission intensity at a certain timestep.
        """
        # interpolate the photon intensity over time
        intensity_interp = scipy.interpolate.CubicSpline(np.linspace(0, len(self.intensity)-1, len(self.intensity)), 
                                                         self.intensity)

        intensities = intensity_interp(times)

        return intensities