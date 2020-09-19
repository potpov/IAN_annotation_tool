# IAN Annotation Tool

## Python environment
Create virtual environment and install requirements via pip. It's important to use pip instead of conda packages in order to package the application into an executable.
```bash
python -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Build executable
### Versions
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
2. Launch `buildExe.py`:
    ```bash
   python buildExe.py build
   ```
3. Check into `build` directory.

