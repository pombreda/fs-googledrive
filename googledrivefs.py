# -*- coding: utf-8 -*-
from __future__ import (print_function, division,
                        absolute_import, unicode_literals)
from apiclient.http import MediaIoBaseUpload

from fs.base import FS
from fs.path import PathMap, basename, pathjoin
import io


class GoogleDriveFS(FS):

    """A filesystem implementation that stores the files in GoogleDrive"""

    _fields = "items(createdDate,fileExtension,fileSize,id,modifiedDate,"\
              "originalFilename,title)"
    _meta = {'thread_safe': False,
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
        self._ids = self._map_ids_to_paths()

    def _map_ids_to_paths(self):
        """Create a map that associates all directory paths with their
        ids because GoogleDrive does not have a concept of file paths.
        """
        ids = PathMap()
        entries = self.client.ListFile({"q": "trashed=false",
                                        "fields": "items(title,id,parents(id,isRoot))"
                                       }).GetList()

        def get_children(parent_id):
            for entry in entries:
                for parent in entry["parents"]:
                    if parent["id"] == parent_id or \
                      (parent["isRoot"] and not parent_id):
                        yield entry

        def build_map_recursive(path, parent_id):
            for child in get_children(parent_id):
                if not child["title"]:
                    continue

                child_path = pathjoin(path, child["title"])
                ids[child_path] = child["id"]
                build_map_recursive(child_path, child["id"])

        build_map_recursive("/", None)
        return ids

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
        remote_file = self.client.files() \
                          .insert(body=body, media_body=media_body) \
                          .execute()
        return remote_file

    def listdir(
            self,
            path="/",
            wildcard=None,
            full=False,
            absolute=False,
            dirs_only=False,
            files_only=False):
        pass

    def isdir(self, path):
        pass

    def isfile(self, path):
        pass

    def makedir(self, path, recursive=False, allow_recreate=False):
        pass

    def remove(self, path):
        pass

    def removedir(self, path, recursive=False, force=False):
        pass

    def rename(self, src, dst):
        pass

    def getinfo(self, path):
        pass
