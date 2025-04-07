#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de ejemplo para mostrar cómo usar el extractor de datos de partidos de fútbol.
Demuestra la funcionalidad del sistema de caché y la nueva estructura de almacenamiento.
"""

import os
import sys
import json
from datetime import datetime
from pprint import pprint

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el extractor de datos
from src.main import FootballDataExtractor

def extract_match_example():
    """
    Ejemplo de extracción de datos de un partido.
    Muestra cómo se extraen los datos y cómo funciona el sistema de caché.
    """
    print("=== EJEMPLO DE EXTRACCIÓN DE DATOS DE UN PARTIDO ===")
    
    # Inicializar el extractor
    extractor = FootballDataExtractor()
    
    # Extraer datos para un partido específico
    match_input = "Fulham vs Liverpool FC - 2025-04-06"
    print(f"\nExtrayendo datos para: {match_input}\n")
    
    # Primera extracción - Generará llamadas a la API
    print("== Primera extracción (datos nuevos) ==")
    data = extractor.extract_match_data(match_input)
    
    # Verificar si hubo algún error
    if "error" in data:
        print(f"Error: {data['error']}")
        return
    
    # Mostrar resumen de los datos extraídos
    print_match_summary(data)
    
    # Segunda extracción - Debería usar la caché
    print("\n== Segunda extracción (usando caché) ==")
    cached_data = extractor.extract_match_data(match_input)
    
    if "error" in cached_data:
        print(f"Error: {cached_data['error']}")
    else:
        print("\nDatos obtenidos de la caché")
        print(f"Archivos utilizados:")
        print(f"- Partido: data/matches/partido_{data['match']['home_team']['id']}_vs_{data['match']['away_team']['id']}_{data['match']['date']}.json")
        print(f"- Equipo local: data/teams/equipo_local_{data['match']['home_team']['id']}.json")
        print(f"- Equipo visitante: data/teams/equipo_visitante_{data['match']['away_team']['id']}.json")

def load_match_example():
    """
    Ejemplo de carga de datos de un partido previamente guardado.
    """
    print("\n=== EJEMPLO DE CARGA DE DATOS DE UN PARTIDO ===")
    
    # Inicializar el extractor
    extractor = FootballDataExtractor()
    
    # Cargar datos para un partido específico
    home_team = "Fulham"
    away_team = "Liverpool FC"
    date = "2025-04-06"
    
    print(f"\nCargando datos para: {home_team} vs {away_team} ({date})\n")
    
    # Obtener los datos
    data = extractor.load_match_data(home_team, away_team, date)
    
    # Verificar si se encontraron datos
    if not data:
        print(f"No se encontraron datos para el partido: {home_team} vs {away_team}")
        return
    
    # Mostrar un resumen de los datos cargados
    print("\n=== DATOS CARGADOS DEL PARTIDO ===")
    print_match_summary(data)

def print_match_summary(data):
    """
    Imprime un resumen de los datos del partido.
    """
    match = data.get("match", {})
    print(f"Equipos: {match.get('home_team', {}).get('name')} vs {match.get('away_team', {}).get('name')}")
    print(f"Fecha y hora: {match.get('date')} {match.get('time')}")
    print(f"Liga: {match.get('league', {}).get('name')}")
    print(f"Estadio: {match.get('venue', {}).get('name')}, {match.get('venue', {}).get('city')}")
    print(f"Árbitro: {match.get('referee')}")
    
    # Mostrar estadísticas del head-to-head
    if "head_to_head" in data and data["head_to_head"]:
        h2h = data["head_to_head"]
        print("\n=== HISTORIAL DE ENFRENTAMIENTOS ===")
        print(f"Total de partidos: {h2h.get('total_matches')}")
        print(f"{match.get('home_team', {}).get('name')}: {h2h.get('home_wins')} victorias")
        print(f"{match.get('away_team', {}).get('name')}: {h2h.get('away_wins')} victorias")
        print(f"Empates: {h2h.get('draws')}")
    
    # Mostrar próximos partidos del equipo local
    if "home_team_next_matches" in data and data["home_team_next_matches"]:
        print(f"\n=== PRÓXIMOS PARTIDOS DE {match.get('home_team', {}).get('name')} ===")
        for idx, next_match in enumerate(data["home_team_next_matches"][:3], 1):
            print(f"{idx}. {next_match.get('home_team')} vs {next_match.get('away_team')} - {next_match.get('date')}")
    
    # Mostrar próximos partidos del equipo visitante
    if "away_team_next_matches" in data and data["away_team_next_matches"]:
        print(f"\n=== PRÓXIMOS PARTIDOS DE {match.get('away_team', {}).get('name')} ===")
        for idx, next_match in enumerate(data["away_team_next_matches"][:3], 1):
            print(f"{idx}. {next_match.get('home_team')} vs {next_match.get('away_team')} - {next_match.get('date')}")
    
    # Mostrar datos del clima si están disponibles
    if "weather" in data and data["weather"]:
        weather = data["weather"]
        print("\n=== CONDICIONES METEOROLÓGICAS ===")
        print(f"Temperatura: {weather.get('temperature')}°C")
        print(f"Descripción: {weather.get('description')}")
        print(f"Humedad: {weather.get('humidity')}%")
        print(f"Velocidad del viento: {weather.get('wind_speed')} km/h")
        print(f"Precipitación: {weather.get('precipitation')} mm")
    
    # Mostrar clasificación si está disponible
    if "standings" in data and data["standings"]:
        print("\n=== CLASIFICACIÓN EN LA LIGA ===")
        for team_standing in data["standings"][:5]:  # Mostrar solo los primeros 5 equipos
            print(f"{team_standing.get('rank')}. {team_standing.get('team_name')} - {team_standing.get('points')} pts")

def test_cache_system():
    """
    Demuestra cómo funciona el sistema de caché para optimizar llamadas a la API.
    """
    print("\n=== TEST DEL SISTEMA DE CACHÉ ===")
    
    # Inicializar el extractor
    extractor = FootballDataExtractor()
    
    # Extraer datos para tres partidos diferentes del mismo equipo
    teams = [
        ("Barcelona", "Real Madrid", "2023-10-28"),
        ("Barcelona", "Atletico Madrid", "2023-09-20"),
        ("Barcelona", "Sevilla", "2023-11-15")
    ]
    
    for home, away, date in teams:
        match_input = f"{home} vs {away} - {date}"
        print(f"\nExtrayendo datos para: {match_input}")
        
        # El primer partido debería hacer todas las llamadas API
        # Los siguientes deberían reutilizar los datos del equipo local (Barcelona)
        data = extractor.extract_match_data(match_input)
        
        if "error" in data:
            print(f"Error: {data['error']}")
        else:
            print(f"Datos extraídos correctamente para {home} vs {away}")

def main():
    """
    Función principal que ejecuta los ejemplos.
    """
    # Ejecutar ejemplo de extracción
    extract_match_example()
    
    # Ejecutar ejemplo de carga
    load_match_example()
    
    # Descomentar para probar el sistema de caché con múltiples partidos
    # test_cache_system()

if __name__ == "__main__":
    main() 