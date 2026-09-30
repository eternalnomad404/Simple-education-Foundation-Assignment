from contextlib import asynccontextmanager

from fastapi import FastAPI
from rich import panel, print
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router


# Async context manager
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print(panel.Panel("Server is started ....", border_style="green"))

    # Some functionality and yeild until the lifespan of teh app

    yield

    print(panel.Panel(".... Stopped!", border_style="red"))

API_DESCRIPTION = """
A Message delivery status tracker
"""


app = FastAPI(
    lifespan=lifespan_handler,
    title="Communicator",
    description=API_DESCRIPTION,
)

# Add all endpoints
app.include_router(master_router)


@app.get("/")
def health_check():
    return {"detail" : "Server running...."}




# Returns the Scalar API documentation interface
@app.get("/scalar", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="Scalar API")