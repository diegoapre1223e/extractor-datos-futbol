#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import time
import uuid

class LocalStorage:
    """
    Clase para gestionar el almacenamiento local de datos en formato JSON
    """
    
    def __init__(self, data_dir="data"):
        """
        Inicializa el almacenamiento local
        
        Args:
            data_dir (str): Directorio donde se guardarán los datos
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "matches"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "teams"), exist_ok=True)
        
    def save_match_data(self, match_key, data):
        """
        Guarda los datos de un partido en almacenamiento local
        
        Args:
            match_key (str): Clave única para el partido
            data (dict): Datos del partido a guardar
            
        Returns:
            str: Ruta del archivo donde se guardaron los datos
        """
        # Añadir timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Sanitizar nombre de archivo
        filename = match_key.replace(" ", "_").lower()
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-'])
        
        # Ruta completa del archivo
        file_path = os.path.join(self.data_dir, "matches", f"{filename}.json")
        
        # Guardar datos
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Datos guardados en: {file_path}")
        return file_path
        
    def load_match_data(self, match_key):
        """
        Carga los datos de un partido desde almacenamiento local
        
        Args:
            match_key (str): Clave única para el partido
            
        Returns:
            dict: Datos del partido o None si no existe
        """
        # Sanitizar nombre de archivo
        filename = match_key.replace(" ", "_").lower()
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-'])
        
        # Ruta completa del archivo
        file_path = os.path.join(self.data_dir, "matches", f"{filename}.json")
        
        # Verificar si existe el archivo
        if not os.path.exists(file_path):
            return None
            
        # Cargar datos
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"Datos cargados desde: {file_path}")
            return data
        except Exception as e:
            print(f"Error al cargar datos: {str(e)}")
            return None
            
    def save_team_data(self, team_id, data):
        """
        Guarda los datos de un equipo en almacenamiento local
        
        Args:
            team_id (int): ID del equipo
            data (dict): Datos del equipo a guardar
            
        Returns:
            str: Ruta del archivo donde se guardaron los datos
        """
        # Añadir timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Ruta completa del archivo
        file_path = os.path.join(self.data_dir, "teams", f"{team_id}.json")
        
        # Guardar datos
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return file_path
        
    def load_team_data(self, team_id):
        """
        Carga los datos de un equipo desde almacenamiento local
        
        Args:
            team_id (int): ID del equipo
            
        Returns:
            dict: Datos del equipo o None si no existe
        """
        # Ruta completa del archivo
        file_path = os.path.join(self.data_dir, "teams", f"{team_id}.json")
        
        # Verificar si existe el archivo
        if not os.path.exists(file_path):
            return None
            
        # Cargar datos
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error al cargar datos del equipo: {str(e)}")
            return None
    
    def save_team_statistics(self, team_id, league_id, stats_data):
        """
        Guarda las estadísticas de un equipo en una liga específica
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            stats_data: Datos de estadísticas
            
        Returns:
            str: Ruta del archivo guardado
        """
        # Crear carpeta de estadísticas si no existe
        stats_folder = os.path.join(self.data_dir, "statistics")
        if not os.path.exists(stats_folder):
            os.makedirs(stats_folder)
        
        # Generar nombre de archivo
        filename = f"team_{team_id}_league_{league_id}.json"
        file_path = os.path.join(stats_folder, filename)
        
        # Añadir timestamp de guardado
        stats_data['timestamp'] = datetime.now().isoformat()
        
        # Guardar datos en formato JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def load_team_statistics(self, team_id, league_id):
        """
        Carga las estadísticas de un equipo para una liga específica
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            
        Returns:
            dict: Estadísticas del equipo o None si no se encuentran
        """
        stats_folder = os.path.join(self.data_dir, "statistics")
        
        if not os.path.exists(stats_folder):
            return None
        
        # Generar nombre de archivo
        filename = f"team_{team_id}_league_{league_id}.json"
        file_path = os.path.join(stats_folder, filename)
        
        # Verificar si existe el archivo
        if not os.path.exists(file_path):
            return None
        
        # Cargar datos
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar archivo {file_path}: {e}")
            return None
    
    def save_players_data(self, team_id, team_name, players_data):
        """
        Guarda los datos de los jugadores en archivos separados
        
        Args:
            team_id: ID del equipo
            team_name: Nombre del equipo
            players_data: Lista de datos de los jugadores
        """
        # Crear directorio del equipo si no existe
        team_players_dir = os.path.join(self.data_dir, 'players', str(team_id))
        os.makedirs(team_players_dir, exist_ok=True)
        
        # Diccionario para almacenar el índice de jugadores
        players_index = {
            "team_id": team_id,
            "team_name": team_name,
            "players": []
        }
        
        # Guardar cada jugador en un archivo separado
        for player in players_data:
            player_id = player.get("id", str(uuid.uuid4()))
            player_name = player.get("name", "Unknown Player")
            
            # Añadir información del equipo
            player["team_id"] = team_id
            player["team_name"] = team_name
            
            # Crear un nombre de archivo seguro
            filename = f"{player_id}.json"
            file_path = os.path.join(team_players_dir, filename)
            
            # Guardar datos del jugador
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(player, f, ensure_ascii=False, indent=2)
            
            # Añadir al índice
            players_index["players"].append({
                "id": player_id,
                "name": player_name,
                "filename": filename,
                "position": player.get("position", ""),
                "injured": player.get("injured", False),
                "likely_starter": player.get("likely_starter", False)
            })
        
        # Guardar el índice de jugadores
        index_path = os.path.join(team_players_dir, "index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(players_index, f, ensure_ascii=False, indent=2)
            
        return players_index
    
    def load_players_data(self, team_id):
        """
        Carga el índice de jugadores para un equipo
        
        Args:
            team_id: ID del equipo
            
        Returns:
            dict: Índice de jugadores o None si no existe
        """
        index_path = os.path.join(self.data_dir, 'players', str(team_id), "index.json")
        
        if not os.path.exists(index_path):
            return None
            
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_player_data(self, team_id, player_id):
        """
        Carga los datos de un jugador específico
        
        Args:
            team_id: ID del equipo
            player_id: ID del jugador o nombre del archivo
            
        Returns:
            dict: Datos del jugador o None si no existe
        """
        # Verificar si player_id es un nombre de archivo
        if player_id.endswith('.json'):
            file_path = os.path.join(self.data_dir, 'players', str(team_id), player_id)
        else:
            file_path = os.path.join(self.data_dir, 'players', str(team_id), f"{player_id}.json")
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f) 