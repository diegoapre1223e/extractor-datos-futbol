import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import argparse
import json
import re
import time

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.football_api import FootballAPI
from src.api.weather_api import WeatherAPI
from src.api.geocoding_api import GeocodingAPI
from src.api.referee_api import RefereeAPI
from src.api.understat_api import UnderstatAPI
from src.utils.data_processor import DataProcessor
from src.utils.storage import LocalStorage

class FootballDataExtractor:
    """
    Clase principal para extraer y procesar datos de partidos de fútbol
    """
    
    def __init__(self):
        """
        Inicializa el extractor de datos de partidos de fútbol
        """
        # Inicializar rutas y directorios
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        
        # Crear directorios si no existen
        os.makedirs(os.path.join(self.data_dir, "matches"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "teams"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "players"), exist_ok=True)
        
        # Inicializar APIs
        self.football_api = FootballAPI()
        self.weather_api = WeatherAPI()
        self.geocoding_api = GeocodingAPI()
        self.referee_api = RefereeAPI(self.football_api)
        self.understat_api = UnderstatAPI(self.football_api)
        self.data_processor = DataProcessor()
        self.storage = LocalStorage()
    
    def extract_match_data(self, team1_name, team2_name, date_str, save_data=True):
        """
        Extrae datos completos de un partido entre dos equipos
        
        Args:
            team1_name: Nombre del equipo local
            team2_name: Nombre del equipo visitante
            date_str: Fecha del partido en formato YYYY-MM-DD
            save_data: Indica si guardar los datos en archivos
            
        Returns:
            dict: Datos completos del partido
        """
        # Limpiar posibles artefactos en los nombres de equipos (sufijos de fecha, etc.)
        team1_name = team1_name.split(' - ')[0].strip()
        team2_name = team2_name.split(' - ')[0].strip()
        
        print(f"Extrayendo datos para: {team1_name} vs {team2_name} {date_str}")
        print(f"Equipos identificados: {team1_name} vs {team2_name}, Fecha: {date_str}")
        
        # Inicializar estructura para los datos del partido
        match_data = {}
        
        try:
            # Buscar IDs de equipos
            print(f"Iniciando búsqueda avanzada para: {team1_name}")
            team1_data = self.football_api.advanced_team_search(team1_name)
            if not team1_data:
                print(f"❌ No se encontró el equipo: {team1_name}. Intentando con el segundo equipo...")
                team2_data = self.football_api.advanced_team_search(team2_name)
                if not team2_data:
                    print(f"❌ No se encontró el equipo: {team2_name}")
                    return None
                print(f"¡Partido encontrado con el segundo equipo! {team2_data['name']} vs {team1_name}")
                team1_data = self.football_api.advanced_team_search(team2_data['name'])
                if not team1_data:
                    print(f"❌ No se encontró el equipo: {team2_data['name']} en la API")
                    return None
            team1_id = team1_data["id"]

            print(f"Iniciando búsqueda avanzada para: {team2_name}")
            team2_data = self.football_api.advanced_team_search(team2_name)
            if not team2_data:
                print(f"❌ No se encontró el equipo: {team2_name}")
                return None
            team2_id = team2_data["id"]
            
            if not team1_id or not team2_id:
                print("❌ No se encontraron los equipos en la API")
                return None
                
            print(f"Equipos identificados: {team1_name} (ID: {team1_id}) vs {team2_name} (ID: {team2_id})")
            
            # Extraer año de la fecha para filtrar por temporada
            match_date = datetime.strptime(date_str, "%Y-%m-%d")
            season_year = str(match_date.year - 1 if match_date.month < 7 else match_date.year)
            
            # Buscar partido programado
            print(f"Buscando partido programado para fecha: {date_str}")
            match_details = self.football_api.get_fixtures(team=team1_id, date=date_str, season=season_year)
            
            if not match_details or "response" not in match_details or not match_details["response"]:
                print("❌ No se encontró el partido programado. Creando estructura básica...")
                # Crear estructura básica para partido no encontrado
                match_data = {
                    "match_id": None,
                    "date": date_str,
                    "team1": {
                        "id": team1_id,
                        "name": team1_name
                    },
                    "team2": {
                        "id": team2_id,
                        "name": team2_name
                    },
                    "status": "Programado",
                    "score": None,
                    "league": None,
                    "venue": None,
                    "referee": None
                }
            else:
                print(f"¡Partido encontrado! {team1_name} vs {team2_name}")
                print("Normalizando datos del partido...")
                
                # Buscar el partido específico entre estos dos equipos
                match_found = None
                for match in match_details["response"]:
                    teams = match.get("teams", {})
                    home_team = teams.get("home", {})
                    away_team = teams.get("away", {})
                    
                    if (home_team.get("id") == team2_id or away_team.get("id") == team2_id):
                        match_found = match
                        break
                
                if match_found:
                    # Normalizar datos del partido encontrado
                    match_data = DataProcessor.normalize_match_data(match_found)
                else:
                    # Buscar con el segundo equipo
                    alt_match_details = self.football_api.get_fixtures(team=team2_id, date=date_str, season=season_year)
                    if alt_match_details and "response" in alt_match_details and alt_match_details["response"]:
                        for match in alt_match_details["response"]:
                            teams = match.get("teams", {})
                            home_team = teams.get("home", {})
                            away_team = teams.get("away", {})
                            
                            if (home_team.get("id") == team1_id or away_team.get("id") == team1_id):
                                match_found = match
                                break
                                
                        if match_found:
                            # Normalizar datos del partido encontrado
                            match_data = DataProcessor.normalize_match_data(match_found)
                        else:
                            # Crear estructura básica ya que no se encontró el partido específico
                            print("❌ No se encontró un partido entre estos equipos en la fecha especificada.")
                            match_data = {
                                "match_id": None,
                                "date": date_str,
                                "team1": {
                                    "id": team1_id,
                                    "name": team1_name
                                },
                                "team2": {
                                    "id": team2_id,
                                    "name": team2_name
                                },
                                "status": "Programado",
                                "score": None,
                                "league": None,
                                "venue": None,
                                "referee": None
                            }
                    else:
                        # Crear estructura básica ya que no se encontró el partido 
                        print("❌ No se encontró un partido entre estos equipos en la fecha especificada.")
                        match_data = {
                            "match_id": None,
                            "date": date_str,
                            "team1": {
                                "id": team1_id,
                                "name": team1_name
                            },
                            "team2": {
                                "id": team2_id,
                                "name": team2_name
                            },
                            "status": "Programado",
                            "score": None,
                            "league": None,
                            "venue": None,
                            "referee": None
                        }
            
            # Obtener información de estadios para calcular distancia
            venue1_info = None
            venue2_info = None
            if match_data.get("venue") and match_data.get("venue").get("id"):
                # Asumimos que el estadio del partido es el del equipo local (team1)
                venue1_info = self.geocoding_api.get_coordinates_from_venue(match_data["venue"]["name"], match_data["venue"]["city"])
                # Necesitamos obtener el estadio del equipo visitante (team2)
                team2_details = self.football_api.search_team(team2_name)
                if team2_details and team2_details.get("venue"):
                    venue2_info = self.geocoding_api.get_coordinates_from_venue(team2_details["venue"]["name"], team2_details["venue"]["city"])

            # Calcular distancia de viaje
            travel_distance = None
            if venue1_info and venue2_info:
                travel_distance = DataProcessor.calculate_travel_distance(venue1_info, venue2_info)
                match_data["travel_distance"] = travel_distance
                print(f"Distancia de viaje calculada: {travel_distance} km")
            else:
                print("No se pudo calcular la distancia de viaje (faltan datos de estadios/coordenadas)")

            # Obtener próximos partidos para ambos equipos
            future_matches = {"team1": None, "team2": None}
            try:
                print(f"Obteniendo próximos 3 partidos para {team1_name}...")
                future_matches["team1"] = self.football_api.get_next_matches(team1_id, num_matches=3, season=season_year)
            except Exception as e:
                print(f"Error obteniendo próximos partidos para equipo 1: {e}")
            try:
                print(f"Obteniendo próximos 3 partidos para {team2_name}...")
                future_matches["team2"] = self.football_api.get_next_matches(team2_id, num_matches=3, season=season_year)
            except Exception as e:
                print(f"Error obteniendo próximos partidos para equipo 2: {e}")

            # Obtener historial de enfrentamientos
            print("Obteniendo historial de enfrentamientos...")
            h2h_data = self.football_api.get_head_to_head(team1_id, team2_id)
            if h2h_data:
                match_data["h2h"] = h2h_data
                
            # Obtener estadísticas del equipo 1
            print(f"Obteniendo estadísticas para el equipo {team1_id}...")
            team1_fixtures = self.football_api.get_fixtures(team=team1_id, last=10, season=season_year)
            if team1_fixtures and "response" in team1_fixtures:
                print(f"Se encontraron {len(team1_fixtures['response'])} partidos para el equipo {team1_id}")
            
            team1_stats = self.football_api.get_team_statistics(team1_id, league_id=None, season=season_year)
            if team1_stats:
                match_data["team1"]["statistics"] = team1_stats

            # Obtener estadísticas del equipo 2
            print(f"Obteniendo estadísticas para el equipo {team2_id}...")
            team2_fixtures = self.football_api.get_fixtures(team=team2_id, last=10, season=season_year)
            if team2_fixtures and "response" in team2_fixtures:
                print(f"Se encontraron {len(team2_fixtures['response'])} partidos para el equipo {team2_id}")
            
            team2_stats = self.football_api.get_team_statistics(team2_id, league_id=None, season=season_year)
            if team2_stats:
                match_data["team2"]["statistics"] = team2_stats
                
            # Obtener estadísticas del equipo 1 contra el equipo 2
            print(f"Obteniendo estadísticas para {team1_id} vs {team2_id}...")
            team1_vs_team2 = self.football_api.get_fixtures(team1_id=team1_id, team2_id=team2_id, last=10, season=season_year)
            if team1_vs_team2 and "response" in team1_vs_team2:
                print(f"Se encontraron {len(team1_vs_team2['response'])} partidos entre {team1_id} y {team2_id}")
            
            team1_vs_team2_stats = self.football_api.get_team_statistics(team1_id, league_id=None, season=season_year)
            if team1_vs_team2_stats:
                match_data["team1"]["vs_team2"] = team1_vs_team2_stats
                
            # Obtener estadísticas del equipo 2 contra el equipo 1
            print(f"Obteniendo estadísticas para {team2_id} vs {team1_id}...")
            if team1_vs_team2 and "response" in team1_vs_team2:
                print(f"Se encontraron {len(team1_vs_team2['response'])} partidos entre {team2_id} y {team1_id}")
            
            team2_vs_team1_stats = self.football_api.get_team_statistics(team2_id, league_id=None, season=season_year)
            if team2_vs_team1_stats:
                match_data["team2"]["vs_team1"] = team2_vs_team1_stats
            
            # Obtener datos de Understat para equipo 1
            team1_understat = None
            try:
                team1_understat = self.understat_api.get_team_data(team1_name, year=season_year)
                print(f"Procesando datos de Understat para equipo 1...")
                if team1_understat and team1_understat.get("status") == "success":
                    match_data["team1"]["understat"] = team1_understat
                    
                    # Procesar métricas avanzadas de jugadores si están disponibles
                    advanced_player_metrics = team1_understat.get("advanced_player_metrics", {})
                    if advanced_player_metrics:
                        match_data["team1"].setdefault("advanced_player_metrics", advanced_player_metrics)
                    
                    # Guardar jugadores en archivos individuales
                    if save_data and "players" in team1_understat and team1_understat["players"]:
                        self.save_players_data(team1_id, team1_name, team1_understat["players"])
                else:
                    print(f"Error al formatear datos de Understat para equipo 1: {team1_understat.get('message', 'Error desconocido')}")
            except Exception as e:
                print(f"Error procesando datos de Understat para equipo 1: {str(e)}")
                
            # Obtener datos de Understat para equipo 2
            team2_understat = None
            try:
                team2_understat = self.understat_api.get_team_data(team2_name, year=season_year)
                print(f"Procesando datos de Understat para equipo 2...")
                if team2_understat and team2_understat.get("status") == "success":
                    match_data["team2"]["understat"] = team2_understat
                    
                    # Procesar métricas avanzadas de jugadores si están disponibles
                    advanced_player_metrics = team2_understat.get("advanced_player_metrics", {})
                    if advanced_player_metrics:
                        match_data["team2"].setdefault("advanced_player_metrics", advanced_player_metrics)
                    
                    # Guardar jugadores en archivos individuales
                    if save_data and "players" in team2_understat and team2_understat["players"]:
                        self.save_players_data(team2_id, team2_name, team2_understat["players"])
                else:
                    print(f"Error al formatear datos de Understat para equipo 2: {team2_understat.get('message', 'Error desconocido')}")
            except Exception as e:
                print(f"Error procesando datos de Understat para equipo 2: {str(e)}")
            
            # Obtener estadísticas detalladas por situación de juego
            print(f"Obteniendo estadísticas detalladas por situación de juego para {team1_name}...")
            team1_situations = self.understat_api.get_detailed_game_situations(team1_name, year=season_year)
            if team1_situations:
                match_data["team1"]["detailed_game_situations"] = team1_situations

            print(f"Obteniendo estadísticas detalladas por situación de juego para {team2_name}...")
            team2_situations = self.understat_api.get_detailed_game_situations(team2_name, year=season_year)
            if team2_situations:
                match_data["team2"]["detailed_game_situations"] = team2_situations

            # Obtener lesiones y sanciones para equipo 1
            try:
                print(f"Consultando lesiones y sanciones para equipo ID: {team1_id}")
                injuries_team1 = self.football_api.get_injuries(team1_id)
                if injuries_team1 and "response" in injuries_team1 and injuries_team1["response"]:
                    match_data["team1"]["injuries"] = injuries_team1["response"]
                else:
                    error_code = injuries_team1.get("errors", {}).get("requests", {})
                    if error_code:
                        print(f"Error al obtener lesiones y sanciones: {error_code}")
                        # Generar datos de lesiones de respaldo
                        match_data["team1"]["injuries"] = self.generate_fallback_injuries(team1_name)
                    else:
                        print("No se encontraron lesiones o sanciones para el equipo 1")
                        # Generar datos de lesiones vacíos pero con estructura correcta
                        match_data["team1"]["injuries"] = []
            except Exception as e:
                print(f"Error consultando lesiones para equipo 1: {str(e)}")
                # Generar datos de lesiones de respaldo en caso de excepción
                match_data["team1"]["injuries"] = self.generate_fallback_injuries(team1_name)
            
            # Obtener lesiones y sanciones para equipo 2
            try:
                print(f"Consultando lesiones y sanciones para equipo ID: {team2_id}")
                injuries_team2 = self.football_api.get_injuries(team2_id)
                if injuries_team2 and "response" in injuries_team2 and injuries_team2["response"]:
                    match_data["team2"]["injuries"] = injuries_team2["response"]
                else:
                    error_code = injuries_team2.get("errors", {}).get("requests", {})
                    if error_code:
                        print(f"Error al obtener lesiones y sanciones: {error_code}")
                        # Generar datos de lesiones de respaldo
                        match_data["team2"]["injuries"] = self.generate_fallback_injuries(team2_name)
                    else:
                        print("No se encontraron lesiones o sanciones para el equipo 2")
                        # Generar datos de lesiones vacíos pero con estructura correcta
                        match_data["team2"]["injuries"] = []
            except Exception as e:
                print(f"Error consultando lesiones para equipo 2: {str(e)}")
                # Generar datos de lesiones de respaldo en caso de excepción
                match_data["team2"]["injuries"] = self.generate_fallback_injuries(team2_name)
            
            # Obtener lesiones de Transfermarkt
            try:
                print(f"Consultando lesiones en Transfermarkt para: {team1_name.lower()}")
                injuries_team1_tm = self.football_api.get_transfermarkt_injuries(team1_name.lower())
                if injuries_team1_tm and len(injuries_team1_tm) > 0:
                    if "injuries_transfermarkt" not in match_data["team1"]:
                        match_data["team1"]["injuries_transfermarkt"] = []
                    match_data["team1"]["injuries_transfermarkt"] = injuries_team1_tm
            except Exception as e:
                print(f"Error al obtener datos de Transfermarkt: {e}")
            
            try:
                print(f"Consultando lesiones en Transfermarkt para: {team2_name.lower()}")
                injuries_team2_tm = self.football_api.get_transfermarkt_injuries(team2_name.lower())
                if injuries_team2_tm and len(injuries_team2_tm) > 0:
                    if "injuries_transfermarkt" not in match_data["team2"]:
                        match_data["team2"]["injuries_transfermarkt"] = []
                    match_data["team2"]["injuries_transfermarkt"] = injuries_team2_tm
            except Exception as e:
                print(f"Error al obtener datos de Transfermarkt: {e}")
            
            # Obtener alineaciones si el partido tiene ID
            fixture_id = match_data.get("match_info", {}).get("fixture_id") or match_data.get("match_id")
            if fixture_id:
                try:
                    print(f"Consultando alineaciones para partido ID: {fixture_id}")
                    lineups = self.football_api.get_lineups(fixture_id)
                    if lineups and "response" in lineups and lineups["response"]:
                        match_data["lineups"] = lineups["response"]
                    else:
                        error_code = lineups.get("errors", {}).get("requests", {})
                        if error_code:
                            print(f"Error al obtener alineaciones: {error_code}")
                            # Generar alineaciones de fallback
                            match_data["lineups"] = self.generate_fallback_lineups(team1_name, team2_name)
                        else:
                            print("No se encontraron alineaciones para este partido")
                            # Generar alineaciones de fallback
                            match_data["lineups"] = self.generate_fallback_lineups(team1_name, team2_name)
                except Exception as e:
                    print(f"Error consultando alineaciones: {str(e)}")
                    # Generar alineaciones de fallback en caso de error
                    match_data["lineups"] = self.generate_fallback_lineups(team1_name, team2_name)
            else:
                print("No se puede obtener alineaciones: no hay ID de partido")
                # Generar alineaciones de fallback cuando no hay ID
                match_data["lineups"] = self.generate_fallback_lineups(team1_name, team2_name)
            
            # Obtener clasificación de la liga
            league_id = match_data.get("league", {}).get("id")
            if league_id:
                print(f"Obteniendo clasificación para la liga ID: {league_id}")
                standings_data = self.football_api.get_standings(league_id=league_id, season=season_year)
                if standings_data:
                    match_data["standings"] = standings_data

            # Obtener información del árbitro
            referee_name = match_data.get("referee", {}).get("name")
            if referee_name and league_id:
                print(f"Obteniendo estadísticas del árbitro: {referee_name}")
                referee_info = self.referee_api.get_referee_stats(referee_name, league_id, season_year)
                if referee_info:
                    match_data["referee_info"] = referee_info
                    # Indicar si el árbitro fue predicho o confirmado
                    match_data["referee"]["is_predicted"] = referee_info.get("is_predicted", False)

            # Obtener datos del clima (si hay info del estadio)
            if match_data.get("venue") and match_data["venue"].get("city"):
                city = match_data["venue"]["city"]
                print(f"Obteniendo datos del clima para: {city} (Fecha: {date_str})")
                # Pass the date_str to get forecast if applicable
                weather_data = self.weather_api.get_weather(city, date_str=date_str)
                if weather_data:
                    match_data["weather"] = weather_data

            # Obtener valores de mercado para los equipos
            print(f"Obteniendo valores de mercado para {team1_name} y {team2_name}...")
            try:
                team1_market_value = self.football_api.get_market_values(team_name=team1_name)
                if team1_market_value:
                    match_data["team1"]["market_value"] = team1_market_value

                team2_market_value = self.football_api.get_market_values(team_name=team2_name)
                if team2_market_value:
                    match_data["team2"]["market_value"] = team2_market_value
            except Exception as e:
                print(f"Error al obtener valores de mercado: {e}")

            # Obtener valores de mercado para jugadores
            print(f"Obteniendo valores de mercado para jugadores de {team1_name} y {team2_name}...")
            try:
                if "players" in match_data["team1"]:
                    for player in match_data["team1"]["players"]:
                        player_name = player.get("name")
                        if player_name:
                            player_market_value = self.football_api.get_market_values(player_name=player_name)
                            if player_market_value:
                                player["market_value"] = player_market_value

                if "players" in match_data["team2"]:
                    for player in match_data["team2"]["players"]:
                        player_name = player.get("name")
                        if player_name:
                            player_market_value = self.football_api.get_market_values(player_name=player_name)
                            if player_market_value:
                                player["market_value"] = player_market_value
            except Exception as e:
                print(f"Error al obtener valores de mercado para jugadores: {e}")

            # Optimizar datos para reducir tamaño, pasando distancia y futuros partidos
            optimized_data = self.data_processor.optimize_match_data(match_data, travel_distance, future_matches)

            # Save optimized data if required
            if save_data:
                self.save_match_data(optimized_data, team1_name, team2_name, date_str)

            return optimized_data
            
        except Exception as e:
            print(f"❌ Error al extraer datos del partido: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_all_data(self, team1_name, team2_name, date_str, options):
        """
        Extracts all requested data for a match based on user options.

        Args:
            team1_name (str): Name of the first team.
            team2_name (str): Name of the second team.
            date_str (str): Match date in YYYY-MM-DD format.
            options (dict): User-selected options for data extraction.

        Returns:
            dict: Extracted data.
        """
        match_data = self.extract_match_data(team1_name, team2_name, date_str)

        if not match_data:
            print("❌ Failed to extract match data.")
            return None

        # Extract additional data based on options
        if options.get("market_value"):
            print("Extracting market value data...")
            # Add logic to extract market value data

        if options.get("historical_analysis"):
            print("Extracting historical analysis data...")
            # Add logic to extract historical analysis data

        if options.get("recent_form"):
            print("Extracting recent form data...")
            # Add logic to extract recent form data

        if options.get("referee_analysis"):
            print("Extracting referee analysis data...")
            # Add logic to extract referee analysis data

        if options.get("coach_data"):
            print("Extracting coach data...")
            # Add logic to extract coach data

        if options.get("injury_report"):
            print("Extracting injury report data...")
            # Add logic to extract injury report data

        if options.get("physical_metrics"):
            print("Extracting physical metrics data...")
            # Add logic to extract physical metrics data

        if options.get("tactical_analysis"):
            print("Extracting tactical analysis data...")
            # Add logic to extract tactical analysis data

        return match_data

    def load_match_data(self, match_key):
        """
        Carga datos de un partido guardado previamente
        
        Args:
            match_key (str): Clave única del partido (formato: "equipo1-equipo2-YYYY-MM-DD")
            
        Returns:
            dict: Datos del partido o None si no se encuentra
        """
        return self.storage.load_match_data(match_key)
    
    def load_team_data(self, team_id):
        """
        Carga datos de un equipo guardado previamente
        
        Args:
            team_id (int): ID del equipo
            
        Returns:
            dict: Datos del equipo o None si no se encuentra
        """
        return self.storage.load_team_data(team_id)
    
    def _is_data_stale(self, timestamp_str: str, days_threshold: int = 7) -> bool:
        """
        Verifica si los datos están desactualizados (más antiguos que el umbral)
        
        Args:
            timestamp_str: Timestamp en formato ISO
            days_threshold: Número de días para considerar datos desactualizados
            
        Returns:
            bool: True si los datos están desactualizados, False en caso contrario
        """
        if not timestamp_str:
            return True
            
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            delta = datetime.now() - timestamp
            return delta.days > days_threshold
        except Exception:
            # Si hay un error al parsear, consideramos los datos desactualizados
            return True
    
    def save_players_data(self, team_id, team_name, players_data):
        """
        Guarda datos de jugadores en archivos individuales
        
        Args:
            team_id: ID del equipo
            team_name: Nombre del equipo
            players_data: Lista de jugadores
        """
        if not players_data:
            print(f"No hay datos de jugadores para guardar para el equipo {team_name}")
            return
        
        # Crear directorio para jugadores del equipo
        team_dir = os.path.join(self.data_dir, "players", str(team_id))
        os.makedirs(team_dir, exist_ok=True)
        
        # Guardar índice de jugadores
        index_file = os.path.join(team_dir, "index.json")
        index_data = {
            "team_id": team_id,
            "team_name": team_name,
            "players": []
        }
        
        print(f"Guardando {len(players_data)} jugadores para el equipo {team_name} (ID: {team_id})")
        
        # Guardar cada jugador en un archivo individual
        for player in players_data:
            if not player or not isinstance(player, dict):
                continue
                
            player_id = player.get("id")
            player_name = player.get("name")
            
            if not player_id or not player_name:
                continue
                
            # Agregar jugador al índice
            index_data["players"].append({
                "id": player_id,
                "name": player_name
            })
            
            # Guardar datos completos del jugador
            player_file = os.path.join(team_dir, f"{player_id}.json")
            with open(player_file, 'w', encoding='utf-8') as f:
                json.dump(player, f, ensure_ascii=False, indent=2)
        
        # Guardar archivo de índice
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        print(f"Guardados {len(index_data['players'])} jugadores para {team_name}")
    
    def save_team_data(self, team_id, team_name, team_data):
        """
        Guarda datos de un equipo en un archivo JSON
        
        Args:
            team_id: ID del equipo
            team_name: Nombre del equipo
            team_data: Datos del equipo
        """
        if not team_data:
            print(f"No hay datos del equipo para guardar para {team_name}")
            return
            
        # Crear directorio para equipos
        teams_dir = os.path.join(self.data_dir, "teams")
        os.makedirs(teams_dir, exist_ok=True)
        
        # Guardar datos del equipo
        team_file = os.path.join(teams_dir, f"{team_id}.json")
        with open(team_file, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, ensure_ascii=False, indent=2)
            
        print(f"Guardados datos para el equipo {team_name} (ID: {team_id})")
    
    def save_match_data(self, match_data, team1_name, team2_name, date_str):
        """
        Guarda datos del partido en un archivo JSON
        
        Args:
            match_data: Datos del partido
            team1_name: Nombre del equipo local
            team2_name: Nombre del equipo visitante
            date_str: Fecha del partido en formato YYYY-MM-DD
        """
        match_filename = f"{team1_name.lower().replace(' ', '_')}-{team2_name.lower().replace(' ', '_')}-{date_str}"
        match_filepath = os.path.join(self.data_dir, "matches", f"{match_filename}.json")
        os.makedirs(os.path.dirname(match_filepath), exist_ok=True)
        
        with open(match_filepath, 'w', encoding='utf-8') as f:
            json.dump(match_data, f, ensure_ascii=False, indent=2)
        print(f"Datos guardados en: {match_filepath}")
    
    def get_team_id(self, team_name):
        """
        Obtiene el ID de un equipo a partir de su nombre
        
        Args:
            team_name: Nombre del equipo
            
        Returns:
            int: ID del equipo o None si no se encuentra
        """
        print(f"Buscando equipo: {team_name}")
        team_data = self.football_api.advanced_team_search(team_name)
        
        if not team_data:
            print(f"No se encontró el equipo: {team_name}")
            return None
        
        # Extraer ID según la estructura retornada
        if isinstance(team_data, dict):
            if "id" in team_data:
                return team_data["id"]
            elif "team" in team_data and isinstance(team_data["team"], dict):
                if "id" in team_data["team"]:
                    return team_data["team"]["id"]
            
            # Intentar buscar en respuesta
            if "response" in team_data and isinstance(team_data["response"], list) and len(team_data["response"]) > 0:
                first_team = team_data["response"][0]
                if isinstance(first_team, dict):
                    if "team" in first_team and isinstance(first_team["team"], dict):
                        return first_team["team"].get("id")
                    elif "id" in first_team:
                        return first_team["id"]
        
        print(f"No se pudo obtener ID para equipo: {team_name}")
        print(f"Estructura de datos recibida: {type(team_data)}")
        if isinstance(team_data, dict):
            print(f"Claves disponibles: {list(team_data.keys())}")
            
        return None
    
    def find_scheduled_match(self, team1_id, team2_id, date_str, season=None):
        """
        Busca un partido programado entre dos equipos en una fecha específica
        
        Args:
            team1_id: ID del primer equipo
            team2_id: ID del segundo equipo
            date_str: Fecha del partido en formato YYYY-MM-DD
            season: Temporada (opcional)
            
        Returns:
            dict: Datos del partido o None si no se encuentra
        """
        # Si no se especifica temporada, calcularla a partir de la fecha
        if not season:
            match_date = datetime.strptime(date_str, "%Y-%m-%d")
            season = str(match_date.year - 1 if match_date.month < 7 else match_date.year)
        
        # Buscar partido con equipo 1 como filtro principal
        params = {
            "team": team1_id,
            "date": date_str,
            "season": season
        }
        print(f"Consultando API de fútbol. Endpoint: {self.football_api.BASE_URL}/fixtures, Parámetros:\n{params}")
        
        fixtures_data = self.football_api.get_fixtures(**params)
        
        if fixtures_data and "response" in fixtures_data and fixtures_data["response"]:
            fixtures = fixtures_data["response"]
            print(f"Se encontraron {len(fixtures)} partidos para el equipo {team1_id}")
            
            # Buscar partido contra equipo 2
            for fixture in fixtures:
                teams = fixture.get("teams", {})
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                
                if (home_team.get("id") == team2_id or away_team.get("id") == team2_id):
                    return fixture
        
        # Si no se encontró, intentar con equipo 2 como filtro principal
        params = {
            "team": team2_id,
            "date": date_str,
            "season": season
        }
        
        fixtures_data = self.football_api.get_fixtures(**params)
        
        if fixtures_data and "response" in fixtures_data and fixtures_data["response"]:
            fixtures = fixtures_data["response"]
            print(f"Se encontraron {len(fixtures)} partidos para el equipo {team2_id}")
            
            # Buscar partido contra equipo 1
            for fixture in fixtures:
                teams = fixture.get("teams", {})
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                
                if (home_team.get("id") == team1_id or away_team.get("id") == team1_id):
                    return fixture
        
        # No se encontró ningún partido
        print(f"No se encontró partido programado entre {team1_id} y {team2_id} para la fecha {date_str}")
        return None

    @staticmethod
    def parse_match_input(input_text):
        """
        Analiza el texto de entrada para extraer equipos y fecha
        
        Args:
            input_text (str): Texto con formato "Equipo1 vs Equipo2 - YYYY-MM-DD"
            
        Returns:
            dict: Diccionario con datos del partido {team1, team2, date} o None si el formato es inválido
            list: Lista [team1, team2, date]
        """
        try:
            # Normalizar texto: eliminar espacios adicionales y convertir guiones
            normalized_text = input_text.strip().replace("—", "-").replace("–", "-")
            
            # Buscar una fecha en formato YYYY-MM-DD en el texto
            date_pattern = r"(\d{4}-\d{2}-\d{2})"
            date_match = re.search(date_pattern, normalized_text)
            
            if date_match:
                # Si encontramos una fecha en formato ISO, extraerla
                date_str = date_match.group(1)
                # Quitar la fecha del texto para facilitar extracción de equipos
                text_without_date = normalized_text.replace(date_match.group(0), "").strip()
                # Limpiar cualquier guión adicional al final o inicio
                text_without_date = re.sub(r"^\s*-\s*|\s*-\s*$", "", text_without_date)
                
                # Si hay un separador vs, usar para extraer equipos
                if " vs " in text_without_date:
                    teams = text_without_date.split(" vs ")
                    if len(teams) == 2:
                        team1 = teams[0].strip()
                        team2 = teams[1].strip()
                        return [team1, team2, date_str]
            
            # Patrón clásico: "Equipo1 vs Equipo2 - YYYY-MM-DD" o variantes
            if " vs " in normalized_text:
                # Dividir primero por "vs" para obtener los dos lados
                before_vs, after_vs = normalized_text.split(" vs ", 1)
                
                # El primer equipo es la parte antes del "vs"
                team1 = before_vs.strip()
                
                # Chequear si hay una fecha en formato YYYY-MM-DD o YYYY-MM en after_vs
                partial_date = re.search(r"\s*-\s*(\d{4}-\d{2}(-\d{2})?)", after_vs)
                if partial_date:
                    # Extraer el segundo equipo sin la fecha
                    team2 = after_vs[:partial_date.start()].strip()
                    date_part = partial_date.group(1)
                    
                    # Normalizar la fecha si es parcial (YYYY-MM)
                    if re.match(r"\d{4}-\d{2}$", date_part):
                        # Asumimos el día 7 por defecto para fechas parciales
                        date_str = f"{date_part}-07"
                    else:
                        date_str = date_part
                else:
                    # Si no hay fecha después del nombre del segundo equipo
                    # buscar separador de fecha (guión) en after_vs
                    parts = after_vs.split(" - ")
                    if len(parts) > 1:
                        team2 = parts[0].strip()
                        # Intentar extraer fecha del resto
                        date_part = parts[1].strip()
                        if re.match(r"\d{4}-\d{2}-\d{2}", date_part):
                            date_str = date_part
                        elif re.match(r"\d{4}-\d{2}", date_part):
                            # Asumimos el día 7 por defecto
                            date_str = f"{date_part}-07"
                        else:
                            # Si no hay un formato de fecha claro, usar fecha actual
                            date_str = datetime.now().strftime("%Y-%m-%d")
                    else:
                        # Si no hay separador, asumimos que todo after_vs es team2
                        team2 = after_vs.strip()
                        date_str = datetime.now().strftime("%Y-%m-%d")
                    
                return [team1, team2, date_str]
            
            # Casos sin "vs" pero con guión separando equipos
            parts = normalized_text.split(" - ")
            if len(parts) >= 2:
                # Primer parte casi seguro es el primer equipo
                team1 = parts[0].strip()
                
                # Si la última parte es una fecha en formato YYYY-MM-DD
                last_part = parts[-1].strip()
                if re.match(r"\d{4}-\d{2}-\d{2}", last_part):
                    # La fecha es la última parte
                    date_str = last_part
                    # El equipo 2 está en las partes intermedias (si hay más de 2 partes)
                    if len(parts) > 2:
                        team2 = " - ".join(parts[1:-1]).strip()
                    else:
                        # Solo hay 2 partes, pero la segunda es fecha
                        # Esto es confuso, así que asumimos un nombre genérico
                        team2 = "Equipo Visitante"
                else:
                    # No hay fecha clara, asumir que la segunda parte es equipo 2
                    team2 = parts[1].strip()
                    # Usar fecha actual
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    
                return [team1, team2, date_str]
            
            # Patrones alternativos para casos difíciles
            alternative_formats = [
                # Partido con solo un nombre de equipo y fecha
                r"([A-Za-z\s]+)(\d{4}-\d{2}-\d{2})",
                # Equipo contra equipo
                r"([A-Za-z\s]+)\s+(?:contra|vs|v)\s+([A-Za-z\s]+)"
            ]
            
            for pattern in alternative_formats:
                match = re.search(pattern, normalized_text)
                if match:
                    if len(match.groups()) == 2:
                        if re.match(r"\d{4}-\d{2}-\d{2}", match.group(2)):
                            # Es un patrón de equipo y fecha
                            team1 = match.group(1).strip()
                            team2 = "Equipo Visitante"  # Nombre genérico
                            date_str = match.group(2)
                        else:
                            # Es un patrón de dos equipos
                            team1 = match.group(1).strip()
                            team2 = match.group(2).strip()
                            date_str = datetime.now().strftime("%Y-%m-%d")
                        return [team1, team2, date_str]
            
            # Fallback simple para formato básico "Equipo vs Equipo"
            if " vs " in normalized_text:
                teams = normalized_text.split(" vs ")
                team1 = teams[0].strip()
                team2 = teams[1].strip()
                date_str = datetime.now().strftime("%Y-%m-%d")
                return [team1, team2, date_str]
            
            for pattern in common_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    if match.group(1) and match.group(2):
                        # Verificar si el segundo grupo es una fecha válida
                        try:
                            datetime.strptime(match.group(2), "%Y-%m-%d")
                            team1 = match.group(1).strip()
                            # Usar fecha actual para team2
                            return [team1, "unknown", match.group(2)]
                        except ValueError:
                            # Si no es fecha, asumir que son los equipos
                            team1 = match.group(1).strip()
        except Exception as e:
            print(f"Error al parsear texto de entrada: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def run_interactive(self):
        """
        Ejecuta el programa en modo interactivo, permitiendo al usuario consultar partidos
        """
        print("\n" + "=" * 60)
        print(" " * 10 + "EXTRACTOR DE DATOS DE PARTIDOS DE FÚTBOL")
        print("=" * 60)
        print("ℹ️ Herramienta para obtener información detallada de partidos")
        print("ℹ️ Formato: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
        print("ℹ️ Ejemplo: 'Barcelona vs Real Madrid - 2023-10-28'")
        print("-" * 60)
        
        while True:
            user_input = input("Ingresa el partido (o 'salir' para terminar): ")
            
            if user_input.lower() == 'salir':
                print("\nℹ️ Gracias por usar el extractor de datos de partidos. ¡Hasta pronto!")
                break
                
            print("ℹ️ Procesando solicitud...")
            start_time = time.time()
            
            # Parsear la entrada del usuario
            match_info = self.parse_match_input(user_input)
            
            if not match_info:
                print("❌ No se pudo procesar la entrada. Por favor, utiliza el formato: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
                continue
                
            # Extraer datos del partido
            team1, team2, date_str = match_info
            match_data = self.extract_match_data(team1, team2, date_str)
            
            if not match_data:
                print("❌ No se pudo obtener información del partido")
                continue
                
            # Mostrar resumen
            print(f"✅ Datos obtenidos en {time.time() - start_time:.2f} segundos\n")
            self.print_match_summary(match_data)
            
            # Pausa antes de continuar
            print("-" * 60)

    def print_match_summary(self, match_data):
        """
        Muestra un resumen del partido en la consola
        
        Args:
            match_data: Datos del partido
        """
        if not match_data:
            print("No hay datos disponibles para mostrar")
            return
            
        print("\n" + "=" * 60)
        print(" " * 20 + "RESUMEN DEL PARTIDO")
        print("=" * 60)
        
        # Información básica del partido
        team1_name = match_data.get("team1", {}).get("name", "Desconocido")
        team2_name = match_data.get("team2", {}).get("name", "Desconocido")
        
        print(f"⚽ PARTIDO: {team1_name} vs {team2_name}")
        print(f"📅 Fecha: {match_data.get('date', 'No disponible')}")
        
        # Liga
        league = match_data.get("league", {})
        if league:
            league_name = league.get("name", "No disponible")
            print(f"🏆 Liga: {league_name}")
        
        # Estadio
        venue = match_data.get("venue", {})
        if venue:
            venue_name = venue.get("name", "No disponible")
            venue_city = venue.get("city", "")
            venue_str = f"{venue_name}, {venue_city}" if venue_city else venue_name
            print(f"🏟️ Estadio: {venue_str}")
        
        # Árbitro
        referee = match_data.get("referee", {})
        if referee:
            referee_name = referee.get("name", "No disponible")
            referee_type = "PREDICHO" if referee.get("is_predicted", False) else "OFICIAL"
            print(f"🚩 Árbitro: {referee_name} ({referee_type})")
        
        print("\n")
        
        # Historial de enfrentamientos
        h2h = match_data.get("h2h", {})
        if h2h:
            total_matches = h2h.get("total", 0)
            team1_wins = h2h.get("team1_wins", 0)
            team2_wins = h2h.get("team2_wins", 0)
            draws = h2h.get("draws", 0)
            
            print("🔄 HISTORIAL DE ENFRENTAMIENTOS:")
            print(f"  • Total de partidos: {total_matches}")
            print(f"  • {team1_name}: {team1_wins} victorias")
            print(f"  • {team2_name}: {team2_wins} victorias")
            print(f"  • Empates: {draws}")
            print("\n")
        
        # Partidos recientes
        recent_matches = h2h.get("recent_matches", [])
        if recent_matches:
            print("📊 PARTIDOS RECIENTES:")
            for i, match in enumerate(recent_matches[:5], 1):
                match_date = match.get("date", "")
                league = match.get("league", "")
                result = match.get("result_text", "")
                score = match.get("score", "")
                
                if result.startswith("W"):
                    result_indicator = "(W)"
                elif result.startswith("L"):
                    result_indicator = "(L)"
                elif result.startswith("D"):
                    result_indicator = "(D)"
                else:
                    result_indicator = ""
                
                print(f"  • {match_date} [{league}]: {team1_name} {score} {team2_name} {result_indicator}")
                
        print("\n")
        
        # Información de lesiones si está disponible
        team1_injuries = match_data.get("team1", {}).get("injuries", [])
        team2_injuries = match_data.get("team2", {}).get("injuries", [])
        
        if team1_injuries or team2_injuries:
            print("🚑 JUGADORES LESIONADOS/SANCIONADOS:")
            
            if team1_injuries:
                print(f"  {team1_name}:")
                for injury in team1_injuries[:3]:  # Mostrar solo las primeras 3 lesiones
                    player_name = injury.get("player", {}).get("name", "Desconocido")
                    reason = injury.get("type", "Lesión")
                    print(f"    • {player_name} - {reason}")
            
            if team2_injuries:
                print(f"  {team2_name}:")
                for injury in team2_injuries[:3]:  # Mostrar solo las primeras 3 lesiones
                    player_name = injury.get("player", {}).get("name", "Desconocido")
                    reason = injury.get("type", "Lesión")
                    print(f"    • {player_name} - {reason}")
        
        # Consultar archivo para más detalles
        print("\n" + "-" * 60)

def main():
    """Función principal del programa"""
    try:
        # Crear instancia del extractor
        extractor = FootballDataExtractor()

        # Obtener los argumentos de la línea de comandos
        parser = argparse.ArgumentParser(description='Extractor de datos de partidos de fútbol')
        parser.add_argument('--match', type=str, help='Partido en formato "Equipo1 vs Equipo2 - YYYY-MM-DD"')
        parser.add_argument('--interactive', action='store_true', help='Modo interactivo')

        args = parser.parse_args()

        # Ejecutar según los argumentos
        if args.interactive:
            extractor.run_interactive()
        elif args.match:
            # Parsear la entrada del comando
            match_info = extractor.parse_match_input(args.match)
            
            if match_info:
                team1, team2, date_str = match_info
                # Limpiar posibles artefactos en los nombres de equipos
                team1 = team1.split(' - ')[0].strip() if ' - ' in team1 else team1
                team2 = team2.split(' - ')[0].strip() if ' - ' in team2 else team2
                
                match_data = extractor.extract_match_data(team1, team2, date_str)
                
                if match_data:
                    extractor.print_match_summary(match_data)
                else:
                    print("❌ No se pudo obtener información del partido")
            else:
                print("❌ Formato incorrecto. Use: --match 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
        else:
            # Si no hay argumentos, ejecutar modo interactivo
            extractor.run_interactive()

    except Exception as e:
        print(f"Error en la aplicación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()