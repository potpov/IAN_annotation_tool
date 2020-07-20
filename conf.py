class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


conf = dotdict({
    # 'DICOM_DIR': r'Y:\work\datasets\maxillo\NNT\patient1\DICOM\annotated\DICOMDIR',
    'DICOM_DIR': r'Y:\work\datasets\maxillo\anonimi\PAZIENTE_7\DICOMDIR',
    'JSON_DIR': r'Y:\work\datasets\canal_segmentation\patient1\labelme\json',
    'SAVE_DIR': r'Y:\work\datasets\canal_segmentation\patient1\labelme\masks'
})

