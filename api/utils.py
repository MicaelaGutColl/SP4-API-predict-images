import os
import hashlib

def allowed_file(filename):
    """
    Checks if the format for the file received is acceptable. For this
    particular case, we must accept only image files.

    Parameters
    ----------
    filename : str
        Filename from werkzeug.datastructures.FileStorage file.

    Returns
    -------
    bool
        True if the file is an image, False otherwise.
    """
    try:
        images_ext = {'.gif', '.jpeg', '.jpg', '.png'} # es un set
        _, img_check = os.path.splitext(filename) # el _ es para descartar una variable de splittext, porque split test te devuelve el nombre
        img_check = img_check.lower()

    except IOError:
        print("===========Error fetching file format")
    valid_file=img_check in images_ext
    return valid_file



def get_file_hash(file):
    """
    Returns a new filename based on the file content using MD5 hashing.
    It uses hashlib.md5() function from Python standard library to get
    the hash.
    Parameters
    ----------
    file : werkzeug.datastructures.FileStorage
        File sent by user.
    Returns
    -------
    str
        New filename based in md5 file hash.
    """
    # Current implementation will return the original file name.
    split_file = os.path.splitext(file.filename)
    data = file.read()
    md5hash = hashlib.md5(data).hexdigest()
    file.seek(0)

    return str(md5hash) + str(split_file[1])