from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Team:
    """Modelo para representar un equipo"""
    id: int
    name: str
    logo: Optional[str] = None
    
@dataclass
class Venue:
    """Modelo para representar un estadio"""
    name: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@dataclass
class League:
    """Modelo para representar una liga"""
    id: int
    name: str
    country: Optional[str] = None
    logo: Optional[str] = None
    season: Optional[int] = None

@dataclass
class WeatherInfo:
    """Modelo para representar información meteorológica"""
    temperature: float
    description: str
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None
    
@dataclass
class TeamStatistics:
    """Modelo para representar estadísticas de un equipo"""
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    form: Optional[str] = None
    
class Match:
    """
    Modelo que representa un partido de fútbol con todos sus datos asociados
    """
    
    def __init__(self, 
                 fixture_id=None,
                 home_team=None,
                 away_team=None,
                 date=None,
                 time=None,
                 referee=None,
                 venue=None,
                 league=None,
                 status=None):
        """
        Inicializa un objeto Match
        
        Args:
            fixture_id: ID del partido
            home_team: Equipo local
            away_team: Equipo visitante
            date: Fecha del partido
            time: Hora del partido
            referee: Árbitro del partido
            venue: Estadio donde se juega
            league: Liga a la que pertenece
            status: Estado del partido
        """
        self.fixture_id = fixture_id
        self.home_team = home_team if home_team else {}
        self.away_team = away_team if away_team else {}
        self.date = date
        self.time = time
        self.referee = referee
        self.venue = venue if venue else {}
        self.league = league if league else {}
        self.status = status
    
    def to_dict(self):
        """
        Convierte el objeto a un diccionario
        
        Returns:
            dict: Representación del objeto como diccionario
        """
        return {
            "fixture_id": self.fixture_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "date": self.date,
            "time": self.time,
            "referee": self.referee,
            "venue": self.venue,
            "league": self.league,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un objeto Match desde un diccionario
        
        Args:
            data: Diccionario con datos del partido
            
        Returns:
            Match: Objeto Match
        """
        return cls(
            fixture_id=data.get("fixture_id"),
            home_team=data.get("home_team"),
            away_team=data.get("away_team"),
            date=data.get("date"),
            time=data.get("time"),
            referee=data.get("referee"),
            venue=data.get("venue"),
            league=data.get("league"),
            status=data.get("status")
        ) 