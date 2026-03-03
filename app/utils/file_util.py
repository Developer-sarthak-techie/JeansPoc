import os
import uuid

UPLOAD_FOLDER = "uploads"

def save_upload_file(file):
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path