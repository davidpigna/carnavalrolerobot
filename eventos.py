import asyncio
import datetime
import time
from collections import defaultdict                                                                                            

import discord
import pymongo
from discord.errors import NotFound
from discord.ext import commands
from pymongo import MongoClient

from responses import handle_response

TOKEN = 'MTE2NDk4Mjg4NDYyOTc0OTg4MQ.G0qkR3.1aFWGitZ_MlwvjEMJSPDSdVFu8rKsE--HwwV2s'
client = pymongo.MongoClient("mongodb+srv://carnavalbot:L1TFC8W9wFFdKJHP@cluster0.kcjjzxf.mongodb.net/?retryWrites=true&w=majority")
db = client.carnavaldbdev
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)
is_registering = False
last_reaction_time = {}
current_timestamp = time.time()
time_struct = time.gmtime(current_timestamp)
year = time_struct.tm_year
user_registration_status = defaultdict(bool)                                                                                      

async def talk_time(payload):
    user = bot.get_user(payload.user_id)
    while True:
        await user.send("Ingrese la fecha y hora de la Charla (formato: DD-MM-AAAA HH:MM:) Ejemplo 25-12-2023 16:00")
        fecha_hora = await bot.wait_for('message', check=lambda m: m.author == user, timeout=300)
        try:
            fecha_hora_datetime = datetime.datetime.strptime(fecha_hora.content, "%d-%m-%Y %H:%M")
            # Pedir selección de zona horaria
            await user.send("Ingrese la zona horaria de la charla (UTC-3, UTC-4, UTC-5, UTC-6):")
            zona_horaria = await bot.wait_for('message', check=lambda m: m.author == user, timeout=300)
            # Obtener la diferencia en horas de la zona horaria seleccionada
            diferencia_horas = {"UTC-3": 3, "UTC-4": 4, "UTC-5": 5, "UTC-6": 6}.get(zona_horaria.content.upper(), 0)
            # Sumar la diferencia horaria a la fecha y hora ingresada
            fecha_hora_datetime += datetime.timedelta(hours=diferencia_horas)
            timestamp = int(fecha_hora_datetime.timestamp())
            break
        except ValueError:
            await user.send("Por favor ingrese la fecha y hora en el formato correcto.")
            continue
    db.charlas.update_one({"messageid": payload.message_id}, {"$set": {"fecha_hora": timestamp}})

