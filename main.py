from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi_sqlalchemy import DBSessionMiddleware
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