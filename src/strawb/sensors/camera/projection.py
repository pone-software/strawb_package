import numpy as np

# unittest  takes another import. Therefore, Distortion2.
from .distortion import Distortion


def reshape_data(y, target):
    """Helper to do numpy calculations with different shapes."""
    y = np.array(y)
    return y.reshape(*y.shape, *[1] * (len(target.shape) - len(y.shape)))


class ProjectionTools:
    @staticmethod
    def spherical2cart(radius, phi, theta=None):
        """Converts spherical or polar coordinates to cartesian.
        sph2cart(1, 0) -> x,y = (1 , 0)
        sph2cart(1, 0, 0) -> x,y,z = (0, 0, 1)
        PARAMETER
        ---------
        radius: int, float, list or ndarray
        phi: int, float, list or ndarray
            should be in the range from [0, 2*np.pi]
        theta: int, float, list or ndarray, optional
            set theta (is not None) to use spherical coordinates
            should be in the range from [0, np.pi]
        RETURN
        ------
        x: float or ndarray
        y: float or ndarray
        z: float or ndarray, optional
            if theta is not None
        """
        rr, pp, tt = np.broadcast_arrays(radius, phi, theta)
        if theta is None:
            x = np.cos(pp) * rr
            y = np.sin(pp) * rr
            return x, y
        else:
            x = np.sin(tt) * np.cos(pp) * rr
            y = np.sin(tt) * np.sin(pp) * rr
            z = np.cos(tt) * rr
            return x, y, z

    @staticmethod
    def cart2spherical(x, y, z=None):
        """Converts cartesian to spherical (z!=None) or polar coordinates.
        cart2sph(1, 0) -> r,phi = (1 , 0)
        cart2sph(0, 0, 1) -> r,phi,theta = (1, 0, 0)
        PARAMETER
        ---------
        x: int, float, list or ndarray
        y: int, float, list or ndarray
        z: int, float, list or ndarray, optional
            set z (is not None) to use spherical coordinates
        RETURN
        ------
        radius: float or ndarray
        phi: float or ndarray
            in the range from [0, 2*np.pi]
        theta: float or ndarray, optional
            in the range from [0, np.pi]
        """
        xx, yy, zz = np.broadcast_arrays(x, y, z)

        r_xy = np.hypot(xx, yy)
        phi = np.arctan2(yy, xx) % (np.pi * 2.)
        if z is None:
            return r_xy, phi

        r_xyz = np.hypot(zz, r_xy)
        theta = np.pi / 2 - np.arctan2(zz, r_xy)
        return r_xyz, phi, theta

    # Translation & Rotation
    @staticmethod
    def rotation(points, alpha=0., beta=0., gamma=0.):
        """
        Rotates points relative to world coordinates point of origin (lens).
        Camera always looks in positive z direction.
        PARAMETER
        ---------
        points: ndarray
            coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        alpha: float, optional
            rotation around x-axis in rad
        beta: float, optional
            rotation around y-axis in rad
        gamma: float, optional
            rotation around z axis in rad
        RETURN
        ------
        points: ndarray
            coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        """
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(alpha), -np.sin(alpha)],
                       [0, np.sin(alpha), np.cos(alpha)]])

        Ry = np.array([[np.cos(beta), 0, np.sin(beta)],
                       [0, 1, 0],
                       [-np.sin(beta), 0, np.cos(beta)]])

        Rz = np.array([[np.cos(gamma), -np.sin(gamma), 0],
                       [np.sin(gamma), np.cos(gamma), 0],
                       [0, 0, 1]])

        return np.dot(np.dot(Rz, np.dot(Ry, Rx)), points)

    @staticmethod
    def translation(points, x=0., y=0., z=0.):
        """
        Translate points according to world coordinates point of origin. Camera
        always looks in positive z direction.
        PARAMETER
        ---------
        points: ndarray
            coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        x,y,z: float, optional
            translate distance in for all axes
        RETURN
        ------
        points: ndarray
            coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        """
        if len(points) == 3:
            return points + reshape_data([x, y, z], target=points)
        else:
            return points + reshape_data([x, y], target=points)


