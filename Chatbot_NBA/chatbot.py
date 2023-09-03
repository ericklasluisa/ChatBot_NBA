import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pymongo
import integracion_open_ai

nltk.download('punkt')
nltk.download('stopwords')

API_BASE_URL = "https://www.balldontlie.io/api/v1"
MONGO_URI = "mongodb+srv://fsquiroga:1234@cluster0.d2ga7nb.mongodb.net/"
MONGO_DB = "NBA"

# Conectar a MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Colección para interacciones
interactions_collection = db["Interactions"]

# Colección para jugadores
players_collection = db["Players"]

def pies_pulgadas_a_metros(pies, pulgadas):
    # 1 pie = 0.3048 metros, 1 pulgada = 0.0254 metros
    altura_metros = (pies * 0.3048) + (pulgadas * 0.0254)
    return round(altura_metros, 2)  # Redondear a dos decimales


def convertir_posicion(posicion_simbolo):
    # Mapeo de símbolos a palabras en español
    posicion_mapeo = {
        "C": "Pívot",
        "F": "Alero",
        'F-C': "Alero y Pivot",
        'C-F': "Alero y Pivot",
        'F-G': "Alero y Base",
        'G-F': "Alero y Base",
        "G": "Base y Escolta",
        "PG": "Base",
        "PF": "Alero alto",
        "SG": "Escolta",
        "SF": "Alero bajo",
    }

    # Verificar si la posición en símbolos está en el mapeo
    if posicion_simbolo in posicion_mapeo:
        posicion_espanol = posicion_mapeo[posicion_simbolo]
    else:
        if posicion_simbolo == None:
            posicion_espanol = "Desconocida"
        else:
            posicion_espanol = posicion_simbolo

    return posicion_espanol


def obtener_respuesta_db(consulta):
    respuesta_db = interactions_collection.find_one({"consulta": consulta})
    if respuesta_db:
        return respuesta_db["respuesta"]
    else:
        return None


def obtener_informacion_de_api(id_jugador):
    respuesta_db = players_collection.find_one({"consulta": id_jugador})

    if respuesta_db:
        respuesta = respuesta_db["respuesta"]
        print("Respuesta encontrada en la colección Players:")
    else:
        endpoint1 = "/players"
        params1 = {"search": id_jugador}

        response = requests.get(API_BASE_URL + endpoint1, params=params1)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                jugador = data['data'][0]
                altura_pies = jugador['height_feet']
                altura_pulgadas = jugador['height_inches']

                # Verificar que altura_pies y altura_pulgadas no sean None
                if altura_pies is not None and altura_pulgadas is not None:
                    altura_metros = pies_pulgadas_a_metros(altura_pies, altura_pulgadas)  # Altura en metros
                else:
                    altura_metros = "No se dispone de esta información"

                posicion_espanol = convertir_posicion(jugador['position'])  # Convertir la posición

                informacion = {
                    "nombre": jugador['first_name'] + " " + jugador['last_name'],
                    "posicion": posicion_espanol,  # Usar la posición en español
                    "altura_metros": altura_metros,
                    "peso_libras": jugador['weight_pounds'],
                    "equipo_id": jugador['team']['id'],
                }

                estadisticas_jugador = obtener_estadisticas_jugador(jugador['id'])
                if estadisticas_jugador is not None:
                    informacion.update(estadisticas_jugador)
                else:
                    informacion.update({"estadisticas": "No se dispone de las estadisticas de este jugador en la temporada actual"})

                informacion_equipo = obtener_informacion_equipo(informacion['equipo_id'])
                if informacion_equipo is not None:
                    informacion.update(informacion_equipo)
                else:
                    informacion.update({"nombre_equipo": "No se dispone de la informacion del equipo de este jugador"})

                players_collection.insert_one({"consulta": id_jugador, "respuesta": informacion})
                respuesta = informacion
            else:
                respuesta = None
        else:
            respuesta = None

    return respuesta


def obtener_informacion_equipo(equipo_id):
    endpoint = f"/teams/{equipo_id}"

    response = requests.get(API_BASE_URL + endpoint)
    if response.status_code == 200:
        equipo = response.json()
        if not equipo:
            informacion_equipo = None
        else:
            informacion_equipo = {
                "nombre_equipo": equipo['full_name'],
                "abreviacion_equipo": equipo['abbreviation'],
                "ciudad_equipo": equipo['city'],
                "conferencia_equipo": equipo['conference'],
                "division_equipo": equipo['division'],
            }
    else:
        informacion_equipo = None

    return informacion_equipo


