# -*- coding: utf-8 -*-
# Patch 0.9.3
from __future__ import unicode_literals

from PIL import Image, ImageDraw
from colorhash import ColorHash

import telegram
from telegram.error import TelegramError

import random

with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

bot = telegram.Bot(token=TOKEN)

class Dice:
    def __init__(self, dice_count, sides):
        self.dice_count = dice_count
        self.sides = sides

    def roll(self):
        return [random.randint(1, self.sides) for _ in range(self.dice_count)]

    def check_doubles(self, roll):
        if len(roll) == 2:
            return roll[0] == roll[1]
        else:
            return False


class Player:
    def __init__(self, user_id, id, name, money):
        self.properties = []
        self.money = money
        self.get_out_free_cards = 0
        self.turns_left_in_jail = -1
        self.id = id
        self.name = name
        self.position = 0
        self.user_id = user_id
        self.total_roll = 0
        self.icon_color = ColorHash(name).rgb

    def get_properties(self):
        return self.properties

    def get_money(self):
        return self.money

    def get_turns_left_in_jail(self):
        return self.turns_left_in_jail

    def get_id(self):
        return self.id

    def get_user_id(self):
        return self.user_id

    def get_get_out_free_cards(self):
        return self.get_out_free_cards

    def add_money(self, money):
        self.money += money

    def add_out_free_card(self):
        self.get_out_free_cards += 1

    def remove_out_free_card(self):
        self.get_out_free_cards -= 1

    def add_property(self, property):
        self.properties.append(property)

    def remove_property(self, property):
        if property in self.properties:
            self.properties.remove(property)

    def get_property_by_id(self, id):
        count = 0
        for p in self.properties:
            if count == id:
                return p
            count += 1
        return None

    def get_properties_str(self):
        text = self.name + " properties:\n\n"
        count = 0
        for p in self.properties:
            if type(p) == Property:
                text += "(" + str(count) + ") " + p.get_name() + " : " + p.get_color() + \
                        " (" + str(p.get_houses()) + " houses, " + str(p.get_hotels()) + " hotels)" + \
                        " [Mortgage Value: " + str(p.get_mortgage_value()) + "] " + \
                        ("[[Mortgaged]]\n" if p.get_mortgaged() else "\n")
            elif type(p) == OtherProperty:
                text += "(" + str(count) + ") " + p.get_name() + " : " + p.get_type() + \
                        " [Mortgage Value: " + str(p.get_mortgage_value()) + "] " + \
                        ("[[Mortgaged]]\n" if p.get_mortgaged() else "\n")
            count += 1
        return text

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def get_total_assets(self):
        total = self.money
        for p in self.properties:
            if type(p) == Property:
                total += p.mortgage_value + p.house_cost * p.houses + p.hotel_cost * p.hotels
            elif type(p) == OtherProperty:
                total += p.mortgage_value
        return total

    def set_turns_left_in_jail(self, turns):
        self.turns_left_in_jail = turns

    def get_name(self):
        return self.name

    def get_total_roll(self):
        return self.total_roll

    def add_to_total_roll(self, roll_sum):
        self.total_roll += roll_sum

    def sort_props_by_color(self):
        self.properties.sort(key=lambda p: p.get_color())

    def get_icon_color(self):
        return self.icon_color


class Property:
    # Note: rents is [base_rent, one_house_rent, ..., four_houses_rent, hotel_rent]
    def __init__(self, name, color, cost, rents, mortgage_value, house_cost, hotel_cost):
        self.name = name
        self.color = color
        self.houses = 0
        self.hotels = 0
        self.rents = rents
        self.mortgage_value = mortgage_value
        self.house_cost = house_cost
        self.hotel_cost = hotel_cost
        self.cost = cost
        self.mortgaged = False
        self.owner = None

    def add_house(self):
        if self.houses < 4 and self.hotels == 0:
            self.houses += 1

    def remove_house(self):
        if self.houses > 0:
            self.houses -= 1

    def add_hotel(self):
        if self.houses == 4:
            self.houses = 0
            self.hotels = 1

    def remove_hotel(self):
        if self.hotels > 0:
            self.hotels = 0
            self.houses = 4

    def get_name(self):
        return self.name

    def get_houses(self):
        return self.houses

    def get_hotels(self):
        return self.hotels

    def get_rent(self):
        return self.rents[self.houses + 5 * self.hotels]

    def get_color(self):
        return self.color

    def get_house_cost(self):
        return self.house_cost

    def get_hotel_cost(self):
        return self.hotel_cost

    def get_cost(self):
        return self.cost

    def get_mortgaged(self):
        return self.mortgaged

    def set_mortgaged(self, val):
        # I'll assume for the moment that it's a bool; I need to add a check for that.
        self.mortgaged = val

    def get_owner(self):
        return self.owner

    def set_owner(self, player):
        self.owner = player

    def get_mortgage_value(self):
        return self.mortgage_value

    def set_houses(self, val):
        self.houses = val

    def set_hotels(self, val):
        self.hotels = val


class OtherProperty:
    def __init__(self, name, cost, rent, mortgage_value, type):
        self.name = name
        self.cost = cost
        self.rent = rent
        self.mortgage_value = mortgage_value
        self.mortgaged = False
        self.type = type
        self.owner = None

    def get_name(self):
        return self.name

    def get_cost(self):
        return self.cost

    def get_rent(self):
        return self.rent

    def get_mortgage_value(self):
        return self.mortgage_value

    def get_type(self):
        return self.type

    def get_owner(self):
        return self.owner

    def set_owner(self, player):
        self.owner = player

    def get_mortgaged(self):
        return self.mortgaged

    def set_mortgaged(self, val):
        # I'll assume for the moment that it's a bool; I need to add a check for that.
        self.mortgaged = val

    # Not technically accurate, but I need it for sorting.
    def get_color(self):
        return self.type