async def editar_charla(ctx: commands.Context, message_id: int):
    try:
        # Buscar la charla en la base de datos utilizando el message_id
        charla = db.charlas.find_one({"messageid": message_id})

        if not charla:
            await ctx.send("No se encontró ninguna charla con el messageid proporcionado.")
            return

        # Solicitar qué campo desea editar
        await ctx.send("¿Qué campo deseas editar?\n1. Nombre\n2. Descripción\n3. Comunidad representante\n4. Imagen\n5. Fecha y hora\nPor favor, responde con el número correspondiente.")
        campo_a_editar = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        if campo_a_editar.content == ".cancelarregistro":
            return

        # Verificar la respuesta del usuario y solicitar el nuevo valor
        campo_a_editar = campo_a_editar.content.lower()
        nuevo_valor = ""
        nueva_descripcion = ""
        nueva_comunidad = ""
        nueva_imagen = ""
        nueva_fecha_hora = charla['fecha_hora']  # Mantén el valor actual como predeterminado

        if campo_a_editar == "1":
            await ctx.send("Ingrese el nuevo nombre de la charla:")
            nuevo_valor = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        elif campo_a_editar == "2":
            await ctx.send("Ingrese la nueva descripción de la charla:")
            nueva_descripcion = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        elif campo_a_editar == "3":
            await ctx.send("Ingrese la nueva comunidad representante (Red Social de preferencia o Sitio web):")
            nueva_comunidad = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        elif campo_a_editar == "4":
            await ctx.send("Ingrese la nueva imagen de la charla (URL):")
            nueva_imagen = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        elif campo_a_editar == "5":
            await ctx.send("Por favor, ingrese la nueva fecha y hora de la charla (formato: DD-MM-AAAA HH:MM):")
            fecha_hora_input = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            fecha_hora_str = fecha_hora_input.content
            try:
                fecha_hora_datetime = datetime.datetime.strptime(fecha_hora_str, "%d-%m-%Y %H:%M")
                # Pedir selección de zona horaria
                await ctx.send("Ingrese la zona horaria de la charla (UTC-3, UTC-4, UTC-5, UTC-6):")
                zona_horaria = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
                # Obtener la diferencia en horas de la zona horaria seleccionada
                diferencia_horas = {"UTC-3": 3, "UTC-4": 4, "UTC-5": 5, "UTC-6": 6}.get(zona_horaria.content.upper(), 0)
                # Sumar la diferencia horaria a la fecha y hora ingresada
                fecha_hora_datetime += datetime.timedelta(hours=diferencia_horas)
                timestamp = int(fecha_hora_datetime.timestamp())
                nueva_fecha_hora = timestamp  # Asigna el nuevo valor de fecha y hora
            except ValueError:
                await ctx.send("Formato de fecha y hora incorrecto o zona horaria no válida. La edición se cancelará.")
                return

        # Actualizar la información de la charla en la base de datos
        campos_actualizados = {}
        if nuevo_valor:
            campos_actualizados["nombre"] = nuevo_valor.content
        if nueva_descripcion:
            campos_actualizados["descripcion"] = nueva_descripcion.content
        if nueva_comunidad:
            campos_actualizados["comunidad"] = nueva_comunidad.content
        if nueva_imagen:
            campos_actualizados["imagen"] = nueva_imagen.content
        if nueva_fecha_hora:
            campos_actualizados["fecha_hora"] = nueva_fecha_hora

        db.charlas.update_one({"messageid": message_id}, {
            "$set": campos_actualizados
        })

        # Editar el mensaje de la charla en el canal de charlas-publicadas
        charlas_publicadas_channel = ctx.bot.get_channel(1067174322222936064)
        mensaje_charla = await charlas_publicadas_channel.fetch_message(message_id)

        # Construir el nuevo contenido del mensaje
        nuevo_contenido = f"{campos_actualizados.get('nombre', charla['nombre'])}\n--------------------------\n{campos_actualizados.get('descripcion', charla['descripcion'])}\n--------------------------\n🤝Comunidad: {campos_actualizados.get('comunidad', charla['comunidad'])}\n🗣️Ponente: {charla['ponente']}\n{campos_actualizados.get('imagen', charla['imagen'])}\nFecha y hora: <t:{campos_actualizados.get('fecha_hora', charla['fecha_hora'])}:F>"

        # Editar el mensaje con la nueva información
        await mensaje_charla.edit(content=nuevo_contenido)

        await ctx.send("Campos de la charla editados correctamente.")

    except Exception as e:
        await ctx.send(f"Se produjo un error: {str(e)}")

