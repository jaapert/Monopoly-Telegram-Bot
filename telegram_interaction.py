# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import Unauthorized
import logging

import sys
import traceback
import logging
import inspect

import monopoly
from responses import static_responses

with open("api_key.txt", 'r', encoding="utf-8") as f:
    TOKEN = f.read().rstrip()

MIN_PLAYERS = 2

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

ERROR_LOGGER = setup_logger("error_logger", "error_logs.log")
INFO_LOGGER = setup_logger("info_logger", "info_logs.log")

bot = telegram.Bot(token=TOKEN)

def send_static_response(chat_id, resp_id):
    if not resp_id in static_responses:
        response = static_responses['unexpected_error']
        ERROR_LOGGER.warning('No static response for resp_id: %s', resp_id)
    else:
        response = inspect.cleandoc(static_responses[resp_id])
    bot.send_message(chat_id=chat_id, text=response)

def static_handler(command):
    return CommandHandler(command,
        lambda update, context: send_static_response(chat_id=update.message.chat.id, resp_id=command))


def reset_chat_data(context):
    context.bot_data["is_game_pending"] = False
    context.bot_data["pending_players"] = {}
    context.bot_data["game_obj"] = None


def check_game_existence(chat_id, game):
    if game is None:
        send_static_response(chat_id=chat_id, resp_id='game_dne_failure')
        return False
    return True


def send_info(bot, chat_id, game, user_id, send_id):
    player = game.players.get(user_id)
    props = player.get_properties_str()
    money = player.get_money()
    cards = player.get_get_out_free_cards()
    total_assets = player.get_total_assets()
    bot.send_message(chat_id=send_id,
                     text=props + "\n\n" + player.get_name() + " money: $" + str(money) +
                                  "\n\n" + player.get_name() + " cards: " + str(cards) +
                                  "\n\n" + player.get_name() + " total assets: $" + str(total_assets) +
                                  "\n-----\n\n")


def send_infos(bot, chat_id, game, players):
    for user_id, nickname in players.items():
        send_info(bot, chat_id, game, user_id, user_id)


def newgame_handler(update, context):
    game = context.bot_data.get("game_obj")
    chat_id = update.message.chat.id

    if game is None and not context.bot_data.get("is_game_pending", False):
        reset_chat_data(context)
        context.bot_data["is_game_pending"] = True
        resp_id = 'new_game'
    elif game is not None:
        resp_id = 'game_ongoing'
    elif context.bot_data.get("is_game_pending", False):
        resp_id = 'game_pending'
    else:
        resp_id = 'unexpected_error'

    send_static_response(chat_id=chat_id, resp_id=resp_id)


def is_nickname_valid(name, user_id, context):
    if len(name) < 1 or len(name) > 15:
        return False
    else:
        return True


def join_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if not context.bot_data.get("is_game_pending", False):
        send_static_response(chat_id=chat_id, resp_id='join_game_not_pending')
        return

    if context.args:
        nickname = " ".join(context.args)
    else:
        nickname = update.message.from_user.first_name

    if is_nickname_valid(nickname, user_id, context.bot_data):
        context.bot_data["pending_players"][user_id] = nickname
        bot.send_message(chat_id=update.message.chat_id,
                         text="Joined with nickname %s!" % nickname)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Current player count: %d" % len(context.bot_data.get("pending_players", {})))
    else:
        send_static_response(chat_id=chat_id, resp_id='invalid_nickname')


def leave_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if not context.bot_data.get("is_game_pending", False):
        resp_id = 'leave_game_not_pending_failure'
    elif user_id not in context.bot_data.get("pending_players", {}):
        resp_id = 'leave_id_missing_failure'
    else:
        resp_id = 'leave_game'
        del context.bot_data["pending_players"][update.message.from_user.id]

    send_static_response(chat_id=chat_id, resp_id=resp_id)


def listplayers_handler(update, context):
    chat_id = update.message.chat_id
    text = "List of players: \n"
    game = context.bot_data.get("game_obj")

    if context.bot_data.get("is_game_pending", False):
        for user_id, name in context.bot_data.get("pending_players", {}).items():
            text += name + "\n"
    elif game is not None:
        for user_id, name in context.bot_data.get("pending_players", {}).items():
            text += "(" + str(game.get_players()[user_id].get_id()) + ") " + name + "\n"
    else:
        text = static_responses['listplayers_failure']

    bot.send_message(chat_id=chat_id, text=text)


# Thanks Amrita!
def feedback_handler(update, context):
    """
    Store feedback from users in a text file.
    """
    if context.args and len(context.args) > 0:
        feedback = open("feedback.txt\n", "a+", encoding="utf-8")
        feedback.write(update.message.from_user.first_name + " (")
        # Records User ID so that if feature is implemented, can message them
        # about it.
        feedback.write(str(update.message.from_user.id) + "): ")
        feedback.write(" ".join(context.args) + "\n")
        feedback.close()
        bot.send_message(chat_id=update.message.chat_id, text="Thanks for the feedback!")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Format: /feedback [feedback]")


