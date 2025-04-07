#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime

class RefereeAPI:
    """
    Clase para obtener información de árbitros de fútbol a través de web scraping
    """
    
    def __init__(self, football_api=None):
        """
        Inicializa la API de árbitros
        
        Args:
            football_api: Instancia de FootballAPI para hacer peticiones HTTP (opcional)
        """
        self.football_api = football_api
        
        # Headers necesarios para web scraping
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
    def search_referee(self, referee_name):
        """
        Busca información de un árbitro en Transfermarkt
        
        Args:
            referee_name (str): Nombre del árbitro
            
        Returns:
            dict: Información del árbitro o un diccionario con errores
        """
        try:
            print(f"Buscando información del árbitro: {referee_name}")
            
            # 1. Buscar en Google con site:transfermarkt.com
            search_query = f"{referee_name} site:transfermarkt.com referee"
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer primer resultado de transfermarkt
            transfermarkt_link = None
            for link in soup.select('a[href]'):
                href = link.get('href')
                if 'transfermarkt.com' in href and '/schiedsrichter/' in href:
                    # Extraer la URL real de la URL de Google
                    match = re.search(r'(?:url\?q=)(.*?)(?:&sa=|$)', href)
                    if match:
                        transfermarkt_link = match.group(1)
                        break
            
            if not transfermarkt_link:
                return {
                    "status": "error",
                    "message": "No se encontró el árbitro en Transfermarkt",
                    "name": referee_name
                }
                
            # 2. Obtener datos de la página del árbitro
            print(f"Obteniendo datos del árbitro desde: {transfermarkt_link}")
            
            # Esperar un poco para evitar bloqueos
            time.sleep(1)
            
            response = requests.get(transfermarkt_link, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer datos básicos
            name = soup.select_one('h1.data-header__headline-wrapper')
            name = name.text.strip() if name else referee_name
            
            age = soup.select_one('span.data-header__label:-soup-contains("Age:") + span')
            age = age.text.strip() if age else "Desconocida"
            
            nationality = soup.select_one('span.data-header__label:-soup-contains("Nationality:") + span')
            nationality = nationality.text.strip() if nationality else "Desconocida"
            
            # Extraer estadísticas de partidos
            matches_info = {}
            stats_table = soup.select_one('div.responsive-table')
            if stats_table:
                for row in stats_table.select('tbody > tr'):
                    cells = row.select('td')
                    if len(cells) >= 6:
                        competition = cells[0].text.strip()
                        matches = cells[1].text.strip()
                        yellow_cards = cells[3].text.strip()
                        red_cards = cells[4].text.strip()
                        
                        matches_info[competition] = {
                            "matches": matches,
                            "yellow_cards": yellow_cards,
                            "red_cards": red_cards
                        }
            
            # Extraer imagen si está disponible
            image_url = soup.select_one('img.data-header__profile-image')
            image_url = image_url['src'] if image_url and 'src' in image_url.attrs else None
            
            return {
                "status": "success",
                "name": name,
                "age": age,
                "nationality": nationality,
                "matches_info": matches_info,
                "image_url": image_url,
                "source_url": transfermarkt_link
            }
            
        except Exception as e:
            print(f"Error al buscar información del árbitro: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "name": referee_name
            }
    
    def get_referee_stats(self, referee_name, team1_name=None, team2_name=None):
        """
        Obtiene estadísticas específicas de un árbitro, opcionalmente filtradas por equipos
        
        Args:
            referee_name (str): Nombre del árbitro
            team1_name (str, optional): Primer equipo para filtrar estadísticas
            team2_name (str, optional): Segundo equipo para filtrar estadísticas
            
        Returns:
            dict: Estadísticas del árbitro
        """
        referee_data = self.search_referee(referee_name)
        
        if referee_data["status"] == "error":
            return referee_data
            
        # Si tenemos los nombres de los equipos, podemos intentar buscar estadísticas específicas
        # Este es un ejemplo básico, el scraping real dependería de la estructura de la página
        if team1_name or team2_name:
            # Aquí iría el código para buscar estadísticas específicas con los equipos
            referee_data["team_specific_stats"] = {
                "message": "Esta funcionalidad requiere scraping adicional específico para cada equipo"
            }
            
        return referee_data 

class RefereeAnalysisAPI:
    """
    API para obtener y analizar datos de árbitros utilizando Understat.
    """
    def __init__(self, understat_api_instance):
        """
        Inicializa la API de Árbitros.

        Args:
            understat_api_instance: Instancia de UnderstatAPI para obtener datos.
        """
        self.understat_api = understat_api_instance
        # En el futuro, podríamos añadir otras fuentes aquí

    def get_referee_analysis(self, referee_name: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene un análisis detallado de un árbitro utilizando UnderstatAPI.

        Args:
            referee_name (str): Nombre del árbitro.
            year (int, optional): Año específico para el análisis.

        Returns:
            Dict[str, Any]: Análisis del árbitro incluyendo:
                - status: Estado de la operación ('success' o 'error').
                - analysis: Datos del análisis (tarjetas, faltas, tendencias, etc.).
                - metadata: Información sobre la consulta.
        """
        if not referee_name:
            return {
                "status": "error",
                "message": "Nombre del árbitro no proporcionado.",
                "analysis": {},
                 "metadata": {"referee_name": referee_name, "year": year, "timestamp": datetime.now().isoformat()}
            }

        print(f"Obteniendo análisis para el árbitro: {referee_name} para el año {year or 'todos'}")
        try:
            # Llamar al método existente en UnderstatAPI
            analysis_data = self.understat_api.analyze_referee_stats(referee_name, year)

            # Podríamos añadir procesamiento adicional o combinar con otras fuentes aquí si fuera necesario

            return analysis_data # La estructura ya incluye status, análisis y metadata

        except Exception as e:
            error_message = str(e)
            print(f"Error obteniendo análisis del árbitro {referee_name}: {error_message}")
            return {
                "status": "error",
                "message": f"Error inesperado: {error_message}",
                "analysis": {},
                "metadata": {
                    "referee_name": referee_name,
                    "year": year,
                    "timestamp": datetime.now().isoformat(),
                    "error_details": error_message
                }
            }