async def register_game(ctx: commands.Context):
    user_id = ctx.author.id                                                  
    try:
        #Preguntar por el nombre de la partida
        while True:
            await ctx.send("Ingrese el nombre de la partida:")
            nombre = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if nombre.content == ".cancelarregistro":
                return
            if nombre.content != ".registrarpartida":
                break
        #Preguntar por la descripcion de la partida
        while True:
            await ctx.send("Ingrese la descripcion de la partida(Síntesis, advertencias de contenido, etc):")
            descripcion = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if descripcion.content == ".cancelarregistro":
                return        
            if descripcion.content != ".registrarpartida":
                break
        #Preguntar por el sistema de la partida
        while True:
            await ctx.send("Ingrese el sistema de la partida:")
            sistema = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if sistema.content == ".cancelarregistro":
                return        
            if sistema.content != ".registrarpartida":
                break
        #Preguntar por la fecha y hora de la partida
        while True:
            await ctx.send("Ingrese la fecha y hora de la partida (formato: DD-MM-AAAA HH:MM): Ejemplo 25-12-2023 16:00")
            fecha_hora = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if fecha_hora.content == ".cancelarregistro":
                return        
            if fecha_hora.content != ".registrarpartida":
                try:
                    fecha_hora_datetime = datetime.datetime.strptime(fecha_hora.content, "%d-%m-%Y %H:%M")
                    # Pedir selección de zona horaria
                    await ctx.send("Ingrese la zona horaria de la partida (UTC-3, UTC-4, UTC-5, UTC-6):")
                    zona_horaria = await bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
                    # Obtener la diferencia en horas de la zona horaria seleccionada
                    diferencia_horas = {"UTC-3": 3, "UTC-4": 4, "UTC-5": 5, "UTC-6": 6}.get(zona_horaria.content.upper(), 0)
                    # Sumar la diferencia horaria a la fecha y hora ingresada
                    fecha_hora_datetime += datetime.timedelta(hours=diferencia_horas)                    
                    timestamp = int(fecha_hora_datetime.timestamp())
                    break
                except ValueError:
                    await ctx.send("Por favor ingrese la fecha y hora en el formato correcto.")
                    continue
        while True:
            await ctx.send("Ingrese cantidad de jugadorxs de la partida:")
            cantidadjugadores = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if cantidadjugadores.content == ".cancelarregistro":
                return        
            if cantidadjugadores.content != ".registrarpartida":
                try:
                    cantidadjugadores_num = int(cantidadjugadores.content)
                    if 2 <= cantidadjugadores_num <= 7:
                        break
                    else:
                        await ctx.send("Por favor ingrese un número entero entre 2 y 7.")
                        continue
                except ValueError:
                    await ctx.send("Por favor ingrese un número entero.")
                    continue
        while True:
            await ctx.send("Ingrese imagen de la partida(URL):")
            imagen = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if imagen.content == ".cancelarregistro":
                return        
            if imagen.content != ".registrarpartida":
                break
    except asyncio.TimeoutError:
        await ctx.send("Tiempo agotado, cancelando registro.") 
    except Exception as e:
        await ctx.send(f"Se produjo un error: {e}") 
    finally:
        # Esto se ejecutará después de que el registro termine, incluso si fue por una excepción o cancelación.
        user_registration_status[user_id] = False        
    #Crear Mensaje de la partida
    partidam = {
    "nombre": nombre.content,
    "descripcion": descripcion.content,
    "sistema": sistema.content,
    "master": ctx.message.author.mention,
    "fecha_hora": f"<t:{timestamp}:F>",
    "cantidadjugadores": cantidadjugadores.content,
    "lugaresdisponibles": cantidadjugadores_num,
    "imagen": imagen.content,
    }
    # Enviar información de la partida al canal de aprobaciones
    aprobaciones_channel = ctx.bot.get_channel(1064767112985456720)
    #partidas_publicadas_channel = ctx.client.get_channel(1064772442771435590)

    # Enviar la información de la partida al canal de aprobaciones
    mensaje = await aprobaciones_channel.send(f"Información de la partida:\n--------------------------")
    await mensaje.add_reaction("👍")
    await mensaje.add_reaction("👎")

    # Guardar la información de la partida en una variable
    partida_info = f'{partidam["nombre"]}\n--------------------------\n{partidam["descripcion"]}\n--------------------------\n🎲Sistema: {partidam["sistema"]}\n🧙Directorx de Juego: {partidam["master"]}\n🗓️Fecha y hora: {partidam["fecha_hora"]}\n🙋Cantidad de Jugadorxs: {partidam["cantidadjugadores"]}\n--------------------------\nLugares disponibles: {partidam["lugaresdisponibles"]}\n--------------------------\n¿Cómo me anoto?\nReacciona a esta publicación con 💪 para anotarte como titular y con 🔁 para anotarte como suplente.\n--------------------------\n{partidam["imagen"]}\n'

    # Añadir la información de la partida al mensaje enviado al canal de aprobaciones
    await mensaje.edit(content=mensaje.content + '\n' + partida_info)

    # Extraer el id del mensaje pendiente de aprobación
    aprobaciones_id = mensaje.id

    #Crear la partida
    partida = {
    "nombre": nombre.content,
    "descripcion": descripcion.content,
    "sistema": sistema.content,
    "master": ctx.message.author.mention,
    "fecha_hora": timestamp,
    "cantidadjugadores": cantidadjugadores_num,
    "lugares": cantidadjugadores_num,
    "imagen": imagen.content,
    "messageid": aprobaciones_id,
    "titulares": [],
    "suplentes": [],
    }
    #Insertar en la base de datos
    db.partidas.insert_one(partida)
    await ctx.send("¡Partida registrada correctamente! ✅, un moderador debe revisarla antes de publicarse en el canal de partidas-publicadas")