class CameraProjection:
    """Calculates the Camera Projection for a pin-hole camera."""

    def __init__(self, focal_length, pixel_size, pixel_center_index, invert_dir=False,
                 distortion=None):
        """Initialise the camera projection parameter.
        Parameter
        ---------
        focal_length: float
            focal length of the lens in meter
        pixel_size: tuple, list, ndarray, int, float
            size of a pixel on the image sensor in meter.
            If tuple, list, ndarray: different sizes in x and y. First values corresponds to x and second to y.
            If int, float: same size for x and y.
        pixel_center_index: tuple, list, ndarray of floats
            pixel indexes of the lens center on the image plane. First values corresponds to x and second to y.
        invert_dir: bool, optional
            if the image should be rotated by 180deg
        distribution: list or Distribution, optional
            one `Distribution` instance or a list of instances. Applied one after the other.
            Must be specified in the order from outside to inside, or real world to camera sensor.
        """
        # set and check distribution
        if distortion is None:
            distortion = []
        elif isinstance(distortion, (Distortion,)):
            distortion = [distortion]

        for distortion_i in distortion:
            if not isinstance(distortion_i, (Distortion,)):
                raise TypeError(f'All distributions must be subclasses of Distortion. Got: {type(distortion_i)}')
        self.distortion = distortion

        self.focal_length = focal_length

        self.invert_dir = bool(invert_dir)

        if isinstance(pixel_size, (int, float)):
            self.pixel_size_x = float(pixel_size)
            self.pixel_size_y = float(pixel_size)
        else:
            self.pixel_size_x = pixel_size[0]
            self.pixel_size_y = pixel_size[1]

        if len(pixel_center_index) != 2:
            raise ValueError(f'pixel_center_index length must be 2. Got: {pixel_center_index}')
        self.pixel_center = np.array(pixel_center_index)

    def pixel_index2image_coordinates(self, x_i, y_i):
        """converts pixel index (can be a float) to location coordinates on the image sensor in meter.
        PARAMETERS
        ----------
        x_i, y_i: float, ndarray
            pixel index in x and y
        RETURNS
        -------
        x_c, y_c: int, float, ndarray
            coordinates on the image plane in meter.
        """
        x_c = (x_i - self.pixel_center[0]) * self.pixel_size_x  # [m]
        y_c = (y_i - self.pixel_center[1]) * self.pixel_size_y  # [m]
        return x_c, y_c

    def image_coordinates2pixel_index(self, x_c, y_c):
        """converts location coordinates on the image sensor in meter to pixel index (can be float)
        PARAMETERS
        ----------
        x_c, y_c: int, float, ndarray
            coordinates on the image plane in meter.
        RETURNS
        -------
        x_i, y_i: float, ndarray
            pixel index in x and y
        """
        x_i = x_c / self.pixel_size_x + self.pixel_center[0]  # [index]
        y_i = y_c / self.pixel_size_y + self.pixel_center[1]  # [index]
        return x_i, y_i

    def image_coordinates2phi(self, x_c, y_c, invert_dir=None):
        """
        PARAMETERS
        ----------
        x_c, y_c: int, float, ndarray
            coordinates on the image plane in meter.
        invert_dir: bool, optional
            if the image should be rotated by 180deg. If None, take the value of the initialisation.
        RETURN
        ------
        phi: float, ndarray
            the phi component of the direction the pixel get projected to
        """
        if invert_dir is None:  # If None, take the value of the initialisation.
            invert_dir = self.invert_dir
        if invert_dir:
            return (np.arctan2(y_c, x_c) + np.pi) % (np.pi * 2)
        else:
            return np.arctan2(y_c, x_c) % (np.pi * 2)

    def phi2image_coordinates(self, phi, radius, invert_dir=None):
        """
        PARAMETERS
        ----------
        phi: float, ndarray
            the phi component of the direction the pixel get projected to
        radius: int, float, ndarray
            radius on the image plane in meter.
        invert_dir: bool, optional
            if the image should be rotated by 180deg (phi). If None, take the value of the initialisation.
        RETURN
        ------
        x_c, y_c: int, float, ndarray
            coordinates on the image plane in meter.
        """
        if invert_dir is None:  # If None, take the value of the initialisation.
            invert_dir = self.invert_dir
        if invert_dir:
            return np.cos(phi + np.pi) * radius, np.sin(phi + np.pi) * radius
        else:
            return np.cos(phi) * radius, np.sin(phi) * radius

    def image_coordinates2theta(self, x_c, y_c):
        """
        PARAMETERS
        ----------
        x_c, y_c: int, float, ndarray
            coordinates on the image plane in meter.
        RETURN
        ------
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        """
        # the radius on the image plane
        r_pixel = np.hypot(x_c, y_c)
        return self.image_radius2theta(r_pixel)

    # image_radius vs. theta: radius_pixel <-> theta
    def image_radius2theta(self, radius_pixel):
        """
        PARAMETERS
        ----------
        radius_pixel: int, float, ndarray
            radius on the image plane in meter.
        RETURN
        ------
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        """
        return np.arctan(radius_pixel / self.focal_length)

    def theta2image_radius(self, theta):
        """
        PARAMETERS
        ----------
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        RETURN
        ------
        radius_pixel: int, float, ndarray
            radius on the image plane in meter.
        """
        return np.tan(theta) * self.focal_length

    # Pixel vs. angle: x_i, y_i <-> phi, theta
    # removed: (r_xyz: the length that the z component of the vector(r_xyz, phi, theta) is 1)
    def pixel2angle(self, x_i, y_i, invert_dir=None):
        """
        PARAMETERS
        ----------
        x_i, y_i: float, ndarray
            pixel index in x and y
        invert_dir: bool, optional
            if the image should be rotated by 180deg (phi). If None, take the value of the initialisation.
        RETURNS
        -------
        phi, theta: float, ndarray
            the phi component of the direction the pixel get projected to,
            the theta component of the direction the pixel get projected to

        removed
        -------
        r_xyz: float, ndarray
            the length that the z component of the vector(r_xyz, phi, theta) is 1
        """
        # pixel coordinates to location on the image sensor in meter
        x_c, y_c = self.pixel_index2image_coordinates(x_i, y_i)  # [m], [m]
        phi = self.image_coordinates2phi(x_c, y_c, invert_dir=invert_dir)
        theta = self.image_coordinates2theta(x_c, y_c)

        # apply distortions
        for distortion_i in self.distortion[::-1]:
            phi = distortion_i.phi_distortion_inv(phi)
            theta = distortion_i.theta_distortion_inv(theta)

        # # provide a radius, that z=1 for all directions (phi, theta)
        # r_xyz = np.hypot(np.tan(theta), 1)
        return phi, theta

    def angle2pixel(self, phi, theta, invert_dir=None):
        """Calculates the pixel corresponding to a direction
        PARAMETERS
        ----------
        phi: float, ndarray
            the phi component of the direction the pixel get projected to
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        invert_dir: bool, optional
            if the image should be rotated by 180deg (phi). If None, take the value of the initialisation.
        RETURNS
        -------
        x_i, y_i: float, ndarray
            pixel index in x and y
        """
        # apply distortions
        for distortion_i in self.distortion:
            phi = distortion_i.phi_distortion(phi)
            theta = distortion_i.theta_distortion(theta)

        radius = self.theta2image_radius(theta)
        x_c, y_c = self.phi2image_coordinates(phi, radius, invert_dir=invert_dir)
        return self.image_coordinates2pixel_index(x_c, y_c)

    # Real world coordinates to pixel coordinates
    def vec2pixel(self, x, y, z, invert_dir=None):
        """
        PARAMETERS
        ----------
        x, y, z: floats or ndarrays
            object coordinates in x, y, z
        invert_dir: bool, optional
            if the image should be rotated by 180deg (phi). If None, take the value of the initialisation.
            invert_dir = self.invert_dir
        RETURNS
        -------
        x_i, y_i: float, ndarray
            pixel index in x and y
        """
        r, phi, theta = ProjectionTools.cart2spherical(x, y, z)
        return self.angle2pixel(phi, theta, invert_dir=invert_dir)

    # Real world coordinates to pixel coordinates
    def pixel2vec(self, x_i, y_i, invert_dir=None):
        """
        PARAMETERS
        ----------
        x_i, y_i: float, ndarray
            pixel index in x and y
        invert_dir: bool, optional
            if the image should be rotated by 180deg (phi). If None, take the value of the initialisation.
        RETURNS
        -------
        x, y, z: ndarrays
            x, y, z coordinates on the unit sphere (r=1)
        """
        # noinspection PyTupleAssignmentBalance
        phi, theta = self.pixel2angle(x_i, y_i, invert_dir=invert_dir)
        return ProjectionTools.spherical2cart(1., phi, theta)


