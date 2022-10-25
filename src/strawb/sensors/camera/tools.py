import cv2
import numpy as np
import shapely.geometry
import shapely.ops
import rasterio.features


def img_rectangle_cut(img, rect=None, angle=None, angle_normalize=True):
    """Translate an image, defined by a rectangle. The image is cropped to the size of the rectangle
    and the cropped image can be rotated.
    The rect must be of the from (tuple(center_xy), tuple(width_xy), angle).
    The angle are in degrees.
    PARAMETER
    ---------
    img: ndarray
    rect: tuple, optional
        define the region of interest. If None, it takes the whole picture
    angle: float, optional
        angle of the output image in respect to the rectangle.
        I.e. angle=0 will return an image where the rectangle is parallel to the image array axes
        If None, no rotation is applied.
    angle_normalize: bool, optional
        normalize angle that angel=0 is vertical, and angel=90 is horizontal.
        Otherwise, this isn't fixed and depends on the rect.
    RETURNS
    -------
    img_return: ndarray
    rect_return: tuple
        the rectangle in the returned image
    t_matrix: ndarray
        the translation matrix
    """
    if rect is None:
        if angle is None:
            angle = 0
        rect = (tuple(np.array(img.shape) * .5), img.shape, 0)
    box = cv2.boxPoints(rect)

    rect_target = rect_rotate(rect, angle=angle, angle_normalize=angle_normalize)
    pts_target = cv2.boxPoints(rect_target)

    # get max dimensions
    size_target = np.int0(np.ceil(np.max(pts_target, axis=0) - np.min(pts_target, axis=0)))

    # translation matrix
    t_matrix = cv2.getAffineTransform(box[:3].astype(np.float32),
                                      pts_target[:3].astype(np.float32))

    # cv2 needs the image transposed
    img_target = cv2.warpAffine(cv2.transpose(img), t_matrix, tuple(size_target))

    # undo transpose
    img_target = cv2.transpose(img_target)
    return img_target, rect_target, t_matrix


def reshape_cv(x, axis=-1):
    """openCV and numpy have a different array indexing (row, cols) vs (cols, rows), compensate it here."""
    x = np.array(x).astype(np.float32)
    if axis < 0:
        axis = len(x.shape) + axis
    return x[(*[slice(None)] * axis, slice(None, None, -1))]


def transform_np(x, t_matrix):
    """Apply a transform on a openCV indexed array and return a numpy indexed array."""
    return transform_cv2np(reshape_cv(x), t_matrix)


def transform_cv2np(x, t_matrix):
    """Apply a transform on a numpy indexed array and return a numpy indexed array."""
    return reshape_cv(cv2.transform(np.array([x]).astype(np.float32), t_matrix)[0])


def rect_scale_pad(rect, scale=1., pad=40.):
    """Scale and/or pad a rectangle."""
    return (rect[0],
            tuple((np.array(rect[1]) + pad) * scale),
            rect[2])


def rect_rotate(rect, angle=None, angle_normalize=True):
    """Rotate a rectangle by an angle in respect to it's center.
    The rect must be of the from (tuple(center_xy), tuple(width_xy), angle).
    The angle is in degrees.
    PARAMETER
    ---------
    rect: tuple
        cv2 rect with format: (tuple(center_xy), tuple(width_xy), angle). Angle in [deg].
    angle: float, optional
        angle to rotate the rect in degree. With angle=0, the rect is parallel to the axes.
        If angle is None, default, it takes the angle of the input rect.
    angle_normalize: bool, optional
        normalize angle that angel=0 is vertical, and angel=90 is horizontal.
        Otherwise, this isn't fixed and depends on the rect.
    RETURN
    ------
    rect: tuple
        cv2 rect with applied rotation. Format: (tuple(center_xy), tuple(width_xy), angle). Angle in [deg].
    """
    if angle is None:
        angle = rect[2]

    # angel=0 vertical; angel=90 horizontal
    if angle_normalize and rect[1][1] > rect[1][0]:
        angle -= 90

    rad = np.deg2rad(np.abs(angle))
    rot_matrix_2d = np.array([[np.cos(rad), np.sin(rad)],
                              [np.sin(rad), np.cos(rad)]])

    # cal. center of rectangle
    center = np.sum(np.array(rect[1]).reshape(1, -1) * rot_matrix_2d, axis=-1) * .5
    center = np.abs(center)

    return tuple(center), rect[1], angle


