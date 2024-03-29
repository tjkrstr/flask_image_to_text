import os
from datetime import datetime
from blake3 import blake3
import magic
import logging

log_format = "%(asctime)s [%(levelname)s] - %(message)s"
logging.basicConfig(filename='upload_file_log.txt', level=logging.INFO, format=log_format)


def allowed_file(filename, extension, file=None):
    """
    Validates whether a file is allowed based on its filename and, optionally, its content.

    Args:
        filename (str): The name of the file, including extension.
        extension (list): A list of allowed file extensions (['jpg', 'jpeg', 'png']).
        file (FileStorage, optional): A file object (e.g., Flask's FileStorage) to perform additional content checks (MIME).

    Returns:
        bool: True if the file is allowed, False otherwise. The decision is based on the following criteria:
        - The file name should have a valid structure (contains at most one '.' symbol).
        - The file extension (if any) should be in the provided list of allowed extensions.
        - If a file object is provided, additional checks include verifying the magic number and MIME type.
    """

    char_file_name = list(filename)

    #handles if no extension is in filename 
    file_extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if '.' not in char_file_name or char_file_name.count('.') > 1:
        return False

    if file_extension not in extension:
        return False

    if file is not None:
        # check magic number to verify file type
        if not is_valid_magic_number(file.stream, file_extension):
            return False

        # check MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file.stream.read(1024))
        file.stream.seek(0)  # reset file pointer to the beginning

        return mime_type in ['image/jpeg', 'image/png']
    

    # if file is not provided, only check the file extension
    return True


def is_valid_magic_number(file_stream, extension):
    
    # define known magic numbers or signatures for allowed file types
    magic_numbers = {
        'png': b'\x89PNG\r\n\x1a\n',
        'jpeg': b'\xff\xd8\xff',
        'jpg': b'\xff\xd8\xff',
    }

    # check magic numbers by maching expected and existing file extensions
    expected_magic_number = magic_numbers.get(extension, None)
    if expected_magic_number is not None:
        actual_magic_number = file_stream.read(len(expected_magic_number))
        file_stream.seek(0)  # reset file pointer to the beginning
        return actual_magic_number == expected_magic_number

    return True


def append_timestamp_to_filename(filename):
    """Append a timestamp to the filename."""
    timestamp = datetime.now().strftime("%Y%m%d")
    base, extension = os.path.splitext(filename)
    return f"{timestamp}_{base}{extension}"


def get_checksum(file_path):
    with open(file_path, 'rb') as file:
        return blake3(file.read()).hexdigest()


def calculate_file_checksum(file):
    """Calculate the checksum of a file using blake3."""
    hash_blake3 = blake3()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_blake3.update(chunk)
    file.seek(0)  # reset file pointer
    return hash_blake3.hexdigest()


def remove_invalid_files(upload_folder, extension):
    uploaded_files = os.listdir(upload_folder)
    for file in uploaded_files:
        file_path = os.path.join(upload_folder, file)
        if os.path.isfile(file_path) and not allowed_file(file_path, extension):
            logging.warning(f"Suspicious file detected and removed: {file_path}")
            os.remove(file_path)

# # dynamic specification of size output
# def convert_bytes(num):
#     """
#     this function will convert bytes to MB.... GB... etc
#     """
#     for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
#         if num < 1024.0:
#             return "%3.1f %s" % (num, x)
#         num /= 1024.0

# select specific file size format as output
def bytesto(bytes, to, bsize=1024): 
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    # r = float(bytes)
    #return int(bytes / (bsize ** a[to]))
    return bytes / (bsize ** a[to])


def get_file_size(file_path):
    """
    This function returns the file size.
    """
    base_dir = os.path.dirname(__file__)  # get the directory of the current script
    abs_file_path = os.path.join(base_dir, file_path)
    if os.path.isfile(abs_file_path):
        file_info = os.stat(abs_file_path)
        return bytesto(file_info.st_size, "m")
    else:
        raise FileNotFoundError(f"File not found: {abs_file_path}")