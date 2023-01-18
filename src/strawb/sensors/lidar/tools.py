# LiDAR tools
import numpy as np
import healpy
import pandas


def circle_segment(x, r):
    """Area of a circle path and a straight line. Its calculated as the
    segment of a circle minus the triangle resulting in area
    PARAMETER
    ----------
    x: float, ndarray
        distance from the center to the line. The returned area is left of the line.
        Therefore: x<-r = 0 and x>r = pi*r^2
    r: float
        radius of the circle

    For different alignments of laser and pmt.
    The laser can't enter if the alignments is greater than FoV (theta_pmt) + laser divergence (theta_laser).
    """
    x, r = np.broadcast_arrays(x, r)
    x, r = x.astype(float), r.astype(float)
    # get an array with 0's to fill it in the next steps
    out = np.zeros_like(x)
    mask = (-r <= x) & (x <= r)
    out[mask] = r[mask] ** 2 * np.arccos(-x[mask] / r[mask]) + x[mask] * np.sqrt(r[mask] ** 2 - x[mask] ** 2)
    out[x > r] = r[x > r] ** 2 * np.pi
    return out


def a_intersection(d, r_0, r_1):
    """Intersection area of two circles.
    A=0 for |d|>r_0+r_1;
    A=min([r_0, r_1])**2*pi; |d|<|r_0-r_1|
    PARAMETER
    ----------
    d: float, ndarray
        distance between the circle's center.
    r_0, r_1: float, ndarray
        radius of the circles
    """
    d, r_0, r_1 = np.broadcast_arrays(d, r_0, r_1)
    d, r_0, r_1 = d.astype(float), r_0.astype(float), r_1.astype(float)
    r_0, r_1 = np.abs(r_0), np.abs(r_1)

    x_1 = (d ** 2 - r_0 ** 2 + r_1 ** 2) / (-2. * np.abs(d))
    x_0 = -np.abs(d) - x_1
    mask = np.abs(x_0) > r_0
    x_0[mask] = np.sign(x_0[mask]) * r_0[mask]
    mask = np.abs(x_1) > r_1
    x_1[mask] = np.sign(x_1[mask]) * r_1[mask]

    return circle_segment(x_0, r_0) + circle_segment(x_1, r_1)


def generate_healpy_file(nside_max=15):
    for close_ring_i in [True, False]:
        # store the first nsides to
        df_list = []
        for nside in range(1, nside_max + 1):
            df_i = pandas.DataFrame(healpy_path(nside=nside, close_ring=close_ring_i,
                                                theta_max=180., phi_max=360.,
                                                add_zenith=False), columns=['theta', 'phi'])
            df_i['nside'] = nside
            df_list.append(df_i)

        # merge dfs
        df = pandas.concat(df_list)

        # get nside as first column
        df = df[['nside', 'theta', 'phi']]

        # store
        if close_ring_i:
            df.to_csv('healpy_path_closed.csv', index=False)
        else:
            df.to_csv('healpy_path.csv', index=False)


def healpy_path(nside=2, theta_max=100., phi_max=330., add_zenith=True, close_ring=True):
    """Calculates a path along the discrete grid of healpy pixel. Te path starts either at the zenith (<->theta=0)
    (add_zenith=True) or the first healpy pixel close to the zenith and going downwards with increasing theta.
    The path is ordered in a way that phi isn't doing a full rotation to prevent rotations in the cabling.
    PARAMETER
    ---------
    nside: int, optional
        healpy nside parameter which defines the number of points (12*nside**2 in 4 pi). Default: 2
    theta_max: float, optional
        cut the healpy to pixels with a theta lower theta_max in degree. Default: 100.
        Gimbal max range is 0->100 deg (limited by the arduino code)
    phi_max: float, optional
        cut the healpy to pixels with a phi lower phi_max in degree. Default: 330.
        Gimbal max range is 0->330 deg (limited by the arduino code)
    add_zenith: bool, optional
        if the zenith should be added as starting point as it is not a healpy pixel
    close_ring: bool, optional
        adds for each ring a pixel to phi=0 and phi=phi_max that the gimbal covers
        0<=phi<=phi_max for each ring. A ring is all pixels that have the same theta.
    Returns
    -------
    positions: ndarray
        the positions as a 2d array with [[theta_0,phi_0], [theta_1, phi_1],...]
    """
    pix_index = np.arange(healpy.nside2npix(nside=nside))
    theta, phi = healpy.pix2ang(nside, pix_index)

    mask_pixel = theta <= np.deg2rad(theta_max)
    pixel_ring = healpy.pix2ring(nside, pix_index[mask_pixel])  # [mask_pixel]
    theta, phi = theta[mask_pixel], phi[mask_pixel]

    if add_zenith:
        path = [[[0], [0]]]
    else:
        path = []

    for i in np.unique(pixel_ring):
        m = (pixel_ring == i) & (phi <= np.deg2rad(phi_max))
        # clockwise
        if i % 2:
            # add a point with phi=0 for the ring
            if close_ring and phi[m][0] != 0:
                path.append([theta[m][:1], [0]])
            path.append([theta[m], phi[m]])
            # add a point with phi=360 for the ring
            if close_ring and phi[m][-1] != np.deg2rad(phi_max):
                path.append([theta[m][:1], [np.deg2rad(phi_max)]])
        # counterclockwise
        else:
            # add a point with phi=0 for the ring
            if close_ring and phi[m][0] != np.deg2rad(phi_max):
                path.append([theta[m][:1], [np.deg2rad(phi_max)]])
            path.append([theta[m][::-1], phi[m][::-1]])
            # add a point with phi=360 for the ring
            if close_ring and phi[m][0] != 0:
                path.append([theta[m][:1], [0]])

    # get it to array: [[theta_0,phi_0], [theta_1, phi_1],...]
    return np.rad2deg(np.concatenate(path, axis=1).T)


def simulate_gimbal(path, n=10):
    """The gimbal moves phi first and theta second. Simulate it here.
    Also add a path of n-points between two pixel to plot the pat, e.g. with a polar plot."""
    path_gimbal = []
    for i, pos_0 in enumerate(path[:-1]):
        path_i = [path[i]]
        if path[i, 1] != path[i + 1, 1]:
            path_ii = np.zeros((n, 2))
            path_ii[:, 0] = path_i[-1][0]
            path_ii[:, 1] = np.linspace(path[i, 1], path[i + 1, 1], n)
            path_i.extend(path_ii)
        if path[i, 0] != path[i + 1, 0]:
            path_ii = np.zeros((n, 2))
            path_ii[:, 1] = path_i[-1][1]
            path_ii[:, 0] = np.linspace(path[i, 0], path[i + 1, 0], n)
            path_i.extend(path_ii)
        path_gimbal.extend(path_i)
    return np.vstack(path_gimbal)