# #### EXAMPLE ####

# # Generate Image
# img = np.zeros((1200, 660), dtype=np.uint8)

# # Draw some lines and gen. points
# x_0 = np.array([150, 600])
# x_1 = np.int0(x_0 + np.array((100, 100)))
# x_2 = np.int0(x_0 + np.array((100, -100)) * 2.5)
# img = cv2.line(img, tuple(x_0), tuple(x_1), 1, 120)
# img = cv2.line(img, tuple(x_0), tuple(x_2), 1, 120)
# points = np.array([x_0, x_1, x_2])

# # Get Box
# rect = cv2.minAreaRect(np.argwhere(img))

# # Apply transformation
# rect_scale = rect_scale_pad(rect, scale=1., pad=40.)
# img_return, rect_target, t_matrix = img_rectangle_cut(
#     img,
#     rect_scale,
#     angle=0,
#     angle_normalize=True  # True <-> angel=0 vertical; angel=90 horizontal
# )

# # PLOT
# fig, ax = plt.subplots(ncols=2, figsize=(10, 5))
# ax = ax.flatten()
# ax[0].imshow(img)

# box_i = reshape_cv(cv2.boxPoints(rect))
# ax[0].plot(*strawb.tools.connect_polar(box_i).T, 'o-', color='gray', alpha=.75, label='Original Box')
# box_i = reshape_cv(cv2.boxPoints(rect_scale))
# ax[0].plot(*strawb.tools.connect_polar(box_i).T, 'o-', color='green', alpha=.75, label='Scaled Box')
# ax[0].plot(*points.T, 'o', label='Points')

# ax[1].imshow(img_return)
# box_i = transform_cv2np(cv2.boxPoints(rect), t_matrix)
# ax[1].plot(*strawb.tools.connect_polar(box_i).T, 'o-', color='gray', alpha=.75, label='Original Box')

# point_t = transform_np(points, t_matrix)
# ax[1].plot(*point_t.T, 'o', label='Points')

# ax[0].set_title('Original')
# ax[1].set_title('Translated')

# for axi in ax:
#     axi.legend(loc=1)
#
# plt.tight_layout()

def equalization(image, dev=8):
    """
    image: RGB as float [0..1] or uint8
    dev: in how many parts n = dev**2, the image should be split and equalized.
    """

    if image.dtype == np.float64:
        image = image.astype(np.float32)
    elif image.dtype == np.uint8:
        pass
    elif image.dtype == np.uint16:
        image = image // 2

    # convert from RGB color-space to YCrCb
    ycrcb_img = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    ycrcb_img = (ycrcb_img * 2 ** 8).astype(np.uint8)

    # equalize the histogram of the Y channel
    #     ycrcb_img[:, :, 0] = cv2.equalizeHist(ycrcb_img[:, :, 0])

    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=tuple([dev] * 2))
    ycrcb_img[:, :, 0] = clahe.apply(ycrcb_img[:, :, 0])

    # convert back to RGB color-space from YCrCb
    img = cv2.cvtColor(ycrcb_img, cv2.COLOR_YCrCb2BGR)
    return img


def get_bit(bit):
    if bit == 8:
        dtype = np.uint8
        n_max = 2 ** 8
    elif bit == 16:
        dtype = np.uint16
        n_max = 2 ** 16
    else:
        raise ValueError(bit)
    return n_max, dtype


