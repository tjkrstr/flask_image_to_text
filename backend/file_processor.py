import os
import fitz
import pytesseract
from PIL import Image
from file_handler import FileHandler
from processfile import ProcessFile, ProcessingStatus


class FileProcessor:
    def __init__(self, app_folder: str = "app_folder"):
        self.path_dir_upload_folder = f"{app_folder}/upload"
        self.path_dir_output_folder = f"{app_folder}/output"
        
        self.file_handler = FileHandler(
            self.path_dir_upload_folder, 
            self.path_dir_output_folder
        )

        #create dir
        os.makedirs(self.path_dir_upload_folder, exist_ok=True)
        os.makedirs(self.path_dir_output_folder, exist_ok=True)


    def image_to_text_from_pixmap(self, pixmap):
        """
        Converts an image in Pixmap format to text using Tesseract OCR.

        Args:
            pixmap (fitz.Pixmap): Pixmap representation of an image.

        Returns:
            str: Extracted text from the image, or an empty string if an error occurs during the process.
        """

        try:
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            text = pytesseract.image_to_string(img, lang="eng")
            return text

        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""


    def append_text_to_file(self, file_path, text):
        """
        Writes text to a specified file.

        Args:
            file_path (str): The path to the file where text will be written.
            text (str): The text to write to the file.

        Returns:
            dict: A dictionary containing the status and a message indicating the outcome of the operation.
        """

        try:
            with open(file_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text)
                text_file.write('\n')
            return {"status": "success", "message": f"Text written to {file_path}"}
        except Exception as e:
            print(f"Error writing text to file {file_path}: {e}")


    def process_file(self, file_path):
        """
        Processes a file, extracting text from each image using Tesseract OCR.

        Args:
            file_path (str): The path to the file to be processed.

        Returns:
            dict: A dictionary containing the status and a message indicating the outcome of the processing operation.
        """
        try:
            zoom = 4
            mat = fitz.Matrix(zoom, zoom)

            # remove any file extension from the filename
            file_id, _ = os.path.splitext(os.path.basename(file_path))
            file_text_path = os.path.join(self.path_dir_output_folder, f"{file_id}.txt")
            
            # find the corresponding file in the queue and update its status to PROCESSING
            for file_obj in self.file_handler.files:
                if file_obj.name == file_id:
                    file_obj.status = ProcessingStatus.PROCESSING
                    break

            doc = fitz.open(file_path)

            for page in doc:
                pix = page.get_pixmap(matrix=mat)
                text = self.image_to_text_from_pixmap(pix)
                self.append_text_to_file(file_text_path, text)

            # find the corresponding file in the queue and update its status to COMPLETED
            for file_obj in self.file_handler.files:
                if file_obj.name == file_id:
                    file_obj.status = ProcessingStatus.COMPLETED
                    break

            return {"status": "success", "message": f"File processed successfully: {file_id}"}

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

            # find the corresponding file in the queue and update its status to ERROR
            for file_obj in self.file_handler.files:
                if file_obj.name == file_id:
                    file_obj.status = ProcessingStatus.ERROR
                    break

            return {"status": "error", "message": f"Error processing {file_path}: {e}"}


    def list_files_in_queue(self):
        """
        Lists all files in the file handler.

        Returns:
            list: A list of dictionaries containing the file name and status.
        """
        return [{
            #'id': file.name + f'.txt',
            'id': file.name,
            'status': file.status.name
        } for file in self.file_handler.files]
