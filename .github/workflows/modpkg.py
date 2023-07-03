import glob
import os
import shutil
import sys
from zipfile import ZipFile

directory = sys.argv[1]
original_name = "widgetastic_core"
new_name = "widgetastic.core"
print(f"dist folder holding whl file: {directory}")
source_file = glob.glob(os.path.join(directory, f"{original_name}*.whl"))[0]
target_file = source_file.replace(original_name, new_name)
tempdir = os.path.join(directory, "temp")

with ZipFile(source_file, "r") as source, ZipFile(target_file, "w") as target:
    for item in source.infolist():
        # Extract the original file to a temporary location
        source.extract(item.filename, path=tempdir)
        # Determine the new filename or directory name
        if original_name in item.filename:
            print(f"Renamed: {original_name} with {new_name}")
            new_filename = item.filename.replace(original_name, new_name)
        else:
            new_filename = item.filename
        target.write(os.path.join(tempdir, item.filename), arcname=new_filename)

        # Remove the temporary extracted file or directory
    os.remove(os.path.join(tempdir, item.filename))
shutil.rmtree(tempdir)
os.remove(source_file)
