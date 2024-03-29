from pathlib import Path
from collections import deque
from processfile import ProcessFile, ProcessingStatus

class FileHandler:
    """File handler class"""

    def __init__(self, path_dir_upload_folder, path_dir_output_folder):
        self.path_dir_upload_folder = path_dir_upload_folder
        self.path_dir_output_folder = path_dir_output_folder

        self.files: list[ProcessFile] = []
        self.processing_queue = deque()

        self.populate_files()


    def list_files_in_dir(self, folder, formatting=None):
        """
        Gets the name of a file.

        Args:
            folder (str): The path to a folder.
            formatting (str): The type of formatting utilized by pathlib (methods and properties like name, stem, suffix).
                If None, the default formatting (full path) is used.

        Returns:
            list[str]: The name of a file(s) in the specified folder.
        """

        files_path = Path(folder)

        if formatting is not None:
            files = [f'{getattr(f, formatting)}' for f in files_path.glob('*') if f.is_file()]
        else:
            files = [f'{f}' for f in files_path.glob('*') if f.is_file()]

        return files


    def populate_files(self):
        """Populate the file list."""

        file_name_uploaded = self.list_files_in_dir(self.path_dir_upload_folder, "stem")
        print(f"Found {len(file_name_uploaded)} files in {self.path_dir_upload_folder}.", flush=True)

        file_name_processed = self.list_files_in_dir(self.path_dir_output_folder, "stem")
        print(f"Found {len(file_name_processed)} files in {self.path_dir_output_folder}.", flush=True)

        # if file name in queue but not in upload nor output folder, remove file from queue
        self.files = [file for file in self.files if file.name in file_name_uploaded or file.name in file_name_processed]
            
        for file_name in file_name_uploaded:
            # check if the file name (excluding extension) is in the output folder
            if file_name in [p for p in file_name_processed]:
                p_file = ProcessFile(file_name, ProcessingStatus.COMPLETED)
            else:
                p_file = ProcessFile(file_name, ProcessingStatus.PENDING)

            print(f"File {p_file.name} marked as {p_file.status.name}.", flush=True)

            self.files.append(p_file)
        

    def add_file_to_process_queue(self, file_name: str):
        """Adds a file to the processing queue given its ID/name."""

        stem_file_name = Path(file_name).stem
        file = ProcessFile(stem_file_name, ProcessingStatus.PENDING)
        self.files.append(file)
        self.processing_queue.append(file)
        print(f"File {file_name} added to the process queue.", flush=True)