def startgame_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    pending_players = context.bot_data.get("pending_players", {})

    if not context.bot_data.get("is_game_pending", False):
        send_static_response(chat_id=chat_id, resp_id='start_game_not_pending')
        return

    if user_id not in context.bot_data.get("pending_players", {}):
        send_static_response(chat_id=chat_id, resp_id='start_game_id_missing_failure')
        return

    if len(pending_players) < MIN_PLAYERS:
        send_static_response(chat_id=chat_id, resp_id='start_game_min_threshold')
        return

    try:
        for user_id, nickname in pending_players.items():
            bot.send_message(chat_id=user_id, text="Trying to start game!")
    except Unauthorized as u:
        send_static_response(chat_id=chat_id, resp_id='start_game_failure')
        return

    context.bot_data["is_game_pending"] = False
    context.bot_data["game_obj"] = monopoly.Game(chat_id, pending_players, bot)
    game = context.bot_data.get("game_obj")
    send_infos(bot, chat_id, game, pending_players)


def endgame_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if context.bot_data.get("is_game_pending", False):
        context.bot_data["is_game_pending"] = False
        send_static_response(chat_id=chat_id, resp_id='end_game')
        return

    if not check_game_existence(chat_id, game):
        return

    if user_id not in game.get_players():
        send_static_response(chat_id=chat_id, resp_id='end_game_id_missing_failure')
        return

    reset_chat_data(context)
    send_static_response(chat_id=chat_id, resp_id='end_game')


def roll_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    players = game.get_players()
    if len(players) == 1:
        winner = list(players.values())[0]
        bot.send_message(chat_id=chat_id, text=winner.get_name() + " has won!")
        endgame_handler(update, context)
        return

    game.roll_dice(user_id)


def bankrupt_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /bankrupt player_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.bankrupt(user_id, " ".join(context.args))

    players = game.get_players()
    if len(players) == 1:
        winner = list(players.values())[0]
        bot.send_message(chat_id=chat_id, text=winner.get_name() + " has won!")
        endgame_handler(update, context)
        return


def purchase_house_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /buyhouse property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.purchase_house(user_id, context.args)


def purchase_hotel_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /buyhotel property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.purchase_hotel(user_id, context.args)


def sell_house_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /sellhouse property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.sell_house(user_id, context.args)


def sell_hotel_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /sellhotel property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.sell_hotel(user_id, context.args)


def purchase_property_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.purchase_property(user_id)


def end_turn_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.end_turn(user_id)
    blame_handler(update, context)


def pay_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 2:
        bot.send_message(chat_id=chat_id, text="Usage: /pay to_person_id amount")
        return

    if not check_game_existence(chat_id, game):
        return

    game.pay(user_id, context.args[0], int(context.args[1]))


def get_out_of_jail_free_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.use_get_out_of_jail_free_card(user_id)


def bail_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.pay_bail(user_id)


def money_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")
    player = game.players.get(user_id)
    playername=player.get_name()
    money = player.get_money()
    bot.send_message(chat_id=chat_id, text="{playername}\'s current funds: ${money}".format(playername=playername, money=money))


def mortgage_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /mortgage property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.mortgage_property(user_id, context.args)


def unmortgage_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /unmortgage property_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.unmortgage_property(user_id, context.args)


def cancel_trade_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.cancel_trade(user_id)


def add_to_trade_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 3:
        bot.send_message(chat_id=chat_id, text="Usage: /addtrade {property_id or -1} money num_get_out_free_cards")
        return

    if not check_game_existence(chat_id, game):
        return

    game.add_to_trade(user_id, int(context.args[0]), int(context.args[1]), int(context.args[2]))


def remove_from_trade_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 3:
        bot.send_message(chat_id=chat_id, text="Usage: /removetrade {property_id or -1} money num_get_out_free_cards")
        return

    if not check_game_existence(chat_id, game):
        return

    game.remove_from_trade(user_id, int(context.args[0]), int(context.args[1]), int(context.args[2]))


def agree_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.agree_to_trade(user_id)


def disagree_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.disagree_to_trade(user_id)


def trade_handler(update, context):
    chat_id = update.message.chat.id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    game.trade()