async def editar_partida(ctx: commands.Context, message_id: int):
    try:
        # Buscar la partida en la base de datos utilizando el message_id
        partida = db.partidas.find_one({"messageid": message_id})

        if not partida:
            await ctx.send("No se encontró ninguna partida con el messageid proporcionado.")
            return

        # Guardar los datos de Titulares y Suplentes antes de editar la partida
        titulares = partida.get('titulares', [])
        suplentes = partida.get('suplentes', [])

        # Solicitar qué campo desea editar
        await ctx.send("¿Qué campo deseas editar?\n1. Nombre\n2. Descripción\n3. Sistema\n4. Fecha y hora\n5. Cantidad de jugadores\n6. Imagen\nPor favor, responde con el número correspondiente.")
        campo_a_editar = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        if campo_a_editar.content == ".cancelarregistro":
            await ctx.send("Edición de partida cancelada.")
            return

        # Verificar la respuesta del usuario y solicitar el nuevo valor
        campo_a_editar = campo_a_editar.content.lower()
        nuevo_valor = None
        nueva_descripcion = None
        nuevo_sistema = None
        nueva_fecha_hora = partida['fecha_hora']  # Mantén el valor actual como predeterminado
        nueva_cantidad_jugadores = partida['cantidadjugadores']
        nueva_imagen = partida['imagen']

        if campo_a_editar == "1":
            await ctx.send("Ingrese el nuevo nombre de la partida:")
            nuevo_valor_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            nuevo_valor = nuevo_valor_message.content
        elif campo_a_editar == "2":
            await ctx.send("Ingrese la nueva descripción de la partida:")
            nueva_descripcion_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            nueva_descripcion = nueva_descripcion_message.content
        elif campo_a_editar == "3":
            await ctx.send("Ingrese el nuevo sistema de la partida:")
            nuevo_sistema_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            nuevo_sistema = nuevo_sistema_message.content
        elif campo_a_editar == "4":
            await ctx.send("Por favor, ingrese la nueva fecha y hora de la partida (formato: DD-MM-AAAA HH:MM):")
            fecha_hora_input_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            fecha_hora_input = fecha_hora_input_message.content
            if fecha_hora_input == ".cancelarregistro":
                await ctx.send("Edición de partida cancelada.")
                return
            try:
                fecha_hora_datetime = datetime.datetime.strptime(fecha_hora_input, "%d-%m-%Y %H:%M")
                # Pedir selección de zona horaria
                await ctx.send("Ingrese la zona horaria de la partida (UTC-3, UTC-4, UTC-5, UTC-6):")
                zona_horaria_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
                zona_horaria = zona_horaria_message.content
                if zona_horaria == ".cancelarregistro":
                    await ctx.send("Edición de partida cancelada.")
                    return
                # Obtener la diferencia en horas de la zona horaria seleccionada
                diferencia_horas = {"UTC-3": 3, "UTC-4": 4, "UTC-5": 5, "UTC-6": 6}.get(zona_horaria.upper(), 0)
                # Sumar la diferencia horaria a la fecha y hora ingresada
                fecha_hora_datetime += datetime.timedelta(hours=diferencia_horas)
                timestamp = int(fecha_hora_datetime.timestamp())
                nueva_fecha_hora = timestamp  # Asigna el nuevo valor de fecha y hora
            except ValueError:
                await ctx.send("Formato de fecha y hora incorrecto o zona horaria no válida. La edición se cancelará.")
                return
        elif campo_a_editar == "5":
            await ctx.send("Ingrese la nueva cantidad de jugadores de la partida (entre 2 y 7):")
            cantidad_jugadores_input_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            cantidad_jugadores_input = cantidad_jugadores_input_message.content
            try:
                nueva_cantidad_jugadores = int(cantidad_jugadores_input)
                if 2 <= nueva_cantidad_jugadores <= 7:
                    pass  # Valor válido
                else:
                    await ctx.send("Por favor ingrese un número entero entre 2 y 7.")
                    return
            except ValueError:
                await ctx.send("Por favor ingrese un número entero.")
                return
        elif campo_a_editar == "6":
            await ctx.send("Ingrese la nueva imagen de la partida (URL):")
            nueva_imagen_message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            nueva_imagen = nueva_imagen_message.content
        
        # Actualizar la información de la partida en la base de datos
        campos_actualizados = {}
        if nuevo_valor is not None:
            campos_actualizados["nombre"] = nuevo_valor
        if nueva_descripcion is not None:
            campos_actualizados["descripcion"] = nueva_descripcion
        if nuevo_sistema is not None:
            campos_actualizados["sistema"] = nuevo_sistema
        if nueva_fecha_hora is not None:
            campos_actualizados["fecha_hora"] = nueva_fecha_hora
        if nueva_cantidad_jugadores is not None:
            campos_actualizados["cantidadjugadores"] = nueva_cantidad_jugadores
        if nueva_imagen is not None:
            campos_actualizados["imagen"] = nueva_imagen

        # Vuelve a incluir los datos de Titulares y Suplentes en la actualización
        campos_actualizados["titulares"] = titulares
        campos_actualizados["suplentes"] = suplentes

        db.partidas.update_one({"messageid": message_id}, {
            "$set": campos_actualizados
        })

        # Editar el mensaje de la partida en el canal de aprobaciones
        aprobaciones_channel = ctx.bot.get_channel(1064772442771435590)
        mensaje_partida = await aprobaciones_channel.fetch_message(message_id)

        # Construir el nuevo contenido del mensaje
        nuevo_contenido = f"{campos_actualizados.get('nombre', partida['nombre'])}\n--------------------------\n{campos_actualizados.get('descripcion', partida['descripcion'])}\n--------------------------\n🎲Sistema: {campos_actualizados.get('sistema', partida['sistema'])}\n🧙Directorx de Juego: {partida['master']}\n🗓️Fecha y hora: <t:{campos_actualizados.get('fecha_hora', partida['fecha_hora'])}:F>\n🙋Cantidad de Jugadorxs: {campos_actualizados.get('cantidadjugadores', partida['cantidadjugadores'])}\n--------------------------\nLugares disponibles: {campos_actualizados.get('cantidadjugadores', partida['cantidadjugadores'])}\n--------------------------\n¿Cómo me anoto?\nReacciona a esta publicación con 💪 para anotarte como titular y con 🔁 para anotarte como suplente."
        
        # Agregar la imagen al contenido si está disponible
        if campos_actualizados.get('imagen'):
            nuevo_contenido += f"\n--------------------------\n{campos_actualizados['imagen']}"

        # Agregar los datos de Titulares y Suplentes nuevamente al mensaje
        nuevo_contenido += f"\nTitulares 💪: {' | '.join(titulares)}" if titulares else ""
        nuevo_contenido += f"\nSuplentes 🔁: {' | '.join(suplentes)}" if suplentes else ""

        # Editar el mensaje con el nuevo contenido
        await mensaje_partida.edit(content=nuevo_contenido)

        await ctx.send("Campos de la partida editados correctamente.")

    except Exception as e:
        await ctx.send(f"Se produjo un error: {str(e)}")


