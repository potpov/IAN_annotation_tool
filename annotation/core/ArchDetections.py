import processing


class ArchDetections():
    def __init__(self, arch_handler):
        """
        Class that stores arch detections and computes them only if not already computed.

        Args:
            arch_handler (ArchHandler): ArchHandler parent object
        """
        self.ah = arch_handler
        self.data = [None] * self.ah.Z

    def compute(self, i):
        """
        Computes arch detection for onle slice of the volume

        Args:
            i (int): slice
        """
        try:
            self.data[i] = processing.arch_detection(self.ah.volume[i])
        except:
            self.data[i] = None

    def get(self, i):
        """
        Returns the arch detection for a slice.

        If it's not available, computes it.

        Args:
            i (int): slice
        """
        if self.data[i] is None:
            self.compute(i)
        return self.data[i]

    def set(self, i, p_start_end):
        """
        Sets an arch detection for a slice.

        Args:
            i (int): slice
            p_start_end ((numpy.poly1d, float, float)): arch detection
        """
        self.data[i] = p_start_end
