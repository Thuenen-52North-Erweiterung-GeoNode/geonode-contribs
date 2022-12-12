from django.conf import settings
from django.core.files.storage import FileSystemStorage
import mimetypes
import zipfile
import uuid
import io
import shutil
import json
import csv


def encode_as_csv(data):
    if (len(data) == 0):
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())

    writer.writeheader()
    for r in data:
        writer.writerow(r)

    return output.getvalue()