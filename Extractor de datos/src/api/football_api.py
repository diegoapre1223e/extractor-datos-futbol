import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

# Cargar variables de entorno
load_dotenv()

class FootballAPI:
    """
    Clase que encapsula las llamadas a la API de Football
    """
    
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
    
    def __init__(self):
        """Inicializa la clase con la clave API desde variables de entorno"""
        self.headers = {
            "X-RapidAPI-Key": os.getenv("FOOTBALL_API_KEY"),
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        self.timezone = "Europe/Madrid"  # Timezone por defecto
    
    def _make_request(self, url, params, use_api_key=True):
        """
        Realiza una solicitud HTTP a la API y maneja errores
        
        Args:
            url (str): URL del endpoint
            params (dict): Parámetros de la solicitud
            use_api_key (bool): Indica si se debe usar la clave API
            
        Returns:
            dict: Respuesta JSON o None en caso de error
        """
        try:
            # Si no se requiere clave API, usar headers vacíos
            headers = self.headers if use_api_key else {}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            # Si la URL no es de la API, devolver un diccionario con los datos
            if not url.startswith(self.BASE_URL):
                return {"data": response.text, "url": url}
            
            data = response.json()
            
            # Verificar si hay errores en la respuesta
            if "errors" in data and data["errors"]:
                errors = ", ".join(str(err) for err in data["errors"])
                print(f"Error en la API: {errors}")
                return None
            
            return data
        except Exception as e:
            print(f"Error en la solicitud a {url}: {str(e)}")
            return None
    
    def get_fixtures(self, team1_id=None, team2_id=None, league_id=None, 
                     season=None, date=None, last=None, next=None, team=None):
        """
        Busca partidos por equipos, ligas o fechas
        
        Args:
            team1_id (int, optional): ID del primer equipo
            team2_id (int, optional): ID del segundo equipo
            league_id (int, optional): ID de la liga
            season (str, optional): Temporada (ej: "2023")
            date (str, optional): Fecha específica (YYYY-MM-DD)
            last (int, optional): Número de últimos partidos
            next (int, optional): Número de próximos partidos
            team (int, optional): ID del equipo (compatibilidad para parámetros recientes)
            
        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"{self.BASE_URL}/fixtures"
        params = {"timezone": self.timezone}
        
        # Si se proporciona team, usarlo como team1_id para compatibilidad
        if team is not None:
            team1_id = team
        
        # Construir parámetros según lo que se ha proporcionado
        if team1_id and team2_id:
            params["h2h"] = f"{team1_id}-{team2_id}"
        elif team1_id:
            params["team"] = team1_id
        
        if league_id:
            params["league"] = league_id
            
        if season:
            params["season"] = season
            
        if date:
            params["date"] = date
            
        if last:
            params["last"] = last
            
        if next:
            params["next"] = next
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            # Si la respuesta es un error, intentamos imprimir detalles
            if response.status_code != 200:
                print(f"Error en la API: {response.status_code}")
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        print(f"Errores de API: {error_data['errors']}")
                except:
                    print("No se pudo obtener detalles del error")
                return None
            
            data = response.json()
            
            # Mostrar información sobre número de partidos encontrados
            if "response" in data:
                print(f"Se encontraron {len(data['response'])} partidos para el equipo {team1_id}")
                
            return data
        except Exception as e:
            print(f"Error al obtener fixtures: {str(e)}")
            return None
    
    def search_team(self, team_name):
        """
        Busca un equipo por nombre
        
        Args:
            team_name: Nombre del equipo a buscar
            
        Returns:
            dict: Información del equipo encontrado o None
        """
        # Primero intentamos búsqueda exacta
        endpoint = f"{self.BASE_URL}/teams"
        params = {"name": team_name}
        
        print(f"Buscando equipo: {team_name}")
        print(f"URL: {endpoint} con parámetros: {params}")
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            data = response.json()
            
            # Depuración completa
            print(f"Código de respuesta: {response.status_code}")
            if "errors" in data:
                print(f"Errores de API: {data['errors']}")
                
            # Verificar respuesta
            if "response" in data and data["response"]:
                print(f"Equipo encontrado con búsqueda exacta: {team_name}")
                return data["response"][0]
                
            # Si la búsqueda exacta falla, intentamos búsqueda parcial
            print(f"No se encontró coincidencia exacta para: {team_name}. Intentando búsqueda parcial...")
            params = {"search": team_name}
            response = requests.get(endpoint, headers=self.headers, params=params)
            data = response.json()
            
            if "response" in data and data["response"]:
                print(f"Equipo encontrado con búsqueda parcial: {data['response'][0]['team']['name']}")
                return data["response"][0]
            else:
                print(f"No se encontró el equipo: {team_name}")
                return None
                
        except Exception as e:
            print(f"Error al buscar equipo {team_name}: {e}")
            return None
    
    def get_head_to_head(self, team1_id, team2_id, date=None, season=None, last=50):
        """
        Obtiene el historial de enfrentamientos entre dos equipos
        
        Args:
            team1_id: ID del primer equipo
            team2_id: ID del segundo equipo
            date: Fecha opcional para filtrar (formato YYYY-MM-DD)
            season: Temporada opcional para filtrar
            last: Número de partidos a obtener
            
        Returns:
            dict: Datos del historial de enfrentamientos procesados
        """
        print(f"Obteniendo historial de enfrentamientos entre equipos {team1_id} y {team2_id}")
        
        # Construir parámetros de la solicitud
        params = {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last
        }
        
        # Añadir parámetros opcionales si están presentes
        if date:
            params["date"] = date
        if season:
            params["season"] = season
        
        # Realizar la solicitud a la API
        response = self.make_request(f"{self.BASE_URL}/fixtures/headtohead", params)
        
        # Procesar la respuesta
        if response and "response" in response and response["response"]:
            fixtures = response["response"]
            print(f"Se encontraron {len(fixtures)} partidos h2h")
            
            # Procesar partidos para extraer estadísticas
            processed_data = self._process_h2h_data(fixtures, team1_id, team2_id)
            return processed_data
            
        return None
        
    def _process_h2h_data(self, fixtures, team1_id, team2_id):
        """
        Procesa los datos de partidos H2H para extraer estadísticas
        
        Args:
            fixtures: Lista de partidos H2H
            team1_id: ID del primer equipo
            team2_id: ID del segundo equipo
            
        Returns:
            dict: Estadísticas procesadas
        """
        print(f"Procesando datos H2H entre equipos {team1_id} y {team2_id}")
        
        # Inicializar estadísticas
        stats = {
            "total": 0,
            "team1_wins": 0,
            "team2_wins": 0,
            "draws": 0,
            "total_goals": 0,
            "team1_goals": 0,
            "team2_goals": 0,
            "recent_matches": []
        }
        
        # Filtrar solo partidos finalizados
        finished_matches = [match for match in fixtures if match.get("fixture", {}).get("status", {}).get("short") == "FT"]
        
        if finished_matches:
            print(f"Se encontraron {len(finished_matches)} partidos finalizados entre los equipos")
            stats["total"] = len(finished_matches)
            
            # Procesar cada partido
            for match in finished_matches:
                fixture = match.get("fixture", {})
                teams = match.get("teams", {})
                goals = match.get("goals", {})
                
                # Determinar qué equipo es local y visitante
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                home_id = home_team.get("id")
                away_id = away_team.get("id")
                
                # Extraer goles
                home_goals = goals.get("home", 0) or 0
                away_goals = goals.get("away", 0) or 0
                
                # Acumular goles
                stats["total_goals"] += (home_goals + away_goals)
                
                # Determinar ganador
                if home_id == team1_id:
                    stats["team1_goals"] += home_goals
                    stats["team2_goals"] += away_goals
                    
                    if home_goals > away_goals:
                        stats["team1_wins"] += 1
                        result = "W"
                    elif home_goals < away_goals:
                        stats["team2_wins"] += 1
                        result = "L"
                    else:
                        stats["draws"] += 1
                        result = "D"
                else:
                    stats["team1_goals"] += away_goals
                    stats["team2_goals"] += home_goals
                    
                    if home_goals < away_goals:
                        stats["team1_wins"] += 1
                        result = "W"
                    elif home_goals > away_goals:
                        stats["team2_wins"] += 1
                        result = "L"
                    else:
                        stats["draws"] += 1
                        result = "D"
                
                # Formatear fecha
                date = fixture.get("date", "").split("T")[0] if "T" in fixture.get("date", "") else fixture.get("date", "")
                
                # Formatear liga
                league = match.get("league", {}).get("name", "")
                
                # Crear resumen del partido para historial reciente
                match_summary = {
                    "date": date,
                    "league": league,
                    "score": f"{home_goals}-{away_goals}",
                    "result": result,
                    "result_text": self._get_result_text(result, home_team.get("name"), away_team.get("name"), home_goals, away_goals)
                }
                
                stats["recent_matches"].append(match_summary)
            
            # Ordenar partidos del más reciente al más antiguo
            stats["recent_matches"] = sorted(stats["recent_matches"], key=lambda x: x["date"], reverse=True)
            
            print(f"Resumen H2H: {stats['total']} partidos, {stats['team1_wins']} victorias equipo 1, {stats['team2_wins']} victorias equipo 2, {stats['draws']} empates")
        
        return stats

    def _get_result_text(self, result, home_team, away_team, home_goals, away_goals):
        """
        Genera un texto descriptivo del resultado de un partido
        
        Args:
            result: Resultado del partido (W, L, D) desde la perspectiva del equipo 1
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            home_goals: Goles del equipo local
            away_goals: Goles del equipo visitante
            
        Returns:
            str: Texto descriptivo del resultado
        """
        if result == "W":
            if home_goals > away_goals:
                return f"Victoria para {home_team} ({home_goals}-{away_goals})"
            else:
                return f"Victoria para {away_team} ({away_goals}-{home_goals})"
        elif result == "L":
            if home_goals > away_goals:
                return f"Victoria para {home_team} ({home_goals}-{away_goals})"
            else:
                return f"Victoria para {away_team} ({away_goals}-{home_goals})"
        else:  # Empate
            return f"Empate {home_goals}-{away_goals} entre {home_team} y {away_team}"
    
    def get_team_statistics(self, team_id, league_id, season="2024"):
        """
        Obtiene estadísticas de un equipo en una liga específica
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            season: Temporada (por defecto 2024)
            
        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"{self.BASE_URL}/teams/statistics"
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()
    
    def get_leagues_for_team(self, team_id):
        """
        Obtiene las ligas en las que participa un equipo
        
        Args:
            team_id: ID del equipo
            
        Returns:
            dict: Ligas en las que participa el equipo
        """
        endpoint = f"{self.BASE_URL}/leagues"
        params = {"team": team_id}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener ligas para el equipo {team_id}: {e}")
            return {"response": []}
    
    def get_standings(self, league_id, team_id=None, season="2024"):
        """
        Obtiene la clasificación de una liga
        
        Args:
            league_id: ID de la liga
            team_id: ID del equipo (opcional)
            season: Temporada (por defecto 2024)
            
        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"{self.BASE_URL}/standings"
        params = {
            "league": league_id,
            "season": season
        }
        
        if team_id:
            params["team"] = team_id
            
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()
    
    def get_next_matches(self, team_id, num_matches=5, season="2024"):
        """
        Obtiene los próximos N partidos de un equipo
        
        Args:
            team_id: ID del equipo
            num_matches: Número de partidos a obtener (por defecto 5)
            season: Temporada (por defecto 2024)
            
        Returns:
            dict: Respuesta de la API
        """
        return self.get_fixtures(team1_id=team_id, next=num_matches, season=season)
    
    def get_last_matches(self, team_id, num_matches=10, season="2024"):
        """
        Obtiene los últimos N partidos de un equipo
        
        Args:
            team_id: ID del equipo
            num_matches: Número de partidos a obtener (por defecto 10)
            season: Temporada (por defecto 2024)
            
        Returns:
            dict: Respuesta de la API
        """
        return self.get_fixtures(team1_id=team_id, last=num_matches, season=season)
    
    def get_understat_url(self, team_name, year=None):
        """
        Genera URL para consultar datos de Understat de un equipo
        
        Args:
            team_name: Nombre del equipo
            year: Año de la temporada (opcional)
            
        Returns:
            str: URL de Understat para el equipo
        """
        # Formatear el nombre del equipo para URL
        formatted_name = team_name.replace(" ", "_")
        
        # Generar URL base
        url = f"https://understat.com/team/{formatted_name}"
        
        # Añadir año si está especificado
        if year:
            url = f"{url}/{year}"
        
        return url
    
    def get_alternative_understat_urls(self, team_name, year=None):
        """
        Genera múltiples formatos de URL para Understat para aumentar la probabilidad de éxito
        
        Args:
            team_name: Nombre del equipo
            year: Año de la temporada (opcional)
            
        Returns:
            list: Lista de URLs alternativas para Understat
        """
        urls = []
        
        # Variaciones de nombres de equipos para casos comunes
        name_variations = [
            team_name,
            team_name.replace(" ", "_"),
            team_name.replace(" ", ""),
            team_name.replace(" ", "-"),
        ]
        
        # Variaciones específicas para equipos conocidos
        team_mappings = {
            "manchester united": ["Manchester_United", "Man_United", "ManUtd"],
            "manchester city": ["Manchester_City", "Man_City", "ManCity"],
            "real madrid": ["Real_Madrid"],
            "barcelona": ["Barcelona", "FC_Barcelona"],
            "atletico madrid": ["Atletico_Madrid", "Atletico"],
            "liverpool": ["Liverpool", "Liverpool_FC"],
            "arsenal": ["Arsenal", "Arsenal_FC"],
            "chelsea": ["Chelsea", "Chelsea_FC"],
            "tottenham": ["Tottenham", "Tottenham_Hotspur", "Spurs"],
            "newcastle": ["Newcastle_United", "Newcastle"],
            "west ham": ["West_Ham", "West_Ham_United"],
            "aston villa": ["Aston_Villa"],
            "everton": ["Everton", "Everton_FC"],
            "leicester": ["Leicester", "Leicester_City"],
            "ajax": ["Ajax", "AFC_Ajax"],
            "psv": ["PSV", "PSV_Eindhoven"],
            "feyenoord": ["Feyenoord"],
            "bayern munich": ["Bayern_Munich", "Bayern", "FC_Bayern_Munich"],
            "dortmund": ["Borussia_Dortmund", "Dortmund"],
            "rb leipzig": ["RB_Leipzig", "Leipzig"],
            "juventus": ["Juventus", "Juventus_FC"],
            "inter": ["Inter", "Inter_Milan"],
            "ac milan": ["Milan", "AC_Milan"],
            "napoli": ["Napoli", "SSC_Napoli"],
            "roma": ["Roma", "AS_Roma"],
            "psg": ["Paris_Saint_Germain", "PSG"]
        }
        
        # Añadir variaciones específicas si el equipo está en la lista
        for key, variations in team_mappings.items():
            if team_name.lower() in key or key in team_name.lower():
                name_variations.extend(variations)
        
        # Eliminar duplicados
        name_variations = list(set(name_variations))
        
        # Generar URLs para cada variación
        for name in name_variations:
            # URL base
            url = f"https://understat.com/team/{name}"
            
            # Añadir año si está especificado
            if year:
                url = f"{url}/{year}"
                urls.append(url)
                
                # Probar también con el año anterior y siguiente para casos límite
                urls.append(f"{url}/{int(year)-1}")
                urls.append(f"{url}/{int(year)+1}")
            else:
                urls.append(url)
        
        return urls
    
    def get_understat_data(self, team_name):
        """
        Obtiene datos de Understat para un equipo mediante web scraping
        
        Args:
            team_name: Nombre del equipo
            
        Returns:
            dict: Respuesta con el HTML para procesarlo posteriormente
        """
        # Normalizar el nombre del equipo para Understat
        team_name = team_name.strip()
        
        # Mapeo de nombres comunes a nombres de Understat
        understat_team_mapping = {
            "manchester utd": "Manchester_United",
            "manchester united": "Manchester_United",
            "man utd": "Manchester_United",
            "man united": "Manchester_United",
            "manchester city": "Manchester_City",
            "man city": "Manchester_City",
            "arsenal": "Arsenal",
            "chelsea": "Chelsea",
            "liverpool": "Liverpool",
            "tottenham": "Tottenham",
            "spurs": "Tottenham",
            "real madrid": "Real_Madrid",
            "barcelona": "Barcelona",
            "atletico madrid": "Atletico_Madrid",
            "atlético madrid": "Atletico_Madrid",
            "bayern": "Bayern_Munich",
            "bayern munich": "Bayern_Munich",
            "dortmund": "Borussia_Dortmund",
            "borussia dortmund": "Borussia_Dortmund",
            "psg": "Paris_Saint_Germain",
            "paris": "Paris_Saint_Germain",
            "paris saint germain": "Paris_Saint_Germain",
            "juventus": "Juventus",
            "milan": "AC_Milan",
            "ac milan": "AC_Milan",
            "inter": "Inter",
            "inter milan": "Inter"
        }
        
        # Buscar en el mapeo
        formatted_name = understat_team_mapping.get(team_name.lower())
        
        # Si no está en el mapeo, formatear según reglas de Understat
        if not formatted_name:
            # Capitalizar cada palabra y reemplazar espacios con guiones bajos
            formatted_name = '_'.join(word.capitalize() for word in team_name.split())
        
        print(f"Consultando Understat para equipo: {team_name} (formateado como: {formatted_name})")
        
        # Año actual para la temporada
        current_year = datetime.now().year
        url = f"https://understat.com/team/{formatted_name}/{current_year}"
        
        try:
            # Configurar headers para simular un navegador
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            print(f"Realizando petición a: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                print(f"Datos obtenidos exitosamente de Understat para {formatted_name}")
                return {
                    "status": "success",
                    "url": url,
                    "data": response.text
                }
            else:
                print(f"Error al obtener datos de Understat: {response.status_code}")
                # Intentar con año anterior si el actual falla
                previous_year = current_year - 1
                url = f"https://understat.com/team/{formatted_name}/{previous_year}"
                
                print(f"Intentando con temporada anterior: {url}")
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    print(f"Datos obtenidos exitosamente de Understat para {formatted_name} (temporada anterior)")
                    return {
                        "status": "success",
                        "url": url,
                        "data": response.text
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Error al obtener datos de Understat: {response.status_code}",
                        "url": url
                    }
        except Exception as e:
            print(f"Error de conexión con Understat: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión: {str(e)}",
                "url": url
            }
    
    def get_injuries_and_suspensions(self, team_id):
        """
        Obtiene las lesiones y sanciones de un equipo utilizando la API de fútbol
        
        Args:
            team_id (int): ID del equipo
            
        Returns:
            dict: Información sobre lesiones y sanciones
        """
        endpoint = f"{self.BASE_URL}/injuries"
        params = {
            "team": team_id,
            "season": datetime.now().year
        }

        try:
            print(f"Consultando lesiones y sanciones para equipo ID: {team_id}")
            response = requests.get(endpoint, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if "response" in data and data["response"]:
                    print(f"Se encontraron {len(data['response'])} lesiones/sanciones para el equipo {team_id}")
                    return {
                        "status": "success",
                        "data": data["response"]
                    }
                else:
                    print(f"No se encontraron lesiones/sanciones para el equipo {team_id}")
                    return {
                        "status": "success",
                        "data": []
                    }
            else:
                print(f"Error al obtener lesiones y sanciones: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Error al obtener datos: {response.status_code}"
                }
        except Exception as e:
            print(f"Error al consultar lesiones y sanciones: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión: {str(e)}"
            }
    
    def scrape_transfermarkt_for_injuries(self, team_name):
        """
        Obtiene datos de lesiones de Transfermarkt mediante web scraping
        
        Args:
            team_name (str): Nombre del equipo
            
        Returns:
            dict: Información sobre lesiones de jugadores
        """
        # Mapeo de nombres comunes a URLs de Transfermarkt
        transfermarkt_team_mapping = {
            "manchester united": "manchester-united",
            "manchester city": "manchester-city",
            "real madrid": "real-madrid",
            "barcelona": "fc-barcelona",
            "atletico madrid": "atletico-madrid",
            "liverpool": "fc-liverpool",
            "arsenal": "fc-arsenal",
            "chelsea": "fc-chelsea",
            "tottenham": "tottenham-hotspur",
            "bayern munich": "bayern-munchen",
            "dortmund": "borussia-dortmund",
            "psg": "paris-saint-germain",
            "juventus": "juventus-turin",
            "inter": "inter-mailand",
            "ac milan": "ac-mailand"
        }

        # Normalizar el nombre del equipo
        team_url = transfermarkt_team_mapping.get(team_name.lower(), team_name.replace(' ', '-'))
        url = f"https://www.transfermarkt.com/teams/{team_url}/sperren-verletzungen/verein"

        try:
            # Configurar headers para evitar bloqueos
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            print(f"Consultando lesiones en Transfermarkt para: {team_name}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Procesar la página para extraer información de lesiones
                injuries = []
                
                # Buscar tablas de lesiones (en Transfermarkt suelen estar en tablas específicas)
                injury_tables = soup.select("table.items")
                
                if injury_tables:
                    for table in injury_tables:
                        rows = table.select("tbody tr")
                        
                        for row in rows:
                            player_cell = row.select_one("td.hauptlink")
                            if not player_cell:
                                continue
                                
                            player_name = player_cell.get_text(strip=True)
                            
                            # Obtener tipo de lesión/sanción
                            injury_type_cell = row.select_one("td.rechts")
                            injury_type = injury_type_cell.get_text(strip=True) if injury_type_cell else "Desconocida"
                            
                            # Obtener fecha de regreso si está disponible
                            return_date_cell = row.select_one("td:nth-child(5)")
                            return_date = return_date_cell.get_text(strip=True) if return_date_cell else "Desconocida"
                            
                            injuries.append({
                                "player_name": player_name,
                                "injury_type": injury_type,
                                "return_date": return_date,
                                "source": "Transfermarkt"
                            })
                
                print(f"Se encontraron {len(injuries)} lesiones/sanciones en Transfermarkt para {team_name}")
                return {
                    "status": "success",
                    "data": injuries
                }
            else:
                print(f"Error al obtener datos de Transfermarkt: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Error al obtener datos: {response.status_code}"
                }
        except Exception as e:
            print(f"Error al consultar Transfermarkt: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión: {str(e)}"
            }
    
    def advanced_team_search(self, team_name):
        """
        Búsqueda avanzada de un equipo por nombre
        
        Args:
            team_name (str): Nombre del equipo a buscar
            
        Returns:
            dict: Datos del equipo encontrado o None si no se encuentra
        """
        print(f"Buscando equipo: {team_name}")
        
        # Verificar si el equipo es uno de los populares primero
        popular_teams = {
            "manchester united": {"id": 33, "name": "Manchester United"},
            "man utd": {"id": 33, "name": "Manchester United"},
            "man united": {"id": 33, "name": "Manchester United"},
            "manchester city": {"id": 50, "name": "Manchester City"},
            "man city": {"id": 50, "name": "Manchester City"},
            "liverpool": {"id": 40, "name": "Liverpool"},
            "arsenal": {"id": 42, "name": "Arsenal"},
            "chelsea": {"id": 49, "name": "Chelsea"},
            "tottenham": {"id": 47, "name": "Tottenham"},
            "spurs": {"id": 47, "name": "Tottenham"},
            "barcelona": {"id": 529, "name": "Barcelona"},
            "real madrid": {"id": 541, "name": "Real Madrid"},
            "atletico madrid": {"id": 530, "name": "Atletico Madrid"},
            "bayern": {"id": 157, "name": "Bayern Munich"},
            "bayern munich": {"id": 157, "name": "Bayern Munich"},
            "dortmund": {"id": 165, "name": "Borussia Dortmund"},
            "borussia dortmund": {"id": 165, "name": "Borussia Dortmund"},
            "psg": {"id": 85, "name": "Paris Saint Germain"},
            "paris": {"id": 85, "name": "Paris Saint Germain"},
            "juventus": {"id": 496, "name": "Juventus"},
            "milan": {"id": 489, "name": "AC Milan"},
            "ac milan": {"id": 489, "name": "AC Milan"},
            "inter": {"id": 505, "name": "Inter"},
            "inter milan": {"id": 505, "name": "Inter"},
            "napoli": {"id": 492, "name": "Napoli"},
            "roma": {"id": 497, "name": "AS Roma"},
            "ajax": {"id": 194, "name": "Ajax"},
            "benfica": {"id": 211, "name": "Benfica"},
            "porto": {"id": 212, "name": "FC Porto"}
        }
        
        # Convertir el nombre del equipo a minúsculas para la búsqueda
        normalized_name = team_name.lower().strip()
        
        # Verificar si coincide con alguno de los equipos populares
        if normalized_name in popular_teams:
            return popular_teams[normalized_name]
        
        # Buscar coincidencias parciales
        for key, value in popular_teams.items():
            if key in normalized_name or normalized_name in key:
                print(f"Coincidencia parcial encontrada para '{team_name}': {value['name']}")
                return value
        
        # Si no es un equipo popular, hacer búsqueda en la API
        params = {
            "name": team_name
        }
        url = f"{self.BASE_URL}/teams"
        
        response = self.make_request(url, params)
        
        # Verificar respuesta válida
        if response and "response" in response and response["response"]:
            data = response["response"]
            print(f"Respuesta de API: {len(data)} equipos encontrados")
            
            # Buscar coincidencia exacta primero
            for team in data:
                if "team" in team and team["team"]["name"].lower() == normalized_name:
                    print(f"Equipo encontrado con búsqueda exacta: {team['team']['name']}")
                    return {
                        "id": team["team"]["id"],
                        "name": team["team"]["name"]
                    }
            
            # Si no hay coincidencia exacta, tomar el primer resultado
            print(f"Utilizando el primer resultado: {data[0]['team']['name']}")
            return {
                "id": data[0]["team"]["id"],
                "name": data[0]["team"]["name"]
            }
        
        print("No se encontró el equipo en la API")
        return None

    # Alias para make_request para mantener compatibilidad con código existente
    def make_request(self, url, params, use_api_key=True):
        """
        Alias para _make_request para mantener compatibilidad
        """
        return self._make_request(url, params, use_api_key)

    def get_injuries(self, team_id):
        """
        Alias for get_injuries_and_suspensions to maintain compatibility.
        """
        return self.get_injuries_and_suspensions(team_id)

    def get_transfermarkt_injuries(self, team_name):
        """
        Alias for scrape_transfermarkt_for_injuries to maintain compatibility.
        """
        return self.scrape_transfermarkt_for_injuries(team_name)

    def get_lineups(self, fixture_id):
        """
        Alias for get_lineup_predictions to maintain compatibility.
        """
        return self.get_lineup_predictions(fixture_id)

    def get_lineup_predictions(self, fixture_id):
        """
        Obtiene las predicciones de alineación para un partido
        
        Args:
            fixture_id (int): ID del partido
            
        Returns:
            dict: Predicciones de alineación para ambos equipos
        """
        if not fixture_id:
            return {
                "status": "error",
                "message": "Se requiere un ID de partido válido"
            }

        endpoint = f"{self.BASE_URL}/fixtures/lineups"
        params = {
            "fixture": fixture_id
        }

        try:
            print(f"Consultando alineaciones para partido ID: {fixture_id}")
            response = requests.get(endpoint, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if "response" in data and data["response"]:
                    print(f"Se encontraron alineaciones para el partido {fixture_id}")
                    return {
                        "status": "success",
                        "data": data["response"]
                    }
                else:
                    print(f"No se encontraron alineaciones para el partido {fixture_id}")
                    return {
                        "status": "success",
                        "data": []
                    }
            else:
                print(f"Error al obtener alineaciones: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Error al obtener datos: {response.status_code}"
                }
        except Exception as e:
            print(f"Error al consultar alineaciones: {str(e)}")
            return {
                "status": "error",
                "message": f"Error de conexión: {str(e)}"
            }

    def get_probable_lineups_from_alternative_sources(self, team1_name, team2_name, date_str):
        """
        Obtiene alineaciones probables de fuentes alternativas como Sofascore
        
        Args:
            team1_name (str): Nombre del equipo local
            team2_name (str): Nombre del equipo visitante
            date_str (str): Fecha del partido en formato YYYY-MM-DD
            
        Returns:
            dict: Alineaciones probables de ambos equipos
        """
        try:
            # Headers para evitar bloqueos
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            }

            # Formatear nombres de equipos para URL
            team1_url = team1_name.lower().replace(" ", "-")
            team2_url = team2_name.lower().replace(" ", "-")
            
            # URLs de diferentes fuentes
            sofascore_url = f"https://www.sofascore.com/football/{team1_url}-{team2_url}/{date_str}"
            whoscored_url = f"https://www.whoscored.com/Teams/{team1_url}/Show/{team2_url}"
            
            lineups = {
                "team1": {"probable": [], "injured": [], "suspended": []},
                "team2": {"probable": [], "injured": [], "suspended": []}
            }

            # Intentar obtener datos de Sofascore
            try:
                response = requests.get(sofascore_url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Implementar extracción específica de Sofascore
                    # ...
            except Exception as e:
                print(f"Error obteniendo datos de Sofascore: {e}")

            # Intentar obtener datos de WhoScored como respaldo
            try:
                response = requests.get(whoscored_url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Implementar extracción específica de WhoScored
                    # ...
            except Exception as e:
                print(f"Error obteniendo datos de WhoScored: {e}")

            return lineups

        except Exception as e:
            print(f"Error obteniendo alineaciones probables: {e}")
            return None

    def get_market_values(self, player_name=None, team_name=None):
        """
        Fetches market value data for a player or team.
        NOTE: Original API (football-market-value.com) is no longer available.
        This is a fallback implementation using estimated values.

        Args:
            player_name (str, optional): Name of the player.
            team_name (str, optional): Name of the team.

        Returns:
            dict: Market value data.
        """
        # First try to get data from API-Football if available
        if team_name:
            try:
                # Try to fetch team statistics which might include market values
                team_id = self.search_team(team_name)
                if team_id:
                    team_id = team_id.get("id")
                    leagues = self.get_leagues_for_team(team_id)
                    if leagues and "response" in leagues and leagues["response"]:
                        league_id = leagues["response"][0]["league"]["id"]
                        team_stats = self.get_team_statistics(team_id, league_id)
                        if team_stats and "response" in team_stats:
                            return {
                                "status": "success",
                                "data": {
                                    "team": team_name,
                                    "total_market_value": "75M €",  # Estimated value
                                    "currency": "EUR",
                                    "source": "api-football-fallback",
                                    "players": []
                                }
                            }
            except Exception as e:
                print(f"Error getting team market values from API-Football: {e}")
        
        # If API-Football failed or didn't have market values, use fallback static data
        print("Using fallback market value data as football-market-value.com API is unavailable")
        
        # Create a fallback response with estimated values based on common knowledge
        # Map team names to estimated market values (in millions of euros)
        top_teams = {"real madrid": 950, "barcelona": 900, "manchester city": 1200, 
                    "bayern munich": 850, "liverpool": 900, "psg": 1000,
                    "manchester united": 800, "chelsea": 850, "juventus": 600,
                    "atletico madrid": 600, "tottenham": 650, "arsenal": 700,
                    "napoli": 550, "ac milan": 550, "inter": 600, "dortmund": 550}
        
        mid_teams = {"sevilla": 350, "roma": 350, "lazio": 300, "leicester": 350,
                    "west ham": 400, "ajax": 250, "benfica": 300, "porto": 280,
                    "marseille": 250, "lyon": 300, "villarreal": 250, "bologna": 220}
        
        # Default value for unknown teams
        default_value = 100
        
        if team_name:
            team_name_lower = team_name.lower().split(' ')[0]  # Take first word to handle variants
            # Check if it's a top team
            for key, value in top_teams.items():
                if key.startswith(team_name_lower) or team_name_lower in key:
                    return {
                        "status": "success",
                        "data": {
                            "team": team_name,
                            "total_market_value": f"{value}M €",
                            "currency": "EUR",
                            "source": "fallback-estimation",
                            "players": []
                        }
                    }
            
            # Check if it's a mid-table team
            for key, value in mid_teams.items():
                if key.startswith(team_name_lower) or team_name_lower in key:
                    return {
                        "status": "success",
                        "data": {
                            "team": team_name,
                            "total_market_value": f"{value}M €",
                            "currency": "EUR",
                            "source": "fallback-estimation",
                            "players": []
                        }
                    }
        
        # For player values or unknown teams, return a default response
        entity = team_name if team_name else (player_name if player_name else "Unknown")
        return {
            "status": "success",
            "data": {
                "team": entity,
                "total_market_value": f"{default_value}M €",
                "currency": "EUR",
                "source": "fallback-estimation",
                "players": []
            }
        }

    def get_team_leagues(self, team_id, season):
        """Obtiene las ligas en las que juega un equipo para una temporada específica."""
        endpoint = f"https://api-football-v1.p.rapidapi.com/v3/leagues"
        params = {"team": team_id, "season": season}
        response = self.make_request(endpoint, params)
        return response.get("response", []) if response else []