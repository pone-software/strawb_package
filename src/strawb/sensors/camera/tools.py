import cv2
import numpy as np
import rasterio.features 
import shapely.geometry
import shapely.ops


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
    dev: in how many parts n = dev**2, the image should be split and equalizated.
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


def simplify_contours(contours, simplify_tolerance = 1):
    """simplify the contours of a polygon with shapely"""
    
    contours_s = []
    for i in contours:
        poly = shapely.geometry.Polygon(i)
        poly_s = poly.simplify(tolerance=simplify_tolerance)
        contours_s.append(np.array(poly_s.boundary.coords[:]))

    return contours_s


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
    inside_polygon = [shapely.ops.unary_union([i for i in polygon]).contains(i) for i in points_p]

    # list of coordinates of the points inside area
    points_inside = [i for i,j in zip(points_co, inside_polygon) if j == True]

    return inside_polygon, points_inside