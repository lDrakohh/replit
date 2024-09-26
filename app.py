from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import csv
import re
from collections import Counter
from fastapi import Request

app = FastAPI()

# Permitir CORS si es necesario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

PALABRAS_IGNORADAS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero',
    'a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 'en', 'entre',
    'hacia', 'hasta', 'para', 'por', 'sin', 'sobre', 'tras', 'que', 'quien',
    'quienes', 'cual', 'cuales', 'me', 'te', 'se', 'nos', 'lo', 'le', 'les',
    'mi', 'tu', 'su', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vosotros',
    'vosotras', 'ellos', 'ellas', 'yo', 'tú', 'él', 'ella', 'nosotros',
    'nosotras', 'vosotros', 'vosotras', 'ellos', 'ellas', 'esto', 'eso',
    'aquello', 'este', 'ese', 'aquel', 'estos', 'esos', 'aquellos', 'estas',
    'esas', 'aquellas', 'no', 'si', 'es', 'ya', 'va', 'hay'
}


def leer_csv(file):
    """Leer el contenido de un archivo CSV."""
    datos = []
    reader = csv.DictReader(file.decode('utf-8').splitlines(), delimiter=';')
    for row in reader:
        datos.append(row)
    return datos


def buscar_mensajes(datos, cadena):
    """Buscar mensajes que contienen una cadena específica."""
    return [
        fila for fila in datos
        if cadena and cadena.lower() in fila['Mensaje'].lower()
    ]


def es_coordenada(mensaje):
    """Identificar coordenadas en un mensaje."""
    patron = r'-?\d+\.\d+;-?\d+\.\d+'
    return re.findall(patron, mensaje)


def contar_palabras(datos):
    """Contar las palabras más usadas en los mensajes."""
    palabras = []
    for fila in datos:
        palabras.extend(re.findall(r'\w+', fila['Mensaje'].lower()))
    # Filtrar palabras ignoradas
    palabras_filtradas = [p for p in palabras if p not in PALABRAS_IGNORADAS]
    conteo = Counter(palabras_filtradas)
    return conteo.most_common(10)  # Retornar las 10 palabras más comunes


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal que permite cargar un archivo CSV y buscar mensajes."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def upload_file(request: Request, file: UploadFile = File(...), cadena: str = Form(None), accion: str = Form(...)):
    """Manejar la carga del archivo CSV y las acciones."""
    # Leer los datos del CSV
    datos = leer_csv(await file.read())

    if accion == "buscar_mensajes":
        mensajes = buscar_mensajes(datos, cadena)
        return templates.TemplateResponse("results.html", {"request": request, "mensajes": mensajes, "cadena": cadena})

    elif accion == "ver_coordenadas":
        coordenadas_encontradas = []
        for fila in datos:
            coordenadas = es_coordenada(fila['Mensaje'])
            if coordenadas:
                coordenadas_encontradas.append((fila['Telefono'], coordenadas))

        return templates.TemplateResponse("coordinates.html", {"request": request, "coordenadas": coordenadas_encontradas})

    elif accion == "ver_palabras":
        palabras = contar_palabras(datos)
        return templates.TemplateResponse("words.html", {"request": request, "palabras": palabras})

# Si deseas ejecutar localmente
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
