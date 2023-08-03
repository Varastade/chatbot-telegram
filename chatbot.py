import random
import json
import pickle
import numpy as np
from telebot import types
from datetime import date
import spacy
from keras.models import load_model
import telebot
import os

#Or implement your .env parser
def read_env_file(file_path):
    env_vars = {}

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

# CAMBIAR
VARIABLES = read_env_file(".env")
CHAT_ID =   int(VARIABLES["CHAT_ID"]) #specific chat id
API_KEY = VARIABLES["API_KEY"]
VERIFY_CHAT = False

bot = telebot.TeleBot(API_KEY)

# Funciones para predicciones y el lemmatizer__________________
def clean_up_sentence(sentence):
    """Lemmatizer de una oracion (para los mensajes)"""
    token_sentence = nlp(sentence)

    sentence_words = []

    for token in token_sentence:

        sentence_words.append(token.lemma_.lower())

    return sentence_words


def bag_of_words(sentence):
    """Retorna el BoW de las palabras utilizadas en la oración"""
    sentence_words = clean_up_sentence(sentence)

    bag = [0] * len(words)

    for w in sentence_words:

        for i, word in enumerate(words):

            if word == w:

                bag[i] = 1

    return np.array(bag)


def predict_class(sentence):
    ''' A partir de la oración, usa el modelo para retornar la lista de las probabilidades'''

    bow = bag_of_words(sentence)

    res = model_global.predict(np.array([bow]))[0]

    ERROR_THRESHOLD = 0.25

    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)

    return_list = []

    for r in results:

        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})

    return return_list


def get_response(intents_list, intents_json):

    tag = intents_list[0]["intent"]

    list_of_intents = intents_json["intents"]

    for i in list_of_intents:

        if i["tag"] == tag:

            result = random.choice(i["responses"])

            break

    return result


# ____________________________


# Funcione adicionales________________________________________________


def get_respuesta_edad(respuesta):
    """Manejador de repuestas con fechas"""
    today = date.today()

    bd = date(2023, 8, 2)

    delta = today - bd

    calc_edad = -1

    if respuesta == "dias":

        calc_edad = delta.days

    elif respuesta == "años":

        calc_edad = delta.days // 365

    elif respuesta == "nextbd":

        delta1 = date(today.year, bd.month, bd.day)

        delta2 = date(today.year + 1, bd.month, bd.day)

        calc_edad = ((delta1 if delta1 > today else delta2) - today).days

    return calc_edad


# TELEGRAM CHATBOT __________________________________________________


def verify_chat(message):
    """Verificador de seguridad para las funciones del telebot, añadir usuarios al array"""

    authorized_users = ["jaram360"]

    if message.from_user.username in authorized_users or message.chat.id == CHAT_ID:

        return True

    else:

        return False


@bot.message_handler(func=verify_chat, commands=["start"])
def start(message):

    if verify_chat(message):

        bot.reply_to(message, "Chat Verificado")

    else:

        bot.reply_to(message, "Chat no autorizado para usar el bot")


@bot.message_handler(func=verify_chat, commands=["help", "ayuda"])
def help(message):

    bot.send_message(
        message.chat.id,
        """
Holii estas hablando con el bot creado por @user.
Para ver la lista de comandos disponibles puedes enviar /listar o puedes intentar enviar un mensaje e intentare responderte.
(Todavia esoy en desarrollo pero haré lo posible \U0001F60A)
""",
    )


# Maneja los comandos para las listas de entretenimiento
@bot.message_handler(func=verify_chat, commands=["peliculas", "series", "musica"])
def peliculas(message):

    mensaje = message.text.split(" ")
    media_type = mensaje[0].strip("/")

    if len(mensaje) == 2:

        bot.send_message(
            message.chat.id, "Necesito más información de lo que quieres añadir/remover"
        )

    if len(mensaje) > 2:

        if mensaje[1] == "add":

            titulo = " ".join(mensaje[2:])
            
            titulo = titulo.title()

            media[media_type].append(titulo)

            respuesta = "'" + titulo + "' añadida a la lista\n--Peliculas En Lista--\n"

            lista = "\n".join(media[media_type])

            bot.send_message(message.chat.id, respuesta + lista)

            json_object = json.dumps(media, indent=len(media))

            with open("media.json", "w") as outfile:

                outfile.write(json_object)

        elif mensaje[1] == "remove":

            titulo = " ".join(mensaje[2:])

            titulo = titulo.title()

            print(titulo)

            if titulo in media[media_type]:

                media[media_type].remove(titulo.title())

                respuesta = "'" + titulo + "' eliminada de la lista\n"

                lista = " - ".join(media[media_type])

                bot.send_message(message.chat.id, respuesta + lista)

                json_object = json.dumps(media, indent=len(media))

                with open("media.json", "w") as outfile:

                    outfile.write(json_object)
            else:

                bot.send_message(
                    message.chat.id, "No encontre ese titulo, vuelve a intentarlo"
                )

    else:
        respuesta = media_type + " en la lista \n"

        lista = "\n".join(media[media_type])

        bot.send_message(message.chat.id, respuesta.title() + lista.title())


@bot.message_handler(func=verify_chat, commands=["edad"])
def resp_edad(message):

    mensaje = message.text.split(" ")

    respuesta = "Sorry, no encontre esa opción "

    if len(mensaje) > 1:

        opt = mensaje[1]

        bd = get_respuesta_edad(opt)

        if opt == "nextbd":

            respuesta = "Faltan " + str(bd) + " dias para mi siguiente cumpleaños!"
        
        if opt == "dias" or opt == "años":
            respuesta = "Yo tengo " + str(bd)+ " " + opt + " de edad "

    else:
        respuesta = "Yo tengo " + str(get_respuesta_edad("años"))+ " años de edad"

    bot.send_message(message.chat.id, respuesta)


