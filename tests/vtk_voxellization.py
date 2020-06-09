import vtk
from vtk.util import numpy_support
import numpy as np

"""
EXPERIMENT WITH VTK LIBRARY
"""
def vtk_voxellization():
    cube = vtk.vtkCubeSource()
    source = np.array([[1, 2, 3], [1, 2, 3]])
    cube = numpy_support.numpy_to_vtk(source)

    cube_mapper = vtk.vtkPolyDataMapper()
    cube_mapper.SetInputConnection(cube.GetOutputPort())

    cube_actor = vtk.vtkActor()
    cube_actor.SetMapper(cube_mapper)
    cube_actor.GetProperty().SetColor(1.0, 0.0, 0.0)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)
    renderer.AddActor(cube_actor)

    render_window = vtk.vtkRenderWindow()
    render_window.SetWindowName("Simple VTK scene")
    render_window.SetSize(400, 400)
    render_window.AddRenderer(renderer)

    # Create an interactor
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    # Initialize the interactor and start the
    # rendering loop
    interactor.Initialize()
    render_window.Render()
    interactor.Start()

    pass