class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


conf = dotdict({
    'DICOM_DIR': r'Y:\work\datasets\NNT\patient1\DICOM\annotated\DICOMDIR',
    'JSON_DIR': r'Y:\work\datasets\side_dumps\patient1\json',
    'SAVE_DIR': r'Y:\work\datasets\side_dumps\patient1\masks'
})

