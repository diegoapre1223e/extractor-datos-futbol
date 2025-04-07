#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script interactivo para el extractor de datos de partidos de fútbol.
Permite al usuario ingresar los datos del partido sin modificar el código.
"""

import os
import sys
import time
from datetime import datetime, timedelta
import re
from colorama import init, Fore, Style

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el extractor de datos
from src.main import FootballDataExtractor
from src.utils.data_processor import DataProcessor

# Inicializar colorama para soporte de colores en terminal
init()

def print_colored(text, color=Fore.WHITE, bold=False):
    """Imprime texto con color y formato"""
    style = Style.BRIGHT if bold else ""
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def print_title(title):
    """Imprime un título formateado"""
    width = 60
    print("\n" + "=" * width)
    print_colored(title.center(width), Fore.CYAN, True)
    print("=" * width)

def print_error(message):
    """Imprime un mensaje de error"""
    print_colored(f"❌ ERROR: {message}", Fore.RED, True)

def print_success(message):
    """Imprime un mensaje de éxito"""
    print_colored(f"✅ {message}", Fore.GREEN, True)

def print_warning(message):
    """Imprime un mensaje de advertencia"""
    print_colored(f"⚠️ {message}", Fore.YELLOW, True)

def print_info(message):
    """Imprime un mensaje informativo"""
    print_colored(f"ℹ️ {message}", Fore.BLUE)

def print_match_summary(match_data):
    """Imprime un resumen del partido"""
    if not match_data:
        print_error("No se pudo obtener información del partido")
        return

    # Información básica del partido
    team1 = match_data.get("team1", {}).get("name", "Desconocido")
    team2 = match_data.get("team2", {}).get("name", "Desconocido")
    date = match_data.get("date", "Fecha no disponible")
    
    # Liga y estadio
    league = match_data.get("league", {}).get("name", "Por determinar")
    venue_name = match_data.get("venue", {}).get("name", "Por determinar")
    venue_city = match_data.get("venue", {}).get("city", "Por determinar")
    
    # Árbitro
    referee = match_data.get("referee", {}).get("name", "No disponible")
    referee_predicted = match_data.get("referee", {}).get("is_predicted", False)
    referee_status = " (PREDICHO)" if referee_predicted else " (OFICIAL)"
    
    # Historial
    h2h = match_data.get("h2h", {})
    total_matches = h2h.get("total_matches", 0)
    team1_wins = h2h.get("team1_wins", 0)
    team2_wins = h2h.get("team2_wins", 0)
    draws = h2h.get("draws", 0)
    
    # Imprimir resumen
    print_title(f"RESUMEN DEL PARTIDO")
    print_colored(f"⚽ PARTIDO: {team1} vs {team2}", Fore.GREEN, True)
    print_colored(f"📅 Fecha: {date}", Fore.YELLOW)
    print_colored(f"🏆 Liga: {league}", Fore.BLUE)
    print_colored(f"🏟️ Estadio: {venue_name}, {venue_city}", Fore.MAGENTA)
    
    # Mostrar información del árbitro con indicación si es predicho
    print_colored(f"🚩 Árbitro: {referee}{referee_status}", Fore.CYAN)
    
    # Historial de enfrentamientos
    print("\n")
    print_colored("🔄 HISTORIAL DE ENFRENTAMIENTOS:", Fore.YELLOW, True)
    print_colored(f"  • Total de partidos: {total_matches}", Fore.WHITE)
    print_colored(f"  • {team1}: {team1_wins} victorias", Fore.GREEN)
    print_colored(f"  • {team2}: {team2_wins} victorias", Fore.RED)
    print_colored(f"  • Empates: {draws}", Fore.YELLOW)
    
    # Partidos recientes
    if h2h.get("matches"):
        print("\n")
        print_colored("📊 PARTIDOS RECIENTES:", Fore.BLUE, True)
        for i, match in enumerate(h2h.get("matches", [])[:5]):
            date = match.get("date", "").split("T")[0] if match.get("date") else "Desconocida"
            league = match.get("league", "Liga desconocida")
            score1 = match.get("team1_score", 0)
            score2 = match.get("team2_score", 0)
            result = match.get("result", "-")
            
            result_color = Fore.GREEN if result == "W" else (Fore.RED if result == "L" else Fore.YELLOW)
            print_colored(f"  • {date} [{league}]: {team1} {score1}-{score2} {team2} ({result})", result_color)
    
    # Clima
    weather = match_data.get("weather", {})
    if weather:
        print("\n")
        print_colored("🌤️ CONDICIONES CLIMÁTICAS:", Fore.CYAN, True)
        temp = weather.get("temperature", "N/A")
        condition = weather.get("condition", "No disponible")
        wind = weather.get("wind_speed", "N/A")
        precip = weather.get("precipitation", "N/A")
        
        print_colored(f"  • Temperatura: {temp}°C", Fore.WHITE)
        print_colored(f"  • Condición: {condition}", Fore.WHITE)
        print_colored(f"  • Viento: {wind} km/h", Fore.WHITE)
        print_colored(f"  • Precipitación: {precip} mm", Fore.WHITE)

def get_match_input():
    """
    Solicita al usuario ingresar los datos del partido
    
    Returns:
        str: Texto en formato "Equipo1 vs Equipo2 - YYYY-MM-DD"
    """
    print_title("EXTRACTOR DE DATOS DE PARTIDOS DE FÚTBOL")
    print_info("Herramienta para obtener información detallada de partidos")
    print_info("Formato: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
    print_info("Ejemplo: 'Barcelona vs Real Madrid - 2023-10-28'")
    
    print("=" * 60)
    print("   EXTRACTOR DE DATOS DE PARTIDOS DE FÚTBOL - MODO INTERACTIVO   ")
    print("=" * 60)
    print("\nIngrese los datos del partido que desea analizar:")
    
    # Lista de equipos populares para sugerencias
    popular_teams = [
        "Barcelona", "Real Madrid", "Manchester United", "Liverpool",
        "Bayern Munich", "PSG", "Manchester City", "Chelsea", "Juventus",
        "Inter", "AC Milan", "Arsenal", "Borussia Dortmund", "Atletico Madrid",
        "Ajax", "Napoli", "Benfica", "Porto", "Sevilla", "Roma"
    ]
    
    print("\nEquipos populares para referencia:")
    for i in range(0, len(popular_teams), 4):
        row = popular_teams[i:i+4]
        print("  " + "  |  ".join(row))
    
    # Obtener nombre del equipo local
    home_team = input("\nEquipo Local: ")
    while not home_team.strip():
        print("El nombre del equipo local no puede estar vacío.")
        home_team = input("Equipo Local: ")
    
    # Obtener nombre del equipo visitante
    away_team = input("\nEquipo Visitante: ")
    while not away_team.strip():
        print("El nombre del equipo visitante no puede estar vacío.")
        away_team = input("Equipo Visitante: ")
    
    # Obtener fecha del partido con validación
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    date_input = input("\nFecha del partido (YYYY-MM-DD): ")
    
    # Si está vacío, usar la fecha actual + 7 días
    if not date_input.strip():
        future_date = datetime.now() + timedelta(days=7)
        date_input = future_date.strftime("%Y-%m-%d")
        print(f"Usando fecha por defecto: {date_input}")
    
    # Validar formato
    while not date_pattern.match(date_input):
        print("Formato de fecha incorrecto. Use el formato YYYY-MM-DD.")
        date_input = input("Fecha del partido (YYYY-MM-DD): ")
    
    # Construir el texto en el formato requerido
    match_input = f"{home_team} vs {away_team} - {date_input}"
    
    return match_input

def ask_yes_no(prompt: str) -> bool:
    """Hace una pregunta de sí/no al usuario."""
    while True:
        response = input(f"{prompt} (s/n): ").lower().strip()
        if response in ['s', 'si', 'sí', 'yes', 'y']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print_warning("Respuesta no válida. Por favor, introduce 's' o 'n'.")

def main():
    print_title("EXTRACTOR DE DATOS DE PARTIDOS DE FÚTBOL")
    print_info("Herramienta para obtener información detallada de partidos")
    print_info("Formato: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
    print_info("Ejemplo: 'Barcelona vs Real Madrid - 2023-10-28'")
    
    # Verificar que las variables de entorno necesarias están definidas
    required_keys = ["FOOTBALL_API_KEY", "OPENCAGE_API_KEY", "METEOBLUE_API_KEY"]
    for key in required_keys:
        if not os.environ.get(key):
            print_error(f"La clave API {key} no está definida en el archivo .env")
            print_info("Asegúrate de crear un archivo .env con las claves API necesarias")
            sys.exit(1)
    
    # Crear el extractor de datos
    extractor = FootballDataExtractor()
    
    while True:
        print("\n" + "-" * 60)
        user_input = input("Ingresa el partido (o 'salir' para terminar): ")
        
        if user_input.lower() in ["salir", "exit", "quit", "q"]:
            print_info("Gracias por usar el extractor de datos de partidos. ¡Hasta pronto!")
            break
        
        print_info("Procesando solicitud...")
        try:
            start_time = time.time()
            
            # Parsear la entrada del usuario
            match_info = extractor.parse_match_input(user_input)
            
            if not match_info:
                print_error("No se pudo procesar la entrada")
                print_warning("Asegúrate de usar el formato correcto: 'Equipo1 vs Equipo2 - YYYY-MM-DD'")
                continue
                
            # Extraer datos del partido
            team1, team2, date_str = match_info
            
            # Preguntar por datos opcionales
            get_market = ask_yes_no("¿Extraer valor de mercado? (Transfermarkt)")
            get_historical = ask_yes_no("¿Extraer análisis histórico? (Understat)")
            get_form = ask_yes_no("¿Extraer forma reciente? (Understat)")
            num_form_matches = 5
            if get_form:
                while True:
                    try:
                        num_matches_input = input("Número de partidos para la forma [5]: ")
                        if not num_matches_input:
                            num_form_matches = 5
                            break
                        num_form_matches = int(num_matches_input)
                        if num_form_matches > 0:
                            break
                        else:
                            print_warning("Introduce un número positivo.")
                    except ValueError:
                        print_warning("Introduce un número válido.")
                        
            get_referee = ask_yes_no("¿Extraer análisis del árbitro? (Understat)")
            referee_name = None
            if get_referee:
                referee_name = input("Nombre del árbitro: ").strip()
                if not referee_name:
                    print_warning("No se proporcionó nombre de árbitro, no se extraerán sus datos.")
                    get_referee = False # Desactivar si no hay nombre

            get_coach = ask_yes_no("¿Extraer datos del entrenador?")
            get_injuries = ask_yes_no("¿Extraer informe de lesiones?")
            # Marcar estas como experimentales o dependientes de API
            get_physical = ask_yes_no("¿Extraer métricas físicas? (Experimental/Dependiente)")
            get_tactical = ask_yes_no("¿Extraer análisis táctico? (Experimental/Dependiente)")

            print_info("\nIniciando extracción...")
            try:
                # Llamar al método principal del extractor
                extractor.extract_all_data(
                    team1_name=team1,
                    team2_name=team2,
                    date_str=date_str,
                    options={
                        "market_value": get_market,
                        "historical_analysis": get_historical,
                        "recent_form": get_form,
                        "referee_analysis": get_referee,
                        "coach_data": get_coach,
                        "injury_report": get_injuries,
                        "physical_metrics": get_physical,
                        "tactical_analysis": get_tactical
                    }
                )
                print_success("\nExtracción completada.")
                print_info(f"Los archivos JSON se han guardado en: {extractor.storage.data_dir}")
                print_info(f"Busca archivos que comiencen con: {team1.replace(' ','_')}_vs_{team2.replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}")

            except Exception as e:
                print_error(f"Error durante la extracción: {e}")
                # Podríamos añadir más detalles o stack trace si fuera necesario

        except KeyboardInterrupt:
            print("\n")
            print_info("Operación interrumpida por el usuario.")
        except EOFError: # Manejar fin de archivo si se redirige la entrada
             print("\n")
             print_info("Entrada finalizada.")
             break
        except Exception as e:
            print_error(f"Error inesperado en el bucle principal: {str(e)}")
            # Considerar si continuar o salir en caso de error grave

    print_info("\n¡Hasta pronto!")


if __name__ == "__main__":
    main()