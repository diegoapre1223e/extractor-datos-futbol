import re
from datetime import datetime
import time
from src.api.geocoding_api import GeocodingAPI  # Added import

class DataProcessor:
    """
    Clase para procesar y normalizar datos de fútbol
    """
    
    @staticmethod
    def parse_match_input(input_text):
        """
        Procesa el texto de entrada para extraer información del partido
        
        Args:
            input_text (str): Texto con formato "Equipo1 vs Equipo2 - YYYY-MM-DD"
                              o "Equipo1 vs Equipo2 YYYY-MM-DD"
            
        Returns:
            dict: Datos normalizados con equipos y fecha
        """
        # Verificar que hay texto de entrada
        if not input_text or not isinstance(input_text, str):
            print("Texto de entrada inválido")
            return None
            
        # Intentar varios patrones de formato
        patterns = [
            # Formato estándar con guion: "Equipo1 vs Equipo2 - YYYY-MM-DD"
            r"(.+)\s+vs\s+(.+)\s+-\s+(\d{4}-\d{2}-\d{2})",
            
            # Formato sin guion: "Equipo1 vs Equipo2 YYYY-MM-DD"
            r"(.+)\s+vs\s+(.+)\s+(\d{4}-\d{2}-\d{2})",
            
            # Solo equipos: "Equipo1 vs Equipo2"
            r"(.+)\s+vs\s+(.+)"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, input_text.strip())
            if match:
                if len(match.groups()) == 3:  # Con fecha
                    team1 = match.group(1).strip()
                    team2 = match.group(2).strip()
                    date = match.group(3).strip()
                    
                    print(f"Equipos identificados: {team1} vs {team2}, Fecha: {date}")
                    return {
                        "team1": team1,
                        "team2": team2,
                        "date": date
                    }
                elif len(match.groups()) == 2:  # Sin fecha
                    team1 = match.group(1).strip()
                    team2 = match.group(2).strip()
                    
                    print(f"Equipos identificados: {team1} vs {team2}, sin fecha especificada")
                    return {
                        "team1": team1,
                        "team2": team2,
                        "date": ""
                    }
                    
        # Si llegamos aquí, ningún patrón coincidió
        print(f"Formato incorrecto: {input_text}. Use: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
        return None
    
    @staticmethod
    def normalize_match_data(match_data):
        """
        Normaliza datos de un partido para tener una estructura consistente
        
        Args:
            match_data (dict): Datos del partido de la API
            
        Returns:
            dict: Datos del partido normalizados
        """
        if not match_data:
            return {
                "match_id": None,
                "date": None,
                "status": "No disponible",
                "team1": {"id": None, "name": "No disponible"},
                "team2": {"id": None, "name": "No disponible"},
                "score": "0-0",
                "league": {"id": None, "name": "No disponible"},
                "venue": {"id": None, "name": "No disponible"},
                "referee": {"id": None, "name": "No disponible"}
            }
        
        # Si es solo una lista, tomar el primer elemento
        if isinstance(match_data, list) and len(match_data) > 0:
            match_data = match_data[0]
        
        # Inicializar estructura normalizada
        normalized = {
            "match_id": None,
            "date": None,
            "status": "No disponible",
            "team1": {"id": None, "name": "No disponible"},
            "team2": {"id": None, "name": "No disponible"},
            "score": "0-0",
            "league": {"id": None, "name": "No disponible"},
            "venue": {"id": None, "name": "No disponible", "city": "No disponible", "country": "No disponible"},
            "referee": {"id": None, "name": "No disponible", "is_predicted": False}
        }
        
        # Extraer ID del partido
        fixture = match_data.get("fixture", {})
        normalized["match_id"] = fixture.get("id")
        
        # Fecha y hora
        date_str = fixture.get("date", "")
        if date_str:
            # Convertir formato de fecha a YYYY-MM-DD
            try:
                date_parts = date_str.split("T")[0] if "T" in date_str else date_str
                normalized["date"] = date_parts
            except:
                normalized["date"] = None
        
        # Estado del partido
        status = fixture.get("status", {})
        normalized["status"] = status.get("long", "No disponible")
        
        # Equipos y marcador
        teams = match_data.get("teams", {})
        goals = match_data.get("goals", {})
        
        # Equipo local
        home_team = teams.get("home", {})
        normalized["team1"]["id"] = home_team.get("id")
        normalized["team1"]["name"] = home_team.get("name", "No disponible")
        normalized["team1"]["winner"] = home_team.get("winner")
        
        # Equipo visitante
        away_team = teams.get("away", {})
        normalized["team2"]["id"] = away_team.get("id")
        normalized["team2"]["name"] = away_team.get("name", "No disponible")
        normalized["team2"]["winner"] = away_team.get("winner")
        
        # Marcador
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        if home_goals is not None and away_goals is not None:
            normalized["score"] = f"{home_goals}-{away_goals}"
        
        # Liga
        league = match_data.get("league", {})
        normalized["league"]["id"] = league.get("id")
        normalized["league"]["name"] = league.get("name", "No disponible")
        normalized["league"]["country"] = league.get("country", "No disponible")
        normalized["league"]["season"] = league.get("season")
        
        # Estadio
        venue = fixture.get("venue", {})
        normalized["venue"]["id"] = venue.get("id")
        normalized["venue"]["name"] = venue.get("name", "No disponible")
        normalized["venue"]["city"] = venue.get("city", "No disponible")
        
        # Árbitro
        referee_name = fixture.get("referee")
        if referee_name:
            normalized["referee"]["name"] = referee_name
            normalized["referee"]["is_predicted"] = False
        
        return normalized
    
    @staticmethod
    def process_team_statistics(stats_data):
        """
        Procesa estadísticas del equipo desde la respuesta de la API
        
        Args:
            stats_data: Datos de estadísticas del equipo
            
        Returns:
            dict: Estadísticas procesadas
        """
        # Verificar si hay datos
        if not stats_data or "response" not in stats_data or not stats_data["response"]:
            return {"error": "No hay información disponible para este equipo"}
        
        # Acceso directo a la respuesta
        stats = stats_data["response"]
        
        # Procesar datos de liga y equipo
        league_info = {
            "id": stats["league"]["id"] if "id" in stats["league"] else None,
            "nombre": stats["league"]["name"] if "name" in stats["league"] else None,
            "logo": stats["league"]["logo"] if "logo" in stats["league"] else None,
            "temporada": stats["league"]["season"] if "season" in stats["league"] else None
        } if "league" in stats else None
        
        team_info = {
            "id": stats["team"]["id"] if "id" in stats["team"] else None,
            "nombre": stats["team"]["name"] if "name" in stats["team"] else None,
            "logo": stats["team"]["logo"] if "logo" in stats["team"] else None
        } if "team" in stats else None
        
        # Procesar estadísticas clave
        fixtures = stats.get("fixtures", {})
        goals = stats.get("goals", {})
        penalty = stats.get("penalty", {})
        cards = stats.get("cards", {})
        
        # Construir objeto de estadísticas
        return {
            "liga": league_info,
            "equipo": team_info,
            "forma": stats.get("form", "No disponible"),
            "partidosJugados": fixtures.get("played", {}).get("total", 0) if fixtures else 0,
            "victorias": fixtures.get("wins", {}).get("total", 0) if fixtures else 0,
            "empates": fixtures.get("draws", {}).get("total", 0) if fixtures else 0,
            "derrotas": fixtures.get("loses", {}).get("total", 0) if fixtures else 0,
            "golesAnotados": {
                "total": goals.get("for", {}).get("total", {}).get("total", 0) if goals and "for" in goals else 0,
                "promedio": goals.get("for", {}).get("average", {}).get("total", "0") if goals and "for" in goals else "0"
            },
            "golesEncajados": {
                "total": goals.get("against", {}).get("total", {}).get("total", 0) if goals and "against" in goals else 0,
                "promedio": goals.get("against", {}).get("average", {}).get("total", "0") if goals and "against" in goals else "0"
            },
            "penaltis": {
                "anotados": penalty.get("scored", {}).get("total", 0) if penalty and "scored" in penalty else 0,
                "fallados": penalty.get("missed", {}).get("total", 0) if penalty and "missed" in penalty else 0,
                "total": penalty.get("total", 0) if penalty else 0
            }
        }
    
    @staticmethod
    def process_leagues_data(leagues_data, team_id):
        """
        Procesa datos de ligas en las que participa un equipo
        
        Args:
            leagues_data: Datos de ligas desde la API
            team_id: ID del equipo
            
        Returns:
            list: Lista de ligas procesadas
        """
        if not leagues_data or "response" not in leagues_data:
            return []
        
        leagues = []
        
        for league_data in leagues_data["response"]:
            league = league_data.get("league", {})
            country = league_data.get("country", {})
            season = league_data.get("seasons", [{}])[0] if league_data.get("seasons") else {}
            
            leagues.append({
                "id": league.get("id"),
                "nombre": league.get("name"),
                "tipo": league.get("type"),
                "pais": country.get("name"),
                "temporadaActual": season.get("current"),
                "equipo": team_id
            })
        
        return leagues
    
    @staticmethod
    def process_h2h_matches(h2h_data, team1_id, team2_id):
        """
        Procesa los datos de enfrentamientos head-to-head entre dos equipos.
        
        Args:
            h2h_data (dict): Datos de enfrentamientos directos de la API
            team1_id (int): ID del primer equipo
            team2_id (int): ID del segundo equipo
            
        Returns:
            dict: Estadísticas procesadas de los enfrentamientos
        """
        print(f"Procesando datos H2H entre equipos {team1_id} y {team2_id}")
        
        # Verificamos que tengamos datos válidos
        if not h2h_data or "response" not in h2h_data or not h2h_data["response"]:
            print("Sin datos H2H para procesar")
            return {
                "total_matches": 0,
                "team1_wins": 0,
                "team2_wins": 0,
                "draws": 0,
                "matches": [],
                "team1_goals": 0,
                "team2_goals": 0
            }
        
        # Filtramos solo partidos finalizados para estadísticas
        finished_matches = []
        for match in h2h_data["response"]:
            # Nos aseguramos que el partido tenga equipos
            if "teams" not in match or "home" not in match["teams"] or "away" not in match["teams"]:
                continue
                
            # Verificamos que el partido sea entre los equipos solicitados
            home_id = match["teams"]["home"]["id"]
            away_id = match["teams"]["away"]["id"]
            if not ((home_id == team1_id and away_id == team2_id) or 
                   (home_id == team2_id and away_id == team1_id)):
                continue
                
            # Solo partidos finalizados para estadísticas
            if match.get("fixture", {}).get("status", {}).get("short") in ["FT", "AET", "PEN"]:
                finished_matches.append(match)
                
        print(f"Se encontraron {len(finished_matches)} partidos finalizados entre los equipos")
        
        # Calculamos estadísticas
        team1_wins = 0
        team2_wins = 0
        draws = 0
        team1_goals = 0
        team2_goals = 0
        match_list = []
        
        for match in finished_matches:
            home_id = match["teams"]["home"]["id"]
            away_id = match["teams"]["away"]["id"]
            
            home_goals = match.get("goals", {}).get("home", 0) or 0
            away_goals = match.get("goals", {}).get("away", 0) or 0
            
            # Normalizamos los resultados para que team1 siempre sea el mismo
            if home_id == team1_id:
                team1_score = home_goals
                team2_score = away_goals
            else:
                team1_score = away_goals
                team2_score = home_goals
                
            team1_goals += team1_score
            team2_goals += team2_score
            
            # Determinamos ganador
            if team1_score > team2_score:
                team1_wins += 1
                result = "W"
            elif team2_score > team1_score:
                team2_wins += 1
                result = "L"
            else:
                draws += 1
                result = "D"
                
            # Creamos resumen del partido
            match_info = {
                "date": match.get("fixture", {}).get("date", ""),
                "league": match.get("league", {}).get("name", "Liga desconocida"),
                "team1_score": team1_score,
                "team2_score": team2_score,
                "result": result
            }
            match_list.append(match_info)
            
        # Ordenamos los partidos por fecha (más recientes primero)
        match_list.sort(key=lambda x: x["date"], reverse=True)
        
        # Resultado final
        h2h_stats = {
            "total_matches": len(finished_matches),
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws,
            "matches": match_list[:10],  # Solo los 10 más recientes
            "team1_goals": team1_goals,
            "team2_goals": team2_goals
        }
        
        print(f"Resumen H2H: {len(finished_matches)} partidos, {team1_wins} victorias equipo 1, " + 
              f"{team2_wins} victorias equipo 2, {draws} empates")
        
        return h2h_stats
    
    @staticmethod
    def get_day_abbreviation(date_str):
        """
        Obtiene la abreviación del día de la semana para una fecha dada
        
        Args:
            date_str: Fecha en formato YYYY-MM-DD
            
        Returns:
            str: Abreviación del día (LUN, MAR, etc.)
        """
        days = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return days[date.weekday()]
        except ValueError:
            return ""
            
    @staticmethod
    def process_standings(standings_data, team_id=None):
        """
        Procesa datos de la clasificación de una liga
        
        Args:
            standings_data: Datos de clasificación desde la API
            team_id: ID del equipo para filtrar (opcional)
            
        Returns:
            dict: Datos procesados de la clasificación
        """
        if not standings_data or "response" not in standings_data:
            return {"error": "No hay datos de clasificación disponibles"}
        
        result = []
        
        for league_data in standings_data["response"]:
            league = league_data.get("league", {})
            league_id = league.get("id")
            league_name = league.get("name")
            league_country = league.get("country")
            league_logo = league.get("logo")
            league_standings = league.get("standings", [])
            
            # Si hay múltiples grupos en la liga (por ejemplo, Champions League)
            for group in league_standings:
                group_teams = []
                
                for team_standing in group:
                    team = team_standing.get("team", {})
                    current_team_id = team.get("id")
                    
                    # Si se especificó un ID de equipo, filtrar solo ese equipo
                    if team_id and str(current_team_id) != str(team_id):
                        continue
                    
                    # Extraer estadísticas
                    stats = {
                        "posicion": team_standing.get("rank"),
                        "equipo": {
                            "id": current_team_id,
                            "nombre": team.get("name"),
                            "logo": team.get("logo")
                        },
                        "puntos": team_standing.get("points"),
                        "partidos": team_standing.get("all", {}).get("played"),
                        "victorias": team_standing.get("all", {}).get("win"),
                        "empates": team_standing.get("all", {}).get("draw"),
                        "derrotas": team_standing.get("all", {}).get("lose"),
                        "golesFavor": team_standing.get("all", {}).get("goals", {}).get("for"),
                        "golesContra": team_standing.get("all", {}).get("goals", {}).get("against"),
                        "diferenciaGoles": team_standing.get("goalsDiff"),
                        "forma": team_standing.get("form")
                    }
                    
                    group_teams.append(stats)
                
                if group_teams:
                    result.append({
                        "liga": {
                            "id": league_id,
                            "nombre": league_name,
                            "pais": league_country,
                            "logo": league_logo
                        },
                        "equipos": group_teams
                    })
        
        return result
        
    @staticmethod
    def process_next_matches(next_matches_data):
        """
        Procesa datos de los próximos partidos de un equipo
        
        Args:
            next_matches_data: Datos de los próximos partidos desde la API
            
        Returns:
            list: Lista de próximos partidos procesados
        """
        if not next_matches_data or "response" not in next_matches_data:
            return []
        
        result = []
        
        for match in next_matches_data["response"]:
            fixture = match.get("fixture", {})
            league = match.get("league", {})
            teams = match.get("teams", {})
            
            # Extraer datos relevantes
            match_info = {
                "fixtureId": fixture.get("id"),
                "fecha": fixture.get("date"),
                "estadio": fixture.get("venue", {}).get("name"),
                "ciudad": fixture.get("venue", {}).get("city"),
                "liga": {
                    "id": league.get("id"),
                    "nombre": league.get("name"),
                    "pais": league.get("country"),
                    "logo": league.get("logo"),
                    "ronda": league.get("round")
                },
                "equipoLocal": {
                    "id": teams.get("home", {}).get("id"),
                    "nombre": teams.get("home", {}).get("name"),
                    "logo": teams.get("home", {}).get("logo")
                },
                "equipoVisitante": {
                    "id": teams.get("away", {}).get("id"),
                    "nombre": teams.get("away", {}).get("name"),
                    "logo": teams.get("away", {}).get("logo")
                },
                "estado": fixture.get("status", {}).get("long")
            }
            
            result.append(match_info)
        
        return result
        
    @staticmethod
    def format_understat_data(understat_html):
        """
        Formatea datos de Understat extrayendo estadísticas avanzadas del HTML
        
        Args:
            understat_html: HTML de la página de Understat
            
        Returns:
            dict: Datos de Understat procesados
        """
        try:
            from bs4 import BeautifulSoup
            import json
            import re
            
            # Verificar que tenemos HTML para procesar
            if not understat_html or "data" not in understat_html:
                print("No hay datos HTML de Understat para procesar")
                return {
                    "status": "error",
                    "message": "No hay datos HTML para procesar"
                }
                
            html_content = understat_html.get("data", "")
            if not html_content or len(html_content) < 100:
                print(f"HTML de Understat demasiado corto o vacío: {len(html_content) if html_content else 0} caracteres")
                return {
                    "status": "error", 
                    "message": "HTML demasiado corto o vacío"
                }
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer datos incrustados en JavaScript
            # Understat almacena los datos en variables JavaScript como "playersData", "datesData", etc.
            scripts = soup.find_all("script")
            
            stats_data = {}
            players_found = False
            matches_found = False
            shots_found = False # Added flag for shots data
            situation_stats_found = False # Added flag for situation stats
            team_stats_found = False # Added flag for general team stats

            # Función auxiliar para limpiar caracteres de escape en JSON
            def clean_json_string(json_str):
                # Reemplazar secuencias de escape comunes
                cleaned = json_str.replace('\\"', '"')
                cleaned = cleaned.replace('\\\\', '\\')
                cleaned = cleaned.replace('\\/', '/')
                cleaned = cleaned.replace('\\n', '\n')
                cleaned = cleaned.replace('\\r', '\r')
                cleaned = cleaned.replace('\\t', '\t')
                
                # A veces hay que hacer múltiples pasadas para limpiar correctamente
                if '\\\\' in cleaned or '\\"' in cleaned:
                    return clean_json_string(cleaned)
                return cleaned
            
            # Buscar datos de jugadores (playersData)
            for script in scripts:
                script_content = script.string
                if not script_content:
                    continue

                # Players Data
                if "playersData" in script_content and not players_found:
                    # ... existing code to parse playersData ...
                    if players_found:
                         print(f"Datos de jugadores de Understat encontrados: {len(stats_data.get('players', []))} jugadores")

                # Matches Data
                if "datesData" in script_content and not matches_found:
                    # ... existing code to parse datesData ...
                    if matches_found:
                        print(f"Datos de partidos de Understat encontrados: {len(stats_data.get('matches', []))} partidos")

                # Shots Data (for situation analysis)
                if "shotsData" in script_content and not shots_found:
                    patterns = [
                        r'shotsData\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)',
                        r'shotsData\s*=\s*JSON\.parse\s*\(\s*"(.*?)"\s*\)',
                        r'shotsData\s*=\s*(.*?);'
                    ]
                    for pattern in patterns:
                        shots_match = re.search(pattern, script_content, re.DOTALL)
                        if shots_match:
                            shots_json_str = shots_match.group(1)
                            try:
                                cleaned_json = clean_json_string(shots_json_str)
                                stats_data["shots"] = json.loads(cleaned_json)
                                shots_found = True
                                print(f"Datos de remates (shotsData) de Understat encontrados: {len(stats_data['shots'])} remates")
                                break
                            except json.JSONDecodeError as e:
                                print(f"Error al decodificar JSON de remates con patrón {pattern}: {str(e)}")
                                continue

                # Team Situation Stats (often directly in JS object)
                if "rosterData" in script_content and not situation_stats_found: # rosterData often contains team-level situation stats
                    patterns = [
                        r'rosterData\s*=\s*(\{.*?\});' # Look for a JS object
                    ]
                    for pattern in patterns:
                        situation_match = re.search(pattern, script_content, re.DOTALL)
                        if situation_match:
                            situation_json_str = situation_match.group(1)
                            try:
                                # This might not be perfect JSON, needs careful parsing or regex
                                # For now, let's assume it's parseable or extract key parts later
                                # We might need more robust regex if json.loads fails
                                stats_data["situation_stats_raw"] = json.loads(situation_json_str) # Store raw for now
                                situation_stats_found = True
                                print(f"Datos de situación de equipo (rosterData) encontrados.")
                                break
                            except json.JSONDecodeError as e:
                                print(f"Error al decodificar JSON de situación (rosterData): {str(e)}")
                                # Could add regex fallback here if needed
                                continue

            # ... existing code to extract team_stats from tables ...
            team_stats = {}
            stats_table = soup.select_one('div.team-stats')
            if stats_table:
                # Extraer valores de estadísticas
                stat_items = stats_table.select('div.card-body div.row')
                for item in stat_items:
                    stat_name_elem = item.select_one('div:nth-child(1)')
                    stat_value_elem = item.select_one('div:nth-child(2)')
                    
                    if stat_name_elem and stat_value_elem:
                        stat_name = stat_name_elem.text.strip()
                        stat_value = stat_value_elem.text.strip()
                        team_stats[stat_name] = stat_value
                        
                print(f"Estadísticas del equipo encontradas: {len(team_stats)} valores")
            else:
                print("No se encontró el contenedor de estadísticas del equipo")
                # Intentar buscar otros elementos que contengan estadísticas
                stat_elements = soup.select('.statistic')
                if stat_elements:
                    for stat_elem in stat_elements:
                        stat_name = stat_elem.select_one('.statistic-name')
                        stat_value = stat_elem.select_one('.statistic-value')
                        if stat_name and stat_value:
                            team_stats[stat_name.text.strip()] = stat_value.text.strip()
                    print(f"Estadísticas alternativas encontradas: {len(team_stats)} valores")
            
            if team_stats:
                team_stats_found = True
                stats_data["team_stats_table"] = team_stats # Store stats found in table

            # --- Post-processing --- 

            # Process Situation Stats from shotsData if available
            processed_situation_stats = {
                'Open Play': {'shots': 0, 'goals': 0, 'xG': 0},
                'Set piece': {'shots': 0, 'goals': 0, 'xG': 0},
                'From corner': {'shots': 0, 'goals': 0, 'xG': 0},
                'Penalty': {'shots': 0, 'goals': 0, 'xG': 0}
            }
            if shots_found and stats_data.get("shots"):
                try:
                    # shotsData is usually a dictionary keyed by team side ('h' or 'a')
                    # We need to aggregate across both sides if scraping a match page,
                    # or just use the single key if it's a team page (might need adjustment)
                    all_shots = []
                    shots_dict = stats_data["shots"]
                    if isinstance(shots_dict, dict):
                        # Check if it's a team page (keys are player IDs) or match page ('h', 'a')
                        is_team_page = all(key.isdigit() for key in shots_dict.keys())
                        if is_team_page:
                            # Aggregate shots from all players on a team page
                            for player_shots in shots_dict.values():
                                if isinstance(player_shots, list):
                                     all_shots.extend(player_shots)
                        else:
                            # Aggregate from home and away on a match page
                            if 'h' in shots_dict: all_shots.extend(shots_dict['h'])
                            if 'a' in shots_dict: all_shots.extend(shots_dict['a'])
                    elif isinstance(shots_dict, list): # Handle case where it's already a list
                        all_shots = shots_dict

                    for shot in all_shots:
                        situation = shot.get('situation', 'Unknown')
                        result = shot.get('result', 'Unknown')
                        xg = float(shot.get('xG', 0))

                        # Normalize situation names
                        if situation == 'OpenPlay': situation = 'Open Play'
                        if situation == 'FromCorner': situation = 'From corner'
                        if situation == 'SetPiece': situation = 'Set piece'
                        if situation == 'DirectFreekick': situation = 'Set piece' # Group freekicks

                        if situation in processed_situation_stats:
                            processed_situation_stats[situation]['shots'] += 1
                            processed_situation_stats[situation]['xG'] += xg
                            if result == 'Goal':
                                processed_situation_stats[situation]['goals'] += 1
                        elif situation == 'Penalty': # Handle penalty separately if not in initial dict
                             if 'Penalty' not in processed_situation_stats:
                                 processed_situation_stats['Penalty'] = {'shots': 0, 'goals': 0, 'xG': 0}
                             processed_situation_stats['Penalty']['shots'] += 1
                             processed_situation_stats['Penalty']['xG'] += xg
                             if result == 'Goal':
                                 processed_situation_stats['Penalty']['goals'] += 1

                    # Round xG values
                    for sit in processed_situation_stats:
                        processed_situation_stats[sit]['xG'] = round(processed_situation_stats[sit]['xG'], 2)

                    stats_data["situation_stats"] = processed_situation_stats
                    situation_stats_found = True # Mark as found if processed
                    print("Estadísticas por situación procesadas desde shotsData.")
                except Exception as e:
                    print(f"Error procesando shotsData para estadísticas de situación: {e}")
                    import traceback
                    traceback.print_exc() # Print detailed traceback for debugging

            # Process Team Stats (including PPDA if found)
            processed_team_stats = {}
            if team_stats_found and stats_data.get("team_stats_table"):
                raw_team_stats = stats_data["team_stats_table"]
                # Normalize keys (e.g., 'Expected Goals' -> 'xG')
                key_mapping = {
                    'Expected Goals': 'xG',
                    'Expected Goals Against': 'xGA',
                    'Expected Points': 'xPTS',
                    'PPDA': 'ppda',
                    'Opposition PPDA': 'op_ppda', # Or similar key used by Understat
                    'Deep': 'deep_completions', # Passes completed within ~20 yards of goal
                    'Deep Allowed': 'op_deep_completions'
                }
                for key, value in raw_team_stats.items():
                    normalized_key = key_mapping.get(key, key.lower().replace(' ', '_'))
                    try:
                        # Try converting to float if possible
                        processed_team_stats[normalized_key] = float(value)
                    except (ValueError, TypeError):
                        processed_team_stats[normalized_key] = value
                stats_data["team_stats"] = processed_team_stats # Overwrite with processed
                print("Estadísticas generales del equipo procesadas (incluyendo PPDA si existe).")
            elif "team_stats" not in stats_data: # Ensure key exists even if empty
                 stats_data["team_stats"] = {}

            # Final check if any data was successfully processed
            if not players_found and not matches_found and not team_stats_found and not situation_stats_found:
                print("No se pudieron procesar datos clave de Understat (jugadores, partidos, stats equipo/situación)")
                # Return error only if ALL key data types are missing
                return {
                    "status": "error",
                    "message": "No se pudieron extraer datos clave de Understat",
                    "url": understat_html.get("url", ""),
                    "year": understat_html.get("year", "desconocido")
                }

            # Prepare final success response
            return {
                "status": "success",
                "team_stats": stats_data.get("team_stats", {}),
                "situation_stats": stats_data.get("situation_stats", {}), # Add situation stats
                "players": stats_data.get("players", []),
                "matches": stats_data.get("matches", []),
                "url": understat_html.get("url", ""),
                "year": understat_html.get("year", "desconocido")
            }

        except Exception as e:
            print(f"Error procesando datos de Understat: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error al procesar datos: {str(e)}",
                "url": understat_html.get("url", "") if isinstance(understat_html, dict) else ""
            }
        
    @staticmethod
    def calculate_travel_distance(venue1, venue2):
        """
        Calcula la distancia de viaje entre dos estadios
        
        Args:
            venue1: Diccionario con información del primer estadio {latitude, longitude}
            venue2: Diccionario con información del segundo estadio {latitude, longitude}
            
        Returns:
            float: Distancia en kilómetros
        """
        if not venue1 or not venue2:
            return None
            
        if "latitude" not in venue1 or "longitude" not in venue1:
            return None
            
        if "latitude" not in venue2 or "longitude" not in venue2:
            return None
        
        # Importar math localmente para no afectar rendimiento global
        import math
        
        # Extraer coordenadas
        lat1 = float(venue1["latitude"])
        lon1 = float(venue1["longitude"])
        lat2 = float(venue2["latitude"])
        lon2 = float(venue2["longitude"])
        
        # Radio de la Tierra en km
        earth_radius = 6371
        
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias
        d_lat = lat2_rad - lat1_rad
        d_lon = lon2_rad - lon1_rad
        
        # Fórmula de Haversine
        a = math.sin(d_lat/2) * math.sin(d_lat/2) + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(d_lon/2) * math.sin(d_lon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius * c
        
        return round(distance, 2)
    
    @staticmethod
    def optimize_match_data(match_data, travel_distance=None, future_matches=None):
        """
        Optimiza los datos del partido eliminando información redundante y dejando solo 
        información relevante para el modelo de predicciones, incluyendo datos derivados.
        
        Args:
            match_data (dict): Datos completos del partido
            travel_distance (float, optional): Distancia de viaje calculada para el equipo visitante.
            future_matches (dict, optional): Próximos partidos para ambos equipos ({'team1': ..., 'team2': ...}).
            
        Returns:
            dict: Datos optimizados sin redundancias
        """
        # Crear una copia para no modificar el original
        optimized = {}
        
        # Extraer información básica de equipos una sola vez
        team1_info = match_data.get("team1", {})
        team2_info = match_data.get("team2", {})
        team1_id = team1_info.get("id")
        team1_name = team1_info.get("name")
        team2_id = team2_info.get("id")
        team2_name = team2_info.get("name")
        league_info = match_data.get("league", {})
        league_id = league_info.get("id")
        league_name = league_info.get("name")
        league_country = league_info.get("country")
        league_round = league_info.get("round")
        
        # Crear la estructura básica optimizada con solo la información esencial
        optimized["match_info"] = {
            "date": match_data.get("date"),
            "team1_id": team1_id,
            "team1_name": team1_name,
            "team2_id": team2_id,
            "team2_name": team2_name,
            "league": {
                "id": league_id,
                "name": league_name,
                "country": league_country,
                "round": league_round
            },
            "fixture_id": match_data.get("match_id"), # Renamed from fixture_id for consistency
            "status": match_data.get("status", "No programado"),
            "timestamp": match_data.get("fixture", {}).get("timestamp") # Get timestamp if available
        }
        
        # Añadir información del estadio si está disponible
        venue_data = match_data.get("venue")
        if venue_data:
            optimized["venue"] = {
                "id": venue_data.get("id"),
                "name": venue_data.get("name"),
                "city": venue_data.get("city")
            }

        # Añadir distancia de viaje si está disponible
        if travel_distance is not None:
            optimized["travel_distance_km"] = round(travel_distance, 2)
            
        # Optimizar y derivar datos de H2H
        h2h_raw = match_data.get("h2h")
        if h2h_raw:
            total_matches = h2h_raw.get("total_matches", 0)
            team1_wins = h2h_raw.get("team1_wins", 0)
            team2_wins = h2h_raw.get("team2_wins", 0)
            draws = h2h_raw.get("draws", 0)
            team1_goals = h2h_raw.get("team1_goals", 0)
            team2_goals = h2h_raw.get("team2_goals", 0)
            
            h2h_stats = {
                "total_matches": total_matches,
                "team1_wins": team1_wins,
                "team2_wins": team2_wins,
                "draws": draws,
                "team1_win_pct": round(team1_wins / total_matches * 100, 1) if total_matches > 0 else 0,
                "team2_win_pct": round(team2_wins / total_matches * 100, 1) if total_matches > 0 else 0,
                "draw_pct": round(draws / total_matches * 100, 1) if total_matches > 0 else 0,
                "avg_goals_team1": round(team1_goals / total_matches, 2) if total_matches > 0 else 0,
                "avg_goals_team2": round(team2_goals / total_matches, 2) if total_matches > 0 else 0,
                "avg_total_goals": round((team1_goals + team2_goals) / total_matches, 2) if total_matches > 0 else 0,
                "recent_matches": h2h_raw.get("matches", []) # Keep recent matches list
            }
            optimized["h2h"] = h2h_stats

        # Añadir información del árbitro con estadísticas derivadas
        referee_info_raw = match_data.get("referee_info")
        if referee_info_raw and referee_info_raw.get("status") == "success":
            referee_name = referee_info_raw.get("name")
            is_predicted = match_data.get("referee", {}).get("is_predicted", False)
            
            optimized_referee = {
                "name": referee_name,
                "is_predicted": is_predicted,
                "nationality": referee_info_raw.get("nationality", "Desconocida"),
                "age": referee_info_raw.get("age", "Desconocida"),
                "stats_by_competition": {}
            }
            
            matches_info = referee_info_raw.get("matches_info", {})
            if matches_info:
                # Prioritize stats from the current match's league
                current_league_stats = matches_info.get(league_name)
                if current_league_stats:
                    matches = int(current_league_stats.get("matches", 0))
                    yellows = int(current_league_stats.get("yellow_cards", 0))
                    reds = int(current_league_stats.get("red_cards", 0))
                    penalties = int(current_league_stats.get("penalties", 0))
                    optimized_referee["stats_current_league"] = {
                        "matches": matches,
                        "yellow_cards": yellows,
                        "red_cards": reds,
                        "penalties": penalties,
                        "yellow_per_match": round(yellows / matches, 2) if matches > 0 else 0,
                        "red_per_match": round(reds / matches, 2) if matches > 0 else 0,
                        "penalties_per_match": round(penalties / matches, 2) if matches > 0 else 0
                    }
                
                # Include stats for other major leagues if available
                relevant_competitions = ["Premier League", "Champions League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
                for competition, stats in matches_info.items():
                    if competition in relevant_competitions and competition != league_name:
                        matches = int(stats.get("matches", 0))
                        if matches > 0:
                            optimized_referee["stats_by_competition"][competition] = {
                                "matches": matches,
                                "yellow_per_match": round(int(stats.get("yellow_cards", 0)) / matches, 2),
                                "red_per_match": round(int(stats.get("red_cards", 0)) / matches, 2),
                                "penalties_per_match": round(int(stats.get("penalties", 0)) / matches, 2)
                            }
            
            # Añadir estadísticas del árbitro con los equipos específicos
            team_stats_raw = referee_info_raw.get("team_stats", {})
            if team_stats_raw:
                optimized_referee["stats_with_teams"] = {}
                for team_name_key, team_id_val, team_label in [(team1_name, team1_id, "team1"), (team2_name, team2_id, "team2")]:
                    stats = team_stats_raw.get(team_name_key, {})
                    matches = stats.get("matches", 0)
                    if matches > 0:
                         optimized_referee["stats_with_teams"][team_label] = {
                            "matches": matches,
                            "wins": stats.get("wins", 0),
                            "draws": stats.get("draws", 0),
                            "losses": stats.get("losses", 0),
                            "yellow_cards": stats.get("yellow_cards", 0),
                            "red_cards": stats.get("red_cards", 0),
                            "win_pct": round(stats.get("wins", 0) / matches * 100, 1),
                            "yellow_per_match": round(stats.get("yellow_cards", 0) / matches, 2),
                            "red_per_match": round(stats.get("red_cards", 0) / matches, 2)
                        }

            optimized["referee"] = optimized_referee
        
        # Añadir información del clima si está disponible
        weather_raw = match_data.get("weather")
        if weather_raw:
            optimized["weather"] = {
                "temperature_celsius": weather_raw.get("temperature"),
                "description": weather_raw.get("description"),
                "humidity_percent": weather_raw.get("humidity"),
                "wind_speed_kph": weather_raw.get("wind", {}).get("speed")
            }

        # Añadir clasificación de la liga si está disponible
        standings_raw = match_data.get("standings")
        if standings_raw and "response" in standings_raw:
            optimized["standings"] = {}
            for league_data in standings_raw["response"]:
                if league_data.get("league", {}).get("id") == league_id:
                    league_standings = league_data.get("league", {}).get("standings", [])
                    for group in league_standings:
                        for team_standing in group:
                            current_team_id = team_standing.get("team", {}).get("id")
                            if current_team_id == team1_id:
                                optimized["standings"]["team1"] = {
                                    "rank": team_standing.get("rank"),
                                    "points": team_standing.get("points"),
                                    "form": team_standing.get("form"),
                                    "goals_diff": team_standing.get("goalsDiff")
                                }
                            elif current_team_id == team2_id:
                                optimized["standings"]["team2"] = {
                                    "rank": team_standing.get("rank"),
                                    "points": team_standing.get("points"),
                                    "form": team_standing.get("form"),
                                    "goals_diff": team_standing.get("goalsDiff")
                                }
                    break # Found the relevant league

        # Procesar datos de los equipos (estadísticas, understat, lesiones)
        for team_key, team_id_val, team_name_val in [("team1", team1_id, team1_name), ("team2", team2_id, team2_name)]:
            team_data_raw = match_data.get(team_key, {})
            optimized_team = {
                "id": team_id_val,
                "name": team_name_val,
                "stats": {},
                "understat_summary": {},
                "injuries_suspensions": []
            }

            # Procesar estadísticas generales del equipo (si existen)
            stats_raw = team_data_raw.get("statistics", {}).get("response")
            if stats_raw:
                fixtures = stats_raw.get("fixtures", {})
                goals = stats_raw.get("goals", {})
                played = fixtures.get("played", {}).get("total", 0)
                wins = fixtures.get("wins", {}).get("total", 0)
                draws = fixtures.get("draws", {}).get("total", 0)
                loses = fixtures.get("loses", {}).get("total", 0)
                goals_for = goals.get("for", {}).get("total", {}).get("total", 0)
                goals_against = goals.get("against", {}).get("total", {}).get("total", 0)
                
                optimized_team["stats"] = {
                    "form": stats_raw.get("form"),
                    "played": played,
                    "wins": wins,
                    "draws": draws,
                    "loses": loses,
                    "win_pct": round(wins / played * 100, 1) if played > 0 else 0,
                    "draw_pct": round(draws / played * 100, 1) if played > 0 else 0,
                    "loss_pct": round(loses / played * 100, 1) if played > 0 else 0,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "goal_diff": goals_for - goals_against,
                    "avg_goals_for": round(goals_for / played, 2) if played > 0 else 0,
                    "avg_goals_against": round(goals_against / played, 2) if played > 0 else 0,
                    # Include goal distribution if available
                    "goals_for_timing": goals.get("for", {}).get("minute"),
                    "goals_against_timing": goals.get("against", {}).get("minute"),
                    # Include card distribution if available
                    "cards_timing": stats_raw.get("cards", {}).get("yellow", {}) # Assuming yellow card timing is representative
                }

            # Procesar datos de Understat (si existen)
            understat_raw = team_data_raw.get("understat")
            if understat_raw and understat_raw.get("status") == "success":
                players = understat_raw.get("players", [])
                team_stats = understat_raw.get("team_stats", {})
                
                # Calculate derived player stats (e.g., per 90)
                processed_players = []
                for player in players:
                    try:
                        minutes = float(player.get("minutes", 0) or 0)
                        if minutes > 0:
                            games = float(player.get("games", 0) or 0)
                            goals = float(player.get("goals", 0) or 0)
                            assists = float(player.get("assists", 0) or 0)
                            shots = float(player.get("shots", 0) or 0)
                            key_passes = float(player.get("key_passes", 0) or 0)
                            xg = float(player.get("xG", 0) or 0)
                            xa = float(player.get("xA", 0) or 0)
                            npg = float(player.get("npg", 0) or 0)
                            npxg = float(player.get("npxG", 0) or 0)
                            
                            player["minutes_per_game"] = round(minutes / games, 1) if games > 0 else 0
                            player["goals_per90"] = round((goals / minutes) * 90, 2)
                            player["assists_per90"] = round((assists / minutes) * 90, 2)
                            player["shots_per90"] = round((shots / minutes) * 90, 2)
                            player["key_passes_per90"] = round((key_passes / minutes) * 90, 2)
                            player["xG_per90"] = round((xg / minutes) * 90, 2)
                            player["xA_per90"] = round((xa / minutes) * 90, 2)
                            player["npg_per90"] = round((npg / minutes) * 90, 2)
                            player["npxG_per90"] = round((npxg / minutes) * 90, 2)
                            player["G_minus_xG"] = round(goals - xg, 2)
                            player["A_minus_xA"] = round(assists - xa, 2)
                            player["G+A"] = goals + assists
                            player["xG+xA"] = round(xg + xa, 2)
                            player["G+A_per90"] = round(player["goals_per90"] + player["assists_per90"], 2)
                            player["xG+xA_per90"] = round(player["xG_per90"] + player["xA_per90"], 2)
                        processed_players.append(player)
                    except (ValueError, TypeError, ZeroDivisionError) as e:
                        # Skip player if data is invalid for calculations
                        print(f"Skipping player {player.get('name')} due to calculation error: {e}")
                        continue
                
                # Sort players by likely starter status and then minutes
                processed_players.sort(key=lambda p: (not p.get('likely_starter', False), -float(p.get('minutes', 0) or 0)))
                
                # Create Understat summary
                optimized_team["understat_summary"] = {
                    "team_xG": team_stats.get("xG"),
                    "team_xGA": team_stats.get("xGA"),
                    "team_xPTS": team_stats.get("xPTS"),
                    "team_ppda": team_stats.get("ppda"), # Pass per defensive action
                    "team_op_ppda": team_stats.get("op_ppda"), # Opponent PPDA
                    "deep_completions": team_stats.get("deep_completions"), # Added
                    "op_deep_completions": team_stats.get("op_deep_completions"), # Added
                    "situation_stats": understat_raw.get("situation_stats", {}), # Added situation stats
                    "top_players_by_xg_xa_per90": sorted(
                        [p for p in processed_players if p.get("minutes", 0) > 90], # Min 90 mins played
                        key=lambda p: p.get("xG+xA_per90", 0), 
                        reverse=True
                    )[:5], # Top 5 players by xG+xA per 90
                    "likely_starters": [p for p in processed_players if p.get('likely_starter', False)]
                }

            # Procesar lesiones y sanciones (combinando API y Transfermarkt si existe)
            injuries_api = team_data_raw.get("injuries", [])
            injuries_tm = team_data_raw.get("injuries_transfermarkt", [])
            combined_unavailable = {}

            if injuries_api:
                for injury in injuries_api:
                    # Validate injury data type
                    if not isinstance(injury, dict):
                        print(f"Invalid injury data format: {injury}")
                        continue

                    player = injury.get("player", {})
                    player_id = player.get("id")
                    player_name = player.get("name")
                    if player_id and player_name:
                         combined_unavailable[player_name] = {
                            "id": player_id,
                            "name": player_name,
                            "type": injury.get("type"),
                            "reason": injury.get("reason"),
                            "source": "API"
                        }
            
            if injuries_tm:
                 for injury in injuries_tm:
                    # Validate injury data type
                    if not isinstance(injury, dict):
                        print(f"Invalid injury data format: {injury}")
                        continue

                    player_name = injury.get("player_name")
                    if player_name and player_name not in combined_unavailable: # Add if not already present from API
                        combined_unavailable[player_name] = {
                            "id": None, # Transfermarkt doesn't provide ID easily
                            "name": player_name,
                            "type": injury.get("injury_type"),
                            "reason": injury.get("injury_type"),
                            "return_date": injury.get("return_date"),
                            "source": "Transfermarkt"
                        }
            
            optimized_team["injuries_suspensions"] = list(combined_unavailable.values())

            # Initialize market_value_data to avoid UnboundLocalError
            market_value_data = market_value_data if 'market_value_data' in locals() else {}

            # Add fallback mechanism for Transfermarkt and market value APIs
            if not market_value_data:
                print("Market value data not available. Using default values.")
                market_value_data = {"default": True}

            optimized[team_key] = optimized_team

        # Procesar resumen de próximos partidos
        if future_matches:
            optimized["future_matches_summary"] = {}
            for team_key, fm_data in future_matches.items():
                team_label = "team1" if team_key == "team1" else "team2"
                if fm_data and fm_data.get("response"):
                    summary = []
                    today = datetime.now().date()
                    for match in fm_data["response"][:3]: # Max 3 future matches
                        try:
                            fixture = match.get("fixture", {})
                            match_date_str = fixture.get("date", "").split("T")[0]
                            match_date = datetime.strptime(match_date_str, "%Y-%m-%d").date()
                            days_until = (match_date - today).days
                            
                            teams = match.get("teams", {})
                            home_team = teams.get("home", {}).get("name")
                            away_team = teams.get("away", {}).get("name")
                            opponent = away_team if teams.get("home", {}).get("id") == optimized[team_label]["id"] else home_team
                            location = "Home" if teams.get("home", {}).get("id") == optimized[team_label]["id"] else "Away"
                            
                            summary.append({
                                "opponent": opponent,
                                "location": location,
                                "league": match.get("league", {}).get("name"),
                                "date": match_date_str,
                                "days_until": days_until
                            })
                        except Exception as e:
                            print(f"Error processing future match: {e}")
                            continue
                    optimized["future_matches_summary"][team_label] = summary

        # Limpiar valores nulos/vacíos al final
        optimized = DataProcessor.remove_null_values(optimized)
        
        return optimized
    
    @staticmethod
    def optimize_team_data(team_data, team_id, team_name):
        """
        Optimize team data for storage, removing duplicated information, HTML, etc.,
        and calculating derived stats.
        
        Args:
            team_data: Team data to optimize
            team_id: ID of the team
            team_name: Name of the team
            
        Returns:
            dict: Optimized team data
        """
        # Verificar que tenemos datos válidos
        if not team_data or not isinstance(team_data, dict):
            return {}
            
        optimized = {
            "id": team_id,
            "name": team_name,
            "last_update": time.time(),
            "leagues": {},
            "players": {},
            "injuries_suspensions": [],
            "venue": None,
            "last_10_matches": [],
            "next_5_matches": []
        }
        
        # Procesar datos por liga (pueden estar en "leagues" o en "stats")
        leagues_data = {}
        if "leagues" in team_data and isinstance(team_data["leagues"], dict):
            leagues_data = team_data["leagues"]
        elif "stats" in team_data and isinstance(team_data["stats"], dict):
            leagues_data = team_data["stats"]
        elif "statistics" in team_data and isinstance(team_data["statistics"], dict): # Handle case where stats are nested
             if "response" in team_data["statistics"]:
                 # If stats are wrapped in 'response', use that directly
                 leagues_data = {team_data["statistics"]["response"].get("league",{}).get("id"): team_data["statistics"]["response"]}
             else:
                 # Assume it's a dict keyed by league ID
                 leagues_data = team_data["statistics"]

        # Procesar cada liga
        current_year = datetime.now().year
        current_season = str(current_year - 1 if datetime.now().month < 7 else current_year)

        for league_id_key, league_data in leagues_data.items():
            if not league_data or not isinstance(league_data, dict):
                 continue
            league_info = league_data.get("league", {}) or league_data.get("liga", {}) # Handle different naming
            season = league_info.get("season") or league_info.get("temporada")
            league_id = league_info.get("id")

            # Ensure we have a valid league ID
            if not league_id:
                league_id = league_id_key # Use the key if ID is missing in data

            # Filter for the current season (adjust logic if needed)
            if str(season) != current_season:
                continue
                
            league_optimized = {}
            
            # Copiar datos básicos de la liga
            league_optimized["league"] = {
                "id": league_id,
                "name": league_info.get("name") or league_info.get("nombre"),
                "country": league_info.get("country"),
                "season": season
            }
            
            # Copiar forma del equipo
            if "form" in league_data:
                league_optimized["form"] = league_data["form"]
                
            # Procesar y derivar estadísticas de partidos
            fixtures = league_data.get("fixtures", {})
            if fixtures:
                played = fixtures.get("played", {}).get("total", 0)
                wins = fixtures.get("wins", {}).get("total", 0)
                draws = fixtures.get("draws", {}).get("total", 0)
                loses = fixtures.get("loses", {}).get("total", 0)
                league_optimized["fixtures"] = {
                    "played": played,
                    "wins": wins,
                    "draws": draws,
                    "loses": loses,
                    "win_pct": round(wins / played * 100, 1) if played > 0 else 0,
                    "draw_pct": round(draws / played * 100, 1) if played > 0 else 0,
                    "loss_pct": round(loses / played * 100, 1) if played > 0 else 0,
                    "played_home": fixtures.get("played", {}).get("home", 0),
                    "wins_home": fixtures.get("wins", {}).get("home", 0),
                    "draws_home": fixtures.get("draws", {}).get("home", 0),
                    "loses_home": fixtures.get("loses", {}).get("home", 0),
                    "played_away": fixtures.get("played", {}).get("away", 0),
                    "wins_away": fixtures.get("wins", {}).get("away", 0),
                    "draws_away": fixtures.get("draws", {}).get("away", 0),
                    "loses_away": fixtures.get("loses", {}).get("away", 0),
                }
                
            # Procesar y derivar estadísticas de goles
            goals = league_data.get("goals", {})
            if goals:
                goals_for = goals.get("for", {}).get("total", {}).get("total", 0)
                goals_against = goals.get("against", {}).get("total", {}).get("total", 0)
                played = league_optimized.get("fixtures", {}).get("played", 0)
                league_optimized["goals"] = {
                    "for_total": goals_for,
                    "against_total": goals_against,
                    "goal_diff": goals_for - goals_against,
                    "avg_for": round(goals_for / played, 2) if played > 0 else 0,
                    "avg_against": round(goals_against / played, 2) if played > 0 else 0,
                    "for_home": goals.get("for", {}).get("total", {}).get("home", 0),
                    "against_home": goals.get("against", {}).get("total", {}).get("home", 0),
                    "for_away": goals.get("for", {}).get("total", {}).get("away", 0),
                    "against_away": goals.get("against", {}).get("total", {}).get("away", 0),
                    "for_timing": goals.get("for", {}).get("minute"),
                    "against_timing": goals.get("against", {}).get("minute")
                }
                
            # Copiar estadísticas de faltas, tarjetas, penaltis, formaciones
            for key in ["fouls", "cards", "penalty", "lineups"]:
                if key in league_data and league_data[key]:
                    league_optimized[key] = league_data[key]
            
            # Añadir al resultado
            optimized["leagues"][str(league_id)] = league_optimized # Use string key for JSON compatibility
        
        # Procesar partidos recientes (last_matches)
        recent_matches_raw = team_data.get("last_matches") or team_data.get("recent_matches")
        if recent_matches_raw:
            optimized["last_10_matches"] = DataProcessor.optimize_matches_data(recent_matches_raw)
            
        # Procesar próximos partidos (upcoming_matches)
        upcoming_matches_raw = team_data.get("upcoming_matches") or team_data.get("next_matches")
        if upcoming_matches_raw:
            optimized["next_5_matches"] = DataProcessor.optimize_matches_data(upcoming_matches_raw)
            
        # Añadir el estadio principal del equipo
        venue_raw = team_data.get("venue") or team_data.get("last_venue") or team_data.get("team", {}).get("venue")
        if venue_raw:
            optimized["venue"] = {
                "id": venue_raw.get("id"),
                "name": venue_raw.get("name"),
                "address": venue_raw.get("address"),
                "city": venue_raw.get("city"),
                "capacity": venue_raw.get("capacity"),
                "surface": venue_raw.get("surface")
            }
            # Get coordinates if not already present
            if "latitude" not in venue_raw or "longitude" not in venue_raw:
                 coords = GeocodingAPI().get_coordinates_from_venue(venue_raw.get("name"), venue_raw.get("city"))
                 if coords:
                     optimized["venue"].update(coords)
            else:
                 optimized["venue"]["latitude"] = venue_raw.get("latitude")
                 optimized["venue"]["longitude"] = venue_raw.get("longitude")
                
        # Añadir información de lesiones y suspensiones (combinada)
        injuries_api = team_data.get("injuries") or team_data.get("injuries_suspensions")
        injuries_tm = team_data.get("injuries_transfermarkt")
        combined_unavailable = {}

        if injuries_api and isinstance(injuries_api, list):
            for injury in injuries_api:
                # Validate injury data type
                if not isinstance(injury, dict):
                    print(f"Invalid injury data format: {injury}")
                    continue

                player = injury.get("player", {})
                player_id = player.get("id")
                player_name = player.get("name")
                if player_id and player_name:
                     combined_unavailable[player_name] = {
                        "id": player_id,
                        "name": player_name,
                        "type": injury.get("type"),
                        "reason": injury.get("reason") or injury.get("type"),
                        "source": "API"
                    }
        
        if injuries_tm and isinstance(injuries_tm, list):
             for injury in injuries_tm:
                # Validate injury data type
                if not isinstance(injury, dict):
                    print(f"Invalid injury data format: {injury}")
                    continue

                player_name = injury.get("player_name")
                if player_name and player_name not in combined_unavailable:
                    combined_unavailable[player_name] = {
                        "id": None,
                        "name": player_name,
                        "type": injury.get("injury_type"),
                        "reason": injury.get("injury_type"),
                        "return_date": injury.get("return_date"),
                        "source": "Transfermarkt"
                    }
        optimized["injuries_suspensions"] = list(combined_unavailable.values())
                
        # Procesar datos de Understat si están disponibles
        understat_data = team_data.get("understat")
        if understat_data and understat_data.get("status") == "success":
            # Add overall team stats from Understat (xG, xGA, PPDA, etc.)
            team_stats_understat = understat_data.get("team_stats", {})
            if team_stats_understat:
                optimized["understat_team_stats"] = {
                    "xG": team_stats_understat.get("xG"),
                    "xGA": team_stats_understat.get("xGA"),
                    "xPTS": team_stats_understat.get("xPTS"),
                    "ppda": team_stats_understat.get("ppda"),
                    "op_ppda": team_stats_understat.get("op_ppda"),
                    "deep_completions": team_stats_understat.get("deep_completions"),
                    "op_deep_completions": team_stats_understat.get("op_deep_completions")
                }
            # Add situation stats from Understat
            situation_stats_understat = understat_data.get("situation_stats", {})
            if situation_stats_understat:
                optimized["understat_situation_stats"] = situation_stats_understat

            players_raw = understat_data.get("players", [])
            if players_raw:
                processed_players = {}
                for player in players_raw:
                    try:
                        player_id = player.get("id")
                        if not player_id:
                            continue # Skip players without ID

                        minutes = float(player.get("minutes", 0) or 0)
                        games = float(player.get("games", 0) or 0)
                        goals = float(player.get("goals", 0) or 0)
                        assists = float(player.get("assists", 0) or 0)
                        shots = float(player.get("shots", 0) or 0)
                        key_passes = float(player.get("key_passes", 0) or 0)
                        xg = float(player.get("xG", 0) or 0)
                        xa = float(player.get("xA", 0) or 0)
                        npg = float(player.get("npg", 0) or 0)
                        npxg = float(player.get("npxG", 0) or 0)
                        
                        player_stats = {
                            "id": player_id,
                            "name": player.get("name") or player.get("player_name"),
                            "position": player.get("position"),
                            "games": games,
                            "minutes": minutes,
                            "goals": goals,
                            "assists": assists,
                            "shots": shots,
                            "key_passes": key_passes,
                            "xG": xg,
                            "xA": xa,
                            "npg": npg,
                            "npxG": npxg,
                            "xGChain": float(player.get("xGChain", 0) or 0),
                            "xGBuildup": float(player.get("xGBuildup", 0) or 0),
                            "likely_starter": False # Default to false, update later
                        }

                        # Calculate per 90 stats if minutes > 0
                        if minutes > 0:
                            player_stats["minutes_per_game"] = round(minutes / games, 1) if games > 0 else 0
                            player_stats["goals_per90"] = round((goals / minutes) * 90, 2)
                            player_stats["assists_per90"] = round((assists / minutes) * 90, 2)
                            player_stats["shots_per90"] = round((shots / minutes) * 90, 2)
                            player_stats["key_passes_per90"] = round((key_passes / minutes) * 90, 2)
                            player_stats["xG_per90"] = round((xg / minutes) * 90, 2)
                            player_stats["xA_per90"] = round((xa / minutes) * 90, 2)
                            player_stats["npg_per90"] = round((npg / minutes) * 90, 2)
                            player_stats["npxG_per90"] = round((npxg / minutes) * 90, 2)
                            player_stats["G_minus_xG"] = round(goals - xg, 2)
                            player_stats["A_minus_xA"] = round(assists - xa, 2)
                            player_stats["G+A"] = goals + assists
                            player_stats["xG+xA"] = round(xg + xa, 2)
                            player_stats["G+A_per90"] = round(player_stats["goals_per90"] + player_stats["assists_per90"], 2)
                            player_stats["xG+xA_per90"] = round(player_stats["xG_per90"] + player_stats["xA_per90"], 2)
                        
                        processed_players[str(player_id)] = player_stats
                    except (ValueError, TypeError, ZeroDivisionError) as e:
                        print(f"Skipping player {player.get('name')} due to calculation error: {e}")
                        continue
                
                # Determine likely starters (top 11 by minutes played)
                sorted_players = sorted(processed_players.values(), key=lambda p: p.get("minutes", 0), reverse=True)
                for i, player in sorted_players:
                    if i < 11:
                        processed_players[str(player["id"])]["likely_starter"] = True
                
                optimized["players"] = processed_players
        
        # Limpiar valores nulos/vacíos al final
        optimized = DataProcessor.remove_null_values(optimized)
        
        return optimized
    
    @staticmethod
    def optimize_matches_data(matches):
        """
        Optimiza los datos de partidos eliminando información redundante
        
        Args:
            matches: Lista de partidos a optimizar
            
        Returns:
            list: Lista de partidos optimizada
        """
        if not matches or not isinstance(matches, list):
            return []
            
        optimized_matches = []
        
        for match in matches:
            if not isinstance(match, dict):
                continue
                
            # Crear estructura básica optimizada del partido
            optimized_match = {
                "id": match.get("fixture", {}).get("id"),
                "date": match.get("fixture", {}).get("date"),
                "timestamp": match.get("fixture", {}).get("timestamp"),
                "status": {
                    "short": match.get("fixture", {}).get("status", {}).get("short"),
                    "long": match.get("fixture", {}).get("status", {}).get("long")
                },
                "teams": {
                    "home": {
                        "id": match.get("teams", {}).get("home", {}).get("id"),
                        "name": match.get("teams", {}).get("home", {}).get("name"),
                        "winner": match.get("teams", {}).get("home", {}).get("winner")
                    },
                    "away": {
                        "id": match.get("teams", {}).get("away", {}).get("id"),
                        "name": match.get("teams", {}).get("away", {}).get("name"),
                        "winner": match.get("teams", {}).get("away", {}).get("winner")
                    }
                }
            }
            
            # Añadir resultado si hay goles
            if "goals" in match and match["goals"]:
                optimized_match["goals"] = match["goals"]
                
            # Añadir estadísticas si hay
            if "statistics" in match and match["statistics"]:
                statistics = []
                
                # Procesar cada conjunto de estadísticas (generalmente uno por equipo)
                for team_stats in match["statistics"]:
                    if not isinstance(team_stats, dict) or "statistics" not in team_stats:
                        continue
                        
                    team_id = team_stats.get("team", {}).get("id")
                    team_name = team_stats.get("team", {}).get("name")
                    
                    # Estructura para las estadísticas de un equipo
                    optimized_stats = {
                        "team": {
                            "id": team_id,
                            "name": team_name
                        },
                        "statistics": {}
                    }
                    
                    # Procesar cada estadística individual
                    for stat in team_stats["statistics"]:
                        if isinstance(stat, dict) and "type" in stat and "value" in stat:
                            # Solo incluir estadísticas con valores no nulos
                            if stat["value"] is not None and stat["value"] != "" and stat["value"] != 0:
                                optimized_stats["statistics"][stat["type"]] = stat["value"]
                    
                    # Solo añadir si hay estadísticas
                    if optimized_stats["statistics"]:
                        statistics.append(optimized_stats)
                
                # Solo añadir si hay estadísticas
                if statistics:
                    optimized_match["statistics"] = statistics
                    
            # Añadir información de la liga
            if "league" in match and match["league"]:
                optimized_match["league"] = {
                    "id": match.get("league", {}).get("id"),
                    "name": match.get("league", {}).get("name"),
                    "country": match.get("league", {}).get("country"),
                    "season": match.get("league", {}).get("season"),
                    "round": match.get("league", {}).get("round")
                }
                
            # Añadir información del estadio
            if "fixture" in match and "venue" in match["fixture"] and match["fixture"]["venue"]:
                optimized_match["venue"] = {
                    "id": match.get("fixture", {}).get("venue", {}).get("id"),
                    "name": match.get("fixture", {}).get("venue", {}).get("name"),
                    "city": match.get("fixture", {}).get("venue", {}).get("city")
                }
                
            # Añadir información del árbitro
            if "fixture" in match and "referee" in match["fixture"] and match["fixture"]["referee"]:
                optimized_match["referee"] = match["fixture"]["referee"]
                
            # Eliminar campos nulos
            optimized_match = DataProcessor.remove_null_values(optimized_match)
            
            optimized_matches.append(optimized_match)
            
        return optimized_matches
        
    @staticmethod
    def remove_null_values(data):
        """
        Elimina valores nulos, vacíos o URLs de un objeto
        
        Args:
            data: Datos a limpiar
            
        Returns:
            Datos limpios sin valores nulos o URLs
        """
        if isinstance(data, dict):
            # Eliminar campos de URL y nulos
            url_fields = ['logo', 'flag', 'image', 'source_url', 'image_url']
            result = {}
            for key, value in data.items():
                # No eliminar la URL de Understat ya que es útil para referencias
                if key == 'url' and 'understat.com' in str(value):
                    result[key] = value
                # Eliminar otros campos URL o valores nulos
                elif key not in url_fields and value is not None and value != "" and value != [] and value != {}:
                    result[key] = DataProcessor.remove_null_values(value)
            return result
        elif isinstance(data, list):
            return [DataProcessor.remove_null_values(element) for element in data if element is not None]
        else:
            return data

    def process_team_leagues(self, leagues_data):
        """Procesa las ligas en las que participa un equipo."""
        if not leagues_data:
            return []

        processed_leagues = []
        for league in leagues_data:
            processed_leagues.append({
                "id": league.get("league", {}).get("id"),
                "name": league.get("league", {}).get("name"),
                "country": league.get("country", {}).get("name"),
                "season": league.get("seasons", [{}])[0].get("year")
            })

        return processed_leagues