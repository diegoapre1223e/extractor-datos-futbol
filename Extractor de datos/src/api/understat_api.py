import json
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
from datetime import datetime

class UnderstatAPI:
    """
    Clase para interactuar con los datos de Understat
    """
    
    # Mapeo de posiciones y sus métricas específicas
    POSITION_METRICS = {
        "Forward": {
            "key_metrics": ["goals", "xG", "shots", "key_passes", "assists", "xA"],
            "advanced_metrics": [
                "goal_conversion_rate",  # goles / tiros
                "xG_per_shot",  # xG / tiros
                "goals_above_xG",  # goles - xG
                "shots_on_target_ratio"  # tiros al arco / tiros totales
            ]
        },
        "Midfielder": {
            "key_metrics": ["key_passes", "assists", "xA", "passes", "through_balls", "tackles"],
            "advanced_metrics": [
                "pass_completion_rate",  # pases completados / pases totales
                "chances_created_per_90",  # (key_passes + assists) / minutos * 90
                "progressive_passes_ratio",  # pases progresivos / pases totales
                "pressure_regains"  # recuperaciones tras presión
            ]
        },
        "Defender": {
            "key_metrics": ["tackles", "interceptions", "clearances", "blocks", "duels_won", "aerial_duels"],
            "advanced_metrics": [
                "tackle_success_rate",  # tackles exitosos / tackles totales
                "aerial_duel_success",  # duelos aéreos ganados / totales
                "pressure_success_rate",  # presiones exitosas / totales
                "progressive_carries"  # conducciones progresivas
            ]
        },
        "Goalkeeper": {
            "key_metrics": ["saves", "goals_conceded", "clean_sheets", "xG_prevented", "crosses_claimed"],
            "advanced_metrics": [
                "save_percentage",  # atajadas / tiros al arco
                "goals_prevented",  # xG contra - goles concedidos
                "distribution_accuracy",  # pases completados / intentos
                "sweeper_actions"  # acciones fuera del área
            ]
        }
    }
    
    def __init__(self, football_api):
        """
        Inicializa la API de Understat
        
        Args:
            football_api: Instancia de FootballAPI para utilizar sus métodos HTTP
        """
        self.football_api = football_api
        self.session = requests.Session()  # Inicializar la sesión para solicitudes HTTP
        
    def _determine_player_position(self, player_data):
        """Determina la posición principal de un jugador basado en sus estadísticas"""
        # Implementar lógica de detección de posición basada en estadísticas
        stats = player_data.get("stats", {})
        
        # Puntajes para cada posición
        position_scores = {
            "Forward": 0,
            "Midfielder": 0,
            "Defender": 0,
            "Goalkeeper": 0
        }
        
        # Analizar estadísticas para determinar posición
        if stats:
            # Métricas ofensivas
            goals = float(stats.get("goals", 0))
            shots = float(stats.get("shots", 0))
            xG = float(stats.get("xG", 0))
            position_scores["Forward"] += (goals * 3 + shots + xG * 2)
            
            # Métricas de mediocampo
            assists = float(stats.get("assists", 0))
            key_passes = float(stats.get("key_passes", 0))
            xA = float(stats.get("xA", 0))
            position_scores["Midfielder"] += (assists * 2 + key_passes + xA * 2)
            
            # Métricas defensivas
            tackles = float(stats.get("tackles", 0))
            interceptions = float(stats.get("interceptions", 0))
            blocks = float(stats.get("blocks", 0))
            position_scores["Defender"] += (tackles * 2 + interceptions * 2 + blocks)
            
            # Métricas de portero
            saves = float(stats.get("saves", 0))
            clean_sheets = float(stats.get("clean_sheets", 0))
            position_scores["Goalkeeper"] += (saves * 3 + clean_sheets * 5)
        
        # Determinar la posición con mayor puntaje
        return max(position_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_position_metrics(self, player_data, position):
        """Calcula métricas específicas para la posición del jugador"""
        stats = player_data.get("stats", {})
        if not stats:
            return {}
            
        metrics = {}
        position_config = self.POSITION_METRICS.get(position, {})
        
        # Calcular métricas básicas de la posición
        for metric in position_config.get("key_metrics", []):
            metrics[metric] = float(stats.get(metric, 0))
        
        # Calcular métricas avanzadas según la posición
        if position == "Forward":
            shots = float(stats.get("shots", 0))
            goals = float(stats.get("goals", 0))
            xG = float(stats.get("xG", 0))
            shots_on_target = float(stats.get("shots_on_target", 0))
            
            if shots > 0:
                metrics["goal_conversion_rate"] = (goals / shots) * 100
                metrics["xG_per_shot"] = xG / shots
                metrics["shots_on_target_ratio"] = (shots_on_target / shots) * 100
            
            metrics["goals_above_xG"] = goals - xG
            
        elif position == "Midfielder":
            minutes = float(stats.get("time", 0))
            key_passes = float(stats.get("key_passes", 0))
            assists = float(stats.get("assists", 0))
            passes = float(stats.get("passes", 0))
            passes_completed = float(stats.get("passes_completed", 0))
            
            if passes > 0:
                metrics["pass_completion_rate"] = (passes_completed / passes) * 100
            
            if minutes > 0:
                metrics["chances_created_per_90"] = ((key_passes + assists) / minutes) * 90
            
        elif position == "Defender":
            tackles = float(stats.get("tackles", 0))
            tackles_won = float(stats.get("tackles_won", 0))
            aerial_duels = float(stats.get("aerial_duels", 0))
            aerial_duels_won = float(stats.get("aerial_duels_won", 0))
            
            if tackles > 0:
                metrics["tackle_success_rate"] = (tackles_won / tackles) * 100
            
            if aerial_duels > 0:
                metrics["aerial_duel_success"] = (aerial_duels_won / aerial_duels) * 100
            
        elif position == "Goalkeeper":
            shots_on_target_against = float(stats.get("shots_on_target_against", 0))
            saves = float(stats.get("saves", 0))
            goals_conceded = float(stats.get("goals_conceded", 0))
            xG_against = float(stats.get("xG_against", 0))
            
            if shots_on_target_against > 0:
                metrics["save_percentage"] = (saves / shots_on_target_against) * 100
            
            metrics["goals_prevented"] = xG_against - goals_conceded
        
        return metrics
    
    def _process_historical_data(self, matches_data, shots_data):
        """Procesa datos históricos para obtener tendencias y patrones"""
        if not matches_data or not shots_data:
            return None
            
        historical_data = {
            "form": [],  # Últimos 5 partidos
            "trends": {},  # Tendencias en diferentes métricas
            "patterns": {},  # Patrones identificados
            "performance_by_situation": {}  # Rendimiento por tipo de situación
        }
        
        # Procesar últimos 5 partidos
        recent_matches = sorted(matches_data, key=lambda x: x.get("date", ""))[-5:]
        for match in recent_matches:
            match_summary = {
                "date": match.get("date"),
                "opponent": match.get("opponent"),
                "result": match.get("result"),
                "goals_for": match.get("goals_for"),
                "goals_against": match.get("goals_against"),
                "xG_for": match.get("xG_for"),
                "xG_against": match.get("xG_against")
            }
            historical_data["form"].append(match_summary)
        
        # Calcular tendencias
        all_matches = matches_data
        if all_matches:
            trends = {
                "goals_trend": [],
                "xG_trend": [],
                "shots_trend": [],
                "points_trend": []
            }
            
            window_size = 5  # Ventana móvil de 5 partidos
            for i in range(len(all_matches) - window_size + 1):
                window = all_matches[i:i+window_size]
                avg_goals = sum(float(m.get("goals_for", 0)) for m in window) / window_size
                avg_xG = sum(float(m.get("xG_for", 0)) for m in window) / window_size
                avg_shots = sum(float(m.get("shots", 0)) for m in window) / window_size
                
                trends["goals_trend"].append(avg_goals)
                trends["xG_trend"].append(avg_xG)
                trends["shots_trend"].append(avg_shots)
            
            historical_data["trends"] = trends
        
        # Analizar patrones
        if shots_data:
            patterns = {
                "shot_locations": {},  # Zonas de tiro preferidas
                "goal_patterns": {},  # Patrones de gol
                "play_patterns": {}  # Patrones de juego
            }
            
            for shot in shots_data:
                # Analizar ubicación del tiro
                location = (shot.get("X"), shot.get("Y"))
                situation = shot.get("situation")
                result = shot.get("result")
                
                # Actualizar patrones de tiro
                zone = self._determine_shot_zone(location)
                patterns["shot_locations"][zone] = patterns["shot_locations"].get(zone, 0) + 1
                
                # Actualizar patrones de gol si el tiro fue gol
                if result == "Goal":
                    patterns["goal_patterns"][situation] = patterns["goal_patterns"].get(situation, 0) + 1
                
                # Actualizar patrones de juego
                patterns["play_patterns"][situation] = patterns["play_patterns"].get(situation, 0) + 1
            
            historical_data["patterns"] = patterns
        
        return historical_data
    
    def _determine_shot_zone(self, location):
        """Determina la zona del campo donde se realizó el tiro"""
        x, y = location
        
        # Dividir el campo en zonas
        if x >= 0.8:  # Área pequeña
            if 0.4 <= y <= 0.6:
                return "six_yard_box"
            else:
                return "penalty_area"
        elif x >= 0.6:  # Área grande
            return "edge_of_box"
        elif x >= 0.4:  # Media distancia
            return "long_range"
        else:  # Larga distancia
            return "very_long_range"
    
    def get_team_data(self, team_name, year=None):
        """
        Obtiene datos de Understat para un equipo
        
        Args:
            team_name: Nombre del equipo
            year: Año de la temporada (opcional)
            
        Returns:
            dict: Datos de Understat procesados
        """
        try:
            # Normalize team name by removing date suffix if present
            if ' ' in team_name:
                team_name = team_name.split(' ')[0]

            # Normalizar el nombre del equipo
            understat_team_mapping = {
                "manchester united": "Manchester_United",
                "manchester city": "Manchester_City",
                "chelsea": "Chelsea",
                # Agregar más mapeos según sea necesario
            }
            formatted_team_name = understat_team_mapping.get(team_name.lower(), team_name.replace(' ', '_'))
            print(f"Consultando Understat para equipo: {team_name} (formateado como: {formatted_team_name})")

            # Generar la URL base de Understat
            base_url = f"https://understat.com/team/{formatted_team_name}"
            if year:
                base_url += f"/{year}"

            print(f"Realizando petición a: {base_url}")
            response = self.session.get(base_url)
            response.raise_for_status()

            # Extraer datos del HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script')

            # Datos a extraer
            team_data = None
            players_data = None
            matches_data = None
            shots_data = None

            for script in script_tags:
                if not script.string:
                    continue
                    
                if 'var teamsData' in script.string:
                    json_str = script.string.split('JSON.parse(')[1].split(')')[0].strip("'")
                    team_data = json.loads(json_str)
                elif 'var playersData' in script.string:
                    json_str = script.string.split('JSON.parse(')[1].split(')')[0].strip("'")
                    players_data = json.loads(json_str)
                elif 'var matchesData' in script.string:
                    json_str = script.string.split('JSON.parse(')[1].split(')')[0].strip("'")
                    matches_data = json.loads(json_str)
                elif 'var shotsData' in script.string:
                    json_str = script.string.split('JSON.parse(')[1].split(')')[0].strip("'")
                    shots_data = json.loads(json_str)

            if not team_data or not players_data:
                return {
                    "status": "error",
                    "message": "No se pudieron extraer los datos del equipo o jugadores"
                }

            # Procesar datos
            result = {
                "status": "success",
                "team_stats": team_data,
                "players": {},
                "matches": matches_data,
                "shots": shots_data,
                "historical_performance": self._process_historical_data(matches_data, shots_data) if matches_data else None,
                "metadata": {
                    "team": team_name,
                    "formatted_team": formatted_team_name,
                    "year": year,
                    "url": base_url,
                    "timestamp": datetime.now().isoformat(),
                    "data_points": len(players_data) if players_data else 0
                }
            }

            # Procesar datos de jugadores con métricas por posición
            for player_id, player_data in players_data.items():
                # Determinar posición
                position = self._determine_player_position(player_data)
                
                # Calcular métricas específicas de la posición
                position_metrics = self._calculate_position_metrics(player_data, position)
                
                # Combinar datos básicos con métricas avanzadas
                result["players"][player_id] = {
                    **player_data,
                    "position": position,
                    "position_metrics": position_metrics
                }

            return result

        except requests.exceptions.RequestException as e:
            print(f"Error en la petición HTTP: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en la petición HTTP: {str(e)}"
            }
        except Exception as e:
            print(f"Error procesando datos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error procesando datos: {str(e)}"
            }

        except Exception as e:
            print(f"Error al obtener datos de Understat: {str(e)}")
            # Provide fallback data when Understat fails
            return self._generate_fallback_team_data(team_name, year)
            
    def _generate_fallback_team_data(self, team_name, year=None):
        """
        Genera datos estimados cuando no es posible obtener datos reales de Understat.
        
        Args:
            team_name: Nombre del equipo
            year: Año de la temporada (opcional)
            
        Returns:
            dict: Datos de estimados para análisis de respaldo
        """
        print(f"Generando datos de respaldo para {team_name} (año: {year})")
        
        # Año actual si no se proporciona
        current_year = datetime.now().year
        year = year if year else current_year
        
        # Generar ID aleatorio para el equipo
        team_id = str(hash(team_name) % 10000)
        
        # Datos básicos del equipo (estimaciones medias razonables)
        team_stats = {
            "team_id": team_id,
            "team_name": team_name,
            "goals": 45,  # ~ goles por temporada
            "goals_against": 40,
            "xG": 48.5,
            "xGA": 42.3,
            "shots": 450,
            "shots_against": 430
        }
        
        # Generar 20 jugadores de ejemplo (estimaciones razonables)
        players = []
        positions = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
        position_counts = {"Forward": 4, "Midfielder": 8, "Defender": 6, "Goalkeeper": 2}
        
        player_id = 0
        for position, count in position_counts.items():
            for i in range(count):
                player_id += 1
                
                # Valores diferentes según la posición
                if position == "Forward":
                    goals = np.random.poisson(8)  # más goles para delanteros
                    assists = np.random.poisson(4)
                    shots = goals * np.random.randint(4, 8)
                    key_passes = np.random.poisson(30)
                    xG = goals * 0.9 + np.random.normal(0, 1)
                    xA = assists * 0.8 + np.random.normal(0, 0.5)
                elif position == "Midfielder":
                    goals = np.random.poisson(4)
                    assists = np.random.poisson(6)  # más asistencias para mediocampistas
                    shots = goals * np.random.randint(3, 6)
                    key_passes = np.random.poisson(50)  # más pases clave
                    xG = goals * 0.85 + np.random.normal(0, 0.8)
                    xA = assists * 0.9 + np.random.normal(0, 0.7)
                elif position == "Defender":
                    goals = np.random.poisson(2)
                    assists = np.random.poisson(2)
                    shots = goals * np.random.randint(2, 5)
                    key_passes = np.random.poisson(20)
                    xG = goals * 0.7 + np.random.normal(0, 0.5)
                    xA = assists * 0.7 + np.random.normal(0, 0.4)
                else:  # Goalkeeper
                    goals = 0
                    assists = np.random.poisson(1)
                    shots = np.random.poisson(1)
                    key_passes = np.random.poisson(5)
                    xG = 0.1
                    xA = assists * 0.5
                
                # Datos básicos comunes
                games = np.random.randint(20, 38)
                minutes = games * np.random.randint(70, 90)
                yellow_cards = np.random.poisson(3)
                red_cards = np.random.poisson(0.2)  # menos frecuentes
                
                player_info = {
                    "player_id": str(player_id),
                    "player_name": f"Player_{player_id}_{position}",
                    "position": position,
                    "games": games,
                    "goals": goals,
                    "assists": assists,
                    "xG": max(0, xG),  # evitar valores negativos
                    "xA": max(0, xA),
                    "shots": shots,
                    "key_passes": key_passes,
                    "yellow_cards": yellow_cards,
                    "red_cards": red_cards,
                    "minutes": minutes
                }
                players.append(player_info)
        
        # Generar datos de partidos de ejemplo (últimos 10 partidos)
        matches = []
        for i in range(10):
            # Simulamos si el partido fue de local o visitante
            is_home = i % 2 == 0
            
            # Generamos resultados aleatorios basados en promedios razonables
            if is_home:
                home_team = team_name
                away_team = f"Opponent_{i+1}"
                goals_home = np.random.poisson(1.5)  # promedio de goles en casa
                goals_away = np.random.poisson(1.0)  # promedio de goles visitante
                xG_home = goals_home * 0.9 + np.random.normal(0, 0.3)
                xG_away = goals_away * 0.85 + np.random.normal(0, 0.2)
            else:
                home_team = f"Opponent_{i+1}"
                away_team = team_name
                goals_home = np.random.poisson(1.4)  # promedio de goles local
                goals_away = np.random.poisson(1.1)  # promedio de goles visitante
                xG_home = goals_home * 0.85 + np.random.normal(0, 0.3)
                xG_away = goals_away * 0.9 + np.random.normal(0, 0.2)
            
            # Determinar resultado para este equipo
            if (is_home and goals_home > goals_away) or (not is_home and goals_away > goals_home):
                result = "W"  # Victoria
            elif (is_home and goals_home < goals_away) or (not is_home and goals_away < goals_home):
                result = "L"  # Derrota
            else:
                result = "D"  # Empate
            
            # Fecha del partido (generamos fechas pasadas)
            days_ago = (i + 1) * 7  # cada 7 días aproximadamente
            match_date = (datetime.now() - pd.Timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            match_info = {
                "match_id": f"m{year}{i}",
                "date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "goals_home": goals_home,
                "goals_away": goals_away,
                "xG_home": max(0, xG_home),  # evitar valores negativos
                "xG_away": max(0, xG_away),
                "result": result
            }
            matches.append(match_info)
        
        # Ordenar partidos por fecha (más reciente primero)
        matches.sort(key=lambda x: x["date"], reverse=True)
        
        # Devolver datos de respaldo
        return {
            "status": "success",
            "source": "fallback-estimation",
            "team": team_stats,
            "players": players,
            "matches": matches,
            "metadata": {
                "team": team_name,
                "year": year,
                "is_fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        }

    def get_team_statistics(self, team_name, season):
        """Obtiene estadísticas relevantes de Understat para un equipo."""
        formatted_name = team_name.replace(" ", "_")
        url = f"https://understat.com/team/{formatted_name}/{season}"
        response = self.make_request(url)
        if response:
            return self.parse_understat_data(response)
        return None

    def get_historical_performance(self, team_name: str, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene y analiza el rendimiento histórico de un equipo.

        Args:
            team_name (str): Nombre del equipo
            start_year (int, optional): Año inicial para el análisis
            end_year (int, optional): Año final para el análisis

        Returns:
            Dict[str, Any]: Datos históricos procesados incluyendo:
                - trends: Tendencias en diferentes métricas
                - patterns: Patrones identificados
                - form: Rendimiento reciente
                - metadata: Información sobre la consulta
        """
        try:
            # Normalizar el nombre del equipo
            formatted_team_name = team_name.replace(' ', '_')
            
            # Si no se especifican años, usar los últimos 3 años
            from datetime import datetime
            current_year = datetime.now().year
            if not end_year:
                end_year = current_year
            if not start_year:
                start_year = end_year - 2

            historical_data = {
                "status": "success",
                "trends": {},
                "patterns": {},
                "form": [],
                "metadata": {
                    "team": team_name,
                    "start_year": start_year,
                    "end_year": end_year,
                    "years_analyzed": end_year - start_year + 1,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Recopilar datos para cada año
            all_matches = []
            all_shots = []
            
            for year in range(start_year, end_year + 1):
                year_data = self.get_team_data(team_name, year)
                if year_data["status"] == "success":
                    if "matches" in year_data:
                        all_matches.extend(year_data["matches"])
                    if "shots" in year_data:
                        all_shots.extend(year_data["shots"])

            if not all_matches:
                return {
                    "status": "error",
                    "message": "No se encontraron datos históricos",
                    "metadata": historical_data["metadata"]
                }

            # Procesar datos históricos
            processed_data = self._process_historical_data(all_matches, all_shots)
            if processed_data:
                historical_data.update(processed_data)

            # Calcular métricas adicionales
            if all_matches:
                # Rendimiento por temporada
                season_performance = {}
                for match in all_matches:
                    season = match.get("season", "unknown")
                    if season not in season_performance:
                        season_performance[season] = {
                            "matches": 0,
                            "wins": 0,
                            "draws": 0,
                            "losses": 0,
                            "goals_for": 0,
                            "goals_against": 0,
                            "xG_for": 0,
                            "xG_against": 0,
                            "points": 0
                        }
                    
                    stats = season_performance[season]
                    stats["matches"] += 1
                    
                    result = match.get("result")
                    if result == "w":
                        stats["wins"] += 1
                        stats["points"] += 3
                    elif result == "d":
                        stats["draws"] += 1
                        stats["points"] += 1
                    elif result == "l":
                        stats["losses"] += 1
                    
                    stats["goals_for"] += int(match.get("goals_for", 0))
                    stats["goals_against"] += int(match.get("goals_against", 0))
                    stats["xG_for"] += float(match.get("xG_for", 0))
                    stats["xG_against"] += float(match.get("xG_against", 0))
                
                historical_data["season_performance"] = season_performance

            return historical_data

        except Exception as e:
            print(f"Error obteniendo datos históricos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "team": team_name,
                    "start_year": start_year,
                    "end_year": end_year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def analyze_tactical_patterns(self, team_name: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analiza los patrones tácticos y formaciones de un equipo.

        Args:
            team_name (str): Nombre del equipo
            year (int, optional): Año para el análisis

        Returns:
            Dict[str, Any]: Análisis táctico incluyendo:
                - formations: Formaciones utilizadas y su frecuencia
                - play_patterns: Patrones de juego identificados
                - possession_stats: Estadísticas de posesión
                - pressure_stats: Estadísticas de presión
        """
        try:
            # Obtener datos del equipo
            team_data = self.get_team_data(team_name, year)
            if team_data["status"] != "success":
                return {
                    "status": "error",
                    "message": "No se pudieron obtener datos del equipo"
                }

            matches = team_data.get("matches", [])
            if not matches:
                return {
                    "status": "error",
                    "message": "No se encontraron partidos para analizar"
                }

            tactical_analysis = {
                "status": "success",
                "formations": {},
                "play_patterns": {
                    "build_up": {},
                    "attacking": {},
                    "defensive": {},
                    "transition": {}
                },
                "possession_stats": {
                    "average_possession": 0,
                    "possession_by_zone": {},
                    "possession_effectiveness": {}
                },
                "pressure_stats": {
                    "high_press_frequency": 0,
                    "press_success_rate": 0,
                    "pressure_zones": {}
                },
                "metadata": {
                    "team": team_name,
                    "year": year,
                    "matches_analyzed": len(matches),
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Analizar formaciones
            total_matches = len(matches)
            for match in matches:
                # Formación utilizada
                formation = match.get("formation", "unknown")
                tactical_analysis["formations"][formation] = tactical_analysis["formations"].get(formation, 0) + 1

                # Patrones de juego
                self._analyze_match_patterns(match, tactical_analysis["play_patterns"])

                # Estadísticas de posesión
                possession = float(match.get("possession", 0))
                tactical_analysis["possession_stats"]["average_possession"] += possession

                # Zonas de posesión
                for zone, value in match.get("possession_by_zone", {}).items():
                    if zone not in tactical_analysis["possession_stats"]["possession_by_zone"]:
                        tactical_analysis["possession_stats"]["possession_by_zone"][zone] = 0
                    tactical_analysis["possession_stats"]["possession_by_zone"][zone] += float(value)

                # Estadísticas de presión
                press_actions = int(match.get("press_actions", 0))
                successful_presses = int(match.get("successful_presses", 0))
                tactical_analysis["pressure_stats"]["high_press_frequency"] += press_actions
                if press_actions > 0:
                    tactical_analysis["pressure_stats"]["press_success_rate"] += (successful_presses / press_actions)

                # Zonas de presión
                for zone, count in match.get("pressure_zones", {}).items():
                    if zone not in tactical_analysis["pressure_stats"]["pressure_zones"]:
                        tactical_analysis["pressure_stats"]["pressure_zones"][zone] = 0
                    tactical_analysis["pressure_stats"]["pressure_zones"][zone] += int(count)

            # Calcular promedios y porcentajes
            if total_matches > 0:
                # Formaciones
                for formation in tactical_analysis["formations"]:
                    tactical_analysis["formations"][formation] = {
                        "count": tactical_analysis["formations"][formation],
                        "percentage": (tactical_analysis["formations"][formation] / total_matches) * 100
                    }

                # Posesión
                tactical_analysis["possession_stats"]["average_possession"] /= total_matches
                for zone in tactical_analysis["possession_stats"]["possession_by_zone"]:
                    tactical_analysis["possession_stats"]["possession_by_zone"][zone] /= total_matches

                # Presión
                tactical_analysis["pressure_stats"]["high_press_frequency"] /= total_matches
                tactical_analysis["pressure_stats"]["press_success_rate"] /= total_matches
                for zone in tactical_analysis["pressure_stats"]["pressure_zones"]:
                    tactical_analysis["pressure_stats"]["pressure_zones"][zone] /= total_matches

            return tactical_analysis

        except Exception as e:
            print(f"Error analizando patrones tácticos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "team": team_name,
                    "year": year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def analyze_physical_load(self, team_name: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analiza la carga física y patrones de fatiga de un equipo.

        Args:
            team_name (str): Nombre del equipo
            year (int, optional): Año para el análisis

        Returns:
            Dict[str, Any]: Análisis de carga física incluyendo:
                - distance_stats: Estadísticas de distancia recorrida
                - intensity_stats: Estadísticas de intensidad de juego
                - fatigue_patterns: Patrones de fatiga identificados
                - performance_impact: Impacto en el rendimiento
        """
        try:
            # Obtener datos del equipo
            team_data = self.get_team_data(team_name, year)
            if team_data["status"] != "success":
                return {
                    "status": "error",
                    "message": "No se pudieron obtener datos del equipo"
                }

            matches = team_data.get("matches", [])
            if not matches:
                return {
                    "status": "error",
                    "message": "No se encontraron partidos para analizar"
                }

            physical_analysis = {
                "status": "success",
                "distance_stats": {
                    "total_distance": 0,
                    "high_intensity_distance": 0,
                    "sprint_distance": 0,
                    "distance_by_position": {}
                },
                "intensity_stats": {
                    "average_intensity": 0,
                    "high_intensity_actions": 0,
                    "sprints": 0,
                    "intensity_by_period": {}
                },
                "fatigue_patterns": {
                    "performance_decline": {},
                    "critical_periods": [],
                    "recovery_indicators": {}
                },
                "performance_impact": {
                    "goals_by_period": {},
                    "errors_by_fatigue": {},
                    "substitution_impact": {}
                },
                "metadata": {
                    "team": team_name,
                    "year": year,
                    "matches_analyzed": len(matches),
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Analizar cada partido
            total_matches = len(matches)
            for match in matches:
                # Estadísticas de distancia
                match_distance = float(match.get("total_distance", 0))
                high_intensity_distance = float(match.get("high_intensity_distance", 0))
                sprint_distance = float(match.get("sprint_distance", 0))

                physical_analysis["distance_stats"]["total_distance"] += match_distance
                physical_analysis["distance_stats"]["high_intensity_distance"] += high_intensity_distance
                physical_analysis["distance_stats"]["sprint_distance"] += sprint_distance

                # Distancia por posición
                for position, distance in match.get("distance_by_position", {}).items():
                    if position not in physical_analysis["distance_stats"]["distance_by_position"]:
                        physical_analysis["distance_stats"]["distance_by_position"][position] = 0
                    physical_analysis["distance_stats"]["distance_by_position"][position] += float(distance)

                # Intensidad de juego
                intensity = float(match.get("average_intensity", 0))
                high_intensity_actions = int(match.get("high_intensity_actions", 0))
                sprints = int(match.get("sprints", 0))

                physical_analysis["intensity_stats"]["average_intensity"] += intensity
                physical_analysis["intensity_stats"]["high_intensity_actions"] += high_intensity_actions
                physical_analysis["intensity_stats"]["sprints"] += sprints

                # Intensidad por periodo
                for period, intensity_value in match.get("intensity_by_period", {}).items():
                    if period not in physical_analysis["intensity_stats"]["intensity_by_period"]:
                        physical_analysis["intensity_stats"]["intensity_by_period"][period] = 0
                    physical_analysis["intensity_stats"]["intensity_by_period"][period] += float(intensity_value)

                # Patrones de fatiga
                self._analyze_fatigue_patterns(match, physical_analysis["fatigue_patterns"])

                # Impacto en el rendimiento
                self._analyze_performance_impact(match, physical_analysis["performance_impact"])

            # Calcular promedios
            if total_matches > 0:
                # Distancia
                physical_analysis["distance_stats"]["total_distance"] /= total_matches
                physical_analysis["distance_stats"]["high_intensity_distance"] /= total_matches
                physical_analysis["distance_stats"]["sprint_distance"] /= total_matches

                for position in physical_analysis["distance_stats"]["distance_by_position"]:
                    physical_analysis["distance_stats"]["distance_by_position"][position] /= total_matches

                # Intensidad
                physical_analysis["intensity_stats"]["average_intensity"] /= total_matches
                physical_analysis["intensity_stats"]["high_intensity_actions"] /= total_matches
                physical_analysis["intensity_stats"]["sprints"] /= total_matches

                for period in physical_analysis["intensity_stats"]["intensity_by_period"]:
                    physical_analysis["intensity_stats"]["intensity_by_period"][period] /= total_matches

            return physical_analysis

        except Exception as e:
            print(f"Error analizando carga física: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "team": team_name,
                    "year": year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def analyze_referee_stats(self, referee_name: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analiza las estadísticas y tendencias de un árbitro.

        Args:
            referee_name (str): Nombre del árbitro
            year (int, optional): Año para el análisis

        Returns:
            Dict[str, Any]: Análisis del árbitro incluyendo:
                - card_stats: Estadísticas de tarjetas
                - decision_trends: Tendencias en decisiones
                - team_history: Historial con equipos específicos
        """
        try:
            # Obtener datos de partidos arbitrados
            matches = self._get_referee_matches(referee_name, year)
            if not matches:
                return {
                    "status": "error",
                    "message": "No se encontraron partidos para el árbitro"
                }

            referee_analysis = {
                "status": "success",
                "card_stats": {
                    "yellow_cards": {
                        "total": 0,
                        "avg_per_match": 0,
                        "by_period": {},
                        "by_foul_type": {}
                    },
                    "red_cards": {
                        "total": 0,
                        "avg_per_match": 0,
                        "by_period": {},
                        "by_foul_type": {}
                    },
                    "second_yellows": {
                        "total": 0,
                        "avg_per_match": 0
                    }
                },
                "decision_trends": {
                    "fouls_called": {
                        "total": 0,
                        "avg_per_match": 0,
                        "by_zone": {}
                    },
                    "penalties": {
                        "total": 0,
                        "avg_per_match": 0,
                        "by_type": {}
                    },
                    "var_interventions": {
                        "total": 0,
                        "overturned": 0,
                        "by_type": {}
                    }
                },
                "team_history": {},
                "metadata": {
                    "referee": referee_name,
                    "year": year,
                    "matches_analyzed": len(matches),
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Analizar cada partido
            for match in matches:
                # Estadísticas de tarjetas
                self._analyze_card_stats(match, referee_analysis["card_stats"])
                
                # Tendencias en decisiones
                self._analyze_decision_trends(match, referee_analysis["decision_trends"])
                
                # Historial con equipos
                self._analyze_team_history(match, referee_analysis["team_history"])

            # Calcular promedios
            total_matches = len(matches)
            if total_matches > 0:
                # Tarjetas
                referee_analysis["card_stats"]["yellow_cards"]["avg_per_match"] = \
                    referee_analysis["card_stats"]["yellow_cards"]["total"] / total_matches
                referee_analysis["card_stats"]["red_cards"]["avg_per_match"] = \
                    referee_analysis["card_stats"]["red_cards"]["total"] / total_matches
                referee_analysis["card_stats"]["second_yellows"]["avg_per_match"] = \
                    referee_analysis["card_stats"]["second_yellows"]["total"] / total_matches

                # Decisiones
                referee_analysis["decision_trends"]["fouls_called"]["avg_per_match"] = \
                    referee_analysis["decision_trends"]["fouls_called"]["total"] / total_matches
                referee_analysis["decision_trends"]["penalties"]["avg_per_match"] = \
                    referee_analysis["decision_trends"]["penalties"]["total"] / total_matches

            return referee_analysis

        except Exception as e:
            print(f"Error analizando estadísticas del árbitro: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "referee": referee_name,
                    "year": year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def _get_referee_matches(self, referee_name: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene los partidos arbitrados por un árbitro.

        Args:
            referee_name (str): Nombre del árbitro
            year (int, optional): Año para filtrar los partidos

        Returns:
            List[Dict[str, Any]]: Lista de partidos arbitrados
        """
        try:
            # Construir URL para obtener datos del árbitro
            base_url = "https://understat.com/referee/"
            formatted_name = referee_name.lower().replace(" ", "_")
            url = f"{base_url}{formatted_name}"
            if year:
                url += f"/{year}"

            # Realizar petición
            response = self.session.get(url)
            response.raise_for_status()

            # Extraer datos de los partidos
            matches = []
            # Aquí iría la lógica para extraer los datos de la respuesta HTML
            # Ya que esto depende de la estructura específica de la página

            return matches

        except Exception as e:
            print(f"Error obteniendo partidos del árbitro: {str(e)}")
            return []

    def _analyze_card_stats(self, match_data: Dict[str, Any], card_stats: Dict[str, Dict]) -> None:
        """
        Analiza las estadísticas de tarjetas en un partido.

        Args:
            match_data: Datos del partido
            card_stats: Diccionario donde almacenar las estadísticas
        """
        # Tarjetas amarillas
        yellows = match_data.get("yellow_cards", [])
        card_stats["yellow_cards"]["total"] += len(yellows)

        for card in yellows:
            # Por periodo
            period = card.get("period", "unknown")
            if period not in card_stats["yellow_cards"]["by_period"]:
                card_stats["yellow_cards"]["by_period"][period] = 0
            card_stats["yellow_cards"]["by_period"][period] += 1

            # Por tipo de falta
            foul_type = card.get("foul_type", "unknown")
            if foul_type not in card_stats["yellow_cards"]["by_foul_type"]:
                card_stats["yellow_cards"]["by_foul_type"][foul_type] = 0
            card_stats["yellow_cards"]["by_foul_type"][foul_type] += 1

        # Tarjetas rojas
        reds = match_data.get("red_cards", [])
        card_stats["red_cards"]["total"] += len(reds)

        for card in reds:
            # Por periodo
            period = card.get("period", "unknown")
            if period not in card_stats["red_cards"]["by_period"]:
                card_stats["red_cards"]["by_period"][period] = 0
            card_stats["red_cards"]["by_period"][period] += 1

            # Por tipo de falta
            foul_type = card.get("foul_type", "unknown")
            if foul_type not in card_stats["red_cards"]["by_foul_type"]:
                card_stats["red_cards"]["by_foul_type"][foul_type] = 0
            card_stats["red_cards"]["by_foul_type"][foul_type] += 1

        # Segundas amarillas
        second_yellows = match_data.get("second_yellow_cards", [])
        card_stats["second_yellows"]["total"] += len(second_yellows)

    def _analyze_decision_trends(self, match_data: Dict[str, Any], decision_trends: Dict[str, Dict]) -> None:
        """
        Analiza las tendencias en las decisiones del árbitro.

        Args:
            match_data: Datos del partido
            decision_trends: Diccionario donde almacenar las tendencias
        """
        # Faltas pitadas
        fouls = match_data.get("fouls", [])
        decision_trends["fouls_called"]["total"] += len(fouls)

        for foul in fouls:
            zone = foul.get("zone", "unknown")
            if zone not in decision_trends["fouls_called"]["by_zone"]:
                decision_trends["fouls_called"]["by_zone"][zone] = 0
            decision_trends["fouls_called"]["by_zone"][zone] += 1

        # Penaltis
        penalties = match_data.get("penalties", [])
        decision_trends["penalties"]["total"] += len(penalties)

        for penalty in penalties:
            pen_type = penalty.get("type", "unknown")
            if pen_type not in decision_trends["penalties"]["by_type"]:
                decision_trends["penalties"]["by_type"][pen_type] = 0
            decision_trends["penalties"]["by_type"][pen_type] += 1

        # Intervenciones VAR
        var_interventions = match_data.get("var_interventions", [])
        decision_trends["var_interventions"]["total"] += len(var_interventions)

        for intervention in var_interventions:
            if intervention.get("overturned", False):
                decision_trends["var_interventions"]["overturned"] += 1

            int_type = intervention.get("type", "unknown")
            if int_type not in decision_trends["var_interventions"]["by_type"]:
                decision_trends["var_interventions"]["by_type"][int_type] = 0
            decision_trends["var_interventions"]["by_type"][int_type] += 1

    def _analyze_team_history(self, match_data: Dict[str, Any], team_history: Dict[str, Dict]) -> None:
        """
        Analiza el historial del árbitro con equipos específicos.

        Args:
            match_data: Datos del partido
            team_history: Diccionario donde almacenar el historial
        """
        home_team = match_data.get("home_team")
        away_team = match_data.get("away_team")

        for team in [home_team, away_team]:
            if team:
                team_name = team.get("name", "unknown")
                if team_name not in team_history:
                    team_history[team_name] = {
                        "matches": 0,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "fouls": 0,
                        "penalties_for": 0,
                        "penalties_against": 0
                    }

                stats = team_history[team_name]
                stats["matches"] += 1
                
                stats["yellow_cards"] += len(team.get("yellow_cards", []))
                stats["red_cards"] += len(team.get("red_cards", []))
                stats["fouls"] += len(team.get("fouls", []))
                stats["penalties_for"] += len(team.get("penalties_for", []))
                stats["penalties_against"] += len(team.get("penalties_against", []))

    def analyze_position_metrics(self, team_name: str, position: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analiza métricas específicas para una posición.

        Args:
            team_name (str): Nombre del equipo
            position (str): Posición a analizar (GK, DEF, MID, FWD)
            year (int, optional): Año para el análisis

        Returns:
            Dict[str, Any]: Análisis de métricas por posición
        """
        try:
            # Definir métricas por posición
            position_metrics = {
                "GK": {
                    "basic": [
                        "saves",
                        "clean_sheets",
                        "goals_conceded",
                        "save_percentage"
                    ],
                    "advanced": [
                        "psxG",  # Post-shot expected goals
                        "psxG_per_shot",
                        "passes_completed",
                        "pass_accuracy",
                        "goal_kicks_length",
                        "cross_stopping_percentage"
                    ]
                },
                "DEF": {
                    "basic": [
                        "tackles",
                        "interceptions",
                        "clearances",
                        "blocks"
                    ],
                    "advanced": [
                        "pressure_regains",
                        "aerial_duels_won",
                        "progressive_passes",
                        "passes_into_final_third",
                        "defensive_actions_per_90",
                        "true_tackle_win_rate"
                    ]
                },
                "MID": {
                    "basic": [
                        "passes_completed",
                        "pass_accuracy",
                        "key_passes",
                        "assists"
                    ],
                    "advanced": [
                        "progressive_carries",
                        "passes_into_box",
                        "through_balls",
                        "pressure_regains",
                        "xA",  # Expected assists
                        "deep_progressions"
                    ]
                },
                "FWD": {
                    "basic": [
                        "goals",
                        "shots",
                        "shots_on_target",
                        "conversion_rate"
                    ],
                    "advanced": [
                        "xG",  # Expected goals
                        "xG_per_shot",
                        "non_penalty_xG",
                        "goal_creating_actions",
                        "touches_in_box",
                        "progressive_receptions"
                    ]
                }
            }

            # Verificar posición válida
            if position not in position_metrics:
                return {
                    "status": "error",
                    "message": f"Posición no válida. Debe ser una de: {list(position_metrics.keys())}"
                }

            # Obtener datos del equipo
            team_data = self.get_team_data(team_name, year)
            if team_data["status"] != "success":
                return {
                    "status": "error",
                    "message": "No se pudieron obtener datos del equipo"
                }

            position_analysis = {
                "status": "success",
                "basic_metrics": {},
                "advanced_metrics": {},
                "performance_trends": {
                    "by_game": [],
                    "by_opponent_level": {},
                    "home_vs_away": {}
                },
                "comparative_analysis": {
                    "team_average": {},
                    "league_average": {},
                    "percentile_ranks": {}
                },
                "metadata": {
                    "team": team_name,
                    "position": position,
                    "year": year,
                    "metrics_analyzed": {
                        "basic": position_metrics[position]["basic"],
                        "advanced": position_metrics[position]["advanced"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Filtrar jugadores por posición
            position_players = [p for p in team_data.get("players", []) if p.get("position") == position]

            # Analizar métricas básicas
            basic_metrics = self._analyze_basic_metrics(
                position_players,
                position_metrics[position]["basic"]
            )
            if basic_metrics:
                position_analysis["basic_metrics"] = basic_metrics

            # Analizar métricas avanzadas
            advanced_metrics = self._analyze_advanced_metrics(
                position_players,
                position_metrics[position]["advanced"]
            )
            if advanced_metrics:
                position_analysis["advanced_metrics"] = advanced_metrics

            # Analizar tendencias de rendimiento
            trends = self._analyze_performance_trends(
                position_players,
                team_data.get("matches", [])
            )
            if trends:
                position_analysis["performance_trends"] = trends

            # Análisis comparativo
            comparative = self._analyze_comparative_metrics(
                position_players,
                position,
                team_name,
                year
            )
            if comparative:
                position_analysis["comparative_analysis"] = comparative

            return position_analysis

        except Exception as e:
            print(f"Error analizando métricas por posición: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "team": team_name,
                    "position": position,
                    "year": year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def get_detailed_game_situations(self, team_name: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas por situación de juego desde Understat.

        Args:
            team_name (str): Nombre del equipo.
            year (int, optional): Año de la temporada.

        Returns:
            dict: Diccionario con las estadísticas detalladas y estado de la operación.
                Incluye:
                - status: 'success' o 'error'
                - message: Mensaje descriptivo del resultado
                - situations: Diccionario con estadísticas por situación
                - metadata: Información adicional sobre la consulta
        """
        from datetime import datetime

        try:
            # Normalizar el nombre del equipo usando el mapeo si existe
            understat_team_mapping = {
                "manchester united": "Manchester_United",
                "manchester city": "Manchester_City",
                "tottenham": "Tottenham",
                "chelsea": "Chelsea",
                "arsenal": "Arsenal",
                "liverpool": "Liverpool",
                # Agregar más mapeos según sea necesario
            }
            formatted_name = understat_team_mapping.get(team_name.lower(), team_name.replace(" ", "_"))
            url = f"https://understat.com/team/{formatted_name}/{year}" if year else f"https://understat.com/team/{formatted_name}"
            
            print(f"Obteniendo estadísticas de situación de juego para {team_name} desde {url}")
            
            # Usar el método HTTP existente de football_api
            response = self.football_api.make_request(url, {}, use_api_key=False)
            
            if not response or not response.get("data"):
                return {
                    "status": "error",
                    "message": "No se pudo obtener respuesta de Understat",
                    "situations": {},
                    "metadata": {
                        "team": team_name,
                        "formatted_team": formatted_name,
                        "year": year,
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "error_type": "no_response"
                    }
                }

            # Parsear el HTML
            soup = BeautifulSoup(response["data"], 'html.parser')
            scripts = soup.find_all('script')

            for script in scripts:
                if 'var situationsData' in script.text:
                    json_data = script.text.split('= ', 1)[1].rsplit(';', 1)[0].strip("'")
                    situations = json.loads(json_data)
                    
                    # Procesar y estructurar los datos
                    processed_data = {
                        "status": "success",
                        "message": "Datos obtenidos correctamente",
                        "situations": {},
                        "metadata": {
                            "team": team_name,
                            "formatted_team": formatted_name,
                            "year": year,
                            "url": url,
                            "timestamp": datetime.now().isoformat(),
                            "data_points": 0,
                            "total_shots": 0,
                            "total_goals": 0,
                            "total_xG": 0.0,
                            "situation_types": []
                        }
                    }
                    
                    # Procesar cada situación
                    for situation_type, stats in situations.items():
                        if situation_type != "total":
                            shots = int(stats.get("shots", 0))
                            goals = int(stats.get("goals", 0))
                            xG = float(stats.get("xG", 0))
                            shots_on_target = int(stats.get("shots_on_target", 0))
                            
                            processed_stats = {
                                "shots": shots,
                                "goals": goals,
                                "xG": xG,
                                "shots_on_target": shots_on_target,
                                "conversion_rate": (goals / shots * 100) if shots > 0 else 0,
                                "xG_per_shot": xG / shots if shots > 0 else 0,
                                "shots_on_target_ratio": (shots_on_target / shots * 100) if shots > 0 else 0,
                                "goals_per_shot_on_target": (goals / shots_on_target) if shots_on_target > 0 else 0
                            }
                            
                            processed_data["situations"][situation_type] = processed_stats
                            processed_data["metadata"]["situation_types"].append(situation_type)
                            
                            # Actualizar metadatos
                            processed_data["metadata"]["data_points"] += 1
                            processed_data["metadata"]["total_shots"] += shots
                            processed_data["metadata"]["total_goals"] += goals
                            processed_data["metadata"]["total_xG"] += xG
                    
                    # Agregar totales
                    if "total" in situations:
                        total_stats = situations["total"]
                        total_shots = int(total_stats.get("shots", 0))
                        total_goals = int(total_stats.get("goals", 0))
                        total_xG = float(total_stats.get("xG", 0))
                        total_shots_on_target = int(total_stats.get("shots_on_target", 0))
                        
                        processed_data["situations"]["total"] = {
                            "shots": total_shots,
                            "goals": total_goals,
                            "xG": total_xG,
                            "shots_on_target": total_shots_on_target,
                            "conversion_rate": (total_goals / total_shots * 100) if total_shots > 0 else 0,
                            "xG_per_shot": total_xG / total_shots if total_shots > 0 else 0,
                            "shots_on_target_ratio": (total_shots_on_target / total_shots * 100) if total_shots > 0 else 0,
                            "goals_per_shot_on_target": (total_goals / total_shots_on_target) if total_shots_on_target > 0 else 0
                        }
                    
                    # Agregar estadísticas adicionales a los metadatos
                    if processed_data["metadata"]["total_shots"] > 0:
                        processed_data["metadata"]["overall_conversion_rate"] = processed_data["metadata"]["total_goals"] / processed_data["metadata"]["total_shots"] * 100
                        processed_data["metadata"]["overall_xG_per_shot"] = processed_data["metadata"]["total_xG"] / processed_data["metadata"]["total_shots"]
                    
                    return processed_data

            return {
                "status": "error",
                "message": "No se encontraron datos de situaciones de juego",
                "situations": {},
                "metadata": {
                    "team": team_name,
                    "formatted_team": formatted_name,
                    "year": year,
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "error_type": "no_data_found"
                }
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"Error al obtener estadísticas detalladas por situación de juego: {error_message}")
            return {
                "status": "error",
                "message": f"Error: {error_message}",
                "situations": {},
                "metadata": {
                    "team": team_name,
                    "year": year,
                    "url": url if 'url' in locals() else None,
                    "timestamp": datetime.now().isoformat(),
                    "error_type": "exception",
                    "error_details": error_message
                }
            }

    def analyze_historical_performance(self, team_name: str, years: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Analiza el rendimiento histórico del equipo.

        Args:
            team_name (str): Nombre del equipo
            years (List[int], optional): Lista de años a analizar

        Returns:
            Dict[str, Any]: Análisis histórico del rendimiento
        """
        try:
            if not years:
                current_year = datetime.now().year
                years = list(range(current_year - 5, current_year + 1))

            analysis = {
                "status": "success",
                "seasonal_performance": {},
                "trends": {
                    "attack": {},
                    "defense": {},
                    "overall": {}
                },
                "key_stats_evolution": {},
                "performance_indicators": {
                    "consistency": {},
                    "improvement_areas": [],
                    "strengths": []
                },
                "historical_rankings": [],
                "head_to_head": {},
                "metadata": {
                    "team": team_name,
                    "years_analyzed": years,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Analizar rendimiento por temporada
            for year in years:
                season_data = self.get_team_data(team_name, year)
                if season_data["status"] == "success":
                    analysis["seasonal_performance"][year] = self._analyze_season_performance(season_data)

            # Analizar tendencias
            trends = self._analyze_historical_trends(analysis["seasonal_performance"])
            if trends:
                analysis["trends"] = trends

            # Analizar evolución de estadísticas clave
            key_stats = self._analyze_key_stats_evolution(analysis["seasonal_performance"])
            if key_stats:
                analysis["key_stats_evolution"] = key_stats

            # Analizar indicadores de rendimiento
            indicators = self._analyze_performance_indicators(analysis["seasonal_performance"])
            if indicators:
                analysis["performance_indicators"] = indicators

            # Obtener rankings históricos
            rankings = self._get_historical_rankings(team_name, years)
            if rankings:
                analysis["historical_rankings"] = rankings

            # Analizar enfrentamientos directos
            h2h = self._analyze_head_to_head(team_name, years)
            if h2h:
                analysis["head_to_head"] = h2h

            return analysis

        except Exception as e:
            print(f"Error analizando rendimiento histórico: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "metadata": {
                    "team": team_name,
                    "years": years,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": str(e)
                }
            }

    def _analyze_season_performance(self, season_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el rendimiento de una temporada específica."""
        try:
            performance = {
                "matches": {
                    "total": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0
                },
                "goals": {
                    "scored": 0,
                    "conceded": 0,
                    "difference": 0
                },
                "expected_goals": {
                    "xG": 0,
                    "xGA": 0,
                    "xGD": 0
                },
                "points": 0,
                "ppg": 0,  # points per game
                "clean_sheets": 0,
                "failed_to_score": 0
            }

            matches = season_data.get("matches", [])
            for match in matches:
                # Actualizar estadísticas básicas
                if match.get("result") == "W":
                    performance["matches"]["wins"] += 1
                    performance["points"] += 3
                elif match.get("result") == "D":
                    performance["matches"]["draws"] += 1
                    performance["points"] += 1
                elif match.get("result") == "L":
                    performance["matches"]["losses"] += 1

                # Actualizar goles
                performance["goals"]["scored"] += match.get("goals_scored", 0)
                performance["goals"]["conceded"] += match.get("goals_conceded", 0)

                # Actualizar xG
                performance["expected_goals"]["xG"] += match.get("xG", 0)
                performance["expected_goals"]["xGA"] += match.get("xGA", 0)

                # Actualizar clean sheets y failed to score
                if match.get("goals_conceded", 0) == 0:
                    performance["clean_sheets"] += 1
                if match.get("goals_scored", 0) == 0:
                    performance["failed_to_score"] += 1

            # Calcular totales y promedios
            performance["matches"]["total"] = len(matches)
            if performance["matches"]["total"] > 0:
                performance["ppg"] = performance["points"] / performance["matches"]["total"]
                performance["goals"]["difference"] = (
                    performance["goals"]["scored"] - performance["goals"]["conceded"]
                )
                performance["expected_goals"]["xGD"] = (
                    performance["expected_goals"]["xG"] - performance["expected_goals"]["xGA"]
                )

            return performance

        except Exception as e:
            print(f"Error analizando rendimiento de temporada: {str(e)}")
            return {}

    def _analyze_historical_trends(self, seasonal_data: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza tendencias históricas."""
        try:
            trends = {
                "attack": {
                    "goals_trend": [],
                    "xG_trend": [],
                    "scoring_efficiency": []
                },
                "defense": {
                    "goals_against_trend": [],
                    "xGA_trend": [],
                    "defensive_efficiency": []
                },
                "overall": {
                    "points_trend": [],
                    "win_rate_trend": [],
                    "performance_trend": []
                }
            }

            # Ordenar temporadas cronológicamente
            seasons = sorted(seasonal_data.keys())
            
            for season in seasons:
                data = seasonal_data[season]
                matches_played = data["matches"]["total"]
                
                if matches_played > 0:
                    # Tendencias ofensivas
                    trends["attack"]["goals_trend"].append({
                        "season": season,
                        "value": data["goals"]["scored"] / matches_played
                    })
                    trends["attack"]["xG_trend"].append({
                        "season": season,
                        "value": data["expected_goals"]["xG"] / matches_played
                    })
                    
                    # Tendencias defensivas
                    trends["defense"]["goals_against_trend"].append({
                        "season": season,
                        "value": data["goals"]["conceded"] / matches_played
                    })
                    trends["defense"]["xGA_trend"].append({
                        "season": season,
                        "value": data["expected_goals"]["xGA"] / matches_played
                    })
                    
                    # Tendencias generales
                    trends["overall"]["points_trend"].append({
                        "season": season,
                        "value": data["ppg"]
                    })
                    trends["overall"]["win_rate_trend"].append({
                        "season": season,
                        "value": data["matches"]["wins"] / matches_played
                    })

            return trends

        except Exception as e:
            print(f"Error analizando tendencias históricas: {str(e)}")
            return {}

    def _analyze_key_stats_evolution(self, seasonal_data: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza la evolución de estadísticas clave."""
        try:
            evolution = {
                "offensive_efficiency": [],  # Goles marcados vs xG
                "defensive_efficiency": [],  # Goles concedidos vs xGA
                "points_efficiency": [],     # Puntos reales vs esperados
                "performance_metrics": {
                    "attack": {},
                    "defense": {},
                    "overall": {}
                }
            }

            seasons = sorted(seasonal_data.keys())
            for season in seasons:
                data = seasonal_data[season]
                matches_played = data["matches"]["total"]
                
                if matches_played > 0:
                    # Eficiencia ofensiva
                    goals = data["goals"]["scored"]
                    xG = data["expected_goals"]["xG"]
                    evolution["offensive_efficiency"].append({
                        "season": season,
                        "actual": goals / matches_played,
                        "expected": xG / matches_played,
                        "efficiency": (goals / xG if xG > 0 else 1) * 100
                    })

                    # Eficiencia defensiva
                    goals_against = data["goals"]["conceded"]
                    xGA = data["expected_goals"]["xGA"]
                    evolution["defensive_efficiency"].append({
                        "season": season,
                        "actual": goals_against / matches_played,
                        "expected": xGA / matches_played,
                        "efficiency": (xGA / goals_against if goals_against > 0 else 1) * 100
                    })

            return evolution

        except Exception as e:
            print(f"Error analizando evolución de estadísticas: {str(e)}")
            return {}

    def _analyze_performance_indicators(self, seasonal_data: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza indicadores de rendimiento."""
        try:
            indicators = {
                "consistency": {
                    "points": 0,
                    "goals": 0,
                    "results": 0
                },
                "improvement_areas": [],
                "strengths": []
            }

            # Calcular consistencia
            points_std = np.std([data["ppg"] for data in seasonal_data.values()])
            goals_std = np.std([data["goals"]["scored"] for data in seasonal_data.values()])
            
            indicators["consistency"]["points"] = 1 / (1 + points_std)
            indicators["consistency"]["goals"] = 1 / (1 + goals_std)

            # Identificar áreas de mejora y fortalezas
            recent_seasons = dict(sorted(seasonal_data.items())[-3:])
            avg_goals = np.mean([data["goals"]["scored"] for data in recent_seasons.values()])
            avg_conceded = np.mean([data["goals"]["conceded"] for data in recent_seasons.values()])
            avg_points = np.mean([data["points"] for data in recent_seasons.values()])

            if avg_goals < 1.5:
                indicators["improvement_areas"].append("scoring_efficiency")
            if avg_conceded > 1.5:
                indicators["improvement_areas"].append("defensive_stability")
            if avg_points / len(recent_seasons) < 1.7:
                indicators["improvement_areas"].append("points_consistency")

            if avg_goals > 2:
                indicators["strengths"].append("attacking_prowess")
            if avg_conceded < 1:
                indicators["strengths"].append("defensive_solidity")
            if avg_points / len(recent_seasons) > 2:
                indicators["strengths"].append("consistent_performance")

            return indicators

        except Exception as e:
            print(f"Error analizando indicadores de rendimiento: {str(e)}")
            return {}

    def _get_historical_rankings(self, team_name: str, years: List[int]) -> List[Dict[str, Any]]:
        """Obtiene rankings históricos del equipo."""
        try:
            rankings = []
            for year in years:
                # Aquí iría la lógica para obtener la posición del equipo en cada temporada
                pass
            return rankings

        except Exception as e:
            print(f"Error obteniendo rankings históricos: {str(e)}")
            return []

    def _analyze_head_to_head(self, team_name: str, years: List[int]) -> Dict[str, Any]:
        """Analiza enfrentamientos directos."""
        try:
            h2h = {
                "overall": {},
                "by_team": {},
                "by_competition": {},
                "trends": {}
            }
            # Aquí iría la lógica para analizar enfrentamientos directos
            return h2h

        except Exception as e:
            print(f"Error analizando enfrentamientos directos: {str(e)}")
            return {}

    def get_team_form(self, team_name: str, num_matches: int = 5) -> Dict[str, Any]:
        """
        Obtiene la forma reciente de un equipo (últimos N partidos).

        Args:
            team_name (str): Nombre del equipo.
            num_matches (int): Número de partidos recientes a considerar (por defecto 5).

        Returns:
            Dict[str, Any]: Análisis de la forma del equipo incluyendo:
                - status: Estado de la operación ('success' o 'error').
                - form_string: Cadena representando la forma (e.g., 'WWLDW').
                - stats: Resumen de victorias, empates, derrotas.
                - recent_matches: Lista de los últimos partidos considerados.
                - metadata: Información sobre la consulta.
        """
        try:
            # Obtener datos históricos recientes (necesitamos los partidos del año actual y quizás anterior)
            current_year = datetime.now().year
            team_data_current = self.get_team_data(team_name, current_year)
            team_data_previous = self.get_team_data(team_name, current_year - 1)
            
            all_matches = []
            if team_data_current.get("status") == "success":
                all_matches.extend(team_data_current.get("matches", []))
            if team_data_previous.get("status") == "success":
                all_matches.extend(team_data_previous.get("matches", []))

            if not all_matches:
                return {
                    "status": "error",
                    "message": "No se encontraron partidos recientes para el equipo.",
                    "metadata": {"team": team_name, "num_matches": num_matches}
                }

            # Ordenar partidos por fecha descendente
            all_matches.sort(key=lambda x: datetime.strptime(x.get('date', '1900-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S'), reverse=True)

            # Seleccionar los últimos N partidos
            recent_matches = all_matches[:num_matches]

            if not recent_matches:
                 return {
                    "status": "error",
                    "message": f"No se encontraron suficientes partidos ({len(all_matches)} disponibles) para analizar la forma.",
                    "metadata": {"team": team_name, "num_matches": num_matches}
                }

            form_string = ""
            stats = {"W": 0, "D": 0, "L": 0}
            
            # Construir la cadena de forma y contar estadísticas (del más reciente al más antiguo)
            for match in recent_matches:
                result = match.get("result")
                if result in stats:
                    form_string += result
                    stats[result] += 1
                else:
                    form_string += '?' # Marcar si falta el resultado

            return {
                "status": "success",
                "form_string": form_string, 
                "stats": stats,
                "recent_matches": recent_matches, # Devolver los partidos usados para el cálculo
                "metadata": {
                    "team": team_name,
                    "num_matches_requested": num_matches,
                    "num_matches_analyzed": len(recent_matches),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            error_message = str(e)
            print(f"Error obteniendo la forma del equipo: {error_message}")
            return {
                "status": "error",
                "message": f"Error: {error_message}",
                "metadata": {
                    "team": team_name,
                    "num_matches": num_matches,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": error_message
                }
            }
