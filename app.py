from flask import Flask, request, jsonify 
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os
import mutagen
from flask_cors import CORS

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'mp3', 'wav'} 

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['gaan']
collection = db['music']

# Helper function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API endpoint for uploading music files
@app.route('/')
def hello_world():
    return 'hello World'
 
@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only MP3 and WAV files are allowed.'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    metadata = extract_metadata(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    collection.insert_one(metadata)
    return jsonify(metadata)

# Helper function to extract metadata from a music file
def extract_metadata(filepath):
    try:
        audio = mutagen.File(filepath)
        title = audio.get('title', 'NA')
        file_type = audio.mime[6:] if audio.mime.startswith('audio/') else 'NA'
        genre = audio.get('genre', 'NA')
        length = str(audio.info.length) if audio.info.length else 'NA'
        size = str(os.path.getsize(filepath)) if os.path.exists(filepath) else 'NA'
    except Exception as e:
        print(f'Error extracting metadata: {e}')
        title, file_type, genre, length, size = 'NA', 'NA', 'NA', 'NA', 'NA'
    metadata = {'title': title, 
                'file_type': file_type, 
                'genre': genre, 
                'length': length, 
                'size': size}
    return metadata

if __name__ == '__main__':
    app.run(debug=True)
