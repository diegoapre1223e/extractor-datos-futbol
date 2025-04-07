import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class GeocodingAPI:
    """
    Clase que encapsula las llamadas a la API de geocodificación OpenCage
    """
    
    BASE_URL = "https://api.opencagedata.com/geocode/v1/json"
    
    def __init__(self):
        """Inicializa la clase con la clave API desde variables de entorno"""
        self.api_key = os.getenv("OPENCAGE_API_KEY")
    
    def get_coordinates(self, location):
        """
        Obtiene las coordenadas geográficas de una ubicación
        
        Args:
            location: Nombre de la ubicación (ej. "Santiago Bernabéu, Madrid")
            
        Returns:
            dict: Coordenadas {latitude, longitude} o None si no se encuentra
        """
        params = {
            "key": self.api_key,
            "q": location
        }
        
        response = requests.get(self.BASE_URL, params=params)
        data = response.json()
        
        if data and "results" in data and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]
            return {
                "latitude": location["lat"],
                "longitude": location["lng"]
            }
        return None
    
    def get_coordinates_from_venue(self, venue_name, city_name):
        """
        Obtiene las coordenadas geográficas de un estadio dado su nombre y ciudad.

        Args:
            venue_name (str): Nombre del estadio.
            city_name (str): Nombre de la ciudad.

        Returns:
            dict: Coordenadas {latitude, longitude} o None si no se encuentra.
        """
        location = f"{venue_name}, {city_name}"
        return self.get_coordinates(location)
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcula la distancia entre dos puntos geográficos usando la fórmula haversine
        
        Args:
            lat1: Latitud del primer punto
            lon1: Longitud del primer punto
            lat2: Latitud del segundo punto
            lon2: Longitud del segundo punto
            
        Returns:
            float: Distancia en kilómetros
        """
        import math
        
        # Radio de la Tierra en kilómetros
        earth_radius = 6371
        
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias entre coordenadas
        d_lat = lat2_rad - lat1_rad
        d_lon = lon2_rad - lon1_rad
        
        # Fórmula haversine
        a = math.sin(d_lat/2) * math.sin(d_lat/2) + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(d_lon/2) * math.sin(d_lon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius * c
        
        return distance