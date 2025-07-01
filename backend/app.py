from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from FastCropper.image_processing import process_image
import os

app = Flask(__name__)
CORS(app)  # Pozwala reactowi łączyć się lokalnie

#TODO lepiej foldery ułożyc i usuwanie danych po przetworzeniu
#TODO przerób FastCropper pod tą apke


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ERROR_FOLDER = 'errors'
os.makedirs(ERROR_FOLDER, exist_ok=True)
OUTPUT_FOLDER = 'output'
os.makedirs(OUTPUT_FOLDER, exist_ok=True) 

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Siema z backendu przytnij Fote!"})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"Saved original file to: {filepath}")

    # Process the image using FastCropper
    try:
        process_image(image_path=filepath,
                         error_folder=ERROR_FOLDER,
                         output_folder=OUTPUT_FOLDER,
                         debug_output=ERROR_FOLDER,
                         res_x=400,
                         res_y=500,
                         top_margin_value=0.4,
                         bottom_margin_value=0.5,
                         left_right_margin_value=0,
                         naming_config={
                             "prefix": "",
                             "name": "",
                             "numbering_type": "",
                             "extension": "Bez zmian"
                         },
                         image_count=1
                         )
    except Exception as e:
        return jsonify({"error": f"Image processing failed: {str(e)}"}), 500

    return jsonify({
        "message": f"File '{filename}' uploaded and processed successfully",
        "cropped_file_url": f"/api/output/{filename}"
    })

@app.route("/api/output/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# Keep the old route for backward compatibility
@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)