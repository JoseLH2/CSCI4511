import click
from shoe import Shoe
from player import Player
from count import HiLoCount
from hand import Hand
from card import Card, CardValue
from dealer import Dealer, HouseRules
from bet import spread1_50, spread1_6
from typing import List
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
from game_actions import GameActions

isVerbose = False
vprint = print if isVerbose else lambda *a, **k: None

@click.command()
@click.option('-s', '--shoesize', default=6, help='An integer representing the amount of decks to use in the shoe. Default is 6 decks.')
@click.option('-b', '--bankroll', default=10000, help='Determines the amount of dollars that each player begins the game with in their bankroll. Default is $10000.')
@click.option('-h', '--hands', default=1000, help='Determines the number of hands to deal. Default is 1000.')
@click.option('-t', '--tablemin', default=10, help='Determines the minimum table bet. Default is $10.')
@click.option('-p', '--penetration', default=0.84, help='Dictates the deck penetration by the dealer. Default is 0.84 which means that the dealer will penetrate 84 percent of the shoe before re-shuffling.')
@click.option('-d', '--dealersettings', default="[17, True, True, True, True]", help='Assigns the dealer rules.')
@click.option('-v', '--verbose', default=False, help='Prints all player, hand, and game information.')
def main(shoesize, bankroll, hands, tablemin, penetration, dealersettings, verbose):

    print("Running blackjack simulation with variables:")
    print("Shoe size: ", shoesize, " | Bankroll: ", bankroll, " | Number of hands to simulate: ", hands, " | Minimum Table Bet: ", tablemin)
    houseRules = HouseRules(standValue=dealersettings[0], DASoffered=dealersettings[1], RSAoffered=dealersettings[2], LSoffered=dealersettings[3], doubleOnSoftTotal=dealersettings[4])
    game = BlackJackGame(shoesize, bankroll, hands, tablemin, penetration, houseRules)
    global isVerbose
    isVerbose = verbose
    game.startGame()
    gamedata = GameData(game)
    gamedata.getDealerStatistics()
    gamedata.getPlayerStatistics()
    gamedata.plotBankrollTime()

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
    
    def getDealerStatistics(self):
        print(" - - - - - ")
        print("Dealer losses: $", self.dealer.losses, " | Dealer gains: $", self.dealer.gains, " | Profit: $", self.dealer.gains - self.dealer.losses)
        print(" - - - - - ")
    
    def getPlayerStatistics(self):
        for player in self.players:
            handsPlayed = len(player.bankrollSnapshots) - 1
            winRate = player.handData[0] / handsPlayed * 100
            loseRate = player.handData[1] / handsPlayed * 100
            drawRate = player.handData[2] / handsPlayed * 100
            endBankroll = player.bankroll
            initialBankroll = player.bankrollSnapshots[0]
            diff = endBankroll - initialBankroll
            earningsPerHand = diff / handsPlayed
            percentChange = (endBankroll - initialBankroll) / initialBankroll * 100
            print(player.name, " | Win %", winRate, " | Lose %", loseRate, " | Draw %", drawRate)
            print("Earnings: ", diff, '(Percent Increase %', percentChange, ") | Average payout per hand: $", earningsPerHand)
    
    def plotBankrollTime(self):
        numHands = self.game.numHands
        playerNames = []
        fig, ax = plt.subplots()
        for player in self.players:
            ax.plot([item for item in range(1, len(player.bankrollSnapshots) + 1)], player.bankrollSnapshots, label=player.name)
            playerNames.append(player.name)
        ax.set_title("Plot of players' bankroll over time in a blackjack game of "+str(numHands)+" rounds")
        ax.set_xlabel("Round number")
        ax.set_ylabel("Bankroll ($)")
        
        # Add the legend
        pos = ax.get_position()
        ax.set_position([pos.x0, pos.y0, pos.width * 0.9, pos.height])
        ax.legend(loc='center right', bbox_to_anchor=(1.5, 0.5), title="Players")
        plt.tight_layout()
        plt.show()

