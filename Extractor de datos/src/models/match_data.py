class MatchData:
    """
    Modelo que representa todos los datos extraídos de un partido de fútbol,
    incluyendo información básica, estadísticas, head-to-head, próximos partidos, etc.
    """
    
    def __init__(self, 
                 match=None,
                 h2h=None,
                 referee_info=None,
                 weather=None,
                 team1=None,
                 team2=None,
                 travel_distance=None, # Added
                 future_matches_summary=None): # Added
        """
        Initialize a MatchData object with optimized fields.

        Args:
            match: Basic match information
            h2h: Head-to-head data for the current season
            referee_info: Referee information
            weather: Weather information
            team1: Data for the home team
            team2: Data for the away team
            travel_distance: Calculated travel distance for away team (Added)
            future_matches_summary: Summary of next matches for both teams (Added)
        """
        self.match = match if match else {}
        self.h2h = h2h if h2h else {}
        self.referee_info = referee_info if referee_info else {}
        self.weather = weather if weather else {}
        self.team1 = team1 if team1 else {}
        self.team2 = team2 if team2 else {}
        self.travel_distance = travel_distance # Added
        self.future_matches_summary = future_matches_summary if future_matches_summary else {} # Added

    def to_dict(self):
        """
        Convierte el objeto a un diccionario
        
        Returns:
            dict: Representación del objeto como diccionario
        """
        return {
            "match": self.match,
            "h2h": self.h2h,
            "referee_info": self.referee_info,
            "weather": self.weather,
            "team1": self.team1,
            "team2": self.team2,
            "travel_distance": self.travel_distance, # Added
            "future_matches_summary": self.future_matches_summary # Added
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un objeto MatchData desde un diccionario
        
        Args:
            data: Diccionario con datos del partido
            
        Returns:
            MatchData: Objeto MatchData
        """
        return cls(
            match=data.get("match"),
            h2h=data.get("h2h"),
            referee_info=data.get("referee_info"),
            weather=data.get("weather"),
            team1=data.get("team1"),
            team2=data.get("team2"),
            travel_distance=data.get("travel_distance"), # Added
            future_matches_summary=data.get("future_matches_summary") # Added
        )