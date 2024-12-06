from blackjack import BlackJackGame
from player import Player
import matplotlib.pyplot as plt
import numpy as np

class GameData:
    def __init__(self, game):
        self.game: BlackJackGame = game
        self.players = self.game.players
        self.dealer = self.game.dealer
        self.bankrollData = {}
        self.getPlayerBankrollSnapshots()
    
    def getPlayerBankrollSnapshots(self):
        for player in self.players:
            self.bankrollData.update({player.name: player.bankrollSnapshots})
    print("Tracked bankroll data for all players, including Monte Carlo Agent.")

    def plotBankrollTime(self):
        numHands = self.game.numHands
        fig, ax = plt.subplots()
        for player in self.players:
            ax.plot(
                range(1, len(player.bankrollSnapshots) + 1),
                player.bankrollSnapshots,
                label=player.name
            )

        ax.set_title(f"Players' Bankrolls Over {numHands} Rounds")
        ax.set_xlabel("Round Number")
        ax.set_ylabel("Bankroll ($)")
        ax.legend(title="Players", loc="upper left")
        plt.tight_layout()
        plt.show()

