# Flask - image to text server

The following project consists of an image to text server created using python. The project itself consists of a Flask server and a simple web interface for users to upload image files. Once uploaded, the images can be processed using Optical Character Recognition (OCR) techniques to extract the text content. The text is then appended to a related text file which can be downloaded as a zip file.

The main focus of the project was to create a simple file uploading app, however this became a bit more extensive than initially anticipared (and this is without a proper GUI).


## Getting started

### Prerequisites
- Flask (2.2.5 or higher)
- Python (3.10 or higher)
- Docker (24.x or higher)
- Docker compose (v2.21.x or higher)
- Windows, macOS, or Linux operating system

### Installation and Setup
The project can be setup on the device itself. Just clone the project:

```console
$ git clone https://github.com/tjkrstr/file_uploader.git
```

and run the app.py file using python:

```console
$ python3 /backend/app.py
```

A `Docker` file and a `docker-compose.yml` file has been created which makes it possible to run the project in a containerized setting. Either use the run script I have created or use docker compose:

```console
$ bash run
$ docker compose up -d
```

### Tesseract setup and install notes:

Tesseract is the tool used to convert pictures to text. It supports a large number of different languages ([Tesseract available languages](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html)). Linux tesseract installation process:

```console
$ sudo apt update
$ sudo apt-get install libleptonica-dev tesseract-ocr tesseract-ocr-dev libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-dan
```

Pip install tesseract:

```console
$ pip install tesseract-ocr
$ pip install pytesseract
```

If you install it this way you do not need to run/use the `pytesseract pytesseract.tesseract_cmd` in your python script. You need this if the script is running on a windows machine: `pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'`

## Improvements and future work
The code itself could be much more efficient. Furthermore there exists logic that is not utilized but may be in the future. Tessearct is also not perfect, for instance when transforming the test file "jpegtest.jpg", it only contains "a"s however when translated to text they are detected as "d"s.

Improvements:
- The status codes are a bit janky and could have been better utilized in regards to other parts of the logic.
- More extensive testing...
- And probably many more...

Future work:
- Add the possibility of processing pdf files.
- Add logic that makes it possible to select the langauge model tesseract should utilize via the GUI.
- A graphical user interface (GUI). This was however not the main goal for this project as it mainly serves as a backend foundation for uploading files.