class EquisolidProjection(CameraProjection):
    """Calculates the Camera Projection for an equisolid distortion."""

    def image_radius2theta(self, radius_pixel):
        """
        PARAMETERS
        ----------
        radius_pixel: int, float, ndarray
            radius on the image plane in meter.
        RETURN
        ------
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        """
        # r_pixel = 2*f*np.sin(theta/2)
        # -> 2 * arcsin(r_pixel/2/f) = theta
        x = np.ma.masked_outside(radius_pixel / 2. / self.focal_length, -1, 1)
        x = 2. * np.ma.arcsin(x)

        # workaround if radius_pixel is an int or float
        if isinstance(x, np.float64):
            return x
        elif isinstance(x, np.ma.core.MaskedConstant):
            return np.nan
        elif isinstance(x, np.ma.core.MaskedArray):
            return x.filled(np.nan)

    def theta2image_radius(self, theta):
        """
        PARAMETERS
        ----------
        theta: float, ndarray
            the theta component of the direction the pixel get projected to
        RETURN
        ------
        radius: int, float, ndarray
            radius on the image plane in meter.
        """
        # r_pixel = 2*f*np.sin(theta/2)
        # -> 2 * arcsin(r_pixel/2/f) = theta
        return 2. * self.focal_length * np.sin(theta / 2.)


