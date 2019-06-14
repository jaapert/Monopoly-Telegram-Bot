# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import monopoly

import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.error import TelegramError, Unauthorized
import logging

import sys, os, threading, time


with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

MIN_PLAYERS = 2
PORT = int(os.environ.get('PORT', '8443'))


def static_handler(command):
    text = open("static_responses/{}.txt".format(command), "r").read()

    return CommandHandler(command,
        lambda bot, update: bot.send_message(chat_id=update.message.chat.id, text=text))


def reset_chat_data(chat_data):
    chat_data["is_game_pending"] = False
    chat_data["pending_players"] = {}
    chat_data["game_obj"] = None


def check_game_existence(chat_id, game):
    if game is None:
        text = open("static_responses/game_dne_failure.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return False
    return True


def send_info(bot, chat_id, game, user_id):
    player = game.players.get(user_id)
    props = player.get_properties_str()
    money = player.get_money()
    cards = player.get_out_free_cards()
    bot.send_message(chat_id=user_id,
                     text=props + "\n\nYour money: $" + str(money) + "\n\n" + "Your cards: " + str(cards))


def send_infos(bot, chat_id, game, players):
    for user_id, nickname in players.items():
        send_info(bot, chat_id, game, user_id)


def newgame_handler(bot, update, chat_data):
    game = chat_data.get("game_obj")
    chat_id = update.message.chat.id

    if game is None and not chat_data.get("is_game_pending", False):
        reset_chat_data(chat_data)
        chat_data["is_game_pending"] = True
        text = open("static_responses/new_game.txt", "r").read()
    elif game is not None:
        text = open("static_responses/game_ongoing.txt", "r").read()
    elif chat_data.get("is_game_pending", False):
        text = open("static_responses/game_pending.txt", "r").read()
    else:
        text = "Something has gone horribly wrong!"

    bot.send_message(chat_id=chat_id, text=text)


def is_nickname_valid(name, user_id, chat_data):
    if len(name) < 3 or len(name) > 15:
        return False

    if user_id in chat_data.get("pending_players", {}):
        if name.lower() == chat_data["pending_players"][user_id].lower():
            return True

    for id, user_name in chat_data.get("pending_players", {}).items():
        if name.lower() == user_name.lower():
            return False

    try:
        float(name)
        return False
    except ValueError as e:
        return True


def join_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if not chat_data.get("is_game_pending", False):
        text = open("static_responses/join_game_not_pending.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    if args:
        nickname = " ".join(args)
    else:
        nickname = update.message.from_user.first_name

    if is_nickname_valid(nickname, user_id, chat_data):
        chat_data["pending_players"][user_id] = nickname
        bot.send_message(chat_id=update.message.chat_id,
                         text="Joined with nickname %s!" % nickname)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Current player count: %d" % len(chat_data.get("pending_players", {})))
    else:
        text = open("static_responses/invalid_nickname.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)


def leave_handler(bot, update, chat_data):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if not chat_data.get("is_game_pending", False):
        text = open("static_responses/leave_game_not_pending_failure.txt", "r").read()
    elif user_id not in chat_data.get("pending_players", {}):
        text = open("static_responses/leave_id_missing_failure.txt", "r").read()
    else:
        text = "You have left the current game."
        del chat_data["pending_players"][update.message.from_user.id]

    bot.send_message(chat_id=chat_id, text=text)


def listplayers_handler(bot, update, chat_data):
    chat_id = update.message.chat_id
    text = "List of players: \n"
    game = chat_data.get("game_obj")

    if chat_data.get("is_game_pending", False):
        for user_id, name in chat_data.get("pending_players", {}).items():
            text += name + "\n"
    elif game is not None:
        for user_id, name in chat_data.get("pending_players", {}).items():
            num_cards_str = str(len(game.get_player(user_id).get_hand()))
            text += "(" + str(game.get_player(user_id).get_id()) + ") " + name + "\n"
    else:
        text = open("static_responses/listplayers_failure.txt", "r").read()

    bot.send_message(chat_id=chat_id, text=text)


# Thanks Amrita!
def feedback_handler(bot, update, args):
    """
    Store feedback from users in a text file.
    """
    if args and len(args) > 0:
        feedback = open("feedback.txt\n", "a+")
        feedback.write(update.message.from_user.first_name + "\n")
        # Records User ID so that if feature is implemented, can message them
        # about it.
        feedback.write(str(update.message.from_user.id) + "\n")
        feedback.write(" ".join(args) + "\n")
        feedback.close()
        bot.send_message(chat_id=update.message.chat_id, text="Thanks for the feedback!")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Format: /feedback [feedback]")


def startgame_handler(bot, update, chat_data):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    pending_players = chat_data.get("pending_players", {})

    if not chat_data.get("is_game_pending", False):
        text = open("static_responses/start_game_not_pending.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    if user_id not in chat_data.get("pending_players", {}):
        text = open("static_responses/start_game_id_missing_failure.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    """if len(pending_players) < MIN_PLAYERS:
        text = open("static_responses/start_game_min_threshold.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return"""

    try:
        for user_id, nickname in pending_players.items():
            bot.send_message(chat_id=user_id, text="Trying to start game!")
    except Unauthorized as u:
        text = open("static_responses/start_game_failure.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    chat_data["is_game_pending"] = False
    chat_data["game_obj"] = monopoly.Game(chat_id, pending_players)
    game = chat_data.get("game_obj")
    send_infos(bot, chat_id, game, pending_players)


def endgame_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if chat_data.get("is_game_pending", False):
        chat_data["is_game_pending"] = False
        text = open("static_responses/end_game.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    if not check_game_existence(chat_id, game):
        return

    if user_id not in game.players_and_names:
        text = open("static_responses/end_game_id_missing_failure.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    reset_chat_data(chat_data)
    text = open("static_responses/end_game.txt", "r").read()
    bot.send_message(chat_id=chat_id, text=text)


def roll_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    players = game.get_players()
    if len(players) == 1:
        winner = list(players.items())[0]
        bot.send_message(chat_id=chat_id, text=winner.get_name() + " has won!")
        endgame_handler(bot, update, chat_data)
        return

    game.roll_dice(user_id)


def bankrupt_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /bankrupt player_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.bankrupt(user_id, int(" ".join(args)))

    players = game.get_players()
    if len(players) == 1:
        winner = list(players.items())[0]
        bot.send_message(chat_id=chat_id, text=winner.get_name() + " has won!")
        endgame_handler(bot, update, chat_data)
        return


def purchase_house_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /buyhouse property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.purchase_house(user_id, int(" ".join(args)))


def purchase_hotel_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /buyhouse property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.purchase_hotel(user_id, int(" ".join(args)))


def purchase_property_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.purchase_property(user_id)


def end_turn_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.end_turn(user_id)


def pay_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 2:
        bot.send_message(chat_id=chat_id, text="Usage: /pay to_person_id amount")
        return

    if not check_game_existence(chat_id, game):
        return

    game.pay(user_id, int(args[0]), int(args[1]))


def get_out_of_jail_free_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.use_get_out_of_jail_free_card(user_id)


def bail_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.pay_bail(user_id)


def mortgage_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /mortgage property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.purchase_house(user_id, int(" ".join(args)))


def cancel_trade_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.cancel_trade(user_id)


def add_to_trade_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 3:
        bot.send_message(chat_id=chat_id, text="Usage: /addtrade property_id money num_get_out_free_cards")
        return

    if not check_game_existence(chat_id, game):
        return

    game.add_to_trade(user_id, int(args[0]), int(args[1]), int(args[2]))


def remove_from_trade_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 3:
        bot.send_message(chat_id=chat_id, text="Usage: /removetrade property_id money num_get_out_free_cards")
        return

    if not check_game_existence(chat_id, game):
        return

    game.remove_from_trade(user_id, int(args[0]), int(args[1]), int(args[2]))


def agree_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.agree_to_trade(user_id)


def disagree_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.disagree_to_trade(user_id)


def trade_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.trade()


def setup_trade_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = chat_data.get("game_obj")

    if len(args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /begintrade player_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.setup_trade(user_id, int(" ".join(args)))


def assets_handler(bot, update, chat_data):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    game = chat_data.get("game_obj")

    if game is None:
        text = open("static_responses/game_dne_failure.txt", "r").read()
    elif user_id not in game.get_players():
        text = open("static_responses/leave_id_missing_failure.txt", "r").read()
    else:
        send_info(bot, chat_id, game, user_id)
        return

    bot.send_message(chat_id=user_id, text=text)


def blame_handler(bot, update, chat_data):
    chat_id = update.message.chat_id
    game = chat_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    if not game.get_ready_to_play():
        text = open("static_responses/not_all_ready_failure.txt", "r").read()
        bot.send_message(chat_id=chat_id, text=text)
        return

    for user_id, nickname in game.get_players().items():
        if game.get_player_id_by_num(game.turn) == user_id:
            bot.send_message(chat_id=chat_id, text="[{}](tg://user?id={})".format(nickname, user_id),
                             parse_mode=telegram.ParseMode.MARKDOWN)
            return


def handle_error(bot, update, error):
    try:
        raise error
    except TelegramError:
        logging.getLogger(__name__).warning('Telegram Error! %s caused by this update: %s', error, update)


if __name__ == "__main__":
    # Set up the bot

    bot = telegram.Bot(token=TOKEN)
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    # Static command handlers

    static_commands = ["start", "rules", "help"]
    for c in static_commands:
        dispatcher.add_handler(static_handler(c))

    # Main command handlers

    join_aliases = ["join"]
    leave_aliases = ["leave", "unjoin"]
    listplayers_aliases = ["listplayers", "list"]
    feedback_aliases = ["feedback"]
    newgame_aliases = ["newgame"]
    startgame_aliases = ["startgame"]
    endgame_aliases = ["endgame"]
    roll_aliases = ["roll", "r"]
    bankrupt_aliases = ["bankrupt"]
    purchase_house_aliases = ["purchasehouse", "buyhouse", "bh", "ph"]
    purchase_hotel_aliases = ["purchasehotel", "buyhotel", "bhh", "phh"]
    purchase_property_aliases = ["purchaseproperty", "buyproperty", "buyprop", "purchaseprop", "bp"]
    end_turn_aliases = ["end", "endturn"]
    pay_aliases = ["pay", "p"]
    get_out_aliases = ["out", "freeme", "usecard"]
    bail_aliases = ["bail", "paybail"]
    mortgage_aliases = ["mortgage", "m"]
    cancel_trade_aliases = ["canceltrade", "ct"]
    add_trade_aliases = ["addtrade", "at"]
    remove_trade_aliases = ["removetrade", "rt"]
    agree_aliases = ["agree", "yes"]
    disagree_aliases = ["disagree", "no"]
    trade_aliases = ["trade"]
    setup_trade_aliases = ["setuptrade", "st"]
    assets_aliases = ["assets", "mystuff"]

    commands = [("feedback", 0, feedback_aliases),
                ("newgame", 1, newgame_aliases),
                ("join", 2, join_aliases),
                ("leave", 1, leave_aliases),
                ("listplayers", 1, listplayers_aliases),
                ("startgame", 1, startgame_aliases),
                ("endgame", 1, endgame_aliases),
                ("roll", 1, roll_aliases),
                ("bankrupt", 2, bankrupt_aliases),
                ("purchase_house", 2, purchase_house_aliases),
                ("purchase_hotel", 2, purchase_hotel_aliases),
                ("purchase_property", 2, purchase_property_aliases),
                ("end_turn", 1, end_turn_aliases),
                ("pay", 2, pay_aliases),
                ("get_out_of_jail_free", 1, get_out_aliases),
                ("bail", 1, bail_aliases),
                ("mortgage", 2, mortgage_aliases),
                ("cancel_trade", 1, cancel_trade_aliases),
                ("add_to_trade", 2, add_trade_aliases),
                ("remove_from_trade", 2, remove_trade_aliases),
                ("agree", 1, agree_aliases),
                ("disagree", 1, disagree_aliases),
                ("trade", 1, trade_aliases),
                ("setup_trade", 2, setup_trade_aliases),
                ("assets", 1, assets_aliases)]
    for c in commands:
        func = locals()[c[0] + "_handler"]
        if c[1] == 0:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_args=True))
        elif c[1] == 1:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True))
        elif c[1] == 2:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True, pass_args=True))
        elif c[1] == 3:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True, pass_user_data=True))

    # Error handlers

    dispatcher.add_error_handler(handle_error)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO, filename='logging.txt', filemode='a')

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.set_webhook("https://la-monopoly-bot.herokuapp.com/" + TOKEN)

    #updater.start_polling()
    updater.idle()