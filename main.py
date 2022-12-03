import random
import sys
from functools import partial
from telegram import Poll, Update, InlineKeyboardButton, \
    InlineKeyboardMarkup, Bot
import pymysql.cursors
from datetime import datetime, timedelta
from utente import Utente
import livelli as liv
import Costanti as api
from telegram.ext import *
from telegram.ext import ApplicationBuilder, CommandHandler, filters


partecipanti = []
bot = Bot(api.API_KEY)
USER = api.USER
PASSWORD = api.PASSWORD


async def start_command(update: Update, context) -> None:
    await update.message.reply_text('Ciao! benvenuto sul bot! \n'
                                    'Iniziamo direttamente con i comandi\n'
                                    '/start ti permette di vedere questo messaggio\n'
                                        '/add NOME COGNOME ti permette di modificare il tuo nome'
                                    '(Es. /add Fabio Siepe\n'
                                    "* NEL CASO DI PIù NOMI INSEIRE SOLO IL PRIMO\n"
                                    "* NEL CASO DI COGNOMI COMPOSTI INSERIRLI ATTACCATI\n"
                                    "    Es. Della Rocca diventa DellaRocca\n"
                                    '/classi per vedere la lista delle classi a cui puoi accedere\n'
                                    '/info per vedere le tue informazioni(punti - livello - esperienza)\n'
                                    '/info_bot per sapere come funziona il gioco')
    await aggiungi_command(update, context)
    print("Chat id: " + str(update.message.chat_id))


async def aggiungi_command(update, context):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    if await aggiungi_utente(connection, update.message.from_user.id, update.message.from_user.first_name):
        await update.message.reply_text("Ciao "+str(update.message.from_user.first_name)+" fai /add per cambiare nome.\n "
                                                               "Ti ricordo che per farlo devi scrivere\n"
                                                               "    /add NOME COGNOME\n"
                                                               "* NEL CASO DI PIù NOMI INSEIRE SOLO IL PRIMO\n"
                                                               "* NEL CASO DI COGNOMI COMPOSTI INSERIRLI ATTACCATI\n"
                                                               "    Es. Della Rocca diventa DellaRocca\n")
        print(update.message.from_user.first_name +" Aggiunto")
    else:
        await update.message.reply_text(text=update.message.from_user.first_name + " già aggiunto")
        print(update.message.from_user.first_name + " Errore Aggiunto/Gia inserito")
    connection.cursor().close()
    if connection.open:
        connection.close()


async def aggiungi_utente(connection, id_telegram, nome):
    connection.ping()
    with connection:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `utenti` (`id_telegram`, `nome`, `punti`, `livello`, `esperienza`) VALUES (%s, %s, %s, %s, %s)"
            try:
                cursor.execute(sql, (str(id_telegram),
                                     str(nome),
                                     int(0),
                                     int(0),
                                     int(0)))

                connection.commit()
            except Exception:
                return False
    return True


async def aggiorna_utente_command(update, context):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        nome = context.args[0] + " " + context.args[1]
        connection.ping()
        with connection:
            with connection.cursor() as cursor:
                sql = "UPDATE utenti SET `nome`=%s  WHERE `id_telegram`=%s"
                cursor.execute(sql, (nome, update.message.from_user.id))

            connection.commit()
        await bot.send_message(text=("Nuovo nome inserito correttamente!\n /info per controllarlo"), chat_id=update.message.chat_id)
        print(nome + " Aggiornato")
    except IndexError:
        await bot.send_message(text=("Errore nell'inseimento "
                                     "\nRIcordati di che devi scrivere NOME COGNOME"), chat_id=update.message.chat_id)
        print(update.message.from_user.first_name +": "+ str(update.message.from_user.id) + " Errore aggiornamento/ Campi vuoti")
    except Exception:
        await bot.send_message(text=("Errore nell'inseimento \nRi controlla il nome che hai inserito e ri prova"), chat_id=update.message.chat_id)
        print(nome + " Errore aggiornamento/ Campi errati")