async def register_talk(ctx: commands.Context):
    user_id = ctx.author.id                                                 
    try:
        #Preguntar por el nombre de la charla
        while True:
            await ctx.send("Ingrese el nombre de la charla:")
            nombre = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if nombre.content == ".cancelarregistro":
                return
            if nombre.content != ".registrarcharla":
                break
        #Preguntar por la descripcion de la charla
        while True:
            await ctx.send("Ingrese la descripcion de la charla:")
            descripcion = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if descripcion.content == ".cancelarregistro":
                return        
            if descripcion.content != ".registrarcharla":
                break
        while True:
            await ctx.send("Ingrese la comunidad representante (Red Social de preferencia o Sitio web):")
            comunidad = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if comunidad.content == ".cancelarregistro":
                return        
            if comunidad.content != ".registrarcharla":
                break    
        while True:
            await ctx.send("Ingrese imagen de la charla(URL):")
            imagen = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
            if imagen.content == ".cancelarregistro":
                return        
            if imagen.content != ".registrarcharla":
                break
    except asyncio.TimeoutError:
        await ctx.send("Tiempo agotado, cancelando registro.") 
    except Exception as e:
        await ctx.send(f"Se produjo un error: {e}") 
    finally:
        # Esto se ejecutará después de que el registro termine, incluso si fue por una excepción o cancelación.
        user_registration_status[user_id] = False
    #Crear Mensaje de la charla
    charlam = {
    "nombre": nombre.content,
    "descripcion": descripcion.content,
    "comunidad": comunidad.content,
    "ponente": ctx.message.author.mention,
    "imagen": imagen.content,
    }
    # Enviar información de la partida al canal de aprobaciones
    aprobaciones_charlas_channel = ctx.bot.get_channel(1067164468066386072)
    #partidas_publicadas_channel = ctx.client.get_channel(1064772442771435590)

    # Enviar la información de la partida al canal de aprobaciones
    mensaje = await aprobaciones_charlas_channel.send(f"Información de la charla:\n--------------------------")
    await mensaje.add_reaction("👍")
    await mensaje.add_reaction("👎")

    # Guardar la información de la partida en una variable
    charla_info = f'{charlam["nombre"]}\n--------------------------\n{charlam["descripcion"]}\n--------------------------\n🤝Comunidad: {charlam["comunidad"]}\n🗣️Ponente: {charlam["ponente"]}\n{charlam["imagen"]}\n'

    # Añadir la información de la partida al mensaje enviado al canal de aprobaciones
    await mensaje.edit(content=mensaje.content + '\n' + charla_info)

    # Extraer el id del mensaje pendiente de aprobación
    aprobaciones_id = mensaje.id

    #Crear la charla
    charla = {
    "nombre": nombre.content,
    "descripcion": descripcion.content,
    "ponente": str(ctx.message.author),
    "comunidad": comunidad.content,
    "imagen": imagen.content,
    "messageid": aprobaciones_id,
    }
    #Insertar en la base de datos
    db.charlas.insert_one(charla)
    await ctx.send("¡Charla registrada correctamente! ✅, un moderador debe revisarla antes de publicarse en el canal de charlas-publicadas")


