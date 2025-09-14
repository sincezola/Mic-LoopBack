// server.js
import net from "net";

const PORT = 5000;
const HOST = "127.0.0.1";

const server = net.createServer();
const clients = new Set(); // sockets

function makeKey(socket) {
  return `${socket.remoteAddress}:${socket.remotePort}`;
}

server.on("connection", (socket) => {
  socket.setNoDelay(true);
  socket._buffer = Buffer.alloc(0);
  socket._registered = false;
  clients.add(socket);

  const key = makeKey(socket);
  console.log("Cliente conectado:", key);

  socket.on("data", (chunk) => {
    // acumula bytes
    socket._buffer = Buffer.concat([socket._buffer, chunk]);

    // processa mensagens completas (4 bytes length + payload)
    while (socket._buffer.length >= 4) {
      const len = socket._buffer.readUInt32BE(0);
      if (socket._buffer.length < 4 + len) break; // espera mais dados

      const payload = socket._buffer.slice(4, 4 + len);
      socket._buffer = socket._buffer.slice(4 + len);

      // payload é um Buffer (pode ser texto ou áudio binário)
      const text = payload.toString();
      if (text === "__client_since") {
        socket._registered = true;
        console.log("Ouvinte registrado:", makeKey(socket));
        continue;
      }

      if (text === "__END__") {
        console.log("Transmissor encerrou (sinal __END__) de", makeKey(socket));
        continue;
      }

      // é um bloco de áudio (ou outro binário) -> repassa para todos os ouvintes
      // reenvia com o mesmo framing
      for (const s of clients) {
        if (s === socket) continue; // não mandar de volta para o emissor
        if (!s._registered) continue; // só para ouvintes registrados
        try {
          const header = Buffer.alloc(4);
          header.writeUInt32BE(payload.length, 0);
          s.write(Buffer.concat([header, payload]));
        } catch (err) {
          console.error("Erro ao enviar para", makeKey(s), err);
        }
      }
    }
  });

  socket.on("close", () => {
    clients.delete(socket);
    console.log("Cliente desconectado:", key);
  });

  socket.on("error", (err) => {
    clients.delete(socket);
    console.error("Erro socket", key, err);
    try { socket.destroy(); } catch { }
  });
});

server.on("listening", () => {
  console.log(`Relay TCP ouvindo em ${HOST}:${PORT}`);
});

server.on("error", (err) => {
  console.error("Erro no servidor:", err);
  server.close();
});

server.listen(PORT, HOST);
