# monte_carlo.py

import random

class MCT_Node:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = {}
        self.U = 0  # Utility
        self.N = 0  # Visit count

def ucb(node):
    """Upper Confidence Bound for Trees"""
    C = 1.41  # Exploration constant
    if node.N == 0:
        return float('inf')  # Favor unexplored nodes
    return node.U / node.N + C * (2 * (node.parent.N if node.parent else 1)) ** 0.5

class BlackjackGame:
    """Game logic for Monte Carlo Tree Search."""
    def __init__(self, state):
        self.initial_state = state

    def actions(self, state):
        """Return the legal actions for the given state."""
        return state['legal_actions']

    def result(self, state, action):
        """Return the next state after applying the action."""
        # Simulate a result for demonstration; replace with actual game logic.
        new_state = state.copy()
        new_state['player_hand'] += random.randint(1, 10) if action == "hit" else 0
        new_state['legal_actions'] = ["stand"] if new_state['player_hand'] >= 21 else state['legal_actions']
        return new_state

    def terminal_test(self, state):
        """Check if the game state is terminal."""
        return state['player_hand'] >= 21 or len(state['legal_actions']) == 0

    def utility(self, state, player):
        """Calculate the utility of the state."""
        if state['player_hand'] > 21:
            return -1  # Bust
        elif state['player_hand'] == 21:
            return 1  # Win
        return 0  # Game still ongoing

def monte_carlo_tree_search(state, game, N=1000):
    def select(node):
        """Select the best child node using UCB."""
        if node.children:
            return select(max(node.children.keys(), key=ucb))
        return node

    def expand(node):
        """Expand the node by adding all possible children."""
        if not node.children and not game.terminal_test(node.state):
            node.children = {MCT_Node(state=game.result(node.state, action), parent=node): action
                             for action in game.actions(node.state)}
        return select(node)

    def simulate(state):
        """Simulate a random playthrough."""
        current_state = state
        while not game.terminal_test(current_state):
            action = random.choice(game.actions(current_state))
            current_state = game.result(current_state, action)
        return game.utility(current_state, None)

    def backpropagate(node, reward):
        """Backpropagate the result to update the node and its ancestors."""
        while node:
            node.N += 1
            node.U += reward
            reward = -reward  # Alternate between win/loss
            node = node.parent

    root = MCT_Node(state)

    for _ in range(N):
        leaf = select(root)
        child = expand(leaf)
        reward = simulate(child.state)
        backpropagate(child, reward)

    best_child = max(root.children.keys(), key=lambda n: n.N)
    return root.children[best_child]
