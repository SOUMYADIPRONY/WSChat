from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Websocket Group Chat</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    </head>
    <body>
    <div class="container mt-3">
      <h1>Group Chat</h1>
      <form id="nameForm" class="mb-3">
          <input type="text" class="form-control" id="username" placeholder="Enter your name" autocomplete="off"/>
          <button class="btn btn-outline-success mt-2">Join Chat</button>
      </form>
      <h2>Welcome, <span id="user-name"></span>!</h2>
      <form action="" onsubmit="sendMessage(event)" style="display: none;" id="chatForm">
          <input type="text" class="form-control" id="messageText" placeholder="Type a message" autocomplete="off"/>
          <button class="btn btn-outline-primary mt-2">Send</button>
      </form>
      <ul id="messages" class="mt-5"></ul>
    </div>
    <script>
      let username = "";
      let ws;

      document.getElementById("nameForm").onsubmit = function(event) {
        event.preventDefault();
        username = document.getElementById("username").value;
        if (!username) {
          alert("Please enter your name!");
          return;
        }
        document.getElementById("user-name").textContent = username;
        document.getElementById("nameForm").style.display = "none";
        document.getElementById("chatForm").style.display = "block";
        ws = new WebSocket(`ws://localhost:8000/ws?name=${username}`);
        ws.onmessage = function(event) {
          const messages = document.getElementById("messages");
          const message = document.createElement("li");
          const content = document.createTextNode(event.data);
          message.appendChild(content);
          messages.appendChild(message);
        };
      };

      function sendMessage(event) {
        event.preventDefault();
        const input = document.getElementById("messageText");
        if (input.value.trim() !== "") {
          ws.send(input.value);
          input.value = "";
        }
      }
    </script>
    </body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, name: str):
        await websocket.accept()
        self.active_connections[name] = websocket

    def disconnect(self, name: str):
        if name in self.active_connections:
            del self.active_connections[name]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_message(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    name = websocket.query_params.get("name")
    if not name:
        await websocket.close()
        return
    
    await manager.connect(websocket, name)
    await manager.broadcast_message(f"{name} has joined the chat!")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_message(f"{name}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(name)
        await manager.broadcast_message(f"{name} has left the chat!")
