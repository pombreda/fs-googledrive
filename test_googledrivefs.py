# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from datetime import datetime
import unittest

from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build
import httplib2

from fs.tests import FSTestCases

from googledrivefs import GoogleDriveFS

credentials = OAuth2Credentials(
    access_token="""4/v52SwfzFzCIRU2hVzsdwBQj7d5JA.QlcY-CmAmRgTOl05ti8ZT3aliS9QigI""",
    client_id="""105537897616-oqt2bc3ffgi3l2bd07o1s3feq68ga5m7.apps.googleusercontent.com""",
    client_secret=u'sC6ZXdmHf_qXR0bQ0XaLvfSp',
    refresh_token=u'1/jqjIdwxzJCLMrb5tLM5nUzk-jSRdZBa_tXAFJb03lfw',
    token_expiry=datetime(2014, 4, 3, 15, 53, 43),
    token_uri='https://accounts.google.com/o/oauth2/token',
    user_agent=None,
    revoke_uri='https://accounts.google.com/o/oauth2/revoke',
    id_token=None)


def cleanup_googledrive(fs):
    """Remove all files and folders from Google Drive"""
    for entry in fs.listdir(files_only=True):
        fs.remove(entry)
    for entry in fs.listdir(dirs_only=True):
        fs.removedir(entry, force=True)


class TestExternalGoogleDriveFS(unittest.TestCase, FSTestCases):
    """This will test the GoogleDriveFS implementation against the
    base tests defined in PyFilesystem"""
    def setUp(self):
        http = httplib2.Http()
        http = credentials.authorize(http)
        drive_service = build('drive', 'v2', http=http)
        self.fs = GoogleDriveFS(drive_service)

    def tearDown(self):
        cleanup_googledrive(self.fs)
        self.fs.close()
