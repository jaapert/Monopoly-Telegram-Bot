import pytest
import re

from monopoly import *

class FakeDice:
    def __init__(self, seq):
        self.s = seq

    def roll(self):
        return self.s.pop(0)

    def check_doubles(self, r):
        return len(r) == 2 and r[0] == r[1]


class FakeBot:
    def __init__(self):
        self.msgs = []

    def send_message(self, chat_id, text):
        self.msgs.append(text)

    def pop(self):
        self.msgs.pop(0)


class FakeGame(Game):
    def __init__(self, chat_id, players, bot):
        self._msgs = []
        super().__init__(chat_id, players, bot)

    def send_message(self, text):
        self._msgs.append(text)

    def get_message(self):
        if len(self._msgs) == 0:
            return None
        return self._msgs.pop(0)

    def clear_messages(self):
        self._msgs.clear()

    def match_message(self, pattern) -> bool:
        """match the top message to pattern. False if the stack is empty"""
        if len(self._msgs) == 0:
            return False
        m = self._msgs.pop(0)
        print(m)
        return bool(re.search(pattern, m))


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def game(nplayers=5):
    players = {}
    for id in range(0, nplayers):
        players[id] = f"testplayer_{id}"
    game = FakeGame("aaa", players, bot)
    game._msgs.clear()
    return game


def test_bankrupt_to_other_user_in_debt(game):
    """ Make sure we can only bankrupt to the user we're in debt to because we
    landed on their property"""

    p0 = game.get_players()[0]
    p1 = game.get_players()[1]
    p2 = game.get_players()[2]

    p0.set_position(1)
    game.purchase_property(p0.id)
    p0.set_position(9)
    game.purchase_property(p0.id)

    game.clear_messages()
    assert len(p0.get_properties()) == 2

    p0.money = -500

    game.pending_payments.append((p0.id, p1.id, 500))

    cur_turn = game.turn
    assert cur_turn == p0.id

    game.bankrupt(p0.id, p2.id)
    assert game.match_message(r"You still have a payment")
    assert cur_turn == game.turn  # assert its still my turn
    assert len(p0.get_properties()) == 2

    game.bankrupt(p0.id, 'bank')
    assert game.match_message(r"You still have a payment")
    assert cur_turn == game.turn  # assert its still my turn
    assert len(p0.get_properties()) == 2

    assert len(p1.get_properties()) == 0  # target has no properties now
    p1_money = p1.money
    game.bankrupt(p0.id, p1.id)

    assert len(p1.get_properties()) == 2
    assert p1.money == p1_money  # target money shouldn't changes because p0 has no money


def test_bankrupt_to_other_user(game):
    p0 = game.get_players()[0]
    p1 = game.get_players()[1]

    p0.set_position(1)
    game.purchase_property(p0.id)
    p0.set_position(9)
    game.purchase_property(p0.id)

    game.clear_messages()
    assert len(p0.get_properties()) == 2
    p0.money = 1500

    p1_money = p1.money
    game.bankrupt(p0.id, p1.id)
    assert len(p1.get_properties()) == 2
    assert p1.money == (p1_money + 1500)


def test_bankrupt_bankr(game):
    p0 = game.get_players()[0]

    p0.set_position(1)
    game.purchase_property(p0.id)
    p0.set_position(9)
    game.purchase_property(p0.id)

    game.clear_messages()

    properties = p0.get_properties()

    assert len(properties) == 2

    game.bankrupt(p0.id, 'bank')
    assert properties[0].owner == None
    assert properties[1].owner == None


