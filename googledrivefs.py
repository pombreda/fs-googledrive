# -*- coding: utf-8 -*-
from __future__ import (print_function, division,
                        absolute_import, unicode_literals)

from fs.errors import (ResourceInvalidError, ResourceNotFoundError,
                       ParentDirectoryMissingError, DestinationExistsError,
                       DirectoryNotEmptyError, RemoveRootError)
from fs.filelike import StringIO
from fs.remote import RemoteFileBuffer
from fs.base import FS
from fs.path import PathMap, basename, pathjoin, dirname, isprefix, abspath
from fs.opener import Opener


class GoogleDriveOpener(Opener):
    names = ['gdrive']
    desc = """An opener for Google Drive.
    Example (authenticate with Google Drive with username and OAUTH):
    * gdrive://user@drive.google.com/path/to/folder"""

    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params,
               fs_path, writeable, create_dir):
        username, password, fs_path = cls._parse_credentials(fs_path)
        fs_path = fs_path.replace("drive.google.com")
        gdrivefs = cls.authenticate(username)

        if create_dir:
            gdrivefs.makedir(fs_path, recursive=True)

        return gdrivefs, fs_path


class GoogleDriveFS(FS):

    """A filesystem implementation that stores the files in GoogleDrive"""
    _folder_mimetype = 'application/vnd.google-apps.folder'
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
        ids['/'] = 'root'
        entries = self.client.ListFile({"q": "trashed=false",
                                        "fields": "items(title,id,"
                                        "parents(id,isRoot))"}).GetList()

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

    def open(self, path, mode='r', buffering=-1, encoding=None, errors=None,
             newline=None, line_buffering=False, **kwargs):
        if self.isdir(path):
            raise ResourceInvalidError(path)
        if 'w' in mode and not self.isdir(dirname(path)):
            raise ParentDirectoryMissingError(path)
        if 'r' in mode and not self.isfile(path):
            raise ResourceNotFoundError(path)
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
        if 'w' in mode and '+' not in mode and self.isfile(path):
            self.remove(path)

        data = ''
        if 'r' in mode:
            data = self.getcontents(path, mode=mode, encoding=encoding,
                                    errors=errors, newline=newline)
        rfile = StringIO(data=data, mode=mode)
        return RemoteFileBuffer(self, path, mode=mode, rfile=rfile)

    def getcontents(self, path, mode='rb', encoding=None,
                    errors=None, newline=None):
        if self.isdir(path):
            raise ResourceInvalidError(path)
        if not self.isfile(path):
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
            raise ResourceNotFoundError(path)

        fh = self.client.CreateFile({'id': self._ids[path]})
        return fh.GetContentString()

    def setcontents(self, path, data='', encoding=None,
                    errors=None, chunk_size=65536):
        if self.isdir(path):
            raise ResourceInvalidError(path)

        if hasattr(data, 'read'):
            data = data.read()

        if self.isfile(path):
            fh = self.client.CreateFile({'id': self._ids[path]})
            fh.SetContentString(data)
            fh.Upload()
        else:
            parent_path = self._ids[dirname(path)]
            fh = self.client.CreateFile({'title': basename(path),
                                         'parents': [{'id': parent_path}]})
            fh.SetContentString(data)
            fh.Upload()
            self._ids[path] = fh['id']

    def listdir(self, path="/", wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False):
        if self.isfile(path):
            raise ResourceInvalidError(path)
        if not self.isdir(path):
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
            raise ResourceNotFoundError(path)

        query = "'{0}' in parents and trashed=false"\
                .format(self._ids[dirname(path)])

        if dirs_only:
            query += " and mimeType = '{0}'".format(self._folder_mimetype)
        if files_only:
            query += " and mimeType != '{0}'".format(self._folder_mimetype)
        self._ids = self._map_ids_to_paths()
        entries = self._ids.names(path)
        # entries = self.client.ListFile({"q": query,
        #                                "fields": "items(title,id,"
        #                                "parents(id,isRoot))"}).GetList()
        # We don't want the _listdir_helper to perform dirs_only
        # and files_only filtering again
        return self._listdir_helper(path, entries, wildcard=wildcard,
                                    full=full, absolute=absolute,
                                    dirs_only=dirs_only,
                                    files_only=files_only)

    def isdir(self, path):
        try:
            fh = self.client.CreateFile({'id': self._ids[path]})
            return fh['mimeType'] == self._folder_mimetype
        except KeyError:
            return False

    def isfile(self, path):
        try:
            fh = self.client.CreateFile({'id': self._ids[path]})
            return fh['mimeType'] != self._folder_mimetype
        except KeyError:
            return False

    def makedir(self, path, recursive=False, allow_recreate=False):
        """Creates a file with mimeType _folder_mimetype
        which acts as a folder in GoogleDrive."""
        if self.isdir(path):
            if allow_recreate:
                return
            else:
                raise DestinationExistsError(path)
        if self.isfile(path):
            raise ResourceInvalidError(path)
        if not recursive and not self.isdir(dirname(path)):
            raise ParentDirectoryMissingError(path)

        if recursive:
            self.makedir(dirname(path), recursive=recursive,
                         allow_recreate=True)

        parent_id = self._ids[dirname(path)]
        fh = self.client.CreateFile({'title': basename(path),
                                     'mimeType': self._folder_mimetype,
                                     'parents': [{'id': parent_id}]})
        fh.Upload()
        self._ids[path] = fh['id']

    def remove(self, path):
        if self.isdir(path):
            raise ResourceInvalidError(path)
        if not self.isfile(path):
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
            raise ResourceNotFoundError(path)

        self.client.auth.service.files() \
                                .delete(fileId=self._ids[path]) \
                                .execute()
        self._ids.pop(path)

    def removedir(self, path, recursive=False, force=False):
        if self.isfile(path):
            raise ResourceInvalidError(path)
        if not self.isdir(path):
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
            raise ResourceNotFoundError(path)
        if abspath(path) == "/":
            raise RemoveRootError(path)
        if force:
            for child_path in self.listdir(path, full=True, dirs_only=True):
                self.removedir(child_path, force=force)
            for child_path in self.listdir(path, full=True, files_only=True):
                self.remove(child_path)
        elif len(self.listdir(path)) > 0:
            raise DirectoryNotEmptyError(path)

        self.client.auth.service.files() \
                                .delete(fileId=self._ids[path]) \
                                .execute()
        self._ids.pop(path)

        if recursive and len(self.listdir(dirname(path))) == 0:
            self.removedir(dirname(path), recursive=recursive)

    def rename(self, src, dst):
        if not self.exists(src):
            raise ResourceNotFoundError(src)
        if self.exists(dst):
            raise DestinationExistsError(dst)
        if isprefix(src, dst):
            raise ResourceInvalidError(dst)

        fh = self.client.CreateFile({'id': self._ids[src],
                                     'title': basename(dst)})
        fh.Upload()
        self._ids[dst] = self._ids.pop(src)

    def copy(self, src, dst, overwrite=False, chunk_size=65536):
        if self.isdir(src):
            raise ResourceInvalidError(src)
        if not self.isfile(src):
            if not self.isdir(dirname(src)):
                raise ParentDirectoryMissingError(src)
            raise ResourceNotFoundError(src)

        if self.isdir(dst):
            raise ResourceInvalidError(dst)
        if self.isfile(dst):
            if overwrite:
                self.remove(dst)
            else:
                raise DestinationExistsError(dst)
        else:
            if not self.isdir(dirname(dst)):
                raise ParentDirectoryMissingError(dst)

        parent_path = self._ids[dirname(dst)]
        copy_fh = {'title': basename(dst), 'parents': [{'id': parent_path}]}
        copy_fh = self.client.auth.service.files() \
                                  .copy(fileId=self._ids[src], body=copy_fh) \
                                  .execute()
        self._ids[dst] = copy_fh['id']

    def getinfo(self, path):
        if self.isdir(path):
            raise ResourceInvalidError(path)
        if not self.isfile(path):
            if not self.isdir(dirname(path)):
                raise ParentDirectoryMissingError(path)
            raise ResourceNotFoundError(path)

        fh = self.client.CreateFile({'id': self._ids[path],
                                     'title': basename(path)})
        return {
            'size': int(fh['fileSize']),
            'created_time': fh['createdDate'],
            'acessed_time': fh['lastViewedByMeDate'],
            'modified_time': fh['modifiedDate']
        }
