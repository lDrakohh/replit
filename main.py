from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import re
from collections import Counter

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
    reader = csv.DictReader(file.read().decode('utf-8').splitlines(),
                            delimiter=';')
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


@app.route('/', methods=['GET', 'POST'])
def index():
    """Página principal que permite cargar un archivo CSV y buscar mensajes."""
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("Debes seleccionar un archivo CSV.")
            return redirect(url_for('index'))

        # Leer los datos del CSV
        datos = leer_csv(file)

        accion = request.form.get('accion')

        if accion == "buscar_mensajes":
            cadena = request.form.get('cadena')
            mensajes = buscar_mensajes(datos, cadena)
            return render_template('results.html',
                                   mensajes=mensajes,
                                   cadena=cadena)

        elif accion == "ver_coordenadas":
            coordenadas_encontradas = []
            for fila in datos:
                coordenadas = es_coordenada(fila['Mensaje'])
                if coordenadas:
                    coordenadas_encontradas.append(
                        (fila['Telefono'], coordenadas))

            return render_template('coordinates.html',
                                   coordenadas=coordenadas_encontradas)

        elif accion == "ver_palabras":
            palabras = contar_palabras(datos)
            return render_template('words.html', palabras=palabras)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
