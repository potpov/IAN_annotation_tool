from annotation.utils.math import get_poly_approx, apply_offset_to_arch


class Arch():
    def __init__(self, arch_handler, arch):
        """
        Arch not handled as a Spline, but as a list of points.

        We can automatically extract its panorex in every moment.

        Args:
            arch_handler (ArchHandler): ArchHandler parent object
            arch (list of (float, float)): list of coordinates
        """
        self.ah = arch_handler
        self.set_arch(arch)
        self.set_panorex(self.compute_panorex())

    def compute_panorex(self):
        """
        Computes a panorex using internal attribute arch.

        Returns:
            (numpy.ndarray): computed panorex
        """
        return self.ah.create_panorex(self.arch)

    def compute_poly(self):
        """
        Computes the polinomial approximation of the internal attribute arch.

        It returns also the minimum and the maximum value for the x axis in arch.

        Returns:
            ((numpy.poly1d, float, float)): polinomial approximation
        """
        return get_poly_approx(self.arch)

    def update(self, arch=None):
        """
        Updates the arch with a new set of points, then recomputes panorex.

        Args:
            arch (list of (float, float)): new list of coordinates
        """
        if arch is not None:
            self.set_arch(arch)
        self.set_panorex(self.compute_panorex())

    def get_offsetted(self, amount):
        """
        Returns a new Arch object that is offsetted from the original one.

        Args:
            amount (int): how much to displace the new Arch from the original

        Returns:
            (Arch): new offsetted arch
        """
        copy = self.copy()
        copy.offset(amount)
        return copy

    def offset(self, amount):
        """
        Applies offset to this Arch object

        Args:
            amount (int): how much to displace the Arch from its current position
        """
        offsetted_arch = apply_offset_to_arch(self.arch, amount, self.poly[0])
        self.update(offsetted_arch)

    def copy(self):
        """
        Creates a copy of this Arch object

        Returns:
            (Arch): copy of this Arch
        """
        arch = self.arch.copy()
        return Arch(self.ah, arch)

    ###########
    # GETTERS #
    ###########
    def get_arch(self):
        """Returns arch"""
        return self.arch

    def get_panorex(self):
        """Returns panorex"""
        return self.panorex

    def get_poly(self):
        """Returns polynomial approximation"""
        return self.poly

    ###########
    # SETTERS #
    ###########

    def set_arch(self, arch):
        """Sets new arch"""
        self.arch = arch
        self.poly = self.compute_poly()

    def set_panorex(self, panorex):
        """Sets new panorex"""
        self.panorex = panorex