def mirror_rgb(rgb, axis=0):
    """ Alias for np.flip with axis=0 as default.
    PARAMETER
    ---------
    rgb: ndarray
        rgb array of an image
    axis: int, optional
        define the axis to mirror. For an image use: 1 for x axis and 0 (default) for y axis. As plt.imshow and other
        plot the first axis of the array as the y axis and the second as x axis.
    RETURN
    ------
    mirror_rgb: ndarray
        mirrored positions
    """
    return np.flip(rgb, axis=axis)


def mirror_position(position, axis=1, axis_length=1280):
    """
    PARAMETER
    ---------
    position: ndarray
        at a least 1d array. First dimension must be is x and y, i.e. shape[0] == 2.
    axis: int, optional
        define the axis to mirror. 0 for x axis and 1 (default) for y axis.
    axis_length: int, optional
        mirroring happens at `axis_length/2`. Depends on the actual image size, for 'x' it is 960 and
        for 'y' it is '1280'.
    RETURN
    ------
    position_mirror: ndarray
        mirrored positions
    """
    position = position.copy()
    position[axis] = axis_length - position[axis]
    return position


def shift_effective_pixel(position, eff_margin=None, inverse=False):
    """ Shift a position to match the shift induced by effective margin cuts from the rgb array.
    PARAMETER
    ---------
    position: ndarray
        at a least 1d array. First dimension must be is x and y.
    eff_margin: bool, list, ndarray, optional
        shifts the position according to the effective margin for images where the margin is cut, e.g. with
        cut2effective_pixel(..., eff_margin=eff_margin),  get_raw_rgb_mask(..., eff_margin=eff_margin)
        If None or True, it takes the default eff_margin = np.array([8, 9, 8, 9])
        If its a list or ndarray: it must has the from [pixel_x_start, pixel_x_stop, pixel_y_start, pixel_y_stop]
        and only integers are allowed.
    inverse: True
        if True, adds the margins: cut margin -> uncut margin
        if False, subtract the margins: uncut margin -> cut margin
    RETURN
    ------
    position_shifted:
        the rgb array with cut margins
    """
    position = np.array(position)

    if eff_margin is None or eff_margin is True:
        eff_margin = np.array([8, 9, 8, 9])

    if inverse:
        return (position.T + [eff_margin[0], eff_margin[2]]).T
    else:
        return (position.T - [eff_margin[0], eff_margin[2]]).T


def get_contours(mask):
    """Generate polygons, aka. contour, which surround the True areas in the 2D mask based on cv2.findContours
    PARAMETER
    ---------
    mask: ndarray
        2d bool array
    RETURNS
    -------
    contours: list
        a list of 2d ndarray in the form [np.array([[x_0, y_0], [x_1, y_1], ...]), np.array(...), ...]
        each list entry is a contour around all 'True' areas in the 2D mask
    hierarchy: ndarray
        forwarded from cv2.findContours
    """
    # get contours, cv2 need uint, here uint8
    contours, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours = [i.reshape((-1, 2)) for i in contours]
    return contours, hierarchy


def simplify_contours(contours, simplify_tolerance=1., preserve_topology=True):
    """Simplify a contour, i.e. points all in a single line will reduce to start and endpoint, removing the points
    in between. It use shapely.geometry.simplify which base on the Douglas-Peucker algorithm.
    PARAMETER
    ---------
    contours: ndarray
        a list of 2d ndarrays in the form [np.array([[x_0, y_0], [x_1, y_1], ...]), np.array(...), ...]
        each list entry is a separate contour
    simplify_tolerance: float, optional
        Coordinates of the simplified geometry will be no more than the tolerance distance from the original.
    preserve_topology: bool, optional
        Unless the topology preserving option is used, the algorithm may produce self-intersecting or
        otherwise invalid geometries. So default is True.
    RETURNS
    -------
    simplify_contours: list
        a list of the simplified contours from the input contours
    """
    # simplify contours with shapely
    contours_s = []
    for i in contours:
        poly = shapely.geometry.Polygon(i)
        poly_s = poly.simplify(tolerance=simplify_tolerance, preserve_topology=preserve_topology)
        contours_s.append(np.array(poly_s.boundary.coords[:]))
    return contours_s


