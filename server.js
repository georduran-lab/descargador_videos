const { Server } = require("socket.io");

// Creamos servidor en el puerto 3000
const io = new Server(3000, {
    cors: { origin: "*" }
});

io.on("connection", (socket) => {
    console.log("Cliente conectado:", socket.id);

    // Ejemplo: enviar progreso simulado
    let progress = 0;
    let interval = setInterval(() => {
        progress += 10;
        socket.emit("progress", { progress, status: progress >= 100 ? "finished" : "downloading" });
        if (progress >= 100) clearInterval(interval);
    }, 1000);

    socket.on("disconnect", () => {
        console.log("Cliente desconectado:", socket.id);
    });
});
