import pydicom
from pydicom.filereader import read_dicomdir
import re
import os
import numpy as np


def load_dicom(dataset_path):
    """
    load DICOM files from path
    :param dataset_path: path where DICOM files are stored, can be: a DICOMDIR, a file .dcm or directory with many DICOM
    :return: pyobject containing all the metadata, numpy array containing the image or the images
    """
    basename = os.path.basename(dataset_path)
    # load bunch of dicom from DICOMDIR
    if basename.lower() == 'dicomdir':
        dirname = os.path.dirname(os.path.abspath(dataset_path))
        return load_from_dicomdir(dirname)
    # load a single DICOM file
    elif os.path.splitext(basename)[1] == '.dcm':
        single = pydicom.dcmread(dataset_path)
        return single, single.pixel_array
    # load bunch of dicom from a directory
    else:
        raise Exception('TODO: cant load dicom from a directory yet')


def load_from_dicomdir(dataset_path):
    """
    load DICOM dataset from path
    :param dataset_path: path where files are loaded, basename should be DICOMDIR
    :return: pyobject containing all the metadata, numpy array containing the image or the images
    """
    dicom_dir = read_dicomdir(os.path.join(dataset_path, 'DICOMDIR'))
    for patient_record in dicom_dir.patient_records:
        studies = patient_record.children
        for study in studies:
            all_series = study.children
            for series in all_series:
                image_records = series.children
                # load data only from the series *301???.dcm or *3001???.dcm
                if bool(re.match("\w*30{1,2}1[0-9]{2,}\.dcm", image_records[0].ReferencedFileID)):
                    image_filenames = [
                        os.path.join(dataset_path, image_rec.ReferencedFileID) for image_rec in image_records
                    ]
                    datasets = [pydicom.dcmread(image_filename) for image_filename in image_filenames]
                    # raw data stacked together
                    volume = np.stack([images.pixel_array for images in datasets])
                    return datasets, volume
            raise Exception('No valid series found, abort!')
    raise Exception('no valid patient or study found in the path, abort!')
