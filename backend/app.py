from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from FastCropper.image_processing import process_image
from utils import clear_client_data
import os
import uuid
import glob

app = Flask(__name__)
CORS(app)  # Pozwala reactowi łączyć się lokalnie

#TODO przerób FastCropper pod tą apke


#Folders with uploaded and processed images
DATA_FOLDER = 'Data'
UPLOAD_FOLDER = os.path.join(DATA_FOLDER, 'uploads')
OUTPUT_FOLDER = os.path.join(DATA_FOLDER, 'output')
ERROR_FOLDER = os.path.join(DATA_FOLDER, 'errors')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Siema z backendu przytnij Fote!"})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    #Get session ID from form or generate a new one
    session_id = request.form.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    user_upload_folder = os.path.join(UPLOAD_FOLDER, session_id)
    user_output_folder = os.path.join(OUTPUT_FOLDER, session_id)
    user_error_folder = os.path.join(ERROR_FOLDER, session_id)
    os.makedirs(user_upload_folder, exist_ok=True)
    os.makedirs(user_output_folder, exist_ok=True)
    os.makedirs(user_error_folder, exist_ok=True)


    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename
    filepath = os.path.join(user_upload_folder, filename)
    file.save(filepath)
    print(f"Saved original file to: {filepath}")

    # Process the image using FastCropper
    try:
        process_image(image_path=filepath,
                         error_folder=user_error_folder,
                         output_folder=user_output_folder,
                         debug_output=user_error_folder,
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
        list_of_files = glob.glob(os.path.join(user_output_folder, '*'))
        if not list_of_files:
            return jsonify({"error": "No processed images found"}), 500
        latest_file = max(list_of_files, key=os.path.getctime)
        output_filename = os.path.basename(latest_file)
    except Exception as e:
        return jsonify({"error": f"Image processing failed: {str(e)}"}), 500

    return jsonify({
        "message": f"File '{filename}' uploaded and processed successfully",
        "cropped_file_url": f"/api/output/{session_id}/{output_filename}",
        "session_id": session_id
    })

@app.route("/api/output/<path:filename>")
def serve_output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# Keep the old route for backward compatibility
@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


@app.route("/api/clear", methods=["POST"])
def clear_data():
    session_id = None
    if request.is_json:
        session_id = request.json.get("session_id")
    else:
        import json
        try:
            data = json.loads(request.data)
            session_id = data.get("session_id")
        except Exception:
            pass
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    user_upload_folder = os.path.join(UPLOAD_FOLDER, session_id)
    user_output_folder = os.path.join(OUTPUT_FOLDER, session_id)
    user_error_folder = os.path.join(ERROR_FOLDER, session_id)
    clear_client_data(user_upload_folder, user_output_folder, user_error_folder)
    return jsonify({"message": "Data cleared"})

if __name__ == "__main__":
    app.run(debug=True)