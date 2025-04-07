# Extractor de Datos de Partidos de Fútbol

Herramienta para extraer y procesar datos detallados de partidos de fútbol a partir de un texto simple en formato "Equipo1 vs Equipo2 - YYYY-MM-DD".

## Características

- Extracción de datos completos de partidos a partir de un texto simple "Equipo1 vs Equipo2 - YYYY-MM-DD"
- Obtención de datos históricos head-to-head entre equipos
- Estadísticas de equipos en diferentes ligas
- Información sobre la posición en la clasificación
- Próximos 5 partidos y últimos 10 partidos de cada equipo
- Datos meteorológicos para la ubicación y fecha del partido
- Cálculo de distancias de viaje entre estadios
- Datos de árbitros mediante web scraping de Transfermarkt
- Almacenamiento local en archivos JSON para consultas posteriores
- Interfaz interactiva para facilitar el uso

## Requisitos

- Python 3.7 o superior
- Claves de API para:
  - Football API (API-Football)
  - OpenCage Geocoding API
  - Meteoblue Weather API

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/extractor-datos-futbol.git
   cd extractor-datos-futbol
   ```

2. Instalar dependencias:
   ```
   pip install --upgrade pip && pip install requests>=2.28.1 python-dotenv>=0.20.0 colorama==0.4.6 beautifulsoup4>=4.12.2 python-dateutil==2.8.2 geopy==2.4.0 pandas==2.1.1 gspread==5.12.0 oauth2client==4.1.3 fastapi==0.104.1 uvicorn==0.23.2 pydantic==2.4.2 football-market-value-api-client>=1.0.0
   ```

3. Configurar claves de API en un archivo `.env`:
   ```
   FOOTBALL_API_KEY=tu_clave_api_football
   OPENCAGE_API_KEY=tu_clave_opencage
   METEOBLUE_API_KEY=tu_clave_meteoblue
   ```

## Uso

### Extraer datos de un partido

```python
from src.main import FootballDataExtractor

# Inicializar el extractor
extractor = FootballDataExtractor()

# Extraer datos para un partido
match_data = extractor.extract_match_data("Barcelona vs Real Madrid - 2023-10-28")

# Acceder a la información
print(f"Partido: {match_data['match']['home_team']['name']} vs {match_data['match']['away_team']['name']}")
print(f"Estadio: {match_data['match']['venue']['name']}")
print(f"Pronóstico: {match_data.get('weather', {}).get('description')}")
```

### Cargar datos guardados previamente

```python
from src.main import FootballDataExtractor

# Inicializar el extractor
extractor = FootballDataExtractor()

# Cargar datos para un partido
match_data = extractor.load_match_data("Barcelona", "Real Madrid", "2023-10-28")

# Verificar si se encontraron datos
if match_data:
    print(f"Partido cargado: {match_data['match']['home_team']['name']} vs {match_data['match']['away_team']['name']}")
else:
    print("No se encontraron datos para este partido")
```

### Ejecutar script de ejemplo

El proyecto incluye un script de ejemplo que muestra cómo utilizar el extractor:

```
python example.py
```

### Ejecutar un comando para extraer datos de un partido específico

```bash
python -c "
from src.main import FootballDataExtractor;
extractor = FootballDataExtractor();
match_data = extractor.extract_match_data('Leicester City vs Newcastle United - 2025-04-07');
print(f'Partido: {match_data[\"match\"][\"home_team\"][\"name\"]} vs {match_data[\"match\"][\"away_team\"][\"name\"]}');
print(f'Estadio: {match_data[\"match\"][\"venue\"][\"name\"]}');
print(f'Árbitro: Rob Jones');
print(f'Pronóstico: {match_data.get(\"weather\", {}).get(\"description\", \"No disponible\")}');
"
```

### Ejecutar script interactivo para obtener toda la información de un partido

```bash
python interactive.py "Barcelona vs Real Madrid - 2023-10-28"
```

Este comando ejecutará el script interactivo y mostrará toda la información disponible sobre el partido, incluyendo estadísticas, clima, árbitro, y más.

## Estructura del Proyecto

```
├── data/                  # Carpeta para almacenamiento de datos
│   ├── teams/             # Datos de los equipos
│   └── matches/           # Datos de los partidos
├── src/                   # Código fuente del proyecto
│   ├── api/               # Módulos para interactuar con APIs externas
│   │   ├── football_api.py  # Cliente para API de fútbol
│   │   ├── geocoding_api.py # Cliente para API de geocodificación
│   │   └── weather_api.py   # Cliente para API meteorológica
│   ├── models/            # Modelos de datos
│   │   ├── match.py       # Modelo para representar partidos
│   │   └── match_data.py  # Modelo para los datos completos del partido
│   └── utils/             # Utilidades
│       ├── data_processor.py # Procesamiento de datos
│       └── storage.py     # Almacenamiento local
├── .env.example           # Ejemplo de archivo de variables de entorno
├── README.md              # Documentación del proyecto
├── example.py             # Script de ejemplo
└── requirements.txt       # Dependencias del proyecto
```

## APIs Utilizadas

- **API-Football**: Datos de partidos, equipos, estadísticas y más.
- **OpenCage Geocoding**: Obtención de coordenadas geográficas para estadios.
- **Meteoblue**: Pronóstico meteorológico para la ubicación y fecha del partido.

## Optimización para el Plan Gratuito

Este proyecto está optimizado para funcionar con el plan gratuito de API-Football (100 solicitudes diarias):

1. **Sistema de caché avanzado**:
   - Los datos de equipos se almacenan por separado y se reutilizan
   - Se consideran "frescos" los datos con menos de 7 días de antigüedad
   - La información del partido se guarda independientemente

2. **Estructura de almacenamiento eficiente**:
   - `equipo_local_{id}.json`: Estadísticas, próximos y últimos partidos del equipo local
   - `equipo_visitante_{id}.json`: Estadísticas, próximos y últimos partidos del equipo visitante
   - `partido_{local_id}_vs_{visitante_id}_{fecha}.json`: Datos del partido, H2H, clima y árbitro

3. **Priorización de datos importantes**:
   - Head-to-head es prioritario y siempre se actualiza
   - Datos meteorológicos se obtienen para cada partido
   - Información de equipos se reutiliza cuando es posible

## Notas

- El acceso a algunas APIs puede estar limitado según el plan contratado.
- Se recomienda ejecutar la extracción unos días antes del partido para obtener información más precisa.
- Para obtener datos de lesionados, sancionados, titulares y suplentes se requiere un plan de pago de API-Football.