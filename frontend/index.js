const express = require('express');

const app = express();

app.use(express.static('./public'));

const server = app.listen(3000, () => {
	console.log('Serving on port 3000');
});

process.on('SIGTERM', () => {
	console.log('Recieved SIGTERM, closing server');
	server.close();
});
