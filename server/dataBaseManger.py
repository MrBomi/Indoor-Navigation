import os

from pycurl import UPLOAD


def addDWGToDatabase(dwg, db):
    """
    Adds a DWG file to the database.

    Parameters:
    dwg (str): The path to the DWG file.
    db (object): The database connection object.

    Returns:
    bool: True if the operation was successful, False otherwise.
    """

UPLOAD_FOLDER = "static/upload"
def saveInLocal(dwg_file, yaml_file):
    os.makedirs("static/upload", exist_ok=True)
    dwg_path = os.path.join(UPLOAD_FOLDER, dwg_file.filename)
    yaml_path = os.path.join(UPLOAD_FOLDER, yaml_file.filename)
    dwg_file.save(dwg_path)
    yaml_file.save(yaml_path)
    return yaml_path , dwg_path



