import sqlite3
import os
from utils import *


class DatabaseManager:
    def __init__(self, database_config):
        self.database_config = database_config


    def db_connection(self):
        return sqlite3.connect(self.database_config)


    def create_database(self):
        try:
            with self.db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS uploaded_files (
                        filename TEXT UNIQUE,
                        blake3_checksum TEXT UNIQUE,
                        file_size_mb DOUBLE
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_files (
                        filename TEXT UNIQUE,
                        blake3_checksum TEXT UNIQUE,
                        file_size_mb DOUBLE
                    )
                ''')
            conn.commit()

            print("Database created successfully.")
        except Exception as e:
            print(f"Error creating database: {str(e)}")


    def fill_database(self, folder_path, table_name):
        try:
            with self.db_connection() as conn:
                cursor = conn.cursor()

                # get the list of files in the folder
                folder_files = set(os.listdir(folder_path))

                for file_name in folder_files:
                    file_path = os.path.join(folder_path, file_name)
                    # calculate the checksum of the file
                    checksum = get_checksum(file_path)
                    file_size = get_file_size(file_path)
                    # insert the file information into the database
                    cursor.execute(f'INSERT OR IGNORE INTO {table_name} (filename, blake3_checksum, file_size_mb) VALUES (?, ?, ?)', (file_name, checksum, file_size))

                conn.commit()
                print(f"Database {table_name} filled successfully.")

        except Exception as e:
            print(f"Error filling database: {str(e)}")


    def update_database_from_folder(self, folder_path, table_name="uploaded_files"):
        """
        Update a specified database table to synchronize it with the contents of a given folder.

        Args:
            folder_path (str): The path to the folder whose contents should be reflected in the database.
            table_name (str, optional): The name of the database table to be updated (default is "uploaded_files").

        Returns:
            None: The function modifies the specified database table in place.
        """
        files_folder = set(os.listdir(folder_path))
        with self.db_connection() as conn:
            cursor = conn.cursor()
            
            # get the list of files in the database
            cursor.execute(f'SELECT filename FROM {table_name}')
            db_files = set(row[0] for row in cursor.fetchall())

            # identify file names present in the database but not in folder
            files_to_remove_from_db = db_files - files_folder
           
            # remove the identified files from the database
            for filename in files_to_remove_from_db:
                cursor.execute(f'DELETE FROM {table_name} WHERE filename = ?', (filename,))
            
            # identify file names present in the folder but not in the database
            files_to_add_to_db = files_folder - db_files
            
            # add the identified files to the database
            for filename in files_to_add_to_db:
                file_path = os.path.join(folder_path, filename)
                checksum = get_checksum(file_path)
                file_size = get_file_size(file_path)
                cursor.execute(f'INSERT INTO {table_name} (filename, blake3_checksum, file_size_mb) VALUES (?, ?, ?)', (filename, checksum, file_size))

            if len(files_to_remove_from_db) <= 0 and len(files_to_add_to_db) <= 0:
                print("No database updates.")
            else:
                print(f"Database update, removed names: {files_to_remove_from_db}, added names: {files_to_add_to_db}")

        conn.commit()


    def add_processed_file(self, filename, checksum, table_name="uploaded_files"):
        with self.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'INSERT OR REPLACE INTO {table_name} (filename, blake3_checksum) VALUES (?, ?)', (filename, checksum))
        
        conn.commit()


    def get_matching_files_in_db(self, table_name, file_stem):
        with self.db_connection() as conn:
            cursor = conn.cursor()

            # get the list of files in the specified database table
            cursor.execute(f'SELECT filename FROM {table_name}')

            # extract the stems from the filenames in the database table
            db_files = set(os.path.splitext(row[0])[0] for row in cursor.fetchall())

            # find files that have a matching stem with the provided file_stem
            matching_files = [filename for filename in db_files if file_stem in filename]

        return matching_files


    def get_files_from_db(self, table_name, filename=None, checksum=None):
        with self.db_connection() as conn:
            cursor = conn.cursor()

            if checksum and filename is not None:
                # compare filename and checksum
                cursor.execute(f'SELECT filename, blake3_checksum FROM {table_name} WHERE filename = ? AND blake3_checksum = ?', (filename, checksum))
            elif checksum is not None:
                # compare checksum
                cursor.execute(f'SELECT blake3_checksum FROM {table_name} WHERE blake3_checksum = ?', (checksum,))
            elif filename is not None:
                # compare filename
                cursor.execute(f'SELECT filename FROM {table_name} WHERE filename = ?', (filename,))
            else:
                # list all file names and checksums in the filename column
                cursor.execute(f'SELECT filename, blake3_checksum, file_size_mb FROM {table_name}')

            result = cursor.fetchall()
            return result
