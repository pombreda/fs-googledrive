# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from apiclient.http import MediaIoBaseUpload

from fs.base import FS
from fs.errors import UnsupportedError
from fs.path import basename
import io


class GoogleDriveFS(FS):
    """A filesystem implementation that stores the files in GoogleDrive"""

    _meta = {'thread_safe': True,
             'virtual': False,
             'read_only': False,
             'case_insensitive_paths': True,
             'network': True,
             'atomic.setcontents': False,
             'atomic.makedir': True,
             'atomic.rename': True,
             'mime_type': 'virtual/googledrive',
    }

    def __init__(self, client, **kwargs):
        super(GoogleDriveFS, self).__init__(**kwargs)
        self.client = client

    def open(self, path, mode='r', **kwargs):
        """
        Open a the given path as a file-like object.
        """
        mime_type = "virtual/googledrive"
        local_file = io.BytesIO(b"...Some data to upload...")
        media_body = MediaIoBaseUpload(local_file, mime_type)
        body = {
            "title": basename(path),
            "description": path,
            "mimeType": mime_type
        }
        remote_file = self.client.files().insert(body=body, media_body=media_body).execute()
        return remote_file