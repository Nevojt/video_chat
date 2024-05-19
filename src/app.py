
from fastapi import FastAPI, staticfiles, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect
from .signaling import MeetingManager


app = FastAPI(root_path="/meet")

app.mount("/static", staticfiles.StaticFiles(directory="src/front-end"), name="static")
templates = Jinja2Templates(directory="src/templates")


meeting_manager = MeetingManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def hello():
    return {"message": "Hello World"}

@app.get("/")
def home(): # type: ignore
    return RedirectResponse("/meet/lobby")

@app.get("/room/{roomName}")
def read_room(request: Request, roomName: str):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/lobby")
def get_lobby(request: Request):
    return templates.TemplateResponse(request=request, name="lobby.html")

@app.websocket("/ws/{client_id}")
async def connet_websocket(websocket: WebSocket, client_id: str):
    """
    This function is responsible for handling the WebSocket connection for a specific client.

    Parameters:
    - websocket (WebSocket): The WebSocket instance representing the connection to the client.
    - client_id (str): A unique identifier for the client.

    The function first joins the client to the meeting manager using the provided client_id and websocket instance.
    Then, it enters an infinite loop where it continuously receives JSON data from the client using `websocket.receive_json()`.
    The received data is then broadcasted to all other clients in the same room as the current client using `meeting_manager.rooms[client_id].broadcast(data, websocket)`.

    If the client disconnects, the function catches the `WebSocketDisconnect` exception and calls `meeting_manager.leave(client_id, websocket)` to remove the client from the meeting manager.

    Returns:
    - None
    """
    await meeting_manager.join(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await meeting_manager.rooms[client_id].broadcast(data, websocket)
    except WebSocketDisconnect:
        meeting_manager.leave(client_id, websocket)