def obtener_estadisticas_jugador(jugador_id):
    endpoint = f"/season_averages?season=2022&player_ids[]={jugador_id}"

    response = requests.get(API_BASE_URL + endpoint)
    if response.status_code == 200:
        estadisticas = response.json()
        if not estadisticas['data']:
            estadisticas_jugador = None

        else:
            estadisticas = estadisticas['data'][0]
            estadisticas_jugador = {
                "partidos_jugados": estadisticas['games_played'],
                "minutos_jugados": estadisticas['min'],
                "canasta_encestada": estadisticas['fgm'],
                "tiro_3puntos_encestados": estadisticas['fg3m'],
                "tiros_libres_encestados": estadisticas['ftm'],
                "rebotes_ofensivos": estadisticas['oreb'],
                "rebotes_defensivos": estadisticas['dreb'],
                "asistencias": estadisticas['ast'],
                "recuperacion_balon": estadisticas['stl'],
                "tiros_taponados": estadisticas['blk'],
                "perdida_balon": estadisticas['turnover'],
                "faltas_personales": estadisticas['pf'],
                "puntos_anotados": estadisticas['pts'],
                "porcentaje_tiros_encestados": estadisticas['fg_pct'],
            }
    else:
        estadisticas_jugador = None

    return estadisticas_jugador


def procesar_entrada(entrada):
    tokens = word_tokenize(entrada.lower())
    stop_words = set(stopwords.words("english"))
    keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
    return " ".join(keywords)


def guardar_interaccion(consulta, respuesta):
    if not obtener_respuesta_db(consulta):
        interactions_collection.insert_one({"consulta": consulta, "respuesta": respuesta})
    else:
        print("La interacción ya existe en la base de datos.")


