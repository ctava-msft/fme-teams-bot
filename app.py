"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from aiohttp import web

from api import api
from config import Config


if __name__ == "__main__":
    try:
        web.run_app(api, host="localhost", port=Config.PORT)
    except Exception as error:
        raise error