def get_contours_simplify(mask, simplify_tolerance=1., preserve_topology=True):
    """ Combines get_contours and simplify_contours and returns the simplified contours.
    PARAMETER
    ---------
    mask: ndarray
        2d bool array
    simplify_tolerance: float, optional
        Coordinates of the simplified geometry will be no more than the tolerance distance from the original.
    preserve_topology: bool, optional
        Unless the topology preserving option is used, the algorithm may produce self-intersecting or
        otherwise invalid geometries. So default is True.
    RETURNS
    -------
    contours: list
        a list of 2d ndarrays in the form [np.array([[x_0, y_0], [x_1, y_1], ...]), np.array(...), ...]
        each list entry is a contour around all 'True' areas in the 2D mask and the contour is simplified.
    hierarchy: ndarray
        forwarded from cv2.findContours
    """
    # get contours, cv2 need uint, here uint8
    contours, hierarchy = get_contours(mask)
    contours = simplify_contours(contours, simplify_tolerance=simplify_tolerance, preserve_topology=preserve_topology)
    return contours, hierarchy


# get distance to polygon (its not too fast)
def get_distance_poly(x, y, poly):
    """Shortest distance between a point and a polygon. Positive values for point is inside the polygon,
    negative when outside.
    PARAMETER
    ---------
    x, y: float
        x and y coordinate
    poly: shapely.geometry.Polygon, ndarray
        a shapely.geometry.Polygon or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the contour
    RETURNS
    -------
    distance: float
        the shortest distance between the polygon boundary and the coordinate. Negative if outside the polygon,
        positive when inside.
    """
    if not isinstance(poly, shapely.geometry.Polygon):
        poly = shapely.geometry.Polygon(poly)
    pt = shapely.geometry.Point(x, y)
    return (1 - poly.contains(pt) * 2) * poly.boundary.distance(pt)


def get_distances_poly(x, y, poly):
    """Calculates the get_distance for array of x,y values to a polygon. X and y must have the same length and 1d.
    PARAMETER
    ---------
    x, y: ndarray
        x and y coordinates as 1d ndarray both with the same length
    poly: shapely.geometry.Polygon, ndarray
        a shapely.geometry.Polygon or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the contour
    RETURNS
    -------
    distances: ndarray
        the shortest distances between the polygon boundary and the coordinates. Negative if outside the polygon,
        positive when inside.
    """
    if not isinstance(poly, shapely.geometry.Polygon):
        poly = shapely.geometry.Polygon(poly)
    return np.array([get_distance_poly(x_i, y_i, poly) for x_i, y_i in zip(x, y)])


# get distance to polygon (its not too fast)
def get_distance_line(x, y, line):
    """Shortest distance between a point and a line. Respect a polygon, a line is not closed.
    PARAMETER
    ---------
    x, y: float
        x and y coordinate
    line: shapely.geometry.LineString or ndarray
        a shapely.geometry.LineString or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the line. Can be multiple points.
    RETURNS
    -------
    distance: float
        the shortest distance between the line and the coordinate. distances>=0
    """
    if not isinstance(line, shapely.geometry.LineString):
        line = shapely.geometry.LineString(line)
    pt = shapely.geometry.Point(x, y)
    return line.distance(pt)


def get_distances_line(x, y, line):
    """Calculates the get_distance for array of x,y values to a line. X and y must have the same length and 1d.
    Respect a polygon, a line is not closed.
    PARAMETER
    ---------
    x, y: ndarray
        x and y coordinates as 1d ndarray both with the same length
    line: shapely.geometry.LineString or ndarray
        a shapely.geometry.LineString or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the line. Can be multiple points.
    RETURNS
    -------
    distances: ndarray
        the shortest distances between the line and the coordinates. distances>=0
    """
    return np.array([get_distance_line(x_i, y_i, line) for x_i, y_i in zip(x, y)])


