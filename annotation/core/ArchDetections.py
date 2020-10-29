import processing


class ArchDetections():
    def __init__(self, arch_handler):
        """
        Class that stores arch detections and computes them only if not already computed.

        Args:
            arch_handler (ArchHandler): ArchHandler parent object
        """
        self.arch_handler = arch_handler
        self.data = [(None, None, None)] * self.arch_handler.Z

    def compute(self, i):
        """
        Computes arch detection for onle slice of the volume

        Args:
            i (int): slice
        """
        try:
            self.data[i] = processing.arch_detection(self.arch_handler.volume[i])
        except:
            self.data[i] = None, None, None

    def get(self, i):
        """
        Returns the arch detection for a slice.

        If it's not available, computes it.

        Args:
            i (int): slice
        """
        if self.data[i][0] is None:
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
