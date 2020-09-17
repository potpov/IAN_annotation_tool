# source: https://en.wikipedia.org/wiki/Centripetal_Catmull%E2%80%93Rom_spline#Code_example_in_Python
import numpy as np

UNIFORM = 0.0
CENTRIPETAL = 0.5
CHORDAL = 1.0


def CatmullRomSpline(P0, P1, P2, P3, kind=CENTRIPETAL):
    """
    Compute the part of the Catmull-Rom spline between points P1 and P2.

    Args:
        P0 ((float, float)): Point 0 coordinates
        P1 ((float, float)): Point 1 coordinates
        P2 ((float, float)): Point 2 coordinates
        P3 ((float, float)): Point 3 coordinates

    Returns:
        (list of (float, float)): List of points of the spline between P1 and P2
    """
    # Convert the points to numpy so that we can do array multiplication
    P0, P1, P2, P3 = map(np.array, [P0, P1, P2, P3])

    # Parametric constant: 0.5 for the centripetal spline, 0.0 for the uniform spline, 1.0 for the chordal spline.
    alpha = kind
    # Premultiplied power constant for the following tj() function.
    alpha = alpha / 2

    def tj(ti, Pi, Pj):
        xi, yi = Pi
        xj, yj = Pj
        return ((xj - xi) ** 2 + (yj - yi) ** 2) ** alpha + ti

    # Calculate t0 to t3
    t0 = 0
    t1 = tj(t0, P0, P1)
    t2 = tj(t1, P1, P2)
    t3 = tj(t2, P2, P3)

    # Only calculate points between P1 and P2
    nPoints = np.linalg.norm(P2 - P1)  # as many points as the euclidean distance
    # nPoints = abs(P2[0] - P1[0]) # one point for each x coordinate (too many points where the arch is steep)
    t = np.linspace(t1, t2, int(nPoints))

    # Reshape so that we can multiply by the points P0 to P3
    # and get a point for each value of t.
    t = t.reshape(len(t), 1)
    A1 = (t1 - t) / (t1 - t0) * P0 + (t - t0) / (t1 - t0) * P1
    A2 = (t2 - t) / (t2 - t1) * P1 + (t - t1) / (t2 - t1) * P2
    A3 = (t3 - t) / (t3 - t2) * P2 + (t - t2) / (t3 - t2) * P3
    B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
    B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
    C = (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2
    return C


def CatmullRomChain(P, kind=CENTRIPETAL):
    """
    Compute Catmull–Rom for a chain of points and return the combined curve.

    Args:
        P (list of (float, float)): list of control points

    Returns:
        (list of list of (float, float)): list of curves that compose the spline, where each curve is a list of points [(x,y), ...]
    """
    sz = len(P)

    C = []
    for i in range(sz - 3):
        c = CatmullRomSpline(P[i], P[i + 1], P[i + 2], P[i + 3], kind)
        C.append(c)

    return C
