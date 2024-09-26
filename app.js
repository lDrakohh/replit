const express = require('express');
const bodyParser = require('body-parser');
const multer = require('multer');
const path = require('path');
const stream = require('stream');
const csv = require('csv-parser');

const app = express();
const upload = multer();
const PORT = process.env.PORT || 3000;

// Configura EJS como motor de plantillas
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'templates')); // Asegúrate de que apunte a la carpeta correcta

// Middleware para analizar el cuerpo de las solicitudes
app.use(bodyParser.urlencoded({ extended: true })); // Para datos de formularios
app.use(bodyParser.json()); // Para datos JSON

// Middleware para servir archivos estáticos
app.use(express.static(path.join(__dirname, 'templates')));

// Array para almacenar los datos del CSV
let datosCSV = [];
const PALABRAS_IGNORADAS = new Set(['el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', /* otras palabras ignoradas */]);

// Función para leer el CSV desde el buffer
function leerCSV(fileBuffer) {
    return new Promise((resolve, reject) => {
        const datos = [];
        const bufferStream = new stream.PassThrough();
        bufferStream.end(fileBuffer);

        bufferStream
            .pipe(csv({ separator: ';' }))
            .on('data', (row) => datos.push(row))
            .on('end', () => resolve(datos))
            .on('error', (error) => {
                console.error("Error al leer el archivo CSV:", error);
                reject(error);
            });
    });
}

// Función para buscar mensajes
function buscarMensajes(datos, cadena) {
    return datos.filter(fila => fila.Mensaje && fila.Mensaje.toLowerCase().includes(cadena.toLowerCase()));
}

// Función para contar palabras
function contarPalabras(datos) {
    const conteoPalabras = {};

    datos.forEach(fila => {
        const telefono = fila.Telefono;
        const mensaje = fila.Mensaje;

        if (mensaje) {
            const palabras = mensaje.toLowerCase().match(/\w+/g) || [];

            palabras.forEach(palabra => {
                if (!PALABRAS_IGNORADAS.has(palabra)) {
                    if (!conteoPalabras[telefono]) {
                        conteoPalabras[telefono] = {};
                    }
                    conteoPalabras[telefono][palabra] = (conteoPalabras[telefono][palabra] || 0) + 1;
                }
            });
        }
    });

    const palabrasMasUsadas = {};
    for (const telefono in conteoPalabras) {
        // Convertir el objeto en un array de entradas y ordenarlas
        const palabrasArray = Object.entries(conteoPalabras[telefono])
            .sort((a, b) => b[1] - a[1]) // Ordenar de mayor a menor
            .slice(0, 10); // Obtener las 10 más usadas
        palabrasMasUsadas[telefono] = palabrasArray; // Almacenar en la estructura final
    }

    return palabrasMasUsadas; // Retornar la estructura final
}


function obtenerCoordenadas(datos) {
    const coordenadas = [];

    datos.forEach(fila => {
        const mensaje = fila.Mensaje;
        if (mensaje) {
            // Cambia la expresión regular para buscar coordenadas separadas por punto y coma
            const regex = /(-?\d+\.\d+);?\s*(-?\d+\.\d+)/g;
            let match;
            while ((match = regex.exec(mensaje)) !== null) {
                coordenadas.push({
                    telefono: fila.Telefono,
                    latitud: match[1],
                    longitud: match[2],
                    mensaje: mensaje,
                });
            }
        }
    });

    return coordenadas;
}


// Ruta para manejar la carga del archivo
app.post('/', upload.single('file'), async (req, res) => {
    if (!req.file) {
        return res.status(400).send("No se ha enviado ningún archivo.");
    }

    try {
        datosCSV = await leerCSV(req.file.buffer);
        res.redirect('/');
    } catch (error) {
        console.error("Error procesando el archivo:", error);
        return res.status(500).send("Error procesando el archivo.");
    }
});

// Rutas para manejar las acciones
app.post('/buscar_mensajes', (req, res) => {
    const { cadena } = req.body;

    const mensajes = buscarMensajes(datosCSV, cadena);
    res.render('results', { mensajes, cadena });
});

app.post('/ver_palabras', (req, res) => {
    const palabras = contarPalabras(datosCSV);
    console.log(palabras);
    res.render('words', { palabras });
});


app.post('/ver_coordenadas', (req, res) => {
    const coordenadas = obtenerCoordenadas(datosCSV);
    res.render('coordinates', { coordenadas });
});

// Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
