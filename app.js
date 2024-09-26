const express = require('express');
const multer = require('multer');
const csv = require('csv-parser');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');

const app = express();
const upload = multer();
const PORT = process.env.PORT || 3000;

app.use(express.static('public'));
app.use(bodyParser.urlencoded({ extended: true }));

const PALABRAS_IGNORADAS = new Set([/* ... */]);

function leerCSV(file) {
    return new Promise((resolve, reject) => {
        const datos = [];
        fs.createReadStream(file)
            .pipe(csv({ separator: ';' }))
            .on('data', (row) => datos.push(row))
            .on('end', () => resolve(datos))
            .on('error', (error) => reject(error));
    });
}

function buscarMensajes(datos, cadena) {
    return datos.filter(fila => fila.Mensaje && fila.Mensaje.toLowerCase().includes(cadena.toLowerCase()));
}

function contarPalabras(datos) {
    const palabras = [];
    datos.forEach(fila => {
        if (fila.Mensaje) {
            palabras.push(...fila.Mensaje.toLowerCase().match(/\w+/g));
        }
    });
    return Array.from(new Set(palabras.filter(p => !PALABRAS_IGNORADAS.has(p)))).slice(0, 10);
}

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/', upload.single('file'), async (req, res) => {
    if (!req.file) {
        return res.status(400).send("No se ha enviado ningún archivo.");
    }

    try {
        const datos = await leerCSV(req.file.buffer);

        if (req.body.accion === "buscar_mensajes") {
            const mensajes = buscarMensajes(datos, req.body.cadena);
            res.render('results', { mensajes, cadena: req.body.cadena });

        } else if (req.body.accion === "ver_palabras") {
            const palabras = contarPalabras(datos);
            res.render('words', { palabras });

        } else if (req.body.accion === "ver_coordenadas") {
            // Implementa la lógica de coordenadas si es necesario
            res.send("Coordenadas: aún no implementado.");
        } else {
            return res.status(400).send("Acción no válida.");
        }

    } catch (error) {
        console.error(error);
        res.status(500).send("Error procesando el archivo.");
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