class Game:
    def __init__(self, chat_id, players):
        self.players = {}
        self.chat_id = chat_id
        self.turn = 0
        self.dice = Dice(2, 6)
        self.has_doubles = False
        # Make pending payments a list of tuples in the form (from, to, amount)
        self.pending_payments = []
        self.last_roll = [-1]
        # (player_1, player_2, money_from_1, money_from_2, props_from_1,
        # props_from_2, cards_from_1, cards_from_2, agreed_1, agreed_2)
        self.pending_trade = None
        self.ids = []
        self.board = \
        [
            "Go",
            Property("Mediterranean Avenue", "Brown", 60, [2, 10, 30, 90, 160, 250], 30, 50, 50),
            "Community Chest",
            Property("Baltic Avenue", "Brown", 60, [4, 20, 60, 180, 320, 450], 30, 50, 50),
            "Income Tax",
            OtherProperty("Reading Railroad", 200, 25, 100, "Railroad"),
            Property("Oriental Avenue", "Light Blue", 100, [6, 30, 90, 270, 400, 550], 50, 50, 50),
            "Chance",
            Property("Vermont Avenue", "Light Blue", 100, [6, 30, 90, 270, 400, 550], 50, 50, 50),
            Property("Connecticut Avenue", "Light Blue", 120, [8, 40, 100, 300, 450, 600], 60, 50, 50),
            "Jail",
            Property("St. Charles Place", "Pink", 140, [10, 50, 150, 450, 625, 750], 70, 100, 100),
            OtherProperty("Electric Company", 150, 1, 75, "Utility"),
            Property("States Avenue", "Pink", 140, [10, 50, 150, 450, 625, 750], 70, 100, 100),
            Property("Virginia Avenue", "Pink", 160, [12, 60, 180, 500, 700, 900], 80, 100, 100),
            OtherProperty("Pennsylvania Railroad", 200, 25, 100, "Railroad"),
            Property("St. James Place", "Orange", 180, [14, 70, 200, 550, 750, 950], 90, 100, 100),
            "Community Chest",
            Property("Tennessee Avenue", "Orange", 180, [14, 70, 200, 550, 750, 950], 90, 100, 100),
            Property("New York Avenue", "Orange", 200, [16, 80, 220, 600, 800, 1000], 100, 100, 100),
            "Free Parking",
            Property("Kentucky Avenue", "Red", 220, [18, 90, 250, 700, 875, 1050], 110, 150, 150),
            "Chance",
            Property("Indiana Avenue", "Red", 220, [18, 90, 250, 700, 875, 1050], 110, 150, 150),
            Property("Illinois Avenue", "Red", 240, [20, 100, 300, 750, 925, 1100], 120, 150, 150),
            OtherProperty("B. & O. Railroad", 200, 25, 100, "Railroad"),
            Property("Atlantic Avenue", "Yellow", 260, [22, 110, 330, 800, 975, 1150], 130, 150, 150),
            Property("Ventnor Avenue", "Yellow", 260, [22, 110, 330, 800, 975, 1150], 130, 150, 150),
            OtherProperty("Water Works", 150, 1, 75, "Utility"),
            Property("Marvin Gardens", "Yellow", 280, [24, 120, 360, 850, 1025, 1200], 140, 150, 150),
            "Go To Jail",
            Property("Pacific Avenue", "Green", 300, [26, 130, 390, 900, 1100, 1275], 150, 200, 200),
            Property("North Carolina Avenue", "Green", 300, [26, 130, 390, 900, 1100, 1275], 150, 200, 200),
            "Community Chest",
            Property("Pennsylvania Avenue", "Green", 320, [28, 150, 450, 1000, 1200, 1400], 160, 200, 200),
            OtherProperty("Short Line", 200, 25, 100, "Railroad"),
            "Chance",
            Property("Park Place", "Blue", 350, [35, 175, 500, 1100, 1300, 1500], 175, 200, 200),
            "Luxury Tax",
            Property("Boardwalk", "Blue", 400, [50, 200, 600, 1400, 1700, 2000], 200, 200, 200)
        ]
        # Somewhat ugly, but I need the reference to the object not a copy.
        self.available_properties = list(filter(lambda x: x is not None,
                                           [p if type(p) == Property or type(p) == OtherProperty
                                            else None for p in self.board]))

        count = 0
        # Maybe randomize for fairness? It matters a bit in Monopoly.
        for user_id, name in players.items():
            self.send_message("(" + str(count) + ") " + name + " has been added to the game.\n")
            self.players[user_id] = Player(user_id, count, name, 1500)
            self.ids += [count]
            count += 1
        self.send_message("The game of Monopoly has begun!")

    def get_players(self):
        return self.players

    def get_pending_payments(self):
        return self.pending_payments

    def send_message(self, text):
        try:
            #print(text)
            bot.send_message(chat_id=self.chat_id, text=text)
        except TelegramError as e:
            raise e

    def check_player_existence_and_turn(self, player):
        if player is None:
            self.send_message("You don't seem to exist!")
            return False

        if player.get_id() != self.turn:
            self.send_message("It is not currently your turn!")
            return False

        return True

    def update_image_gamestate(self):
        img = Image.open("monopoly_board.jpg")
        draw = ImageDraw.Draw(img)

        for p in self.players.values():
            draw.rectangle((1522, 88 + p.get_id() * 40), (1542, 108 + p.get_id() * 40), fill=p.get_icon_color())

    def check_pass_go(self, text, last_total_roll, current_total_roll, player):
        if player.get_position() == 0 and current_total_roll > 0:
            self.send_message("You landed on Go and collected $200!")
            player.add_money(200)
            return

        if last_total_roll // len(self.board) < current_total_roll // len(self.board):
            self.send_message("You " + text + " Go and collected $200!")
            player.add_money(200)

    def get_player_by_local_id(self, id):
        for p in self.players.values():
            if p.get_id() == id:
                return p
        return None

    def get_player_by_name(self, name):
        for p in self.players.values():
            if p.get_name().lower() == name.lower():
                return p
        return None

    def pay_bail(self, id):
        player = self.players.get(id)

        if not self.check_player_existence_and_turn(player):
            return

        if player.get_turns_left_in_jail() == -1:
            self.send_message("You are not currently in jail!")
            return

        if player.get_money() < 50:
            self.send_message("You don't have enough in money to pay your $50 bail!")
            return

        if player.get_total_assets() < 50:
            self.send_message("You don't even have enough in total assets to pay your $50 bail!")
            return

        if player.get_money() >= 50:
            player.set_turns_left_in_jail(-1)
            player.add_money(-50)
            self.send_message("You have paid your $50 bail and escaped jail!")
            return

        if player.get_total_assets() >= 50:
            self.send_message("You have enough in total assets to pay your bail, \
                              but you need to sell some houses or mortgage some properties.")

    def use_get_out_of_jail_free_card(self, id):
        player = self.players.get(id)

        if not self.check_player_existence_and_turn(player):
            return

        if player.get_turns_left_in_jail() == -1:
            self.send_message("You are not currently in jail!")
            return

        if player.get_get_out_free_cards() <= 0:
            self.send_message("You don't have any Get Out of Jail Free cards!")
            return

        player.set_turns_left_in_jail(-1)
        player.remove_out_free_card()
        self.send_message("You have used a Get Out of Jail Free card to escape jail!")

    # This pay will be called using the pending pays list in the game.
    def pay(self, from_id, to_id, amount):
        payer = self.players.get(from_id)
        if to_id is None or to_id == "bank":
            payee = None
        else:
            if to_id.isdigit():
                payee = self.get_player_by_local_id(int(to_id))
            else:
                payee = self.get_player_by_name(to_id)

        if (payer, payee, amount) not in self.pending_payments:
            self.send_message("That transaction is not a pending payment!")
            return

        if payee is None:
            if payer.get_money() >= amount:
                payer.add_money(-amount)
                self.pending_payments.remove((payer, payee, amount))
                self.send_message("You paid the bank $" + str(amount) + "!")
            elif payer.get_total_assets() < amount:
                self.send_message("You do not have enough total assets to pay the bank!")
                self.send_message("You can either go bankrupt or convince someone else to trade for what you need!")
            else:
                self.send_message("You have enough total assets to pay the bank, but need to sell some houses or "
                                  "mortgage properties.")
        else:
            if payer.get_money() >= amount:
                payer.add_money(-amount)
                payee.add_money(amount)
                self.pending_payments.remove((payer, payee, amount))
                self.send_message("You paid " + payee.get_name() + " $" + str(amount) + "!")
            elif payer.get_total_assets() < amount:
                self.send_message("You do not have enough total assets to pay " + payee.get_name() + "!")
                self.send_message("You can either go bankrupt or convince someone else to trade for what you need!")
            else:
                self.send_message("You have enough total assets to pay " + payee.get_name() + \
                                  ", but need to sell some houses or mortgage properties.")

    def end_turn(self, id):
        player = self.players.get(id)

        if not self.check_player_existence_and_turn(player):
            return

        if sum(self.last_roll) == -1:
            self.send_message("You must roll the dice before ending your turn!")
            return

        if len(self.pending_payments) > 0:
            self.send_message("You cannot end the turn! There are still pending payments to be made!")
            for p in self.pending_payments:
                text = p[0].get_name() + " owes "
                if p[1] is None:
                    text += "the bank"
                else:
                    text += p[1].get_name()
                text += " $" + str(p[2]) + "!"
            return

        self.pending_trade = None

        if not self.has_doubles:
            self.turn = self.ids[(self.ids.index(self.turn) + 1) % len(self.players)]
        self.last_roll = [-1]
        self.has_doubles = False

        #self.send_message(player.get_name() + " has ended their turn.")
        self.send_message(player.get_name() + " has ended their turn. The current player's turn is: " + \
                          self.get_player_by_local_id(self.turn).get_name())

    # I need to be careful about making sure the objects aren't copied.
    # I need the original objects to be passed around.
    def purchase_property(self, id):
        player = self.players.get(id)
        property = self.board[player.get_position()]

        if not self.check_player_existence_and_turn(player):
            return

        if property not in self.available_properties:
            self.send_message("You cannot buy a property that is already owned or isn't a property!")
            return

        property_cost = property.get_cost()

        if player.get_money() < property_cost:
            self.send_message("You do not have enough money to buy this property!")
            return

        player.add_money(-property_cost)
        property.set_owner(player)
        self.available_properties.remove(property)
        player.add_property(property)
        player.sort_props_by_color()

        self.send_message("You have purchased " + property.get_name() + " for $" + str(property_cost) + "!")

    def mortgage_property(self, id, prop_id):
        player = self.players.get(id)
        property = player.get_property_by_id(prop_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot mortgage a property that isn't yours!")
            return

        if property.get_mortgaged():
            self.send_message("You cannot mortgage a property that's already mortgaged!")
            return

        # I'm going to have mortgage property autosell the houses and hotels on the property.

        mortgage_value = property.get_mortgage_value()
        if type(property) == Property:
            mortgage_value += property.get_houses() * property.get_house_cost()
            mortgage_value += property.get_hotels() * property.get_hotel_cost() + \
                              property.get_hotels() * property.get_house_cost() * 4
            property.set_houses(0)
            property.set_hotels(0)

        player.add_money(mortgage_value)
        property.set_mortgaged(True)
        self.send_message("You have mortgaged " + property.get_name() + " for $" + str(mortgage_value) + "!")


    def unmortgage_property(self, id, prop_id):
        player = self.players.get(id)
        property = player.get_property_by_id(prop_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot mortgage a property that isn't yours!")
            return

        if not property.get_mortgaged():
            self.send_message("You cannot unmortgage a property that isn't mortgaged!")
            return

        unmortgage_cost = property.get_mortgage_value()

        if player.get_money() < unmortgage_cost:
            self.send_message("You don't have enough in money to unmortgage that property!")
            return

        if player.get_total_assets() < unmortgage_cost:
            self.send_message("You don't even have enough in total assets to unmortgage that property!")
            return

        player.add_money(-unmortgage_cost)
        property.set_mortgaged(False)
        self.send_message("You have unmortgaged " + property.get_name() + " for $" + str(unmortgage_cost) + "!")

    # This will work as follows:
    # The current turn player will propose a trade -- if one is not in progress.
    # They choose with whom they want to trade, which sets the Game variable.
    # They can then add props, money, and cards to the trade as desired.
    # They can also remove them as desired.
    # They also specify what they want from the other player.
    # The other player can also change these terms simultaneously.
    # Once both players agree to the trade, it will go through.
    def setup_trade(self, id_1, id_2):
        player_1 = self.players.get(id_1)
        player_2 = self.get_player_by_local_id(id_2)

        if not self.check_player_existence_and_turn(player_1):
            return

        if player_2 is None:
            self.send_message("The second trader doesn't seem to exist!")
            return

        self.pending_trade = [player_1, player_2, 0, 0, [], [], 0, 0, False, False]
        self.send_message("A trade is now pending between " + player_1.get_name() + " and " + player_2.get_name() + "!")

    def cancel_trade(self, id):
        player = self.players.get(id)

        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        if player not in self.pending_trade:
            self.send_message("You are not in this trade and therefore cannot cancel it.")
            return

        self.pending_trade = None
        self.send_message("The pending trade has been cancelled.")

    # Both players call this to add items to the trade. The agreement on what to add is
    # made in the chat.
    def add_to_trade(self, id, prop, money, cards):
        player = self.players.get(id)

        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        if player not in self.pending_trade:
            self.send_message("You are not in this trade and therefore cannot change its terms.")
            return

        if self.pending_trade[8] or self.pending_trade[9]:
            self.send_message("At least one person has agreed to the current trade. You cannot change its terms.")
            return

        if money < 0:
            self.send_message("You cannot trade negative money.")
            return

        if cards < 0:
            self.send_message("You cannot trade negative quantities of cards.")
            return

        if player == self.pending_trade[0]:
            current_money = self.pending_trade[2]
            current_props = self.pending_trade[4]
            current_cards = self.pending_trade[6]
        elif player == self.pending_trade[1]:
            current_money = self.pending_trade[3]
            current_props = self.pending_trade[5]
            current_cards = self.pending_trade[7]

        if money + current_money > player.get_money():
            self.send_message("You cannot trade more money than you have!")
            return

        if prop >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        if prop >= 0:
            property = player.get_property_by_id(prop)

            if property in current_props:
                self.send_message("That property is already in the trade!")
                return

            if property.get_houses() > 0 or property.get_hotels() > 0:
                self.send_message("You cannot trade a property with houses or hotels on it.")
                return

            color_count = 0
            hh_count = 0
            prop_color = property.get_color()
            for p in player.get_properties():
                if type(p) == Property and p.get_color() == prop_color:
                    color_count += 1
                    hh_count += p.get_houses() + p.get_hotels()

            if color_count == 2 and (prop_color == "Dark Blue" or prop_color == "Brown") and hh_count > 0:
                self.send_message("You cannot trade a property in a monopoly "
                                  "if any other properties in the monopoly have houses or hotels!")
                return
            if color_count == 3 and not (prop_color == "Dark Blue" or prop_color == "Brown") and hh_count > 0:
                self.send_message("You cannot trade a property in a monopoly "
                                  "if any other properties in the monopoly have houses or hotels!")
                return

        if cards + current_cards > player.get_get_out_free_cards():
            self.send_message("You do not have that many Get Out of Jail Free cards to trade!")
            return

        if player == self.pending_trade[0]:
            self.pending_trade[2] += money
            if prop >= 0: self.pending_trade[4].append(property)
            self.pending_trade[6] += cards
        elif player == self.pending_trade[1]:
            self.pending_trade[3] += money
            if prop >= 0: self.pending_trade[5].append(property)
            self.pending_trade[7] += cards

        text = "The following is now in the trade. \n\n From " + self.pending_trade[0].get_name() + ":\n\n" + \
                          "Money: $" + str(self.pending_trade[2]) + "\n" + "Get Out of Jail Free cards: " + \
                          str(self.pending_trade[6]) + "\n" + "Properties:\n"

        for p in self.pending_trade[4]:
            if type(p) == Property:
                text += p.get_name() + " : " + p.get_color() + \
                        " (" + str(p.get_houses()) + " houses, " + str(p.get_hotels()) + " hotels)" + \
                        " [Mortgage Value: " + str(p.get_mortgage_value()) + "] " + \
                        ("[[Mortgaged]]\n" if p.get_mortgaged() else "\n")
            elif type(p) == OtherProperty:
                text += p.get_name() + " : " + p.get_type() + "\n" + \
                        " [Mortgage Value: " + str(p.get_mortgage_value()) + "] " + \
                        ("[[Mortgaged]]\n" if p.get_mortgaged() else "\n")

        text += "\nFrom " + self.pending_trade[1].get_name() + ":\n\n" + \
                          "Money: $" + str(self.pending_trade[3]) + "\n" + "Get Out of Jail Free cards: " + \
                          str(self.pending_trade[7]) + "\n" + "Properties:\n"
        for p in self.pending_trade[5]:
            text += p.get_name()
            if type(p) == Property:
                text += " (" + p.get_color() + ")\n"
            elif type(p) == OtherProperty:
                text += " (" + p.get_type() + ")\n"

        self.send_message(text)

    def remove_from_trade(self, id, prop, money, cards):
        player = self.players.get(id)

        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        if player not in self.pending_trade:
            self.send_message("You are not in this trade and therefore cannot change its terms.")
            return

        if self.pending_trade[8] or self.pending_trade[9]:
            self.send_message("At least one person has agreed to the current trade. You cannot change its terms.")
            return

        if player == self.pending_trade[0]:
            current_money = self.pending_trade[2]
            current_props = self.pending_trade[4]
            current_cards = self.pending_trade[6]
        elif player == self.pending_trade[1]:
            current_money = self.pending_trade[3]
            current_props = self.pending_trade[5]
            current_cards = self.pending_trade[7]

        if prop >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        if prop >= 0:
            property = player.get_property_by_id(prop)

            if property not in current_props:
                self.send_message("That property is not in the trade!")
                return

        # Money and cards when removed are thresholded to 0 if lower than 0.
        if player == self.pending_trade[0]:
            self.pending_trade[2] = 0 if current_money - money <= 0 else self.pending_trade[2] - money
            if prop >= 0: self.pending_trade[4].remove(property)
            self.pending_trade[6] = 0 if current_cards - cards <= 0 else self.pending_trade[6] - cards
        elif player == self.pending_trade[1]:
            self.pending_trade[3] = 0 if current_money - money <= 0 else self.pending_trade[2] - money
            if prop >= 0: self.pending_trade[5].remove(property)
            self.pending_trade[7] = 0 if current_cards - cards <= 0 else self.pending_trade[6] - cards

        text = "The following is now in the trade. \n\n From " + self.pending_trade[0].get_name() + ":\n\n" + \
                          "Money: $" + str(self.pending_trade[2]) + "\n" + "Get Out of Jail Free cards: " + \
                          str(self.pending_trade[6]) + "\n" + "Properties:\n"
        for p in self.pending_trade[4]:
            text += p.get_name() + "\n"

        text += "\nFrom " + self.pending_trade[1].get_name() + ":\n\n" + \
                          "Money: $" + str(self.pending_trade[3]) + "\n" + "Get Out of Jail Free cards: " + \
                          str(self.pending_trade[7]) + "\n" + "Properties:\n"
        for p in self.pending_trade[5]:
            text += p.get_name() + "\n"
        self.send_message(text)

    def agree_to_trade(self, id):
        player = self.players.get(id)

        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        if player not in self.pending_trade:
            self.send_message("You are not in this trade and therefore cannot agree to have it.")
            return

        if player == self.pending_trade[0]:
            self.pending_trade[8] = True
        elif player == self.pending_trade[1]:
            self.pending_trade[9] = True

        self.send_message(player.get_name() + " has agreed to the trade!")

    def disagree_to_trade(self, id):
        player = self.players.get(id)

        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        if player not in self.pending_trade:
            self.send_message("You are not in this trade and therefore cannot agree to have it.")
            return

        if player == self.pending_trade[0]:
            self.pending_trade[8] = False
        elif player == self.pending_trade[1]:
            self.pending_trade[9] = False

        self.send_message(player.get_name() + " has disagreed to the trade!")

    def trade(self, bankrupt=False):
        if self.pending_trade is None:
            self.send_message("There is no pending trade!")
            return

        player_1 = self.pending_trade[0]
        player_2 = self.pending_trade[1]
        money_from_1 = self.pending_trade[2]
        money_from_2 = self.pending_trade[3]
        props_from_1 = self.pending_trade[4]
        props_from_2 = self.pending_trade[5]
        cards_from_1 = self.pending_trade[6]
        cards_from_2 = self.pending_trade[7]
        agreed_1 = self.pending_trade[8]
        agreed_2 = self.pending_trade[9]

        if not agreed_1 or not agreed_2:
            self.send_message("At least one of the players has not consented to this trade.")
            return

        # I might do the checks when the player is adding items to the trade rather
        # than when the trade occurs? Either way, maybe keeping this here is a good
        # precaution.
        if money_from_1 > player_1.get_money() or money_from_2 > player_2.get_money():
            self.send_message("You cannot trade more money than you have!")
            return

        if not all(p in player_1.get_properties() for p in props_from_1) or not all(p in player_2.get_properties()
                                                                                    for p in props_from_2):
            self.send_message("You cannot trade properties you do not have!")
            return

        if cards_from_1 > player_1.get_get_out_free_cards() or cards_from_2 > player_2.get_get_out_free_cards():
            self.send_message("You cannot trade more Get Out of Jail free cards than you have!")
            return

        if not bankrupt:
            player_1.add_money(-money_from_1)
            player_1.add_money(money_from_2)
            self.send_message(player_2.get_name() + " has traded $" + str(money_from_2) +
                              " to " + player_1.get_name() + "!")
        player_2.add_money(-money_from_2)
        player_2.add_money(money_from_1)
        self.send_message(player_1.get_name() + " has traded $" + str(money_from_1) +
                          " to " + player_2.get_name() + "!")

        if not bankrupt:
            for p in props_from_2:
                player_2.remove_property(p)
                p.set_owner(player_1)
                player_1.add_property(p)
                self.send_message(player_2.get_name() + " has traded " + p.get_name() + " to " + player_1.get_name() + "!")
        for p in props_from_1:
            player_1.remove_property(p)
            p.set_owner(player_2)
            player_2.add_property(p)
            self.send_message(player_1.get_name() + " has traded " + p.get_name() + " to " + player_2.get_name() + "!")

        if not bankrupt:
            for i in range(cards_from_2):
                player_1.add_out_free_card()
        for i in range(cards_from_1):
            player_2.add_out_free_card()

        if not bankrupt:
            self.send_message(player_2.get_name() + " has traded " + str(cards_from_2) + " cards to " + player_1.get_name() + "!")
        self.send_message(player_1.get_name() + " has traded " + str(cards_from_1) + " cards to " + player_2.get_name() + "!")

        player_1.sort_props_by_color()
        player_2.sort_props_by_color()

        if not bankrupt:
            self.send_message("The trade has completed!")

    def purchase_house(self, id, property_id):
        player = self.players.get(id)

        if property_id < 0 or property_id >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        property = player.get_property_by_id(property_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot buy a house on a property that isn't yours!")
            return

        if type(property) == OtherProperty:
            self.send_message("You cannot buy houses on a Railroad or Utility!")
            return

        if property.get_houses() == 4 or property.get_hotels() == 1:
            self.send_message("That property has the maximium number of houses already!")
            return

        color_count = 0
        prop_color = property.get_color()
        for p in player.get_properties():
            if type(p) == Property and p.get_color() == prop_color:
                color_count += 1

        if color_count < 2 and (prop_color == "Dark Blue" or prop_color == "Brown"):
            self.send_message("You do not own the full set of this color property!")
            return
        if color_count < 3 and not (prop_color == "Dark Blue" or prop_color == "Brown"):
            self.send_message("You do not own the full set of this color property!")
            return

        if player.get_money() < property.get_house_cost():
            self.send_message("You do not have enough money to afford a house on that property!")
            return

        player.add_money(-property.get_house_cost())
        property.add_house()
        self.send_message("You have added a house to " + property.get_name() + "!")

    def purchase_hotel(self, id, property_id):
        player = self.players.get(id)

        if property_id < 0 or property_id >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        property = player.get_property_by_id(property_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot buy a hotel on a property that isn't yours!")
            return

        if type(property) == OtherProperty:
            self.send_message("You cannot buy hotels on a Railroad or Utility!")
            return

        if property.get_houses() < 4 or property.get_hotels() == 1:
            self.send_message("That property has too few houses or already has a hotel!")
            return

        if player.get_money() < property.get_hotel_cost():
            self.send_message("You do not have enough money to afford a hotel on that property!")
            return

        player.add_money(-property.get_hotel_cost())
        property.add_hotel()
        self.send_message("You have added a hotel to " + property.get_name() + "!")

    def sell_house(self, id, property_id):
        player = self.players.get(id)

        if property_id < 0 or property_id >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        property = player.get_property_by_id(property_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot sell a house on a property that isn't yours!")
            return

        if type(property) == OtherProperty:
            self.send_message("You cannot sell houses on a Railroad or Utility!")
            return

        if property.get_houses() == 0:
            self.send_message("That property has no houses!")
            return

        color_count = 0
        prop_color = property.get_color()
        for p in player.get_properties():
            if type(p) == Property and p.get_color() == prop_color:
                color_count += 1

        if color_count < 2 and (prop_color == "Blue" or prop_color == "Brown"):
            self.send_message("You do not own the full set of this color property!")
            return
        if color_count < 3 and not (prop_color == "Blue" or prop_color == "Brown"):
            self.send_message("You do not own the full set of this color property!")
            return

        player.add_money(property.get_house_cost())
        property.remove_house()
        self.send_message("You have removed a house from " + property.get_name() + "!")

    def sell_hotel(self, id, property_id):
        player = self.players.get(id)

        if property_id < 0 or property_id >= len(player.get_properties()):
            self.send_message("That is not a property you own.")
            return

        property = player.get_property_by_id(property_id)

        if not self.check_player_existence_and_turn(player):
            return

        if property not in player.get_properties():
            self.send_message("You cannot sell a hotel on a property that isn't yours!")
            return

        if type(property) == OtherProperty:
            self.send_message("You cannot sell hotels on a Railroad or Utility!")
            return

        if property.get_hotels() == 0:
            self.send_message("That property does not have a hotel!")
            return

        player.add_money(property.get_hotel_cost())
        property.remove_hotel()
        self.send_message("You have removed a hotel from " + property.get_name() + "!")

    def chance_result(self, player):
        # Due to the difficulty of implementation, I've skipped implementing
        # the chance card that say "Advance to the nearest..."
        card = random.randint(0, 12)
        if card == 0:
            self.send_message("Chance Card: Advance to Go! Collect $200!")
            pos = player.get_position()
            player.set_position(0)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll(0 - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 1:
            self.send_message("Chance Card: Advance to Illinois Avenue!")
            pos = player.get_position()
            player.set_position(24)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll(24 - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 2:
            self.send_message("Chance Card: Advance to St. Charles Place!")
            pos = player.get_position()
            player.set_position(11)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll(11 - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 3:
            self.send_message("Chance Card: Band pays you dividend of $50.")
            player.add_money(50)
        elif card == 4:
            self.send_message("Chance Card: You got a Get Out of Jail Free card!")
            player.add_out_free_card()
        elif card == 5:
            self.send_message("Chance Card: Go back three spaces!")

            player.set_position((player.get_position() - 3) % len(self.board))
            player.add_to_total_roll(-3)

            self.enact_roll_result(player)
        elif card == 6:
            self.send_message("Chance Card: Go directly to jail!")
            pos = player.get_position()
            player.set_position(10)

            player.add_to_total_roll(10 - pos)

            player.set_turns_left_in_jail(3)
        elif card == 7:
            self.send_message("Chance Card: Make general repairs on all your property! For each house pay $25, "
                              "for each hotel pay $100!")
            owed = 0
            for p in player.get_properties():
                if type(p) == Property:
                    owed += p.get_houses() * 25 + p.get_hotels() * 100
            self.send_message("You owe $" + str(owed) + " in total.")
            if owed > 0:
                self.pending_payments.append((player, None, owed))
        elif card == 8:
            self.send_message("Chance Card: Pay poor tax of $15.")
            self.pending_payments.append((player, None, 15))
        elif card == 9:
            self.send_message("Chance Card: Take a trip to Reading Railroad!")
            pos = player.get_position()
            player.set_position(5)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll(5 - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 10:
            self.send_message("Chance Card: Take a walk on the Boardwalk!")
            pos = player.get_position()
            player.set_position(len(self.board) - 1)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll((len(self.board) - 1) - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 11:
            self.send_message("Chance Card: You've been elected chairman of the board! Pay each player $50.")
            for id in self.players.keys():
                if id != player.get_id():
                    self.pending_payments.append((player, self.players[id], 50))
        elif card == 12:
            self.send_message("Chance Card: Your building loan matures! Recieve $150.")
            player.add_money(150)

    def cc_result(self, player):
        card = random.randint(0, 14)
        if card == 0:
            self.send_message("Community Chest Card: Advance to Go! Collect $200!")
            pos = player.get_position()
            player.set_position(0)

            last_total_roll = player.get_total_roll()
            player.add_to_total_roll(0 - pos)
            current_total_roll = player.get_total_roll()
            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)
        elif card == 1:
            self.send_message("Community Chest Card: Bank error in your favor! Collect $200!")
            player.add_money(200)
        elif card == 2:
            self.send_message("Community Chest Card: Doctor's fees! Pay $50.")
            self.pending_payments.append((player, None, 50))
        elif card == 3:
            self.send_message("Community Chest Card: From stock sale you get $50!")
            player.add_money(50)
        elif card == 4:
            self.send_message("Community Chest Card: You got a Get Out of Jail Free card!")
            player.add_out_free_card()
        elif card == 5:
            self.send_message("Community Chest Card: Go directly to jail!")
            pos = player.get_position()
            player.set_position(10)

            player.add_to_total_roll(10 - pos)

            player.set_turns_left_in_jail(3)
        elif card == 6:
            self.send_message("Community Chest Card: Holiday fund matures. Collect $100!")
            player.add_money(100)
        elif card == 7:
            self.send_message("Community Chest Card: Income tax refund. Collect $20!")
            player.add_money(20)
        elif card == 8:
            self.send_message("Community Chest Card: It's your birthday! Collect $10 from each player.")
            for id in self.players.keys():
                if id != player.get_id():
                    self.pending_payments.append((self.players[id], player, 10))
        elif card == 9:
            self.send_message("Community Chest Card: Life insurance matures. Collect $100!")
            player.add_money(100)
        elif card == 10:
            self.send_message("Community Chest Card: School fees! Pay $50.")
            self.pending_payments.append((player, None, 50))
        elif card == 11:
            self.send_message("Community Chest Card: Receive $25 consultancy fee!")
            player.add_money(25)
        elif card == 12:
            self.send_message("Community Chest Card: You are assessed for street repairs: Pay $40 per house "
                              "and $115 per hotel you own.")
            owed = 0
            for p in player.get_properties():
                if type(p) == Property:
                    owed += p.get_houses() * 40 + p.get_hotels() * 115
            self.send_message("You owe $" + str(owed) + " in total.")
            if owed > 0:
                self.pending_payments.append((player, None, owed))
        elif card == 13:
            self.send_message("Community Chest Card: You won second place in a beauty contest. Receive $10!")
            player.add_money(10)
        elif card == 14:
            self.send_message("Community Chest Card: You inherit $100!")
            player.add_money(100)

    def enact_roll_result(self, player):
        position = player.get_position()
        if position > len(self.board):
            self.send_message("You have somehow managed to get to a position not on the board!")
            return

        if self.board[position] == "Go":
            #self.check_pass_go("landed on", 0, player.get_total_roll(), player)
            return

        if self.board[position] == "Go To Jail":
            self.send_message("You landed on Go To Jail! As you might expect, you're going to jail. "
                              "You can pay your $50 bail now using /bail if you wish.")
            pos = player.get_position()
            player.set_position(10)

            player.add_to_total_roll(10 - pos)

            player.set_turns_left_in_jail(3)
            return

        if self.board[position] == "Free Parking":
            self.send_message("You landed on Free Parking!")
            return

        if self.board[position] == "Jail" and player.get_turns_left_in_jail() != -1:
            self.send_message("You are currently in jail! Escape by rolling doubles, a Get Out of Jail Free card, "
                              "or paying your $50 bail.")
            return

        if self.board[position] == "Jail" and player.get_turns_left_in_jail() == -1:
            self.send_message("You are currently visiting jail.")
            return

        if self.board[position] == "Chance":
            self.chance_result(player)
            return

        if self.board[position] == "Community Chest":
            self.cc_result(player)
            return

        if self.board[position] == "Luxury Tax":
            self.send_message("You landed on Luxury Tax! Pay $100.")
            self.pending_payments.append((player, None, 100))
            return

        if self.board[position] == "Income Tax":
            self.send_message("You landed on Income Tax! Pay $200.")
            self.pending_payments.append((player, None, 200))
            return

        if type(self.board[position]) == Property:
            property = self.board[position]
            self.send_message("You landed on " + property.get_name() + "!")

            if property in self.available_properties:
                self.send_message("This property is available! You can buy " + \
                                  str(property.get_name()) + " (" + str(property.get_color()) + ") for $" + \
                                  str(property.get_cost()) + ".")
                return
            else:
                if property not in player.get_properties():
                    owner = property.get_owner()
                    rent = property.get_rent()
                    if not property.get_mortgaged():
                        self.send_message("You owe " + owner.get_name() + " $" + str(rent) + ".")
                        self.pending_payments.append((player, owner, rent))
                    else:
                        self.send_message("This property is mortgaged!")
                else:
                    self.send_message("You own this property!")

        if type(self.board[position]) == OtherProperty:
            property = self.board[position]
            self.send_message("You landed on " + property.get_name() + "!")

            if property in self.available_properties:
                self.send_message("This property is available! You can buy " + \
                                  str(property.get_name()) + " for $" + str(property.get_cost()) + ".")
                return
            else:
                if property not in player.get_properties():
                    owner = property.get_owner()
                    rent = property.get_rent()
                    if property.get_type() == "Railroad":
                        num_railroads = 0
                        for p in owner.get_properties():
                            if type(p) == OtherProperty and p.get_type() == "Railroad":
                                num_railroads += 1
                        final_rent = rent * 2 ** (num_railroads - 1)
                        self.send_message("You owe " + owner.get_name() + " $" + str(final_rent) + ".")
                        self.pending_payments.append((player, owner, final_rent))
                    elif property.get_type() == "Utility":
                        num_utils = 0
                        for p in owner.get_properties():
                            if type(p) == OtherProperty and p.get_type() == "Utility":
                                num_utils += 1
                        rent = 10 * sum(self.last_roll) if num_utils == 2 else 4 * sum(self.last_roll)
                        self.send_message("You owe " + owner.get_name() + " $" + str(rent) + ".")
                        self.pending_payments.append((player, owner, rent))
                    else:
                        self.send_message("This is not a valid property type!")
                else:
                    self.send_message("You own this property!")

    def bankrupt(self, id_1, id_2):
        # Player 1 bankrupts to Player 2.
        player_1 = self.players.get(id_1)
        player_2 = self.get_player_by_local_id(id_2)

        if player_1 is None:
            self.send_message("You do not seem to exist!")
            return

        if player_2 is None:
            self.send_message("The other player does not seem to exist!")
            return

        self.pending_trade = (player_1, player_2, player_1.get_money(), 0, player_1.get_properties(), [],
                              player_1.get_get_out_free_cards(), 0, True, True)
        self.trade()
        self.send_message(player_1.get_name() + " has bankrupted to " + player_2.get_name() + "!")

        self.ids.remove(self.players[id_1].get_id())
        del self.players[id_1]
        self.turn = self.turn % len(self.players)

        self.pending_trade = None
        self.pending_payments = None
        self.has_doubles = False
        self.last_roll = [-1]

        self.send_message("The current player's turn is: " + self.get_player_by_local_id(self.turn).get_name())

    def roll_dice(self, id):
        player = self.players.get(id)

        if not self.check_player_existence_and_turn(player):
            return

        if sum(self.last_roll) != -1:
            self.send_message("You already rolled this turn!")
            return

        roll = self.dice.roll()
        self.has_doubles = self.dice.check_doubles(roll)

        text = "You rolled a ["
        for n in roll:
            text += str(n) + ","
        text = text[:-1]
        text += "]!"

        self.send_message(text)

        if self.has_doubles:
            self.send_message("You rolled doubles! You'll get an extra turn after this.")

        if player.get_turns_left_in_jail() > 0 and self.has_doubles:
            player.set_turns_left_in_jail(-1)
            self.last_roll = [-1]

            self.send_message("You escaped jail!")
        elif player.get_turns_left_in_jail() > 0 and not self.has_doubles:
            player.set_turns_left_in_jail(player.get_turns_left_in_jail() - 1)
            self.send_message("You did not escape jail! You can wait, pay $50 bail, "
                              "or use a Get Out of Jail Free card.")
            self.last_roll = roll
        else:
            player.set_turns_left_in_jail(-1)

            last_total_roll = player.get_total_roll()
            self.last_roll = roll
            player.set_position((player.get_position() + sum(roll)) % len(self.board))
            player.add_to_total_roll(sum(roll))
            current_total_roll = player.get_total_roll()

            self.check_pass_go("passed", last_total_roll, current_total_roll, player)

            self.enact_roll_result(player)

"""
if __name__ == "__main__":
    players = {"0" : "name", "1" : "name2"}
    game = Game("test", players)
    game.bankrupt("1")
"""