"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import os

class Config:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword")
    OAUTH_CONNECTION_NAME = os.environ.get("ConnectionName")