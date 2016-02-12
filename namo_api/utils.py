__author__ = 'ujjwal'
import os
import glob
import gzip
from namo_app.config import Config, get_env


def get_ingest_files(files_dir, wildcard="*"):
    data_dir = Config(env=get_env()).datadir
    pattern = os.path.join(data_dir, files_dir, wildcard)
    return glob.glob(pattern)


def check_zip(filename):
    ext_parts = os.path.splitext(filename)
    ext = ext_parts[1]
    if ext == ".gz":
        _file_copy = ext_parts[0]
        with open(_file_copy, 'wb') as nc_file:
            gz_file = gzip.open(filename, 'rb')
            gz_bytes = gz_file.read()

            nc_file.write(gz_bytes)
            gz_file.close()

        return _file_copy

    else:
        return filename