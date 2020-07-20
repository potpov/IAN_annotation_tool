import numpy as np


class Plane:

    def __init__(self, plane_z, plane_w):
        """
        create a new (empty) plane of coords, shape of the plane must be declared here
        Args:
            plane_z (Int): z shape of the plane (usually the Z len of the volume to cut)
            plane_w (Int): w shape of the plane (usually the len of the xy set of coordinates)
        """
        self.Z, self.W = plane_z, plane_w
        self.plane = np.empty((3, self.Z, self.W))
        # centre
        self.x_c = 0
        self.y_c = 0
        self.z_c = 0
        # axis
        self.ux = 0
        self.uy = 0
        self.uz = 0

    def from_line(self, xy_set):
        """
        load coordinates from a line (duplicating xy values over all the Z axis)
        Args:
            xy_set (numpy array): set of xy values
        """
        if len(xy_set.shape) > 2:
            raise Exception("coords_to_plane: feed this function with just one set of coords per time")

        # central point of this plane
        self.set_plane_centre(xy_set[len(xy_set) // 2, 0], xy_set[len(xy_set) // 2, 1], self.Z // 2)

        # vectors of axis of this plane
        self.set_plane_axis(xy_set)

        x_set, y_set = xy_set[:, 0], xy_set[:, 1]
        self.plane = np.stack((
            np.tile(x_set, (self.Z, 1)),
            np.tile(y_set, (self.Z, 1)),
            np.moveaxis(np.tile(np.arange(0, self.Z, dtype=np.float), (x_set.size, 1)), 0, 1)
        ))

    def set_plane_centre(self, x, y, z):
        """
        define the vectors on which the geometric transformation are executed (instead of the origin)
        Args:
            x (float): x axis vector
            y (float): y axis vector
            z (float): z axis vector
        """
        self.x_c = x
        self.y_c = y
        self.z_c = z

    def set_plane_axis(self, xy_set):
        u = np.array([
            xy_set[1, 0] - xy_set[0, 0],
            xy_set[1, 1] - xy_set[0, 1],
            1
        ])
        self.ux, self.uy, self.uz = u / np.linalg.norm(u)  # normalization

    def tilt_x(self, degrees):
        # shifting to the origin
        self.plane[0] = np.subtract(self.plane[0], self.x_c)
        self.plane[1] = np.subtract(self.plane[1], self.y_c)
        self.plane[2] = np.subtract(self.plane[2], self.z_c)

        # ROTATION AROUND Z
        angle = np.radians(degrees)
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])
        self.plane = np.tensordot(self.plane, rotation_matrix, axes=(0, 1))
        self.plane = np.moveaxis(self.plane, 2, 0)

        # shifting to the origin
        self.plane[0] = np.add(self.plane[0], self.x_c)
        self.plane[1] = np.add(self.plane[1], self.y_c)
        self.plane[2] = np.add(self.plane[2], self.z_c)

    def tilt_z(self, degrees):
        # shifting to the origin
        self.plane[0] = np.subtract(self.plane[0], self.x_c)
        self.plane[1] = np.subtract(self.plane[1], self.y_c)
        self.plane[2] = np.subtract(self.plane[2], self.z_c)

        # align with respect to XZ
        # uz is set to zero in here because the starting plane is parallel to the axis but we might be
        # using a tilt plane in the future, let's consider it
        d = np.sqrt(self.uy ** 2 + self.ux ** 2)
        if d != 0:
            axis_align_matr = np.array([
                [self.uy / d, -self.ux / d, 0],
                [self.ux / d, self.uy / d, 0],
                [0, 0, 1]
            ])
            self.plane = np.tensordot(self.plane, axis_align_matr, axes=(0, 1))
            self.plane = np.moveaxis(self.plane, 2, 0)

        angle = np.radians(degrees)
        rotation_matrix = np.array([
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],

        ])
        self.plane = np.tensordot(self.plane, rotation_matrix, axes=(0, 1))
        self.plane = np.moveaxis(self.plane, 2, 0)

        if d != 0:
            axis_align_matr = np.array([
                [self.uy / d, self.ux / d, 0],
                [-self.ux / d, self.uy / d, 0],
                [0, 0, 1]
            ])
            self.plane = np.tensordot(self.plane, axis_align_matr, axes=(0, 1))
            self.plane = np.moveaxis(self.plane, 2, 0)

        # shifting to the origin
        self.plane[0] = np.add(self.plane[0], self.x_c)
        self.plane[1] = np.add(self.plane[1], self.y_c)
        self.plane[2] = np.add(self.plane[2], self.z_c)

        # TODO: update axis vector and plane centre for the next rotation!

    def get_plane(self):
        """
        order of coordinates in the plane are [0] X, [1] Y, [2] Z
        Returns (numpy array): plane of coordinates
        """
        return self.plane

    def set_plane(self, plane):
        """
        load the data from an existing plane
        Args:
            plane numpy array: plane of coordinates
        """
        # TODO: set the centre of the plane and the axis vectors starting from a plane
        #  [important for further rotations!!]
        self.plane = plane

    def __getitem__(self, coord_set):
        return self.plane[coord_set]