from unittest import TestCase
import numpy as np

from src.strawb.sensors.camera.projection import CameraProjection, EquisolidProjection, ProjectionTools, \
    SphereDistortion


class TestCameraProjection(TestCase):
    def setUp(self) -> None:
        # config
        self.focal_length = 2
        self.center_index = np.array([10, 15])
        self.pixel_size = 1e-5  # meter
        self.projection = CameraProjection(self.focal_length,
                                           pixel_size=self.pixel_size,
                                           pixel_center_index=self.center_index)

    def test_index2coordinates(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_i = np.array([np.cos(phi) + self.center_index[0],
                          np.sin(phi) + self.center_index[1]])

        # convert
        pos_c = self.projection.pixel_index2image_coordinates(*pos_i)
        self.assertAlmostEqual(np.hypot(*pos_c).max(), self.pixel_size, places=12)

        # and convert the way back
        pos_ii = self.projection.image_coordinates2pixel_index(*pos_c)
        self.assertAlmostEqual(np.hypot(*(pos_ii - pos_i)).max(), 0, places=12)

    def test_image_coordinates2phi(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        # convert
        for invert_dir_i in [False, True]:
            pos_cor = self.projection.pixel_index2image_coordinates(*pos_index)
            pos_cor = np.array(pos_cor)
            phi_c = self.projection.image_coordinates2phi(*pos_cor, invert_dir=invert_dir_i)
            self.assertAlmostEqual(np.abs(np.unwrap(phi_c) - phi).max(), np.pi * invert_dir_i, places=12,
                                   msg=f'invert_dir={invert_dir_i}')

            # and convert the way back
            pos_cor_inv = self.projection.phi2image_coordinates(phi_c,
                                                                radius=self.pixel_size,
                                                                invert_dir=invert_dir_i)
            pos_cor_inv = np.array(pos_cor_inv)
            self.assertAlmostEqual(np.hypot(*(pos_cor_inv - pos_cor)).max(), 0, places=12,
                                   msg=f'invert_dir={invert_dir_i}')

    def test_image_radius2theta(self):
        radius = np.linspace(0, self.focal_length * 5, 10)
        theta = self.projection.image_radius2theta(radius)
        radius_inv = self.projection.theta2image_radius(theta)
        msg = '\n'.join([f'theta={np.rad2deg(theta)} [deg]'
                         f'radius    ={radius}',
                         f'radius_inv={radius_inv}'])
        self.assertAlmostEqual((radius_inv - radius)[~np.isnan(theta)].max(), 0, places=12, msg=msg)

    def test_pixel2angle(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        for invert_dir_i in [False, True]:
            phi, theta = self.projection.pixel2angle(*pos_index, invert_dir=invert_dir_i)
            pos_index_inv = self.projection.angle2pixel(phi, theta, invert_dir=invert_dir_i)
            pos_index_inv = np.array(pos_index_inv)
            self.assertAlmostEqual(np.hypot(*(pos_index_inv - pos_index)).max(), 0, places=12,
                                   msg=f'invert_dir={invert_dir_i}')

    def test_pixel2vec(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        for invert_dir_i in [False, True]:
            x, y, z = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            pos_index_inv = self.projection.vec2pixel(x, y, z, invert_dir=invert_dir_i)
            pos_index_inv = np.array(pos_index_inv)
            self.assertAlmostEqual(np.hypot(*(pos_index_inv - pos_index)).max(), 0, places=10,
                                   msg=f'invert_dir={invert_dir_i};\n'
                                       f'pos_index={pos_index};\n'
                                       f'pos_index_inv={pos_index_inv}')

    def test_vec2pixel(self):
        # create points on a circle around the center with radius 1 pixel
        radius = 1.5
        phi, theta = np.meshgrid(np.linspace(0, np.pi*2., 9),
                                 np.linspace(0, np.pi/2., 7))
        vec = radius * np.array([np.cos(phi) * np.sin(theta),
                                 np.sin(phi) * np.sin(theta),
                                 np.cos(theta)]).reshape(3, -1)

        for invert_dir_i in [False, True]:
            pos_index = self.projection.vec2pixel(*vec, invert_dir=invert_dir_i)
            vec_inv = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            vec_inv = np.array(vec_inv) * radius

            r, phi, theta = ProjectionTools.cart2spherical(*(vec_inv - vec))
            msg = '\n'.join(['invert_dir_i= {invert_dir_i}',
                             # f'vec    ={vec}',
                             # f'vec_inv={vec_inv}',
                             # f'r      ={r}'
                             ])
            self.assertAlmostEqual(r.max(), 0, places=12, msg=msg)


class TestEquisolidProjection(TestCase):
    def setUp(self) -> None:
        # config
        self.focal_length = 2
        self.center_index = np.array([10, 15])
        self.pixel_size = 1e-5  # meter
        self.projection = EquisolidProjection(self.focal_length,
                                              pixel_size=self.pixel_size,
                                              pixel_center_index=self.center_index)

    def test_image_radius2theta(self):
        radius = np.linspace(0, self.focal_length * 5, 10)
        theta = self.projection.image_radius2theta(radius)
        radius_inv = self.projection.theta2image_radius(theta)
        msg = '\n'.join([f'theta={np.rad2deg(theta)} [deg]'
                         f'radius    ={radius}',
                         f'radius_inv={radius_inv}'])
        self.assertAlmostEqual((radius_inv - radius)[~np.isnan(theta)].max(), 0, places=12, msg=msg)

    def test_pixel2angle(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        for invert_dir_i in [False, True]:
            phi, theta = self.projection.pixel2angle(*pos_index, invert_dir=invert_dir_i)
            pos_index_inv = self.projection.angle2pixel(phi, theta, invert_dir=invert_dir_i)
            pos_index_inv = np.array(pos_index_inv)
            self.assertAlmostEqual(np.hypot(*(pos_index_inv - pos_index)).max(), 0, places=12,
                                   msg=f'invert_dir={invert_dir_i}')

    def test_pixel2vec(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        for invert_dir_i in [False, True]:
            x, y, z = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            pos_index_inv = self.projection.vec2pixel(x, y, z, invert_dir=invert_dir_i)
            pos_index_inv = np.array(pos_index_inv)
            self.assertAlmostEqual(np.hypot(*(pos_index_inv - pos_index)).max(), 0, places=10,
                                   msg=f'invert_dir={invert_dir_i};\n'
                                       f'pos_index={pos_index};\n'
                                       f'pos_index_inv={pos_index_inv}')

    def test_vec2pixel(self):
        # create points on a circle around the center with radius 1 pixel
        radius = 1.5
        phi, theta = np.meshgrid(np.linspace(0, np.pi * 2., 9),
                                 np.linspace(0, np.pi / 2., 7))
        vec = radius * np.array([np.cos(phi) * np.sin(theta),
                                 np.sin(phi) * np.sin(theta),
                                 np.cos(theta)]).reshape(3, -1)

        for invert_dir_i in [False, True]:
            pos_index = self.projection.vec2pixel(*vec, invert_dir=invert_dir_i)
            vec_inv = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            vec_inv = np.array(vec_inv) * radius

            r, phi, theta = ProjectionTools.cart2spherical(*(vec_inv - vec))
            msg = '\n'.join(['invert_dir_i= {invert_dir_i}',
                             # f'vec    ={vec}',
                             # f'vec_inv={vec_inv}',
                             # f'r      ={r}'
                             ])
            self.assertAlmostEqual(r.max(), 0, places=12, msg=msg)


class TestSphereDistortion(TestCase):
    def setUp(self) -> None:
        # config
        self.focal_length = 2
        self.center_index = np.array([10, 15])
        self.pixel_size = 1e-5  # meter
        # Values for STRAWb
        self.distortion = SphereDistortion(h=.063, r=.1531, d=.012, n_a=1., n_g=1.52, n_w=1.35)
        self.projection = EquisolidProjection(self.focal_length,
                                              pixel_size=self.pixel_size,
                                              pixel_center_index=self.center_index,
                                              distortion=self.distortion,
                                              )

    def test_theta_distortion(self):
        theta = np.linspace(0, np.pi, 10)
        theta_dis = self.distortion.theta_distortion(theta)
        theta_inv = self.distortion.theta_distortion_inv(theta_dis)
        msg = '\n'.join([f'theta     ={np.rad2deg(theta)} [deg]',
                         f'theta     ={theta}',
                         f'theta_inv ={theta_inv}'])
        self.assertAlmostEqual((theta - theta_inv)[~np.isnan(theta_dis)].max(), 0, places=10, msg=msg)

    def test_theta_distortion_inv(self):
        theta_dis = np.linspace(0, np.pi, 10)
        theta = self.distortion.theta_distortion_inv(theta_dis)
        theta_dis_inv = self.distortion.theta_distortion(theta)
        msg = '\n'.join([f'theta     ={np.rad2deg(theta)} [deg]',
                         f'theta     ={theta_dis}',
                         f'theta_inv ={theta_dis_inv}'])
        self.assertAlmostEqual((theta_dis - theta_dis_inv)[~np.isnan(theta_dis_inv)].max(), 0, places=10, msg=msg)

    def test_pixel2vec(self):
        # create points on a circle around the center with radius 1 pixel
        phi = np.linspace(0, np.pi * 2, 9)
        pos_index = np.array([np.cos(phi) + self.center_index[0],
                              np.sin(phi) + self.center_index[1]])

        for invert_dir_i in [False, True]:
            x, y, z = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            pos_index_inv = self.projection.vec2pixel(x, y, z, invert_dir=invert_dir_i)
            pos_index_inv = np.array(pos_index_inv)
            self.assertAlmostEqual(np.hypot(*(pos_index_inv - pos_index)).max(), 0, places=10,
                                   msg=f'invert_dir={invert_dir_i};\n'
                                       f'pos_index={pos_index};\n'
                                       f'pos_index_inv={pos_index_inv}')

    def test_vec2pixel(self):
        # create points on a circle around the center with radius 1 pixel
        radius = 1.5
        phi, theta = np.meshgrid(np.linspace(0, np.pi * 2., 9),
                                 np.linspace(0, np.pi / 2., 7))
        vec = radius * np.array([np.cos(phi) * np.sin(theta),
                                 np.sin(phi) * np.sin(theta),
                                 np.cos(theta)]).reshape(3, -1)

        for invert_dir_i in [False, True]:
            pos_index = self.projection.vec2pixel(*vec, invert_dir=invert_dir_i)
            vec_inv = self.projection.pixel2vec(*pos_index, invert_dir=invert_dir_i)
            vec_inv = np.array(vec_inv) * radius

            r, phi, theta = ProjectionTools.cart2spherical(*(vec_inv - vec))
            msg = '\n'.join(['invert_dir_i= {invert_dir_i}',
                             # f'vec    ={vec}',
                             # f'vec_inv={vec_inv}',
                             # f'r      ={r}'
                             ])
            self.assertAlmostEqual(r.max(), 0, places=12, msg=msg)