from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import mysql.connector
import os, zipfile
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- Helper function to create a fresh connection per request ---
def get_db():
    return mysql.connector.connect(
        host = os.environ.get("RDS_HOST"),
        user=os.environ.get("RDS_USER"),
        password=os.environ.get("RDS_PASSWORD"),
        database=os.environ.get("RDS_DB"),
        autocommit=True
    )

# --- Create table if not exists ---
# This runs once at startup using a temporary connection
db_init = get_db()
cursor = db_init.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS can_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255),
    content LONGTEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
db_init.close()

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

# --- Upload Endpoint ---
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        db = get_db()
        cursor = db.cursor()
        files = request.files.getlist('files')
        if not files:
            return "No files received!", 400
        for file in files:
            content = file.read().decode('utf-8')
            cursor.execute(
                "INSERT INTO can_logs (filename, content) VALUES (%s, %s)",
                (file.filename, content)
            )
        db.commit()
        db.close()
        return "Uploaded and saved to MySQL successfully!", 200
    except Exception as e:
        return f"Upload failed: {str(e)}", 500

# --- Download All Files Endpoint ---
@app.route('/download', methods=['GET'])
def download_data():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT filename, content FROM can_logs")
        rows = cursor.fetchall()
        db.close()

        export_dir = "export"
        os.makedirs(export_dir, exist_ok=True)

        # Write individual CSV files
        for filename, content in rows:
            clean_name = filename.replace("/", "_")
            if not clean_name.endswith(".csv"):
                clean_name += ".csv"
            with open(os.path.join(export_dir, clean_name), "w") as f:
                f.write(content)

        # Zip them
        zip_filename = f"can_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(export_dir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in os.listdir(export_dir):
                if file.endswith('.csv'):
                    zipf.write(os.path.join(export_dir, file), arcname=file)

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return f"Download failed: {str(e)}", 500

# --- Delete All Files Endpoint ---
@app.route('/delete', methods=['DELETE'])
def delete_all():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM can_logs")
        db.commit()
        db.close()
        return "All records deleted from MySQL.", 200
    except Exception as e:
        return f"Delete failed: {str(e)}", 500

# --- List Uploaded Files ---
@app.route('/files', methods=['GET'])
def list_files():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, filename, uploaded_at FROM can_logs ORDER BY uploaded_at DESC")
        rows = cursor.fetchall()
        db.close()
        files = [
            {
                "id": row[0],
                "filename": row[1],
                "uploaded_at": row[2].strftime("%Y-%m-%d %H:%M:%S")
            }
            for row in rows
        ]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Delete File by ID ---
@app.route('/delete/<int:file_id>', methods=['DELETE'])
def delete_file_by_id(file_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM can_logs WHERE id = %s", (file_id,))
        db.commit()
        db.close()
        return f"Deleted file with ID {file_id}", 200
    except Exception as e:
        return f"Delete failed: {str(e)}", 500

# --- Download File by ID ---
@app.route('/download/<int:file_id>', methods=['GET'])
def download_file_by_id(file_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT filename, content FROM can_logs WHERE id = %s", (file_id,))
        result = cursor.fetchone()
        db.close()
        if result:
            filename, content = result
            export_dir = "export"
            os.makedirs(export_dir, exist_ok=True)
            safe_name = filename.replace("/", "_")
            file_path = os.path.join(export_dir, safe_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return send_file(file_path, as_attachment=True)
        else:
            return "File not found.", 404
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
