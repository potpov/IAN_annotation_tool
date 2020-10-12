# IAN Annotation Tool

This tool is designed to help in the annotation of the inferior alveolar nerve (IAN) canal in cone beam TAC.
It is developed using:
- `PyQt5` (GUI)
- `mayavi` (3D visualization)
- `opencv`, `scikit` (Image processing)


## Run with Python interpreter
Create virtual environment and install requirements via pip. It's important to use pip instead of conda packages in order to package the application into an executable.
```bash
python -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### On Linux
It is required to install PyQt5 on the system.
```bash
sudo apt-get install python3-pyqt5
```

## Build executable
What follows is the configuration used to freeze the application into an executable.

|             | **Version**                     |
|-------------|---------------------------------|
| OS          | Windows 10 2004 build 19041.508 |
| Python      | `3.7.3`                         |
| `cx_Freeze` | `6.1`                           |

1. Setup virtual environment from `requirements.txt`:
    ```bash
    python -m virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2. Add DLLs to virtual environment. DLLs are available in Python installation,
so navigate to that folder, copy `DLLs` directory and paste it into `venv`.
2. Launch `build_exe.py`:
    ```bash
    python build_exe.py build
    ```
    Instead, to create an installer for Windows, run the following command:
    ```bash
    python build_exe.py bdist_msi
    ```
3. Check into `build` directory.


