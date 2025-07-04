# app.py
from flask import Flask, jsonify, request
import pandas as pd
import re
from flask_cors import CORS # Importa la extensión CORS
import os

# Inicializa la aplicación Flask
app = Flask(__name__)
# Habilita CORS para todas las rutas de tu aplicación Flask.
# Esto es crucial para que tu frontend (desde React Native) pueda hacer solicitudes a esta API.
# En producción, considera restringir 'origins' a tu dominio específico de React Native.
CORS(app) 

# --- Función para parsear una línea del TXT usando Regex ---
def parse_line(line):
    """
    Parsea una línea del archivo TXT de códigos postales usando expresiones regulares.
    El formato esperado de la línea es el que se observa en la imagen proporcionada:
    CP|ASENTAMIENTO|TIPO_ASENTAMIENTO|MUNICIPIO|ESTADO|CIUDAD|c_estado_code|c_oficina_code|c_cp_code||c_mnpio_code|id_asenta_cpcons_code|d_zona|tipo_asentamiento_desc|c_cve_ciudad_code

    Ejemplo: 01000|San Ángel|Colonia|Álvaro Obregón|Ciudad de México|Ciudad de México|01001|09|01001||09|010|0001|Urbano|01
    """
    # Expresión regular ajustada para capturar los diferentes grupos de datos
    # basados en el delimitador '|' y el formato que se observa en las líneas de ejemplo.
    # ^ : Inicio de la línea
    # ([^|]+) : Captura cualquier carácter que no sea un pipe, una o más veces.
    # ([^|]*) : Captura cualquier carácter que no sea un pipe, cero o más veces (para campos que pueden estar vacíos como '||').
    # \| : Coincide con el carácter pipe literal (escapado con '\').
    # $ : Fin de la línea.
    
    # Asegúrate de que esta regex coincida con el formato EXACTO de tus líneas de datos.
    # Si hay variaciones en tu TXT, esta regex podría necesitar ajustes.
    regex_pattern = r"^([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)$"
    match = re.match(regex_pattern, line)

    if match:
        try:
            # Mapeamos los grupos capturados a nombres descriptivos.
            return {
                'codigo_postal': match.group(1).strip(),
                'asentamiento': match.group(2).strip(),
                'tipo_asentamiento': match.group(3).strip(),
                'municipio': match.group(4).strip(),
                'estado': match.group(5).strip(),
                'ciudad': match.group(6).strip(), # Asumiendo que el 6to campo es la ciudad
                'c_estado_code': match.group(7).strip(),
                'c_oficina_code': match.group(8).strip(),
                'c_cp_code': match.group(9).strip(),
                'empty_field_1': match.group(10).strip(), # Campo que estaba vacío (||)
                'c_mnpio_code': match.group(11).strip(),
                'id_asenta_cpcons_code': match.group(12).strip(),
                'd_zona': match.group(13).strip(), # d_zona
                'tipo_asentamiento_desc': match.group(14).strip(), # "Urbano", "Rural" etc.
                'c_cve_ciudad_code': match.group(15).strip(), # c_cve_ciudad
            }
        except IndexError:
            # Esto debería ocurrir si la regex no tiene suficientes grupos para una línea específica.
            print(f"Warning: Regex did not capture all expected groups for line: {line.strip()}")
            return None
    else:
        # Si la línea no coincide con el patrón esperado, se omite.
        print(f"Warning: Line did not match expected pattern and will be skipped: {line.strip()}")
        return None

# --- Cargar los datos del TXT al inicio de la aplicación ---
data = []
# Define la ruta al archivo TXT. 'codigos_postales.txt' debe estar en el mismo directorio que app.py.
file_path = 'codigos_postales.txt' 

try:
    # Abre el archivo TXT. Es crucial usar la codificación correcta.
    # 'utf-8' es el estándar recomendado para la web. Asegúrate de que tu archivo TXT esté guardado en UTF-8 (sin BOM).
    with open(file_path, 'r', encoding='utf-8') as f:
        # Saltar la primera línea (el encabezado descriptivo del archivo, no de datos)
        next(f) 
        for line in f:
            parsed_data = parse_line(line.strip())
            if parsed_data:
                data.append(parsed_data)
    
    # Crea un DataFrame de Pandas con los datos parseados.
    df_codigos_postales = pd.DataFrame(data)
    print(f"Postal code data loaded successfully from '{file_path}'. Loaded {len(df_codigos_postales)} records.")

    # Asegura que la columna 'codigo_postal' sea de tipo string para evitar problemas
    # con ceros iniciales o comparaciones numéricas incorrectas.
    df_codigos_postales['codigo_postal'] = df_codigos_postales['codigo_postal'].astype(str)

except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found. Make sure it is in the same directory as 'app.py'.")
    df_codigos_postales = pd.DataFrame() # Empty DataFrame to prevent further errors
except Exception as e:
    print(f"Error loading or parsing TXT file: {e}")
    df_codigos_postales = pd.DataFrame()

# --- Rutas de la API ---

@app.route('/')
def home():
    """
    Home route for the API. Provides a welcome message.
    """
    return "Welcome to the Mexico Postal Code API! Use /api/codigo_postal/<codigo>."

@app.route('/api/codigo_postal/<string:codigo>', methods=['GET'])
def get_info_by_codigo_postal(codigo):
    """
    Endpoint to get information for a specific postal code.
    Example usage: GET /api/codigo_postal/01000
    """
    if df_codigos_postales.empty:
        # If the DataFrame is empty (due to a loading error), return a 500 error.
        return jsonify({"error": "Postal code data not loaded. Verify the TXT file and its format."}), 500

    # Filter the DataFrame to find the postal code.
    # `.to_dict(orient='records')` converts the results into a list of dictionaries,
    # which is a common format for API JSON responses.
    results = df_codigos_postales[df_codigos_postales['codigo_postal'] == codigo].to_dict(orient='records')
    
    if results:
        # If results are found, return them as JSON.
        return jsonify(results)
    else:
        # If the postal code is not found, return a 404 (Not Found) message.
        return jsonify({"mensaje": f"Postal code {codigo} not found."}), 404

if __name__ == '__main__':
    # Run the application in debug mode.
    # This is only for local development.
    # In a production environment, it is recommended to use a WSGI server like Gunicorn.
    app.run(debug=True, port=5000)