async def edit_message_players(message, player, role):
    content = message.content
    partida = db.partidas.find_one({"messageid": message.id})
    lugares = partida["lugares"]
    lines = content.split("\n") # Divide el contenido en líneas
    role_line = None
    for line in lines:
        if role in line: # Si la línea contiene la palabra "role"
            role_line = line
            break
        if "Lugares disponibles:" in line:
            lines[lines.index(line)] = f"Lugares disponibles: {lugares}"
    if role_line:
        try:
            players = role_line.split(": ")[1] # Obtiene los jugadores actuales
        except IndexError:
            players= ""
        if player.mention not in players: # Si el jugador no está ya registrado
            players += f", {player.mention}" # Agrega al jugador a la lista
            lines[lines.index(role_line)] = f"{role}: {players}" # Reemplaza la línea en la lista de líneas
    else:
        lines.append(f"{role}: {player.mention}") # Si no hay línea, agrega una nueva
    content = "\n".join(lines) # Junta todas las líneas en un solo string
    await message.edit(content=content)

async def remove_player(message, player, role):
    content = message.content
    partida = db.partidas.find_one({"messageid": message.id})
    lugares = partida["lugares"]
    lines = content.split("\n") # Divide el contenido en líneas
    role_line = None
    for line in lines:
        if role in line: # Si la línea contiene la palabra "role"
            role_line = line
            break
        if "Lugares disponibles:" in line:
            lines[lines.index(line)] = f"Lugares disponibles: {lugares}"
    if role_line:
        try:
            players = role_line.split(": ")[1]
        except IndexError:
            players = ""
        # Obtiene los jugadores actuales
        if player.mention in players:
            players_list = [p.strip() for p in players.split(",")]  # Divide los jugadores actuales
            players_list.remove(player.mention)  # Elimina al jugador
            players = ", ".join(players_list)  # Reconstruye la lista de jugadores
            lines[lines.index(role_line)] = f"{role}: {players}" # Reemplaza la línea en la lista de líneas
            # Actualiza las listas de jugadores en la base de datos
            if role == "Titulares 💪":
                db.partidas.update_one({"messageid": message.id}, {"$pull": {"titulares": player.mention}})
            elif role == "Suplentes 🔁":
                db.partidas.update_one({"messageid": message.id}, {"$pull": {"suplentes": player.mention}})
    content = "\n".join(lines) # Junta todas las líneas en un solo string
    await message.edit(content=content)



#############COMANDOS##############
@bot.event
async def on_ready():
    print ("Iniciando Comandos")
    try:
        synced = await bot.tree.sync()
        print (f"Synced {len(synced)} command(s)")
    except Exception as e:
        print (e) 