def setup_trade_handler(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    game = context.bot_data.get("game_obj")

    if len(context.args) != 1:
        bot.send_message(chat_id=chat_id, text="Usage: /setuptrade player_id")
        return

    if not check_game_existence(chat_id, game):
        return

    game.setup_trade(user_id, " ".join(context.args))


def assets_handler(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    game = context.bot_data.get("game_obj")

    if game is None:
        resp_id = 'game_dne_failure'
    elif user_id not in game.get_players():
        resp_id = 'leave_id_missing_failure'
    else:
        send_info(bot, chat_id, game, user_id, user_id)
        return

    send_static_response(chat_id=chat_id, resp_id=resp_id)


def blame_handler(update, context):
    chat_id = update.message.chat_id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    for user_id, player in game.get_players().items():
        if game.get_player_by_local_id(game.turn).get_user_id() == user_id:
            for (payer, payee, amount) in game.get_pending_payments():
                bot.send_message(chat_id=chat_id, text="[{}](tg://user?id={})".format(payer.get_name(),
                                                                                      payer.get_user_id()),
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                return
            bot.send_message(chat_id=chat_id, text="[{}](tg://user?id={})".format(player.get_name(),
                                                                                  user_id),
                             parse_mode=telegram.ParseMode.MARKDOWN)
            return


def all_assets_handler(update, context):
    chat_id = update.message.chat_id
    game = context.bot_data.get("game_obj")

    if not check_game_existence(chat_id, game):
        return

    for user_id, player in game.get_players().items():
        send_info(bot, chat_id, game, user_id, chat_id)


def board_handler(update, context):
    chat_id = update.message.chat_id

    bot.send_photo(chat_id=chat_id, photo=open("monopoly_board_org.jpg", "rb"))


def log_action(update, func_name):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    INFO_LOGGER.info("%s called %s in %s.", user_id, func_name, chat_id)


def handle_error(update, context):
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    ERROR_LOGGER.warning("Telegram Error! %s with context error %s caused by this update: %s", trace, context.error, update)


if __name__ == "__main__":
    # Set up the bot
    persistence = PicklePersistence(filename='persistent_bot_state.pkl')
    updater = Updater(token=TOKEN, persistence=persistence)
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
    roll_aliases = ["roll", "r", "rol", "oll"]
    bankrupt_aliases = ["bankrupt"]
    purchase_house_aliases = ["purchasehouse", "buyhouse", "bh", "ph"]
    purchase_hotel_aliases = ["purchasehotel", "buyhotel", "bhh", "phh"]
    purchase_property_aliases = ["purchaseproperty", "buyproperty", "buyprop", "purchaseprop", "bp"]
    end_turn_aliases = ["end", "endturn", "endme", "ednme", "edna"]
    pay_aliases = ["pay", "p"]
    get_out_aliases = ["out", "freeme", "usecard", "goofg"]
    bail_aliases = ["bail", "paybail"]
    money_aliases=["showmethemoney","money","funds"]
    mortgage_aliases = ["mortgage", "m"]
    unmortgage_aliases = ["unmortgage", "um"]
    cancel_trade_aliases = ["canceltrade", "ct"]
    add_trade_aliases = ["addtrade", "at"]
    remove_trade_aliases = ["removetrade", "rt"]
    agree_aliases = ["agree", "yes"]
    disagree_aliases = ["disagree", "no"]
    trade_aliases = ["trade"]
    setup_trade_aliases = ["setuptrade", "st"]
    assets_aliases = ["assets", "mystuff"]
    blame_aliases = ["blame", "blam"]
    sell_house_aliases = ["sellhouse", "sh"]
    sell_hotel_aliases = ["sellhotel", "shh"]
    all_assets_aliases = ["allassets", "aa"]
    board_aliases = ["board", "gameboard", "monopolyboard", "whatdoesitlooklikeagain"]

    commands = [("feedback", feedback_aliases),
                ("newgame", newgame_aliases),
                ("join", join_aliases),
                ("leave", leave_aliases),
                ("listplayers", listplayers_aliases),
                ("startgame", startgame_aliases),
                ("endgame", endgame_aliases),
                ("roll", roll_aliases),
                ("bankrupt", bankrupt_aliases),
                ("purchase_house", purchase_house_aliases),
                ("purchase_hotel", purchase_hotel_aliases),
                ("purchase_property", purchase_property_aliases),
                ("end_turn", end_turn_aliases),
                ("pay", pay_aliases),
                ("get_out_of_jail_free", get_out_aliases),
                ("bail", bail_aliases),
                ("money",money_aliases),
                ("mortgage", mortgage_aliases),
                ("unmortgage", unmortgage_aliases),
                ("cancel_trade", cancel_trade_aliases),
                ("add_to_trade", add_trade_aliases),
                ("remove_from_trade", remove_trade_aliases),
                ("agree", agree_aliases),
                ("disagree", disagree_aliases),
                ("trade", trade_aliases),
                ("setup_trade", setup_trade_aliases),
                ("assets", assets_aliases),
                ("blame", blame_aliases),
                ("sell_house", sell_house_aliases),
                ("sell_hotel", sell_hotel_aliases),
                ("all_assets", all_assets_aliases),
                ("board", board_aliases)]
    for base_name, aliases in commands:
        func = locals()[base_name + "_handler"]
        dispatcher.add_handler(CommandHandler(aliases, func))

    # Error handlers
    dispatcher.add_error_handler(handle_error)

    updater.start_polling()
    updater.idle()
