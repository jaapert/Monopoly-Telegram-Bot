# -*- coding: utf-8 -*-
#!/usr/bin/env python3

static_responses = {
    'end_game': "The game has been terminated!",
    'end_game_id_missing_failure': "You cannot end the game since you aren't playing!",
    'game_dne_failure': "You cannot do this; a game does not currently exist!",
    'game_ongoing': "A game is currently being played! A new one cannot be started in this chat!",
    'game_pending': "A game is already pending! You can join with /join or leave with /leave.",
    'start_game_failure': "All players must have messaged the bot in order to start the game! Use the /startgame command to begin the game once this is true.",
    'start_game_id_missing_failure': "You cannot start the game since you aren't playing!",
    'start_game_min_threshold': "There must be at least two players to start the game!",
    'start_game_not_pending': "Cannot start a game that isn't pending!",
    'unexpected_error': "Something has gone horribly wrong!",
    'invalid_nickname': "That is not a valid nickname.",
    'join_game_not_pending': "You cannot join; a game is not currently pending!",
    'leave_failure': "You cannot leave. You are here forever. Good luck!",
    'leave_game': "You have left the game",
    'leave_game_not_pending_failure': "You cannot leave the game; there's no game pending!",
    'leave_id_missing_failure': "You cannot leave the game; you aren't in it!",
    'listplayers_failure': "A game has not been started, so there aren't any players to list!",
    'new_game': """A  new game has been created for this chat and is currently pending.
                /join [nickname] will let you join the game under a nickname or your username as a default.
                /leave command will remove you from the game.
                /listplayers will list all players in the current game.
                /endgame will end the current game.
                /startgame will start the current game.

                If you join the game, you must have messaged privately in order to see your hand!""",
    'rules': """Each player rolls the dice to see who goes first. The person who rolls the largest number goes first. Everyone starts on the space that says, "Go".

                Whenever you land on a land that no one owns, you can buy it from the bank. If you do not want to buy it the Banker sells it at an auction. (Not everyone plays by the auction rule). All of the prices for the land are on the board. Once you own the land, players must pay a rent if they are waiting on your land.

                If you land on a Chance or a Community Chest card, you must do what it says. For example, "Go to Jail, Directly to Jail", "Advance to Go".

                If you roll doubles (the same number on both dice) you get to roll again.

                When you pass "Go", you collect $200 from the bank. (Unless you have to go to jail).

                "Free Parking" is an area that is free to be in. If you land in the area you do not have to worry about paying for anything.

                There are two ways to get into jail: (1) You land on the space labeled "Go to Jail" or (2) You pick a Chance or Community Chest card that says "Go to Jail". There are three ways to get out of jail: (1) You get three turns to roll a double, if you do not roll a double in the three turns you must pay the $50 fine, (2) using a "Get out of Jail Free" card (that can be found in Chance or Community Chest), or (3) pay a fine of $50.

                Once you own all of one color, you can start to build houses. Houses make the land more costly and every time you add a house the price goes up more. Once there are four houses on each land you can get a hotel (there can only be one hotel on any land).

                You can trade properties, "Get Out of Jail Free" cards, and money with other players on your turn.

                If you are bankrupt, you cannot pay someone rent or cannot pay a tax. If you declare bankruptcy you are done with the game.""",
    'start': """Hello! This bot was made to let people play Monopoly in Telegram. In order to use me, you'll need to add me to a chat and have everyone who wishes to play directly message me.

                Commands:

                /newgame - Begins a new game of Monopoly.
                /rules - Sends a message with the rules of Monopoly.
                /help - Sends a message with additional commands and information."
                'start_game': "This is the game of Monopoly, play begins with a randomly chosen first player.

                /roll will roll the dice to determine where you land.
                /bankrupt [player_id] will bankrupt you to the player with that ID.
                /purchase_house [property_id] will purchase a house on that property.
                /purchase_hotel [property_id] will purchase a hotel on that property.
                /purchase_property will purchase the property at your position.
                /end_turn will end your turn.
                /pay [player_id or "bank"] [amount] will pay the respective person or the bank the specified amount.
                /freeme will play a Get Out of Jail Free card if you have one.
                /bail will pay your jail bail.
                /mortgage [property_id] will mortgage your property with that ID.
                /canceltrade will cancel a pending trade.
                /addtrade [property_id] [money] [num_cards] will add no property (if -1), else the property with that ID, the money, and number of Get Out of Jail Free Cards specified.
                /addtrade [property_id] [money] [num_cards] will remove no property (if -1), else the property with that ID, the money, and number of Get Out of Jail Free Cards specified.
                /agree will cause you to agree to the pending trade.
                /disagree will cause you to disagree to the pending trade.
                /trade will commence the pending trade if both players have agreed.
                /setuptrade [player_id] will begin a trade between you and the player with that ID.
                /assets will send you your current money, properties, and cards.""",
      'help': """'help': "Here's a list of helpful commands:
                /start will start the bot.
                /rules will display a list of rules.
                /feedback [text] will record feedback.
                /newgame will begin a new game.
                /startgame will start a game, if there are at least 2 players.
                /listplayers will list all players in the current game.
                /join [nickname] will add the sender to the game under an optional name or their username as a default, if a game is pending.
                /leave will remove the sender from the game, if a game is pending.
                /help displays a list of these commands.
                /endgame will end the current game, if it exists.
                /blame will @ the current player's turn.
                /roll will roll the dice to determine where you land.
                /bankrupt [player_id] will bankrupt you to the player with that ID.
                /buyhouse [property_id] will purchase a house on that property for $200.
                /buyhotel [property_id] will purchase a hotel on that property for $200, if you have 4 houses.
                /sellhouse [property_id] will sell a house on that property.
                /sellhotel [property_id] will sell a hotel on that property.
                /buyproperty will purchase the property at your position.
                /endturn will end your turn.
                /pay [player_id or "bank"] [amount] will pay the respective person or the bank the specified amount.
                /freeme will play a Get Out of Jail Free card if you have one.
                /bail will pay your jail bail.
                /mortgage [property_id] will mortgage your property with that ID.
                /unmortgage [property_id] will pay back mortgage on your property with that ID.
                /canceltrade will cancel a pending trade.
                /addtrade [property_id] [money] [num_cards] will add no property (if -1), else the property with that ID, the money, and number of Get Out of Jail Free Cards specified.
                /agree will cause you to agree to the pending trade.
                /disagree will cause you to disagree to the pending trade.
                /trade will commence the pending trade if both players have agreed.
                /setuptrade [player_id] will begin a trade between you and the player with that ID.
                /assets will send you your current money, properties, and cards.
                /aa will display everyone's assets in the chat.""",
        'invalid_nickname': "That is not a valid nickname.",
        'join_game_not_pending': "You cannot join; a game is not currently pending!",
        'leave_failure': "You cannot leave. You are here forever. Good luck!",
        'leave_game_not_pending_failure': "You cannot leave the game; there's no game pending!",
        'leave_id_missing_failure': "You cannot leave the game; you aren't in it!",
        'listplayers_failure': "A game has not been started, so there aren't any players to list!",
        'new_game': """A  new game has been created for this chat and is currently pending.

                /join [nickname] will let you join the game under a nickname or your username as a default.
                /leave command will remove you from the game.
                /listplayers will list all players in the current game.
                /endgame will end the current game.
                /startgame will start the current game.

                If you join the game, you must have messaged me in PM in order to see your hand!"""
}
