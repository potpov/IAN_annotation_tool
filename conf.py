class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


conf = dotdict({
    'DICOM_DIR': r'Y:\work\datasets\NNT\SPERANZONI_ALBERTO_1993_04_23_NNTViewer&DICOM\DICOM\annotated\DICOMDIR',
    # 'DICOM_DIR': r'Y:\work\datasets\NNT\SPERANZONI_ALBERTO_1993_04_23_NNTViewer&DICOM\DICOM\annotated\55aci73ejbi703011071.dcm',
})

