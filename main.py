from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from Base.BaseModel import Base
from Party.router import router
from Configuration import Configuration
Configuration()

Base.metadata.create_all(bind=create_engine(Configuration.database.url))

app = FastAPI(title="LleidaHack API",
              description="LleidaHack API",
              version="2.0",
              docs_url='/docs',
              redoc_url='/redoc',
              openapi_url='/openapi.json',
              debug=True,
              swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

from error import error_handler as eh
from error.InvalidDataException import InvalidDataException

app.add_exception_handler(InvalidDataException,
                                eh.invalid_data_exception_handler)

app.add_middleware(DBSessionMiddleware, db_url=Configuration.database.url)

app.include_router(router)
for route in app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.tags[-1].replace(
            ' ', '').lower() if len(route.tags) > 0 else ''
        route.operation_id += '_' + route.name
@app.get("/")
def root():
    return RedirectResponse(url='/docs')

# from fastapi import FastAPI, WebSocket

# from utils.ConnectionManager import ConnectionManager

# app = FastAPI()

# manager = ConnectionManager()

# @app.websocket("/communicate")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(f"Received:{data}",websocket)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.send_personal_message("Bye!!!",websocket)