@bot.event
async def on_message(message):
    if not message.content.startswith(bot.command_prefix):
        response, pv = handle_response(message.content)
        if response:
            try:
                if pv:
                    await message.author.send(response)
                else:
                    await message.channel.send(response)
            except discord.errors.HTTPException as e:
                if e.status == 400 and e.code == 50035:
                    await message.channel.send("El mensaje es demasiado largo para enviarlo al canal.")
                else:
                    raise e
    else:
        await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    user = bot.get_user(payload.user_id)
    now = asyncio.get_event_loop().time()
    if user.id == bot.user.id:
        return
    elif user.id in last_reaction_time and now - last_reaction_time[user.id] < 2:
        await message.remove_reaction(payload.emoji, user)
        await user.send("Por favor, no reacciones a los mensajes tan rápido")
    else:
        last_reaction_time[user.id] = now
    if message.channel.id == 1064767112985456720:
        partidas_publicadas_channel = bot.get_channel(1064772442771435590)
        user = bot.get_user(payload.user_id)
        if user.id == bot.user.id:
            return
        if payload.emoji.name == "👍":
            msg = await partidas_publicadas_channel.send(message.content)    
            await msg.add_reaction("💪")
            await msg.add_reaction("🔁")
            db.partidas.update_one({"messageid": message.id}, {"$set": {"messageid": msg.id}})
            await message.delete()
        elif payload.emoji.name == "👎":
            await message.delete()
            db.partidas.delete_one({"messageid": message.id})
    elif message.channel.id == 1064772442771435590:
        user = bot.get_user(payload.user_id)
        if user.id == bot.user.id:
            return
        partida = db.partidas.find_one({"messageid": message.id})
        lugares = partida["lugares"]   
        if user.id == bot.user.id:
            return
        if user.mention in partida["titulares"] or user.mention in partida["suplentes"] or user.name in partida["master"]:
            await user.send("Ya estás anotado a esta partida.")
            await message.remove_reaction(payload.emoji, user)
        else:
            if lugares != 0:
                if payload.emoji.name == "💪":
                    db.partidas.update_one({"messageid": message.id}, {"$push": {"titulares": user.mention}})
                    db.partidas.update_one({"messageid": message.id}, {"$inc": {"lugares": -1}})
                    await edit_message_players(message, user, "Titulares 💪")
                if payload.emoji.name == "🔁":
                    await edit_message_players(message, user, "Suplentes 🔁")
                    db.partidas.update_one({"messageid": message.id}, {"$push": {"suplentes": user.mention}})
            elif lugares == 0:
                if payload.emoji.name == "💪":
                    await message.remove_reaction(payload.emoji, user)
                    await user.send("¡No hay lugares disponibles en la partida, puedes anotarte como suplente!🔁")
                if payload.emoji.name == "🔁":
                    await edit_message_players(message, user, "Suplentes 🔁")
                    db.partidas.update_one({"messageid": message.id}, {"$push": {"suplentes": user.mention}})    
    elif message.channel.id == 1067164468066386072:
        charlas_publicadas_channel = bot.get_channel(1067174322222936064)
        user = bot.get_user(payload.user_id)
        if user.id == bot.user.id:
            return
        if payload.emoji.name == "👍":
            await talk_time(payload)
            msg = await charlas_publicadas_channel.send(message.content)
            charla = db.charlas.find_one({"messageid": message.id})
            # Obtener el timezone correspondiente según el país seleccionado
            time = charla["fecha_hora"]
            # Aplicar el timezone a la fecha y hora obtenida
            msg.content += f"\nFecha y hora: <t:{time}:F>"
            await msg.edit(content=msg.content)
            db.charlas.update_one({"messageid": message.id}, {"$set": {"messageid": msg.id}})
            await message.delete()
        elif payload.emoji.name == "👎":
            await message.delete()
            db.charlas.delete_one({"messageid": message.id})