class TransformCoordinates:
    def __init__(self, projection, position_module, position_steel_cable, position_module_vec=None):
        """Helper class to transform the real world coordinates to the camera coordinates including the inverse
        transformation. The real world coordinates are defined by the steel line. The line is expected to be vertical
        and defines the z-axis. The module is positioned at x=.295m and y=0m, as the module center is seperated by 295mm
         from the steel cable in STRAW-b.

        Parameters
        ----------
        projection: CameraProjection
            projection model of the camera
        position_module: ndarray, list[float]
            the position of the module in pixel coordinates [pixel_x, pixel_y].
            Usually this is 'camera.config.position_module'.
        position_steel_cable: ndarray, list[float]
            the position of the steel cable in pixel coordinates [pixel_x, pixel_y].
            Usually this is 'camera.config.position_steel_cable'.
        position_module_vec: ndarray, list[float], optional
            the position of the module in the real world as vector [x,y,z] in meter. Usually (also the default if None)
            this is: '[.295, 0., 0.], for STRAW-b as the module center is seperated by 295mm from the steel cable.
        """
        if position_module_vec is None:
            position_module_vec = [.295, 0., 0.]
        self.projection = projection
        self.position_module_vec = position_module_vec

        # noinspection PyTupleAssignmentBalance
        self.phi_module, self.theta_module = self.projection.pixel2angle(*position_module[None].T)
        # projection.pixel2angle returns an array here with shape= (1,), extract the floats
        self.phi_module, self.theta_module = self.phi_module[0], self.theta_module[0]

        # not 100% the true solution, but close
        steel_cable_vec = self._align_camera_(projection.pixel2vec(*position_steel_cable[None].T))
        self.phi_cable = -np.pi + projection.pixel2angle(*projection.vec2pixel(*steel_cable_vec))[0][0]

    def _align_camera_(self, points, inverse=False):
        """ Align to real world orientation to the camera orientation or vise versa.
        Parameters
        ----------
        points: ndarray
            real world coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        inverse:
            if True calculates the inverse camera -> real world. Default False.
        Returns
        -------
        points: ndarray
            camera coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        """
        if inverse:
            # real world -> Camera
            # first rotation around z <-> gamma <-> phi
            points = ProjectionTools.rotation(points, beta=self.theta_module)
            # second rotation around y <-> beta <-> theta
            return ProjectionTools.rotation(points, gamma=self.phi_module)

        else:
            # Camera -> real world
            # first rotation around y <-> beta <-> theta
            points = ProjectionTools.rotation(points, gamma=-self.phi_module)
            # second rotation around z <-> gamma <-> phi
            return ProjectionTools.rotation(points, beta=-self.theta_module)

    def real2camera(self, points):
        """ Transform the real world coordinates (x,y,z) to the camera coordinates (x',y',z')
        Parameters
        ----------
        points: ndarray
            real world coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]

        Returns
        -------
        points: ndarray
            camera coordinates of points with the shape [[x'_0,...], [y'_0,...], [z'_0,...]]
        """
        # the string is .295 from the module center == optical axis
        points = ProjectionTools.translation(points,
                                             x=-self.position_module_vec[0],
                                             y=-self.position_module_vec[1],
                                             z=-self.position_module_vec[2])

        # align to the cable orientation
        points = ProjectionTools.rotation(points, gamma=self.phi_cable)

        # align to the module position
        return self._align_camera_(points, inverse=True)

    def camera2real(self, points):
        """ Transform the camera coordinates (x',y',z') to real world coordinates (x,y,z)
        Parameters
        ----------
        points: ndarray
            camera coordinates of points with the shape [[x'_0,...], [y'_0,...], [z'_0,...]]

        Returns
        -------
        points: ndarray
            real world coordinates of points with the shape [[x_0,...], [y_0,...], [z_0,...]]
        """
        # align to the module position
        # align to the module position
        points = self._align_camera_(points, inverse=False)

        # align to the cable orientation
        points = ProjectionTools.rotation(points, gamma=-self.phi_cable)

        # the string is .295 from the module center == optical axis
        return ProjectionTools.translation(points,
                                           x=self.position_module_vec[0],
                                           y=self.position_module_vec[1],
                                           z=self.position_module_vec[2])
