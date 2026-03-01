class DifficultyAdaptationAgent:
    def decide_next_difficulty(self, learning_index, current_difficulty):
        difficulty = int(current_difficulty)
        li = float(learning_index)

        if li > 0.75:
            return min(5, difficulty + 1)
        if li < 0.40:
            return max(1, difficulty - 1)
        return difficulty