@bot.event
async def on_raw_reaction_remove(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if message.channel.id == 1064772442771435590:
        user = bot.get_user(payload.user_id)
        if user.id == bot.user.id:
            return
        if payload.emoji.name == "💪":
            match = db.partidas.find_one({"messageid": message.id, "titulares": user.mention})
            if match:
                db.partidas.update_one({"messageid": message.id}, {"$pull": {"titulares": user.mention}})
                db.partidas.update_one({"messageid": message.id}, {"$inc": {"lugares": +1}})
                await remove_player(message, user, "Titulares 💪")
        if payload.emoji.name == "🔁":
            match = db.partidas.find_one({"messageid": message.id, "suplentes": user.mention})
            if match:
                await remove_player(message, user, "Suplentes 🔁")
                db.partidas.update_one({"messageid": message.id}, {"$pull": {"suplentes": user.mention}})

@bot.tree.command(name="comandos", description=f"Comandos del bot")
async def Ayudin(interaction: discord.Interaction):
    await interaction.response.send_message(f"`.registrarpartida` Para registrar una partida en el Carnaval Rolero {year}\n`.registrarcharla` Para registrar una charla en el Carnaval Rolero {year}\n `roll (dado)d(número)+-(modificador)` Puedes tirar dados con este bot en cualquier canal sin necesidad de prefijo. Ejemplo: `roll 1d20+3`, o `pv roll d20+1`. (tirada privada)", ephemeral=True)    

@bot.tree.command(name="ayudaregistro", description=f"Como registrar una partida o charla en el Carnaval Rolero {year}")
async def Ayudin(interaction: discord.Interaction):
    await interaction.response.send_message(f"¡Hola {interaction.user.mention}! para registrar una partida puedes mandarme el comando `.registrarpartida` y seguir los pasos que te indicaré, ten en cuenta que antes de aparecer en el canal de partidas-publicadas **debe aprobarla un moderador**. Para registrar una charla puedes mandarme el comando `.registrarcharla`, en este caso antes de aparecer en el canal de **charlas-publicadas** debe pasar por un proceso de revisión, luego un moderador se comunicara contigo para arreglar la fecha y hora en la que darás la charla (en caso de ser aprobada)", ephemeral=True)

@bot.command(name="registrarpartida", description="Registrá una partida en el Carnaval Rolero!")
async def register_game_cmd(ctx):
    user_id = ctx.author.id  # Obtén el ID del autor del mensaje.

    if user_registration_status[user_id]:
        # El usuario ya está en un proceso de registro; no iniciar uno nuevo.
        await ctx.send("Ya estás en un proceso de registro. Por favor, espera a que finalice.")
        return

    # Si llegamos aquí, el usuario no está en un proceso de registro.
    if ctx.guild is None:  # Si el comando se usa en un mensaje directo.
        # Intente iniciar el proceso de registro.
        try:
            # Marca al usuario como en proceso de registro.
            user_registration_status[user_id] = True

            # Inicia el proceso de registro.
            await register_game(ctx)
        except Exception as e:
            # Si hay un error, informa al usuario.
            await ctx.send(f"Se produjo un error: {e}")
        finally:
            # Después de intentar registrar (independientemente de si fue exitoso), resetea el estado de registro del usuario.
            user_registration_status[user_id] = False
    else:
        await ctx.send("Este comando solo puede ser utilizado en una conversación privada con el bot.", ephemeral=True)

@bot.command(name="editcharla", description="Editar una charla existente.")
async def edit_charla_cmd(ctx: commands.Context):
    await ctx.send("Por favor, proporciona el ID del mensaje de la charla que deseas editar.")
    try:
        message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        if message.content == ".cancelarregistro":
            await ctx.send("Edición de charla cancelada.")
            return
        message_id = int(message.content)
        await editar_charla(ctx, message_id)
    except asyncio.TimeoutError:
        await ctx.send("Tiempo agotado, cancelando la edición de charla.")
    except ValueError:
        await ctx.send("El ID del mensaje debe ser un número válido.")

@bot.command(name="editpartida", description="Editar una partida existente.")
async def edit_partida_cmd(ctx: commands.Context):
    await ctx.send("Por favor, proporciona el ID del mensaje de la partida que deseas editar.")
    try:
        message = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.message.author, timeout=300)
        if message.content == ".cancelarregistro":
            await ctx.send("Edición de partida cancelada.")
            return
        message_id = int(message.content)  # Convierte el contenido del mensaje en un entero
        await editar_partida(ctx, message_id)  # Llama a la función para editar la partida
    except ValueError:
        await ctx.send("ID de mensaje no válido. La edición de partida se cancelará.")


async def register_talk_cmd(ctx):
    user_id = ctx.author.id  # Obtén el ID del autor del mensaje.
    # Comprobar si el usuario ya está en un proceso de registro.
    if user_registration_status[user_id]:
        # El usuario ya está en un proceso de registro; no iniciar uno nuevo.
        await ctx.send("Ya estás en un proceso de registro. Por favor, espera a que finalice.")
        return
    # Si llegamos aquí, el usuario no está en un proceso de registro.
    if ctx.guild is None:  # Si el comando se usa en un mensaje directo.
        user_registration_status[user_id] = True  # Marca al usuario como en proceso de registro.
        try:
            # Aquí iría tu lógica actual para registrar una charla.
            await register_talk(ctx)
        except Exception as e:
            # Si hay un error, informa al usuario.
            await ctx.send(f"Se produjo un error: {e}")
        finally:
            # Después de intentar registrar (independientemente de si fue exitoso), resetea el estado de registro del usuario.
            user_registration_status[user_id] = False
    else:
        # Si el comando no se usó en un DM, informa al usuario que debe hacerlo.
        await ctx.send("Este comando solo puede ser utilizado en una conversación privada con el bot.", ephemeral=True)

@bot.command(name="cancelarregistro", description="Cancela el registro de una partida en el Carnaval Rolero.")
async def cancel_register_game(ctx):
    if ctx.guild is None:
        global is_registering
        is_registering = False
        await ctx.send("Registro de partida/charla cancelado.")
    else:
        await ctx.send("Este comando solo puede ser utilizado en una conversación privada con el bot.", ephemeral=True)   

@bot.command()
async def sincronizar(ctx):
    await bot.tree.sync()
    await ctx.send("Sincronizado!")

bot.run(TOKEN)

# https://discord.com/api/oauth2/authorize?client_id=1064659903710511124&permissions=8&scope=bot