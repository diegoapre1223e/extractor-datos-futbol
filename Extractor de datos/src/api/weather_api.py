import os
import requests
from datetime import datetime

class WeatherAPI:
    """
    Clase para interactuar con la API de Meteoblue
    """
    
    BASE_URL = "https://api.meteoblue.com"

    def __init__(self):
        """Inicializa la clase con la clave API desde variables de entorno"""
        self.api_key = os.getenv('METEOBLUE_API_KEY')
        if not self.api_key:
            raise ValueError("Meteoblue API key is not configured. Please set the 'METEOBLUE_API_KEY' environment variable.")

    def get_weather(self, city, date_str=None):
        """
        Obtiene el clima actual o el pronóstico para una ciudad y fecha específicas
        
        Args:
            city (str): Nombre de la ciudad
            date_str (str, optional): Fecha en formato YYYY-MM-DD para obtener el pronóstico.
                                      Si es None o la fecha es hoy, obtiene el clima actual.
                                      
        Returns:
            dict: Datos del clima o pronóstico, o None en caso de error
        """
        endpoint = f"{self.BASE_URL}/weather/current"
        params = {
            "apikey": self.api_key,
            "city": city,
            "date": date_str if date_str else datetime.now().strftime("%Y-%m-%d")
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con la API de Meteoblue: {e}")
            return None
        except Exception as e:
            print(f"Error procesando respuesta de Meteoblue: {e}")
            return None