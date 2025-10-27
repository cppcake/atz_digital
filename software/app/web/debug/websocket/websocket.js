console.log("websocket.js loaded");

const ws = new WebSocket("ws://localhost:8000/subscribe_change");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};
