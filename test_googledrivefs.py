# -*- coding: utf-8 -*-
from __future__ import (print_function, division,
                        absolute_import, unicode_literals)
import unittest
from mock import Mock
from pytest import fixture

from oauth2client.client import OAuth2Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from fs.tests import FSTestCases

from googledrivefs import GoogleDriveFS

client_config = {
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'client_id': '105537897616-oqt2bc3ffgi3l2bd07o1s3feq68ga5m7'
                 '.apps.googleusercontent.com',
    'client_secret': 'sC6ZXdmHf_qXR0bQ0XaLvfSp',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'revoke_uri': None,
    'token_uri': 'https://accounts.google.com/o/oauth2/token'}

credentials = '{"_module": "oauth2client.client", "token_expiry": "2014-06-07T17:04:26Z", "access_token": "ya29.KgBLjqMlBwNydhoAAACKi7Trb4b3VyN4LZX5JHHTz9wdUeAOqupcFn65q9p0kA", "token_uri": "https://accounts.google.com/o/oauth2/token", "invalid": false, "token_response": {"access_token": "ya29.KgBLjqMlBwNydhoAAACKi7Trb4b3VyN4LZX5JHHTz9wdUeAOqupcFn65q9p0kA", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "1/1Ani7Ovt_KmBPaQxbyc4ZGvhTHMNu4gwVdPiBR8_8BQ"}, "client_id": "105537897616-oqt2bc3ffgi3l2bd07o1s3feq68ga5m7.apps.googleusercontent.com", "id_token": null, "client_secret": "sC6ZXdmHf_qXR0bQ0XaLvfSp", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class": "OAuth2Credentials", "refresh_token": "1/1Ani7Ovt_KmBPaQxbyc4ZGvhTHMNu4gwVdPiBR8_8BQ", "user_agent": null}'


def cleanup_googledrive(fs):
    """Remove all files and folders from Google Drive"""
    for entry in fs.listdir(files_only=True):
        fs.remove(entry)
    for entry in fs.listdir(dirs_only=True):
        fs.removedir(entry, force=True)
    fs.client.auth.service.files().emptyTrash().execute()

class TestGoogleDriveFS():

    @fixture
    def fs(self):
        gauth = GoogleAuth()
        gauth.credentials = OAuth2Credentials.from_json(credentials)
        gauth.client_config = client_config
        gauth.settings["client_config_backend"] = "settings"
        drive = GoogleDrive(gauth)
        return GoogleDriveFS(drive)

    def test_map_ids_to_paths(self, fs):
        # Arrange
        file_list = [
            {'parents': [{'id': '0B_lkT', 'isRoot': True}],
             'id': '1APq7o', 'title': 'file_at_root.txt'},
            {'parents': [{'id': '0B_lkT', 'isRoot': True}],
             'id': '1xp13X', 'title': 'folder_at_root'},
            {'parents': [{'id': '1xp13X', 'isRoot': False}],
             'id': '13PuVd', 'title': 'file1_in_folder.txt'},
            {'parents': [{'id': '1xp13X', 'isRoot': False}],
             'id': '1ovGwK', 'title': 'file2_in_folder.txt'},
            {'parents': [{'id': '1xp13X', 'isRoot': False}],
             'id': '0Ap6n5', 'title': 'folder_in_folder'},
        ]
        fs.client.ListFile = Mock()
        fs.client.ListFile.return_value.GetList.return_value = file_list
        # Act
        ids = fs._map_ids_to_paths()
        # Assert
        assert ids['/file_at_root.txt'] == '1APq7o'
        assert ids['/folder_at_root'] == '1xp13X'
        assert ids['/folder_at_root/file1_in_folder.txt'] == '13PuVd'
        assert ids['/folder_at_root/file2_in_folder.txt'] == '1ovGwK'
        assert ids['/folder_at_root/folder_in_folder'] == '0Ap6n5'


class TestExternalGoogleDriveFS(unittest.TestCase, FSTestCases):
    """This will test the GoogleDriveFS implementation against the
    base tests defined in PyFilesystem"""
    def setUp(self):
        gauth = GoogleAuth()
        gauth.credentials = OAuth2Credentials.from_json(credentials)
        gauth.client_config = client_config
        gauth.settings["client_config_backend"] = "settings"
        drive = GoogleDrive(gauth)
        self.fs = GoogleDriveFS(drive)

    def tearDown(self):
        cleanup_googledrive(self.fs)
        self.fs.close()
