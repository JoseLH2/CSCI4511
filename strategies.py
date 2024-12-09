from hand import Hand
from enum import Enum, auto
from dealer import HouseRules
import random
class GameActions(Enum):
    HIT = 'H'
    STAND = 'S'
    DOUBLE = 'D'
class StrategyInterface:
    def __init__(self, houseRules: HouseRules, isCounting):
        pass
    
    def hardTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, numSoftAces: int):
        pass

    def shouldSplitPair(self, pairValue: int, dealerUpcard: int) -> bool:
        pass

    def softTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, softTotalDeductionCount:int) -> GameActions:
        pass
    
    def willTakeInsurance(self, runningCount) -> None:
        pass

# RandomStrategy represents the strategy of a player who will leave every single game decision up to chance.
# This goes without saying, do not attempt this strategy in a real life casino :)
class RandomStrategy(StrategyInterface):
    def __init__(self, houseRules, isCounting, accuracy):
        self.houseRules = houseRules
        self.isCounting = isCounting
        self.accuracy = accuracy
        self.name = "random"
    
    def hardTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, numSoftAces):
        return random.choice([GameActions.HIT.value, GameActions.STAND.value, GameActions.DOUBLE.value])
    
    def shouldSplitPair(self, pairValue: int, dealerUpcard: int) -> bool:
        return bool(random.getrandbits(1))
    
    def softTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, softTotalDeductionCount: int) -> GameActions:
        return random.choice([GameActions.HIT.value, GameActions.STAND.value, GameActions.DOUBLE.value])
    
    def willTakeInsurance(self, runningCount):
        return bool(random.getrandbits(1))

# CasinoStrategy represents the strategy of a player who will play exactly how the casino plays. In other words,
# if the dealer was an actual player at the table this is who they'd be. 
class CasinoStrategy(StrategyInterface):
    def __init__(self, houseRules: HouseRules, isCounting, accuracy):
        self.name = "casino"
        self.houseRules = houseRules
        self.isCounting = isCounting
        self.accuracy = accuracy
    
    def hardTotalOptimalDecision(self, hand: Hand, dealerUpcard, numSoftAces):
        handValue = hand.getHandValue() - numSoftAces * 10
        if handValue < 17:
            return GameActions.HIT.value
        return GameActions.STAND.value
    
    def shouldSplitPair(self, pairValue: int, dealerUpcard: int):
        # Casinos never split pairs! 
        return False
    
    def softTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, softTotalDeductionCount) -> GameActions:
        acelessTotalVal = hand.getSoftTotalAcelessValue(softTotalDeductionCount)
        if acelessTotalVal >= 6:
            return GameActions.STAND.value
        return GameActions.HIT.value
    
    def willTakeInsurance(self, runningCount) -> None:
        # Casinos never take insurance!
        return False

