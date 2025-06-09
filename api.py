"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Description: initialize the api and route incoming messages
to our app
"""

from http import HTTPStatus

from aiohttp import web
import os
from botbuilder.core.integration import aiohttp_error_middleware
from urllib.parse import unquote
from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
from azure.storage.blob import BlobServiceClient
import logging

from bot import app

routes = web.RouteTableDef()


@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    res = await app.process(req)
    if res is not None:
        return res
    return web.Response(status=HTTPStatus.OK)

# @routes.get("/api/get-blob")
# async def get_blob(req: web.Request) -> web.StreamResponse:
#     try:
#         blob_name = unquote(req.rel_url.query.get("blob_name", ""))
#         logging.info(f"Starting get_blob function for blob: {blob_name}")

#         client_credential = ChainedTokenCredential(
#             ManagedIdentityCredential(),
#             AzureCliCredential()
#         )

#         STORAGE_ACCOUNT = os.getenv("STORAGE_ACCOUNT")
#         blob_service_client = BlobServiceClient(
#             f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
#             credential=client_credential
#         )

#         blob_client = blob_service_client.get_blob_client(container='documents', blob=blob_name)
#         blob_data = blob_client.download_blob()
#         blob_text = blob_data.readall()

#         content_type = blob_client.get_blob_properties().content_settings.content_type

#         return web.Response(body=blob_text, content_type=content_type)

#     except Exception as e:
#         logging.exception("[aiohttp backend] Exception in /api/get-blob")
#         return web.json_response({"error": str(e)}, status=500)




api = web.Application(middlewares=[aiohttp_error_middleware])
api.add_routes(routes)