def mostrar_informacion(informacion, consulta):
    salida = ""
    if informacion:
        palabras_clave = consulta.split()

        for palabra in palabras_clave:
            if palabra.lower() == "nombre":
                if (informacion['nombre'] == "No se dispone de esta informacion"):
                    print(informacion['nombre'])
                else:
                    salida = salida + (f"\nClaro! El nombre del jugador es {informacion['nombre']}.")
            elif palabra.lower() in ["estatura", "altura","mide"]:
                if (informacion['altura_metros'] == "No se dispone de esta informacion"):
                    print(informacion['altura_metros'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! La altura del jugador es {informacion['altura_metros']} metros.")
            elif palabra.lower() == "equipo":
                if (informacion['nombre_equipo'] == "No se dispone de esta informacion"):
                    print(informacion['nombre_equipo'])
                else:
                    salida = salida + (f"\nCon gusto! El jugador pertenece al equipo {informacion['nombre_equipo']}.")
            elif palabra.lower() == "peso":
                if (informacion['peso_libras'] == "No se dispone de esta informacion"):
                    print(informacion['peso_libras'])
                else:
                    salida = salida + (f"\n¡Claro! El peso del jugador es {informacion['peso_libras']} libras.")
            elif palabra.lower() == "posicion":
                if (informacion['posicion'] == "No se dispone de esta informacion"):
                    print(informacion['posicion'])
                else:
                    salida = salida + (f"\n¡Por supuesto! El jugador ocupa la posición de {informacion['posicion']}.")
            elif palabra.lower() == "ciudad":
                if (informacion['ciudad_equipo'] == "No se dispone de esta informacion"):
                    print(informacion['ciudad_equipo'])
                else:
                    salida = salida + (f"\n¡Con gusto! El equipo está en la ciudad de {informacion['ciudad_equipo']}.")
            elif palabra.lower() == "conferencia":
                if (informacion['conferencia_equipo'] == "No se dispone de esta informacion"):
                    print(informacion['conferencia_equipo'])
                else:
                    salida = salida + (
                        f"\n¡Por supuesto! El equipo pertenece a la conferencia {informacion['conferencia_equipo']}.")
            elif palabra.lower() in ["partidos", "jugado"]:
                if (informacion['partidos_jugados'] == "No se dispone de esta informacion"):
                    print(informacion['partidos_jugados'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El numero de partidos jugados del jugador en la ultima temporada es {informacion['partidos_jugados']}.")
            elif palabra.lower() in ["minutos", "tiempo"]:
                if (informacion['minutos_jugados_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['minutos_jugados_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador ha jugado en promedio {informacion['minutos_jugados_promedio_por_partido']} minutos en la ultima temporada.")
            elif palabra.lower() in ["encestados", "canastas"]:
                if (informacion['canasta_encestada_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['canasta_encestada_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador encestó en promedio {informacion['canasta_encestada_promedio_por_partido']} tiros en la ultima temporada.")
            elif palabra.lower() in ["3", "tres"]:
                if (informacion['tiro_3puntos_encestado_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['tiro_3puntos_encestado_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador encestó en promedio {informacion['tiro_3puntos_encestado_promedio_por_partido']} tiros de tres puntos en la ultima temporada.")
            elif palabra.lower() in ["libres"]:
                if (informacion['tiros_libres_encestados_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['tiros_libres_encestados_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador encestó en promedio {informacion['tiros_libres_encestados_promedio_por_partido']} tiros libres en la ultima temporada.")
            elif palabra.lower() in ["ofensivos"]:
                if (informacion['rebotes_ofensivos_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['rebotes_ofensivos_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador recuperó en promedio {informacion['rebotes_ofensivos_promedio_por_partido']} rebotes ofensivos en la ultima temporada.")
            elif palabra.lower() in ["defensivos"]:
                if (informacion['rebotes_defensivos_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['rebotes_defensivos_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador recuperó en promedio {informacion['rebotes_defensivos_promedio_por_partido']} rebotes defensivos en la ultima temporada.")
            elif palabra.lower() in ["asistencias", "asistencia", "asistio", "asistir"]:
                if (informacion['asistencias_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['asistencias_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El numero de asistencias del jugador fueron en promedio {informacion['asistencias_promedio_por_partido']} en la ultima temporada.")
            elif palabra.lower() in ["recuperacion", "recupero", "recuperar"]:
                if (informacion['recuperacion_balon_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['recuperacion_balon_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador recuperó en promedio {informacion['recuperacion_balon_promedio_por_partido']} balones en la ultima temporada.")
            elif palabra.lower() in ["tapones", "tapon", "tapo", "tapar", "taponados"]:
                if (informacion['tiros_taponados_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['tiros_taponados_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador tapó en promedio {informacion['tiros_taponados_promedio_por_partido']} tiros en la ultima temporada.")
            elif palabra.lower() in ["perdida", "perdidas", "perdio", "perder"]:
                if (informacion['perdida_balon_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['perdida_balon_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador perdió en promedio {informacion['perdida_balon_promedio_por_partido']} balones en la ultima temporada.")
            elif palabra.lower() in ["faltas", "falta"]:
                if (informacion['faltas_personales_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['faltas_personales_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador cometió en promedio {informacion['faltas_personales_promedio_por_partido']} faltas personales en la ultima temporada.")
            elif palabra.lower() in ["puntos", "punto", "anoto", "anotar"]:
                if (informacion['puntos_anotados_promedio_por_partido'] == "No se dispone de esta informacion"):
                    print(informacion['puntos_anotados_promedio_por_partido'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El jugador anotó en promedio {informacion['puntos_anotados_promedio_por_partido']} tiros en la ultima temporada.")
            elif palabra.lower() in ["porcentaje", "porcentajes", "porcentual"]:
                if (informacion['porcentaje_tiros_encestados'] == "No se dispone de esta informacion"):
                    print(informacion['porcentaje_tiros_encestados'])
                else:
                    salida = salida + (
                        f"\nPor supuesto! El porcentaje de tiros encestados por el jugador es del {informacion['porcentaje_tiros_encestados']}% en la ultima temporada.")
            elif palabra.lower() in ["hablame", "informacion", "quien"]:
                if (informacion['nombre'] == "No se dispone de esta informacion"):
                    print(informacion['nombre'])
                else:
                    salida = salida + ("\nInformación detallada del jugador:")
                    for clave, valor in informacion.items():
                        salida = salida + (f"\n{clave.capitalize()}: {valor}")
                    break


    else:
        salida = salida + (
            "\nNo puedo responder a tu pregunta, recuerda que solo poseo informacion acerca de\n los jugadores de la NBA. Intenta nuevamente.")

    return salida


def ingreso(entrada):
    salida = ""
    consulta_procesada = procesar_entrada(entrada)
    palabras = consulta_procesada.split()
    if len(palabras) >= 2:
        jugador_o_equipo = " ".join(palabras[-2:])

        respuesta_db = obtener_respuesta_db(consulta_procesada)
        if respuesta_db:

            salida = respuesta_db
        else:
            informacion = obtener_informacion_de_api(jugador_o_equipo)
            if informacion is not None:
                salida = mostrar_informacion(informacion, consulta_procesada)
                # Guardar la interacción completa en la colección "Interactions"
                # guardar_interaccion(consulta_procesada, informacion)
            else:
                salida = integracion_open_ai.obtener_respuesta_API(consulta_procesada)
                salida = agregar_salto_linea(salida)

        guardar_interaccion(consulta_procesada, salida)

    else:
        salida = ("La consulta es demasiado corta. Intenta nuevamente.")

    return salida


def agregar_salto_linea(texto):
    palabras = texto.split()
    resultado = ""

    for i, palabra in enumerate(palabras, start=1):
        resultado += palabra + " "

        if i % 9 == 0:
            resultado += "\n"

    return resultado