async def classi_command(update, context):
    testo = ('Queste sono le classi disponibili \n'
             'Clicca sul nome di una classe per aggiungerti.\n')
    keyboard = [
        [
            InlineKeyboardButton(text="DEMO CLASSE", url="https://t.me/+ssqLbXY0s985NjY0"),
            InlineKeyboardButton(text="DEMO CLASSE2", url="https://t.me/+7fdL14_YpMtkZWQ8"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text=testo, reply_markup=reply_markup)
    print(update.message.from_user.first_name + " " + str(update.message.from_user.id)+ " Classi")

async def info_command(update, context):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    utente = await cerca_utente(connection, update.message.from_user.id)
    info = utente.nome + ": \n" + "\nPunti: " + str(utente.punti) + "\nLivello: " + str(utente.livello) + "\nEsperienza: " + str(utente.esperienza)
    await update.message.reply_text(info)
    print(utente.nome+" info")
    if connection.open:
        connection.close()


async def info_bot_command(update, context):
    info = ('\nIl gioco funziona in modo molto semplice:\n'
            'Rispondi alle domande per ottenere punti ed esperienza\n'
            'Più risposte giuste di fila aumentano i punti ottenuti\n'
            'Con i punti potrai scalare la classifica\n'
            'Con esperienza otterai nuovi potenziamenti utilizzabili\n'
            'durante i quiz\n'
            'Ci sono due potenziamenti:\n'
            '❌*Doppi punti*: Ti permettono di ricevere doppi punti sulla domanda\n'
            '  *che la risposta sia giusta o no :) *\n'
            'Quando utilizzato apparirà un messggio in alto\n'
            '🔢*50/50*: ti aprirà un messaggio con due numeri\n'
            '    Es. 3 || 1 \n'
            '    La risposta giusta è la 1ª o la 3ª\n'
            'I POTENZIAMENTI POSSONO ESSERE UTILIZZATI CIASCUNO UNA SOLA VOLTA PER QUIZ\n')

    await update.message.reply_text(info, parse_mode='Markdown')
    print(update.message.from_user.first_name+" info_bot")


async def cerca_utente(connection, id_telegram):
    with connection:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `utenti` WHERE `id_telegram`=%s"
            cursor.execute(sql, (id_telegram))
        connection.commit()
        utente = cursor.fetchone()
        r_utente = Utente(utente["id_telegram"], utente["nome"], utente["punti"], utente["livello"], utente["esperienza"])
        return r_utente


async def test_command(update, context) -> None:
    id = 5709534695
    print("Grandezza: " + str(sys.getsizeof(context.bot_data)))
    for n in range (1, 310):
        payload = {

            id: {  "Nome":"prova", "Punti":random.randint(-10,50), "pot1D": True, "pot1U": False,
                                                 "pot2D": True, "pot2U": False,
                                                 }

        }
        #40 bytes
        payload2 = {
            id*2: {"chat_id": update.effective_chat.id, "message_id": 5000000,
                              "correctOption": 10, "inizio": datetime.now(),
                              "durata": 10}
        }
        context.bot_data.update(payload)
        context.bot_data.update(payload2)
        partecipanti.append(id)
        print(str(n) + " Grandezza P1: " + str(sys.getsizeof(context.bot_data[id])))
        print(str(n) + " Grandezza P2: " + str(sys.getsizeof(context.bot_data[id*2])))
        id = id +1
    print("Grandezza: " + str(sys.getsizeof(context.bot_data)))
    id = id -1
    for i in range (1, 900):
        #print(context.bot_data[id])
        #print(context.bot_data[id*2])
        if id % 3 == 0:
            id = id -1
    print("pre connection")
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    print("post connection")
    for x in range (1, 500):
        connection.ping()
        with connection:
            with connection.cursor() as cursor:
                sql = "INSERT INTO `utenti` (`id_telegram`, `nome`, `punti`, `livello`, `esperienza`) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (x,
                                     "prova",
                                     int(0),
                                     int(0),
                                     int(0)))

                connection.commit()
    print("post insert")
    for y in range(1, 500):
        connection.ping()
        with connection:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT * FROM `utenti` WHERE `id_telegram`=%s"
                cursor.execute(sql, y)
            connection.commit()
            utente = cursor.fetchone()
            r_utente = Utente(utente["id_telegram"], utente["nome"], utente["punti"], utente["livello"], utente["esperienza"])
        #print(r_utente.id_telegram + " " + r_utente.nome)

    print("Chat id: "+str(update.message.chat_id))


