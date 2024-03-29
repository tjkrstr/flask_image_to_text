import os
import zipfile
import io
from database import DatabaseManager 
from blake3 import blake3
from utils import *
from file_processor import FileProcessor, ProcessingStatus
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)

#enabled CORS on entire app. May change to specific routes or origins.
CORS(app)

db_manager = DatabaseManager("./files_database.db")
file_processor = FileProcessor()

app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 #max allowed size of a single file

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']


@app.route('/', methods=['GET'])
def index():
    uploaded_files = file_processor.file_handler.list_files_in_dir(file_processor.path_dir_upload_folder, "name")
    processed_files = file_processor.file_handler.list_files_in_dir(file_processor.path_dir_output_folder, "stem")

    print("Updating database...", flush=True)
    print("uploaded_files table data", flush=True)    
    db_manager.update_database_from_folder(file_processor.path_dir_upload_folder)
    
    print("processed_files table data", flush=True)    
    db_manager.update_database_from_folder(file_processor.path_dir_output_folder, "processed_files")

    # if no files in folders clear file queue
    if len(uploaded_files) == 0 and len(processed_files) == 0:
        file_processor.file_handler.files = []

    for file_obj in file_processor.file_handler.files:
        # if file is removed from folder
        if file_obj.name not in processed_files and file_obj.status == ProcessingStatus.COMPLETED:
            file_obj.status = ProcessingStatus.PENDING
        # if file is added to folder
        elif file_obj.name in processed_files and file_obj.status == ProcessingStatus.PENDING:
            file_obj.status = ProcessingStatus.COMPLETED
        # ensure the file goes through the different status during processing
        else:
            file_obj.status = file_obj.status

    return render_template('index.html', uploaded_files=uploaded_files, processed_files=file_processor.list_files_in_queue())


@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    uploaded_files = request.files.getlist('files')

    for uploaded_file in uploaded_files:
        if uploaded_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(uploaded_file.filename, ALLOWED_EXTENSIONS, uploaded_file):
            return jsonify({'error': 'Invalid file type. Please upload file with allowed extension.'}), 400

        original_filename = secure_filename(uploaded_file.filename)

        # compare database file data with uploaded file data (name and checksum)
        file_checksum = calculate_file_checksum(uploaded_file)
        existing_files_db = db_manager.get_files_from_db("uploaded_files")

        excluded_files = []

        for existing_file, existing_file_checksum_db, _ in existing_files_db:
            if existing_file_checksum_db == file_checksum:
                excluded_files.append(uploaded_file.filename)
            elif existing_file == original_filename:
                original_filename = append_timestamp_to_filename(original_filename)

        if excluded_files:
            return jsonify({'error': f'File(s) with equal content {", ".join(excluded_files)} already exists'}), 400

        # add file to process queue
        file_processor.file_handler.add_file_to_process_queue(original_filename)

        uploaded_file.save(os.path.join(file_processor.path_dir_upload_folder, original_filename))

    db_manager.fill_database(file_processor.path_dir_upload_folder, "uploaded_files")

    remove_invalid_files(file_processor.path_dir_upload_folder, ALLOWED_EXTENSIONS)   
    
    return redirect(url_for('index'))


@app.route('/process', methods=['POST'])
def process():
    uploaded_files = file_processor.file_handler.list_files_in_dir(file_processor.path_dir_upload_folder, "name")

    # check if the upload folder is empty
    if not uploaded_files:
        return jsonify({"message": "Upload folder is empty. No files to process."})

    processed_uploaded_files = []

    for file_name in uploaded_files:
        file_path = os.path.join(file_processor.path_dir_upload_folder, file_name)

        # check only based on file name
        if allowed_file(file_name, ALLOWED_EXTENSIONS):
            try:
                # get the stem of the current file_name
                file_stem = os.path.splitext(file_name)[0]

                # check if there are matching stems in the processed_files table
                matching_files = db_manager.get_matching_files_in_db("processed_files", file_stem)

                if not matching_files:
                    result = file_processor.process_file(file_path)

                    if result['status'] == 'success':
                        processed_uploaded_files.append(file_name)
            except Exception as e:
                print(f"Error processing file {file_name}: {str(e)}")

    # update the database after processing all files
    db_manager.fill_database(file_processor.path_dir_output_folder, "processed_files")

    response_message = f"Processing completed. Processed files: {processed_uploaded_files}"
    return jsonify({"message": response_message})

# NOTE: the {zip_checksum}.zip varies from each download dispite no changes to the files (mainly due to changes in timestamps).
@app.route('/download_output', methods=['GET'])
def download_output():
    checksum_file = "checksums.txt"

    try:
        # check if the output folder is empty
        processed_files = file_processor.file_handler.list_files_in_dir(file_processor.path_dir_output_folder, "name")

        if not processed_files:
            return jsonify({'error': 'Output folder is empty'}), 404

        # get the list of processed files from the database
        db_processed_files = db_manager.get_files_from_db("processed_files")

        zip_buffer = io.BytesIO()

        # create checksums.txt before entering the zip block
        checksums_filepath = os.path.join(file_processor.path_dir_output_folder, checksum_file)
        with open(checksums_filepath, 'w') as checksums_file:
            # iterate through the files in the database and write to checksums.txt
            for file_info in db_processed_files:
                checksums_file.write(f"{file_info[0]}, {file_info[1]}, {file_info[2]}\n")

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(file_processor.path_dir_output_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, file_processor.path_dir_output_folder))

        # blake3 checksum of zip file
        zip_buffer.seek(0)
        zip_checksum = blake3(zip_buffer.read()).hexdigest()
        zip_buffer.seek(0)

        # set the response headers to force download
        response = send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'{zip_checksum}.zip'
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # remove the checksums.txt file after zipping
        os.remove(checksums_filepath)

        return response
    except Exception as e:
        return f"An error occurred while preparing the zip file: {str(e)}", 500

if __name__ == '__main__':
    db_manager.create_database()
    print("==========================", flush=True)
    print("Server ready for action!", flush=True)
    app.run(debug=True, port=5000)
