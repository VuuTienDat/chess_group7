import json
import math
import os

class EloSystem:
    def __init__(self, ratings_file="ai_ratings.json"):
        self.ratings_file = ratings_file
        self.ratings = self._load_ratings()
        self.K = 32  # K-factor determines how much ratings can change
        self.default_rating = 1500  # Starting rating for new players

    def _load_ratings(self):
        """Load ratings from file or create new if doesn't exist"""
        if os.path.exists(self.ratings_file):
            with open(self.ratings_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_ratings(self):
        """Save current ratings to file"""
        with open(self.ratings_file, 'w') as f:
            json.dump(self.ratings, f, indent=4)

    def get_rating(self, player_id):
        """Get rating for a player, create new entry if doesn't exist"""
        if player_id not in self.ratings:
            self.ratings[player_id] = self.default_rating
            self._save_ratings()
        return self.ratings[player_id]

    def calculate_expected_score(self, rating1, rating2):
        """Calculate expected score using ELO formula"""
        return 1 / (1 + math.pow(10, (rating2 - rating1) / 400))

    def update_ratings(self, player1_id, player2_id, result):
        """Update ratings after a match
        result: 1 for player1 win, 0 for player2 win, 0.5 for draw
        """
        rating1 = self.get_rating(player1_id)
        rating2 = self.get_rating(player2_id)

        expected1 = self.calculate_expected_score(rating1, rating2)
        expected2 = self.calculate_expected_score(rating2, rating1)

        # Update ratings
        self.ratings[player1_id] = round(rating1 + self.K * (result - expected1))
        self.ratings[player2_id] = round(rating2 + self.K * ((1 - result) - expected2))
        
        # Save updated ratings
        self._save_ratings()
        
        return self.ratings[player1_id], self.ratings[player2_id]

    def get_all_ratings(self):
        """Get all player ratings"""
        return self.ratings