class BlackJackGame:
    def __init__(self, shoeSize, bankroll, hands, tableMin, penetration, houseRules):
        vprint("Initializing game...")
        self.shoeSize = shoeSize
        self.bankroll = bankroll
        self.numHands = hands
        self.tableMin = tableMin
        self.penetration = penetration
        self.houseRules = houseRules
        self.tableMin = tableMin

        vprint("Dealer has rules: ")
        vprint("Deck Penetration %: ", penetration, " | Minimum table bet: $", tableMin)

        # Lazy imports for strategies to avoid circular import issues
        from strategies import BasicStrategy, CasinoStrategy, RandomStrategy, MonteCarloStrategy

        self.dealer = Dealer(penetration, shoeSize, houseRules, CasinoStrategy(houseRules, isCounting=False, accuracy=1), isVerbose)

        self.players = [
            Player("Counting with 1-6 Bet Spread", bankroll, BasicStrategy(houseRules, isCounting=True, accuracy=1), spread1_6(), isVerbose),
            Player("Counting with 1-50 Bet Spread", bankroll, BasicStrategy(houseRules, isCounting=True, accuracy=1), spread1_50(), isVerbose),
            Player('Counting with 1-6 Bet Spread, 50% Accurate Basic Strategy', bankroll, BasicStrategy(houseRules, isCounting=True, accuracy=0.50), spread1_6(), isVerbose),
            Player("Perfect Basic Strategy", bankroll, BasicStrategy(houseRules, isCounting=False, accuracy=1), spread1_6(), isVerbose),
            Player('99% Accurate Basic Strategy', bankroll, BasicStrategy(houseRules, isCounting=False, accuracy=0.99), spread1_50(), isVerbose),
            Player('95% Accurate Basic Strategy', bankroll, BasicStrategy(houseRules, isCounting=False, accuracy=0.95), spread1_50(), isVerbose),
            Player('75% Accurate Basic Strategy', bankroll, BasicStrategy(houseRules, isCounting=False, accuracy=0.75), spread1_50(), isVerbose),
            Player('Casino Rules', bankroll, CasinoStrategy(houseRules, isCounting=False, accuracy=1), spread1_6(), isVerbose),
            Player("Random", bankroll, RandomStrategy(houseRules, isCounting=False, accuracy=1), spread1_6(), isVerbose),
            Player("Monte Carlo Agent", bankroll, MonteCarloStrategy(houseRules, iterations=1000), spread1_6(), isVerbose)
        ]

        vprint("There are ", len(self.players), " players in the game.")
    def clearAllCards(self, players: List[Player]):
        # Collect the cards from each player before moving onto the next round and put the cards in the
        # discard pile
        for player in players:
            for hand in player.hands:
                if isVerbose: hand.printHand(player.name)
                self.dealer.discardPlayersCards(hand, player.name)
            
            player.clearAllHands()
        
        # Discard the dealer's cards and move them to the discard pile
        self.dealer.discardDealersCards()

    def dealDealersHand(self, count):
        # Deal out the dealers cards
        upcard = self.dealer.dealCard()
        self.dealer.setUpCard(upcard)
        count.updateRunningCount(upcard.getValue())
        # The hidden card is not added to the count yet as only the dealer knows this information
        hiddenCard = self.dealer.dealCard()
        dealerHand = Hand([upcard, hiddenCard], 0)
        self.dealer.updateHand(dealerHand)
        vprint("Dealer shows:")
        if isVerbose: upcard.printCard()
        vprint("Dealer hides:")
        if isVerbose: hiddenCard.printCard()

    def dealPlayersHands(self, players, count):
        vprint("Dealing hands...")
        for player in players:
            betSize = player.calculateBetSize(self.tableMin, self.getTrueCount(count))

            card1: Card = self.dealer.dealCard()
            card2: Card = self.dealer.dealCard()

            count.updateRunningCount(card1.getValue())
            count.updateRunningCount(card2.getValue())

            player.updateBankroll(-1 * betSize)
            player.updateHand(Hand([card1, card2], betSize))
            if isVerbose: player.getStartingHand().printHand(player.name)
    
    def doubleDown(self, player: Player, hand: Hand, count: HiLoCount):
        vprint("Doubling down!")
        player.updateBankroll(-1 * hand.getInitialBet())
        hand.doubleDown()
        self.hit(player, hand, count)
    
    def getTrueCount(self, count: HiLoCount):
        decksRemaining = self.dealer.shoe.getDecksRemaining()
        trueCount = count.getTrueCount(decksRemaining)
        return trueCount
    
    def handleBustHand(self, player: Player, hand: Hand):
        vprint("Hand went bust.")
        self.dealer.updateGains(hand.getInitialBet())
        self.dealer.discardPlayersCards(hand, player.name)
        player.clearHand(hand)
    
    def handleDealerBlackjack(self, players: List[Player], count: HiLoCount):
        # Need to update the count as the dealer reveals the hidden card to show blackjack
        # Guaranteed to have a count value of -1
        count.updateRunningCount(10)

        for player in players:
            for hand in player.hands:
                if hand.isBlackjack():
                    vprint("Player ", player.name, " pushes with another blackjack.")
                    player.updateBankroll(hand.betSize)
                elif hand.isInsured:
                    vprint("Player ", player.name, "'s hand is insured!")
                    player.updateBankroll(hand.betSize + hand.insuranceBet)
                else:
                    self.dealer.updateGains(hand.betSize)
    
    def handleInsurance(self, players: List[Player], count: HiLoCount):
        vprint("Dealer shows ace - Insurance offered")
        trueCount = self.getTrueCount(count)
        for player in players:
            for hand in player.hands:
                if player.strategy.willTakeInsurance(trueCount) and not hand.isBlackjack():
                    player.updateBankroll(-1 * hand.betSize / 2)
                    hand.insureHand()
                    vprint("Player ", player.name, " has insured their hand.")
        vprint("Insurance closed.")

    def handlePlayerBlackjack(self, player: Player, hand: Hand):
        payout = self.dealer.handlePayout(hand.betSize, isBlackjack=True)
        vprint("Blackjack! Initial bet: $", hand.getInitialBet(), " Payout: $", payout)
        player.updateBankroll(hand.betSize + payout)
        self.dealer.discardPlayersCards(hand, player.name)
        player.clearHand(hand)
    
    def handleRemainingHands(self, players: List[Player]):
        dealerValue = self.dealer.hand.finalHandValue
        for player in players:
            for hand in player.hands:
                vprint(player.name, " has ", hand.finalHandValue, " against the dealer's ", dealerValue)
                if hand.finalHandValue > dealerValue:
                    vprint("Player wins!")
                    payout = self.dealer.handlePayout(hand.betSize, isBlackjack=False)
                    vprint("Initial bet: $", hand.getInitialBet(), " Payout: $", payout)
                    player.updateBankroll(hand.betSize + payout)
                elif hand.finalHandValue < dealerValue:
                    vprint("Player loses!")
                    self.dealer.updateGains(hand.betSize)
                else:
                    vprint("Player pushes.")
                    player.updateBankroll(hand.betSize)

    def handleSplitPair(self, player: Player, hand: Hand, dealerUpcard: Card, count: HiLoCount):
        vprint("Determining whether or not to split pair based on player's strategy...")
        trueCount = self.getTrueCount(count)
        if player.strategy.shouldSplitPair(hand.getHandValue() / 2, dealerUpcard.getValue()) and player.calculateBetSize(self.tableMin, trueCount) <= player.bankroll:
            vprint("Splitting pair!")
            splitHand = player.splitPair(hand)
            return splitHand
        vprint("Player decided not to split pair.")
        return None

    
    def hit(self, player: Player, hand: Hand, count: HiLoCount):
        hitCard = self.dealer.dealCard()
        count.updateRunningCount(hitCard.getValue())
        hand.addCard(hitCard)
        vprint(player.name, " has new hand: ")
        if isVerbose: hand.printHand(player.name)

    def playDealerHand(self, count):
        vprint("Dealer is now playing their hand...")
        action: GameActions = None
        softTotalDeductionCount = 0

        while (action != GameActions.STAND.value):
            if self.dealer.hand.isBust():
                if softTotalDeductionCount < self.dealer.hand.getAcesCount():
                    vprint("Dealer busts! Ace now becomes 1. Old hand value: ", self.dealer.hand.getHandValue(), " New value: ", self.dealer.hand.getHandValue() - 10)
                    softTotalDeductionCount += 1
                else:
                    vprint("Dealer busts! All players are rewarded")
                    break
            if self.dealer.hand.isSoftTotal(softTotalDeductionCount) and softTotalDeductionCount < self.dealer.hand.getAcesCount():
                vprint("Dealer has soft total.")
                action = self.dealer.strategy.softTotalOptimalDecision(self.dealer.hand, self.dealer.upcard, softTotalDeductionCount)
            else:
                vprint("Dealer has hard total...")
                action = self.dealer.strategy.hardTotalOptimalDecision(self.dealer.hand, self.dealer.upcard.getValue(), softTotalDeductionCount)
            
            if (action == GameActions.HIT.value):
                vprint("Dealer hits...")
                hitCard = self.dealer.dealCard()
                count.updateRunningCount(hitCard.getValue())
                self.dealer.hand.addCard(hitCard)
                vprint("Dealer now has hand: ")
                if isVerbose: self.dealer.hand.printHand("Dealer")
            elif (action == GameActions.STAND.value):
                vprint("Dealer will stand...")
                self.dealer.hand.setFinalHandValue(self.dealer.hand.getHandValue() - softTotalDeductionCount * 10)
                break

    def playHands(self, player: Player, dealerUpcard: Card, handNumber, count):
        dealtHand = player.getStartingHand()
        vprint(player.name, " is playing their hand...")

        # Check if the dealt hand is a blackjack and payout immediately if it is
        if dealtHand.isBlackjack():
            self.handlePlayerBlackjack(player, dealtHand)
        else:
            handQueue = deque()
            handQueue.append(player.getStartingHand())

            while len(handQueue) > 0:
                hand = handQueue.pop()
                action: GameActions = None
                softTotalDeductionCount = 0

                while (action != GameActions.STAND.value):
                    if hand.isBust():
                        if softTotalDeductionCount < hand.getAcesCount():
                            vprint("BUST! Ace now becomes 1. Old hand value: ", hand.getHandValue(), " New value: ", hand.getHandValue() - 10)
                            softTotalDeductionCount += 1
                        else:
                            vprint("BUST! Value is: ", hand.getHandValue() - softTotalDeductionCount * 10)
                            self.handleBustHand(player, hand)
                            break
                    if hand.isPair():
                        vprint("We have a pair...")
                        splitHand = self.handleSplitPair(player, hand, dealerUpcard, count)
                        if splitHand is not None:
                            handQueue.append(splitHand)
                            handQueue.append(hand)
                            break
                    
                    if hand.isSoftTotal(softTotalDeductionCount) and softTotalDeductionCount < hand.getAcesCount():
                        vprint("We have a soft total...")
                        action = player.strategy.softTotalOptimalDecision(hand, dealerUpcard.getValue(), softTotalDeductionCount)
                    else:
                        # Get hard total value
                        vprint("We have a hard total of ", hand.getHandValue()- softTotalDeductionCount * 10)
                        action = player.strategy.hardTotalOptimalDecision(hand, dealerUpcard.getValue(), softTotalDeductionCount)
                    if (action == GameActions.HIT.value):
                        vprint("Player is gonna hit!")
                        self.hit(player, hand, count)
                    elif (action == GameActions.STAND.value):
                        vprint("Player will stand")
                        hand.setFinalHandValue(hand.getHandValue() - softTotalDeductionCount * 10)
                        break
                    elif (action == GameActions.DOUBLE.value):
                        vprint("Double down!")
                        self.doubleDown(player, hand, count)
                    
        vprint(player.name, " has played all of their hands!")
    def terminal_test(self, state):
        """
        Determines if the game state is terminal (no further actions possible).
        A game is terminal if:
        - The number of hands played exceeds the specified number of hands.
        - The player's bankroll is below the table minimum (bankrupt player).
        """
        # Example condition for terminal state
        is_terminal = (
            state.get("hands_played", 0) >= self.numHands or  # Check if all hands have been played
            state.get("bankroll", self.bankroll) < self.tableMin  # Check if the player is bankrupt
        )
        return is_terminal
      
    
    def printRoundInformation(self, players: List[Player], count: HiLoCount, roundNumber: int):
        print(" - - - - - - - - - - -")
        print(" - - - - - - - - - - -")
        print("Round: ", roundNumber, " Running Count: ", count.runningCount)
        print(" - - - - - - - - - - -")
        print(" - - - - - - - - - - -")
        for player in players:
            prevIndex = len(player.bankrollSnapshots) - 2
            print(player.name, ' has a bankroll of $', player.bankroll, " (Prev hand: $", player.bankrollSnapshots[prevIndex], ")")
    def actions(self, state):
        """
        Returns the set of valid actions for the current game state.
        """
        valid_actions = set()

        # Check if the player can hit (hand value < 21)
        if state['player_hand'] < 21:
            valid_actions.add("H")  # Hit

        # Check if the player can stand
        valid_actions.add("S")  # Stand

        # Check if the player can double (some rules restrict doubling)
        if len(state.get('player_cards', [])) == 2:  # Usually allowed only on the first two cards
            valid_actions.add("D")  # Double

        # Check if the player can split (requires two cards of the same rank)
        if len(state.get('player_cards', [])) == 2 and state['player_cards'][0] == state['player_cards'][1]:
            valid_actions.add("P")  # Split

        return valid_actions
    def result(self, state, action):
        new_state = state.copy()  # Make a copy of the current state to simulate changes

        if 'bet' not in new_state:
            new_state['bet'] = self.tableMin  # Default to table minimum if not already set

        if action == "H":  # Hit
            new_card = self.dealer.dealCard()
            new_state['player_cards'].append(new_card)
            new_state['player_hand'] += new_card.getValue()

        elif action == "S":  # Stand
            new_state['is_player_done'] = True

        elif action == "D":  # Double
            new_state['bet'] *= 2
            new_card = self.dealer.dealCard()
            new_state['player_cards'].append(new_card)
            new_state['player_hand'] += new_card.getValue()
            new_state['is_player_done'] = True

        elif action == "P":  # Split
            if len(new_state['player_cards']) == 2 and new_state['player_cards'][0] == new_state['player_cards'][1]:
                new_state['split_hands'] = [
                    [new_state['player_cards'][0], self.dealer.dealCard()],
                    [new_state['player_cards'][1], self.dealer.dealCard()],
                ]
                new_state['player_hand'] = None

        if new_state['player_hand'] and new_state['player_hand'] > 21:
            new_state['is_bust'] = True

        return new_state


    def startGame(self):
        self.dealer.shuffle()
        vprint("Starting new blackjack game!")

        handCount = 1
        playersInGame: List[Player] = []
        playersInBreak: List[Player] = []

        for player in self.players:
            playersInGame.append(player)
            vprint("Player: ", player.name, " has joined the game.")

        count = HiLoCount()

        # Play the game! 
        while (handCount <= self.numHands and len(playersInGame) > 0):
            if isVerbose:
                self.printRoundInformation(playersInGame, count, handCount)
            # Deal out the players' and dealer's cards
            self.dealPlayersHands(playersInGame, count)
            self.dealDealersHand(count)

            # If the dealer shows an ace, dealer will offer insurance to all players.
            if self.dealer.insuranceIsOffered():
                self.handleInsurance(playersInGame, count)
            
            # If the dealer was dealt a blackjack, all players automatically lose UNLESS they too have a blackjack
            if self.dealer.hand.isBlackjack():
                self.handleDealerBlackjack(playersInGame, count)
            else:
                # Allow players to play out each of their hands
                for player in playersInGame:
                    self.playHands(player, self.dealer.upcard, handCount, count)
            
            # Now, the dealer will play out their hand
            self.playDealerHand(count)

            # Next, determine which existing hands beat the dealer and perform all necessary payouts
            self.handleRemainingHands(playersInGame)
        
            handCount = handCount + 1

            self.clearAllCards(playersInGame)

            # Used to debug deck sizes to ensure that no cards are being lost:
            self.dealer.ensureDeckCompleteness(isVerbose=True)
            
            # If we have exceeded or reached optimal shoe penetration, reset the shoe and the running count
            if self.dealer.deckPenetrationTooHigh():
                self.dealer.shuffle()
                count.resetCount()
            
            
            for player in playersInGame:
                player.takeBankrollSnapshot()
                if player.bankroll < self.tableMin:
                    vprint(player.name, " has gone broke and is out of the game.")
                    playersInGame.remove(player)




if __name__ == '__main__':
    main()