# See https://www.blackjackapprenticeship.com/wp-content/uploads/2018/08/BJA_Basic_Strategy.jpg for charts
class BasicStrategy(StrategyInterface):
    def __init__(self, houseRules: HouseRules, isCounting, accuracy):
        self.houseRules = houseRules
        self.isCounting = isCounting
        self.accuracy = accuracy
        if self.houseRules.doubleAfterSplitOffered:
            self.DASdeviations()
        if not self.houseRules.doubleOnSoftTotal:
            self.softTotalDeviations()
    
    # Contains the optimal pair splitting strategy given the rank of the player's pair and the
    # dealer's upcard according to Basic Strategy principles. 
        #     A       2      3      4      5      6      7      8      9      10  
    pairSplitting = {
        1:  [True,  True,  True,  True,  True,  True,  True,  True,  True,  True],
        10: [False, False, False, False, False, False, False, False, False, False],
        9:  [False, True,  True,  True,  True,  True,  False, True,  True,  False],
        8:  [True,  True,  True,  True,  True,  True,  True,  True,  True,  True],
        7:  [False, True,  True,  True,  True,  True,  True,  False, False, False],
        6:  [False, False, True,  True,  True,  True,  False, False, False, False],
        5:  [False, False, False, False, False, False, False, False, False, False],
        4:  [False, False, False, False, False, False, False, False, False, False],
        3:  [False, False, False, True,  True,  True,  True,  False, False, False],
        2:  [False, False, False, True,  True,  True,  True,  False, False, False]
    }

    # Contains the optimal hit/stand/double strategy given that the player has one ace and another card
    # of a certain value and the dealer's upcard according to Basic Strategy principles. 
        #    A    2    3    4    5    6    7    8    9    10
    softTotals = {
        10: ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        9:  ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        8:  ["S", "S", "S", "S", "S", "D", "S", "S", "S", "S"],
        7:  ["H", "D", "D", "D", "D", "D", "S", "S", "H", "H"],
        6:  ["H", "H", "D", "D", "D", "D", "H", "H", "H", "H"],
        5:  ["H", "H", "H", "D", "D", "D", "H", "H", "H", "H"],
        4:  ["H", "H", "H", "D", "D", "D", "H", "H", "H", "H"],
        3:  ["H", "H", "H", "H", "D", "D", "H", "H", "H", "H"],
        2:  ["H", "H", "H", "H", "D", "D", "H", "H", "H", "H"]
    }

    # Contains the optimal hit/stand/double strategy for the player's cards against the dealer's upcard
    # according to Basic Strategy principles.
        #     A    2    3    4    5    6    7    8    9    10
    hardTotals = {
        17: ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        16: ["H", "S", "S", "S", "S", "S", "H", "H", "H", "H"],
        15: ["H", "S", "S", "S", "S", "S", "H", "H", "H", "H"],
        14: ["H", "S", "S", "S", "S", "S", "H", "H", "H", "H"],
        13: ["H", "S", "S", "S", "S", "S", "H", "H", "H", "H"],
        12: ["H", "H", "H", "S", "S", "S", "H", "H", "H", "H"],
        11: ["D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],
        10: ["H", "D", "D", "D", "D", "D", "D", "D", "D", "H"],
        9:  ["H", "H", "D", "D", "D", "D", "H", "H", "H", "H"],
        8:  ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    }
    # Handles pair splitting deviations in the event that double-after-split (DAS) is offered.
    def DASdeviations(self):
        self.pairSplitting.update({6: [False, True, True,  True,  True,  True,  False, False, False, False]})
        self.pairSplitting.update({4: [False, False, False, False, True, True, False, False, False, False]})
        self.pairSplitting.update({3: [False, True, True, True,  True,  True,  True,  False, False, False]})
        self.pairSplitting.update({2: [False, True, True, True,  True,  True,  True,  False, False, False]})
    
    def hardTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, numSoftAces):
        if random.randrange(0,1) > self.accuracy:
            return random.choice([GameActions.HIT.value, GameActions.STAND.value, GameActions.DOUBLE.value])
        handValue = hand.getHandValue() - numSoftAces * 10
        if handValue <= 8:
            return GameActions.HIT.value
        if handValue >= 17:
            return GameActions.STAND.value
        return self.hardTotals.get(handValue)[dealerUpcard - 2]

    def shouldSplitPair(self, pairValue: int, dealerUpcard: int):
        if dealerUpcard == 11:
            dealerUpcard = 1
        if pairValue == 11:
            return self.pairSplitting.get(1)[dealerUpcard - 1]
        return self.pairSplitting.get(pairValue)[dealerUpcard - 1]
    
    # Handles soft total deviations in the event that players cannot double on a soft total.
    def softTotalDeviations(self):
        self.softTotals.update({8: ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"]})
        self.softTotals.update({7: ["H", "S", "S", "S", "S", "S", "S", "S", "H", "H"]})
        self.softTotals.update({6: ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]})
        self.softTotals.update({5: ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]})
        self.softTotals.update({4: ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]})
        self.softTotals.update({3: ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]})
        self.softTotals.update({2: ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]})
    
    def softTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, softTotalDeductionCount):
        if random.randrange(0,1) > self.accuracy:
            return random.choice([GameActions.HIT.value, GameActions.STAND.value, GameActions.DOUBLE.value])
        acelessTotalVal = hand.getSoftTotalAcelessValue(softTotalDeductionCount)
        if acelessTotalVal >= 8:
            return GameActions.STAND.value
        if dealerUpcard == 11:
            dealerUpcard = 1
        chartVal: GameActions = self.softTotals.get(acelessTotalVal)[dealerUpcard - 1]
        return chartVal
    
    def willTakeInsurance(self, runningCount):
        # Perfect basic strategy never takes insurance unless running count is exceptionally high
        return runningCount >= 8
class MCTSNode:
    def __init__(self, state):
        self.state = state
        self.visits = 0
        self.value = 0
        self.children = {}

    def ucb(self, total_visits):
        if self.visits == 0:
            return float('inf')
        return self.value / self.visits + 2 * ((total_visits ** 0.5) / (1 + self.visits))


class MCTSStrategy(StrategyInterface):
    def __init__(self, houseRules: HouseRules, iterations: int):
        self.houseRules = houseRules
        self.iterations = iterations
        self.isCounting = False  # Ensures compatibility with Player class
        self.name = "Monte Carlo Tree Search"

    def hardTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, numSoftAces: int):
        handValue = hand.getHandValue() - numSoftAces * 10
        if handValue < 12:
            return GameActions.HIT.value
        elif 12 <= handValue < 17:
            return random.choice([GameActions.HIT.value, GameActions.STAND.value])
        else:
            return GameActions.STAND.value

    def shouldSplitPair(self, pairValue: int, dealerUpcard: int) -> bool:
        # MCTS does not involve pair splitting logic
        return False

    def softTotalOptimalDecision(self, hand: Hand, dealerUpcard: int, softTotalDeductionCount: int) -> GameActions:
        return self.hardTotalOptimalDecision(hand, dealerUpcard, softTotalDeductionCount)

    def willTakeInsurance(self, runningCount) -> bool:
        # MCTS does not take insurance
        return False

    def monteCarloSimulate(self, state):
        # Placeholder logic for simulation
        return random.choice([-1, 1])  # Random win/loss simulation

    def monteCarloTreeSearch(self, state, game, N=1000):
        # Placeholder logic for MCTS
        return random.choice([GameActions.HIT.value, GameActions.STAND.value])
