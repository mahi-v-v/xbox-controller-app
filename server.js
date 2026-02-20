const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static('public'));

io.on('connection', (socket) => {
    console.log('Phone connected');
    
    socket.on('input', (data) => {
        // This is where the magic happens.
        // On the PC, we'll listen to these events and inject them into the OS.
        process.stdout.write(`\rInput: ${JSON.stringify(data).slice(0, 100)}...`);
    });

    socket.on('disconnect', () => {
        console.log('Phone disconnected');
    });
});

const PORT = 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
    console.log(`Access this on your phone using your PC's IP address.`);
});