def get_nearest_point_line(x, y, line):
    """Closest point on the line to the coordinate.
    PARAMETER
    ---------
    x, y: float
        x and y coordinate
    line: shapely.geometry.LineString or ndarray
        a shapely.geometry.LineString or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the line. Can be multiple points. For a polygon you can use
        get_nearest_point_line(x,y, polygon.boundary).
    RETURNS
    -------
    coordinate: ndarray
        coordinate [x,y] of the closest point on the line to the given point.
    """
    if not isinstance(line, shapely.geometry.LineString):
        line = shapely.geometry.LineString(line)
    pt = shapely.geometry.Point(x, y)

    # want [0] - [1] is the point again, would be different if it not a point
    return np.array(shapely.ops.nearest_points(line, pt)[0].coords).flatten()


def get_nearest_points_line(x, y, line):
    """Closest point on the line to multiple coordinates.
    PARAMETER
    ---------
    x, y: ndarray
        x and y coordinates as 1d ndarray both with the same length
    line: shapely.geometry.LineString or ndarray
        a shapely.geometry.LineString or a 2d ndarray in the form np.array([[x_0, y_0], [x_1, y_1], ...])
        defining the line. Can be multiple points.
    RETURNS
    -------
    coordinates: ndarray
        coordinates [[x,y], ...] of the closest points on the line to the given points.
    """
    return np.array([get_nearest_point_line(x_i, y_i, line) for x_i, y_i in zip(x, y)])


def get_polygon(mask):
    """
    Get the polygon around a certain area and its coordinates.

    PARAMETER
    ---------
    mask: 2darray, bool
        Array the same size as the pixel arrangement of the camera, each element representing a pixel. 
        True if pixel is inside an contiguous area, else False.

    RETURNS
    -------
    polygons: MultiPolygon
        Polygon around considered area.
    contours: list
        List of coordinates of the points forming the polygons. Each element of the list belongs to one polygon 
        and contains two other lists, the first one are the x-coordinates, the second one the y-coordinates.
    """

    # array with 1 if pixel is inside the mask, else 0 as int32
    im = np.where(mask == True, 1, 0).astype('int32')  

    # get shapes and values of connected regions in array
    shapes = rasterio.features.shapes(im) 

    # get the polygon around each shape
    polygons = [shapely.geometry.Polygon(shape[0]['coordinates'][0]) for shape in shapes if shape[1] == 1]

    # get coordinates of the polygon points
    contours = [(i.boundary.coords) for i in polygons]
    contours = [np.array(i) for i in contours]

    return polygons, contours


def inside_polygon(polygon, points_x, points_y):
    """
    Check if points are inside a polygon.

    PARAMETER
    ---------
    polygon: polygon
    points_x: pandas series
        Pandas series with x-coordinates of the points to be checked.
    points_y: pandas series
        Pandas series with y-coordinate of the points to be checked.

    RETURNS
    -------
    inside_polygon: list
        List with True if point is inside the polygon, else False.
    points_inside: list
        List of points inside the considered area.
    """

    # list of coordinates of points as tuples
    points_co = [(x,y) for x,y in zip(points_x, points_y)]
    # make coordinates "Point" objects
    points_p = [shapely.geometry.Point(i,j) for i,j in zip(points_x.astype('int32'), 
                                                           points_y.astype('int32'))]
    
    # list with True if point is inside the given area, else False
    inside_polygon = [polygon.contains(i) for i in points_p]

    # list of coordinates of the points inside area
    points_inside = [i for i,j in zip(points_co, inside_polygon) if j == True]

    return inside_polygon, points_inside