async def quiz(update, context):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    #memoria svuotata all'inizio e alla fine di ogni quiz perche se si utilizzano i potenziamenti dopo che il quiz è finito
    #viene salvato in memoria che sono stati utilizzati e non sono disponibili per il prossimo
    await svuota_memoria(context)
    gruppo = context.args[0]
    if gruppo == "demo1":
        chatid = "-802277146"
    elif gruppo == "demo2":
        chatid = "-843153124"
    elif gruppo == "test":
        chatid = "-877192235"
    else:
        chatid = update.message.chat_id
    domanda = await cerca_domanda(connection, context.args[1])
    if connection.open:
        connection.close()

    tempo = datetime.now() + timedelta(seconds=3)
    tempo_s = 3
    count = 0
    for quest in domanda:
        count = count + 1
        g = partial(manda_quiz, update, context, quest, tempo, count, len(domanda), chatid)
        context.job_queue.run_once(g, when=tempo_s, name="peppe")
        tempo = tempo + timedelta(seconds=quest["period"]) + timedelta(seconds=2)
        tempo_s = tempo_s + quest["period"] + 2

    await bot.send_message(text="Il test su " + context.args[1] + " che continene " + str(count) + " domande sta per partire",chat_id=chatid)
    await bot.send_message(text="Il test partirà tra 2 secondi...", chat_id=chatid)
    c = partial(manda_classifica, chatid, context)
    context.job_queue.run_once(c, when=tempo_s + 2, name="prova", chat_id=update.message.chat_id)
    context.job_queue.run_once(svuota_memoria, when=tempo_s + 4, chat_id=update.message.chat_id)


async def cerca_domanda(connection, argomento):
    connection.ping()
    with connection:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `domande` WHERE `argomento`=%s"
            cursor.execute(sql, argomento)
        connection.commit()
        domanda = cursor.fetchall()
        return domanda


