const express = require("express");
const http = require("http");
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// Ejemplo de evento
io.on("connection", (socket) => {
    console.log("Cliente conectado ✅");
    socket.emit("progress", { progress: 0, status: "iniciando" });
});

server.listen(3000, "0.0.0.0", () => {
    console.log("Servidor Node.js con Socket.IO corriendo en http://0.0.0.0:3000");
});