def get_quiz_dictionary(indice):

    dic_trivia = data["trivia"][indice]

    return dic_trivia


def get_markup(indice):

    dic_quiz = get_quiz_dictionary(indice)

    markup = types.InlineKeyboardMarkup(row_width=1)

    # Buttons
    bt1 = types.InlineKeyboardButton(
        dic_quiz["options"][0], callback_data="0" + str(indice)
    )

    bt2 = types.InlineKeyboardButton(
        dic_quiz["options"][1], callback_data="1" + str(indice)
    )

    bt3 = types.InlineKeyboardButton(
        dic_quiz["options"][2], callback_data="2" + str(indice)
    )

    bt4 = types.InlineKeyboardButton(
        dic_quiz["options"][3], callback_data="3" + str(indice)
    )

    markup.add(bt1, bt2, bt3, bt4)

    return markup


@bot.message_handler(func=verify_chat, commands=["quiz"])
def quiz(message):

    mensaje = message.text.split(" ")

    if len(mensaje) > 1:

        try:

            indice = int(mensaje[1]) - 1

        except:

            bot.send_message(
                message.chat.id, "No pude encontrar ese numero de pregunta, hay 7"
            )

            return

    else:

        indice = random.randint(0, len(data["trivia"]) - 1)

    dict_quiz = get_quiz_dictionary(indice)

    bot.send_message(
        message.chat.id, dict_quiz["question"], reply_markup=get_markup(indice)
    )


@bot.callback_query_handler(func=lambda call: True)
def escoger_quiz(call):

    respuesta = int(call.data[0])

    dic_quiz = data["trivia"][int(call.data[1:])]

    if call.message:

        if respuesta == dic_quiz["correct_id"]:

            if int(call.data[1:]) == 0:

                date_inicio = date.today() - date(2016, 7, 12)

                bot.edit_message_text(
                    dic_quiz["correcto"] + str(date_inicio.days),
                    call.message.chat.id,
                    call.message.id,
                    parse_mode="Markdown",
                )
            else:

                bot.edit_message_text(
                    dic_quiz["correcto"],
                    call.message.chat.id,
                    call.message.id,
                    parse_mode="Markdown",
                )

        else:

            bot.edit_message_text(
                dic_quiz["incorrecto"],
                call.message.chat.id,
                call.message.id,
                parse_mode="Markdown",
            )


@bot.message_handler(func=verify_chat, commands=["wp", "wallpaper"])
def wallpaper(message):
    """Metodo para el bot que envia el wp de Whatsapp del 2021 """
    bot.send_message(message.chat.id, "Dame un ratito y lo busco...")

    bot.send_chat_action(message.chat.id, "upload_photo")

    photo = open("images/Planets3.png", "rb")

    bot.send_photo(message.chat.id, photo, "Dibujo del 2021 ")



@bot.message_handler(func=verify_chat, commands=["respondmsg"])
def respondmsg(message):
    """Metodo para apagar las respuestas automaticas del bot"""

    mensaje = message.text.split(" ")

    if len(mensaje) == 1:

        bot.send_message(message.chat.id, "Necesito saber si quieres que envie o no un mensaje ('si' o 'no')")

    elif mensaje[1].lower() == "si":

        responde_mensajes[0] = True

        bot.send_message(message.chat.id, "El bot respondera a todos los mensajes")

    elif mensaje[1].lower() == "no":

        responde_mensajes[0] = False

        bot.send_message(message.chat.id, "El bot solo respondera a los comandos")

    else:

        bot.send_message(message.chat.id, "Utiliza un 'si' o 'no' despues del comando")

@bot.message_handler(func=verify_chat, commands=["listar"])
def listar(message):
    """Lista todos los comandos que puede hacer el bot con sus variantes entre corchetes"""
    comandos = [
        "/help",
        "/edad [nextbd]",
        "/wp, /wallpaper",
        "/quiz [#pregunta]",
        "/peliculas [add,remove]",
        "/series [add,remove]",
        "/musica [add,remove]",
        "/respondmsg [si,no]"
    ]

    mensaje = "--Lista de comandos--\n"

    mensaje = mensaje + "\n ".join(comandos)

    bot.send_message(message.chat.id, mensaje)




@bot.message_handler(
    func=lambda message: verify_chat(message) and message.text is not None
)
def procesar_mensaje_texto(message):
    """Procesa todos los mensajes de texto enviados al bot """
    msg = message.text + " " + message.text

    ints = predict_class(msg)

    res = get_response(ints, intents)

    intent = ints[0]["intent"]

    if responde_mensajes[0]:
        
        if intent == "querer":

            bot.reply_to(message, res)

        else:

            bot.send_message(message.chat.id, res)

if __name__ == "__main__":

    nlp = spacy.load("es_core_news_md")

    classes = pickle.load(open("classes.pkl", "rb"))

    words = pickle.load(open("words.pkl", "rb"))

    intents = json.loads(open("intents.json", encoding="utf-8").read())

    data = json.loads(open("data.json", encoding="utf-8").read())

    media = json.loads(open("media.json", encoding="utf-8").read())

    model_global = load_model("chatbotmodel.h5")

    responde_mensajes = [True]

    # CAMBIAR
    print("Bot running")

    bot.infinity_polling()