async def manda_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, quest, tempo, count, numero_domande, chatid, ciao):
    questions = [quest["opz1"], quest["opz2"], quest["opz3"], quest["opz4"]]
    keyboard = [
        [
            InlineKeyboardButton("❌ Doppi Punti", callback_data="Pot 1"),
            InlineKeyboardButton("🔢 50 / 50 ", callback_data=quest["opzCorrect"]),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await bot.send_poll(
        question="("+str(count)+"/"+str(numero_domande)+") "+quest["domanda"], options=questions, type=Poll.QUIZ, correct_option_id=quest["opzCorrect"],
        is_anonymous=False, open_period=quest["period"], reply_markup=reply_markup, chat_id=chatid
    )
    payload = {
        message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id,
                          "correctOption": quest["opzCorrect"], "inizio": tempo,
                          "durata": quest["period"], "difficolta":quest["difficolta"]}
    }
    context.bot_data.update(payload)


async def manda_classifica(chatid, context, nulla):
    risultati = "Risultati della Giornata\n"
    # sorted(partecipanti.values())
    classifica = {}
    for id in partecipanti:
        data = context.bot_data[id]
        classifica[id] = data["Punti"]

    numero_utenti = 0
    for id in sorted(classifica, key=classifica.get, reverse=True):
        numero_utenti = numero_utenti + 1
        partecipante = context.bot_data[id]
        risultati = risultati + '%-10s %s' % (partecipante["Nome"], str(round(partecipante["Punti"],2))) + "\n"
        if numero_utenti == 100:
            await bot.send_message(text=risultati, chat_id=chatid)
            numero_utenti = 0
            risultati = ""
    await bot.send_message(text=risultati, chat_id=chatid)


async def svuota_memoria(context):
    print("Grandezza Partecipanti Finale: " + str(sys.getsizeof(partecipanti)) +" Byte")
    print("Grandezza Bot Data Finale: " + str(sys.getsizeof(context.bot_data)) +" Byte")
    partecipanti.clear()
    context.bot_data.clear()
    print("Memoria Svuotata")


async def classifica_command(update, context):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    utenti = trova_classifica(connection)
    calssifica = "`Questa è la classifica della classe:\n"
    numero_utenti = 0
    for utente in utenti:
        numero_utenti = numero_utenti +1
        calssifica = calssifica + '%-10s %s' % (utente["nome"], str(utente["punti"])) + "\n"
        if numero_utenti == 100:
            calssifica = calssifica + "`"
            await bot.send_message(text=calssifica, chat_id=update.message.chat_id , parse_mode="MarkdownV2")
            numero_utenti = 0
            calssifica = "`"
    calssifica = calssifica + "`"
    await bot.send_message(text=calssifica, chat_id=update.message.chat_id , parse_mode="MarkdownV2")
    if connection.open:
        connection.close()


def trova_classifica(connection):
    with connection:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `utenti` ORDER BY `punti` DESC"
            cursor.execute(sql)
        connection.commit()
        utenti = cursor.fetchall()
        return utenti


async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    utente = await cerca_utente(connection, update.poll_answer.user.id)
    try:
        utente_partecipante = context.bot_data[utente.id_telegram]
    except:
        payload = {

            utente.id_telegram: { "Nome": utente.nome, "Punti": 0, "streak":0,
                                                "pot1D": True, "pot1U": False,
                                                 "pot2D": True, "pot2U": False,
                                                 }

        }
        context.bot_data.update(payload)
        utente_partecipante = context.bot_data[utente.id_telegram]
        partecipanti.append(utente.id_telegram)
    quiz_data = context.bot_data[update.poll_answer.poll_id]

    punti = await calcola_punti(quiz_data["inizio"], quiz_data["durata"], utente_partecipante)
    if update.poll_answer.option_ids[0] == quiz_data["correctOption"]:
        #Aggiunta modificatore difficolta / streak
        moltiplicatore_difficolta = ((quiz_data["difficolta"]-1) / 10) +1
        moltiplicatore_streak = (utente_partecipante["streak"] / 10) + 1
        utente_partecipante["streak"] = utente_partecipante["streak"] + 2
        # Punti totali
        punti = punti * moltiplicatore_difficolta *  moltiplicatore_streak
        punti_round = utente.punti + punti
        utente.set_punti(punti_round)
        # Punti gioranta
        utente_partecipante["Punti"] = utente_partecipante["Punti"] + punti
        # Esperienza (solo in caso di risposta esatta)
        utente = await calcola_esperienza(utente)
        print(utente.nome + ": +" + str(round(punti, 2)) +" / "+str(quiz_data["durata"]))
    else:
        # Punti totali
        punti_round = utente.punti - punti
        utente.set_punti(punti_round)
        # Punti gioranta
        utente_partecipante["Punti"] = utente_partecipante["Punti"] - punti
        utente_partecipante["streak"] = 0
        print(utente.nome + ": -" + str(round(punti, 2)) +" / "+str(quiz_data["durata"]))

    await aggiorna_punti_livello_esperienza_utente(connection, utente)
    if connection.open:
        connection.close()


async def calcola_punti(inizio, durata, utente):
    tempo_risposta = datetime.now() - inizio
    moltiplicatore_potenziamento = 1
    try:
        if utente["pot1U"]:
            utente["pot1D"] = False
            utente["pot1U"] = False
            moltiplicatore_potenziamento = 2
    except:
        print("376: Errore nel calcolo punti")
    finally:
        punti = round(float(timedelta(seconds=durata).total_seconds() - tempo_risposta.total_seconds()), 3) * 100
        return moltiplicatore_potenziamento * int(punti)


async def calcola_esperienza(utente):
    utente.esperienza = utente.esperienza + 10
    if utente.esperienza >= liv.LIV1:
        utente.livello = 1
    if utente.esperienza >= liv.LIV2:
        utente.livello = 2
    if utente.esperienza >= liv.LIV3:
        utente.livello = 3
    if utente.esperienza >= liv.LIV4:
        utente.livello = 4
    if utente.esperienza >= liv.LIV5:
        utente.livello = 5
    if utente.esperienza >= liv.LIV6:
        utente.livello = 6
    if utente.esperienza >= liv.LIV7:
        utente.livello = 7
    if utente.esperienza >= liv.LIV8:
        utente.livello = 8
    if utente.esperienza >= liv.LIV9:
        utente.livello = 9
    if utente.esperienza >= liv.LIV10:
        utente.livello = 10
    return utente


async def aggiorna_punti_livello_esperienza_utente(connection, utente):
    connection.ping()
    with connection:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "UPDATE utenti SET `punti`=%s , `livello`=%s, `esperienza`=%s WHERE `id_telegram`=%s"
            cursor.execute(sql, (round(utente.get_punti(),2), utente.livello, utente.esperienza, utente.id_telegram))
        connection.commit()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    connection = pymysql.connect(host='localhost',
                                 user=USER,
                                 password=PASSWORD,
                                 database='botdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    utente_trovato = await cerca_utente(connection, update.callback_query.from_user.id)
    try:
        utente = context.bot_data[utente_trovato.id_telegram]
    except:
        payload = {

            utente_trovato.id_telegram: {"Nome": utente_trovato.nome, "Punti": 0, "streak": 0,
                                 "pot1D": True, "pot1U": False,
                                 "pot2D": True, "pot2U": False,
                                 }

        }
        context.bot_data.update(payload)
        utente = context.bot_data[utente_trovato.id_telegram]
        partecipanti.append(utente_trovato.id_telegram)
    selezionato = query.data
    if selezionato == "Pot 1":
        if utente["pot1D"]:
            print(str(utente["Nome"]) + ": Doppi punti")
            utente["pot1U"] = True
            utente["pot1D"] = False
            await bot.answer_callback_query(update.callback_query.id,
                                            "✅Doppi punti Utilizzati✅")
        else:
            await bot.answer_callback_query(update.callback_query.id,
                                            "‼Potenziamento Doppi punti già utilizzato‼")


    if selezionato == "0" or selezionato == "1" or selezionato == "2" or selezionato == "3":
        if utente["pot2D"]:
            print(str(utente["Nome"]) + ": 50/50")
            utente["pot2U"] = True
            utente["pot2D"] = False
            sol1 = str(int(selezionato) + 1)
            sol2 = sol1
            while sol1 == sol2:
                sol2 = str(random.randint(1, 4))
            if int(datetime.now().second) % 2:
                soluzione = "AIUTO: " + sol1 + " || " + sol2
            else:
                soluzione = "AIUTO: " + sol2 + " || " + sol1
            await bot.answer_callback_query(update.callback_query.id,
                                            soluzione,
                                            show_alert=True)
        else:
            await bot.answer_callback_query(update.callback_query.id,
                                            "‼Potenziamento 50 / 50 già utilizzato‼")

def main():
    application = ApplicationBuilder().token(api.API_KEY).read_timeout(100).write_timeout(100).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("add", aggiorna_utente_command))
    application.add_handler(CommandHandler("classi", classi_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("info_bot", info_bot_command))
    application.add_handler(CommandHandler("test", test_command, filters.User(username=["@Fabbbooh"])))
    application.add_handler(CommandHandler("poll", quiz,filters.User(username=["@Fabbbooh"])))
    application.add_handler(CommandHandler("leaderboard", classifica_command))

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(PollAnswerHandler(receive_quiz_answer))

    application.run_polling()


main()
