import numpy as np
import scipy.interpolate


class Distortion:
    def theta_distortion(self, theta, *args, **kwargs):
        """Prototype for a distortion in theta. Theta is undistorted and theta_dis is distorted.
        E.g. for a distribution of a lens, theta refers to the angle in the read world and theta_dis to the angle
        after the lens.
        PARAMETER
        ---------
        theta: ndarray, float
            undistorted theta
        args: iterable, optional
        kwargs: dict, optional
        RETURN
        ---------
        theta_dis: ndarray, float
            distorted theta
        """
        return theta

    def theta_distortion_inv(self, theta_dis, *args, **kwargs):
        """Prototype for the inverse distortion of theta. Theta is undistorted and theta_dis is distorted.
        E.g. for a distribution of a lens, theta refers to the angle in the read world and theta_dis to the angle
        after the lens.
        PARAMETER
        ---------
        theta_dis: ndarray, float
            distorted theta
        args: iterable, optional
        kwargs: dict, optional
        RETURN
        ---------
        theta: ndarray, float
            undistorted theta
        """
        return theta_dis

    def phi_distortion(self, phi, *args, **kwargs):
        """Prototype for a distortion in phi. Phi is undistorted and phi_dis is distorted.
        E.g. for a distribution of a lens, phi refers to the angle in the read world and phi_dis to the angle
        after the lens.
        PARAMETER
        ---------
        phi: ndarray, float
            undistorted phi
        args: iterable, optional
        kwargs: dict, optional
        RETURN
        ---------
        phi_dis: ndarray, float
            distorted phi
        """
        return phi

    def phi_distortion_inv(self, phi_dis, *args, **kwargs):
        """Prototype for the inverse distortion of phi. Phi is undistorted and phi_dis is distorted.
        E.g. for a distribution of a lens, phi refers to the angle in the read world and phi_dis to the angle
        PARAMETER
        ---------
        phi_dis: ndarray, float
            distorted phi
        args: iterable, optional
        kwargs: dict, optional
        RETURN
        ---------
        phi: ndarray, float
            undistorted phi
        """
        return phi_dis


class SphereDistortion(Distortion):
    """Calculates the Distortion of a sphere."""

    def __init__(self, r_position, r_sphere, thickness_sphere, n_a=1., n_g=1.52, n_w=1.35):
        """Calculates the Distortion of a sphere.
        Values for STRAWb:
        r_position=.063, r_sphere=.1531, thickness_sphere=.012, n_a=1., n_g=1.52, n_w=1.35
        PARAMETER
        ---------
        r_position: float; radius at which theta is measured, e.g. the location of camera in meter
        r_sphere: float; inner radius of the sphere in meter
        thickness_sphere: float; thickness of the sphere in meter
        n_a: float, optional; refractive index inside the sphere (air)
        n_g: float, optional; refractive index of the sphere (glass)
        n_w: float, optional; refractive index outside the sphere (water)
        """
        self.r_position = r_position  # radius at which theta is measured, e.g. the location of camera in meter
        self.r_sphere = r_sphere  # inner radius of the sphere in meter
        self.thickness_sphere = thickness_sphere  # thickness of the sphere in meter
        self.n_a = n_a  # refractive index inside the sphere (air)
        self.n_g = n_g  # refractive index of the sphere (glass)
        self.n_w = n_w  # refractive index outside the sphere (water)

        # to calculate the inverse numerically
        self.__theta_distortion__ = None

    def theta_distortion(self, theta, n=int(1e6), **kwargs):
        """Applies the theta distortion: theta -> theta_distortion
        PARAMETER
        ---------
        theta: ndarray
            undistorted theta values
        n: int
            the inverse is calculated numerically at the positions: `np.linspace(0, np.pi, n)`.
            Therefore higher n provides more accuracy.
        args: iterable, optional
            to match signature of the base method `SphereDistortion.theta_distortion_inv()'
        """
        # only calculate or update it when needed
        if self.__theta_distortion__ is None or int(n) != len(self.__theta_distortion__.x):
            theta_numeric = np.linspace(0, np.pi, int(n))
            beta = self.theta_distortion_inv(theta_numeric)
            self.__theta_distortion__ = scipy.interpolate.interp1d(x=beta, y=theta_numeric,
                                                                   kind='cubic', assume_sorted=True)
        return self.__theta_distortion__(theta)

    def theta_distortion_inv(self, theta_dis, n=10000, **kwargs):
        """Applies the theta inverse distortion: theta_distortion -> theta.
        PARAMETER
        ---------
        theta_dis: ndarray
            distorted theta values
        args: iterable, optional
            to match signature of the base method `SphereDistortion.theta_distortion_inv()'
        """
        # only calculate or update it when needed
        a_0 = np.arcsin(self.r_position / self.r_sphere * np.sin(theta_dis))
        a_1 = np.arcsin(self.n_a / self.n_g * self.r_position / self.r_sphere * np.sin(theta_dis))
        b_0 = np.arcsin(self.r_position / (self.r_sphere + self.thickness_sphere) * np.sin(theta_dis))
        b_1 = np.arcsin(self.n_a / self.n_w * self.r_position / (self.r_sphere + self.thickness_sphere) * np.sin(theta_dis))
        return theta_dis - a_0 + a_1 - b_0 + b_1
