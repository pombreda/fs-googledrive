# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from datetime import datetime
import unittest

from pytest import fixture

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


from fs.tests import FSTestCases

from googledrivefs import GoogleDriveFS

client_config = {
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'client_id': '105537897616-oqt2bc3ffgi3l2bd07o1s3feq68ga5m7.apps.googleusercontent.com',
    'client_secret': 'sC6ZXdmHf_qXR0bQ0XaLvfSp',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'revoke_uri': None,
    'token_uri': 'https://accounts.google.com/o/oauth2/token'
    }


class TestGoogleDriveFS():
    @fixture
    def fs(self):
        gauth = GoogleAuth()
        gauth.client_config = client_config
        gauth.settings["client_config_backend"] = "settings"
        drive = GoogleDrive(gauth)
        return GoogleDriveFS(drive)

    def test_map_ids_to_paths(self, fs):
        #import ipdb; ipdb.set_trace()
        fs._map_ids_to_paths()
        print(list(fs._ids.iternames()))
        print(list(fs._ids.itervalues()))
        print(list(fs._ids.keys()))
        assert False

    def cleanup_googledrive(fs):
        """Remove all files and folders from Google Drive"""
        for entry in fs.listdir(files_only=True):
            fs.remove(entry)
        for entry in fs.listdir(dirs_only=True):
            fs.removedir(entry, force=True)


# class TestExternalGoogleDriveFS(unittest.TestCase, FSTestCases):
#     """This will test the GoogleDriveFS implementation against the
#     base tests defined in PyFilesystem"""
#     def setUp(self):
#         gauth = GoogleAuth()
#         gauth.client_config = client_config
#         gauth.settings["client_config_backend"] = "settings"
#         drive = GoogleDrive(gauth)
#         self.fs = GoogleDriveFS(drive)

#     def tearDown(self):
#         cleanup_googledrive(self.fs)
#         self.fs.close()
