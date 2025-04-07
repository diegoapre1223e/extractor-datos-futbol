"""
Definición de las estructuras de datos JSON para cada API.
"""

UNDERSTAT_SCHEMA = {
    "team_data": {
        "status": "success/error",
        "team_info": {
            "name": str,
            "league": str,
            "season": str
        },
        "players": [
            {
                "id": str,
                "name": str,
                "position": str,
                "games": int,
                "goals": int,
                "assists": int,
                "shots": int,
                "key_passes": int,
                "yellow_cards": int,
                "red_cards": int,
                "xG": float,
                "xA": float,
                "npxG": float,
                "xGChain": float,
                "xGBuildup": float
            }
        ],
        "matches": [
            {
                "id": str,
                "home_team": str,
                "away_team": str,
                "score": str,
                "date": str,
                "league": str,
                "season": str,
                "stats": {
                    "shots": int,
                    "shots_on_target": int,
                    "deep_passes": int,
                    "ppda": float,
                    "xG": float
                }
            }
        ]
    }
}

INJURY_SCHEMA = {
    "injury_analysis": {
        "status": "success/error",
        "current_injuries": [
            {
                "player": str,
                "type": str,
                "start_date": str,
                "expected_return": str,
                "games_missed": int
            }
        ],
        "injury_history": {
            "by_player": {
                "player_id": {
                    "total_injuries": int,
                    "days_missed": int,
                    "types": dict
                }
            },
            "by_type": {
                "injury_type": {
                    "count": int,
                    "avg_recovery_time": float
                }
            },
            "by_season": {
                "season": {
                    "total_injuries": int,
                    "impact_score": float
                }
            }
        },
        "injury_patterns": {
            "common_types": dict,
            "risk_factors": list,
            "seasonal_trends": dict,
            "position_impact": dict
        }
    }
}

PHYSICAL_SCHEMA = {
    "team_physical": {
        "status": "success/error",
        "team_metrics": {
            "total_distance": float,
            "total_sprints": int,
            "high_intensity_runs": int,
            "average_speed": float
        },
        "player_metrics": {
            "player_id": {
                "distance_covered": float,
                "sprints": int,
                "high_intensity_runs": int,
                "average_speed": float,
                "max_speed": float,
                "acceleration_efforts": int,
                "metabolic_power": float
            }
        },
        "intensity_zones": {
            "sprint": dict,
            "high": dict,
            "medium": dict,
            "low": dict
        },
        "temporal_analysis": {
            "first_half": dict,
            "second_half": dict,
            "by_15min": dict
        }
    }
}

TACTICAL_SCHEMA = {
    "team_tactics": {
        "status": "success/error",
        "formation_analysis": {
            "base_formation": str,
            "variations": list,
            "player_positions": dict,
            "formation_changes": list
        },
        "playing_style": {
            "possession": {
                "possession_percentage": float,
                "passes_completed": int,
                "pass_types": dict,
                "build_up_patterns": list
            },
            "pressing": {
                "intensity": str,
                "trigger_zones": list,
                "success_rate": float
            },
            "attacking_patterns": {
                "main_channels": list,
                "crossing_frequency": float,
                "shot_creation": dict
            }
        },
        "set_pieces": {
            "corners": {
                "total": int,
                "patterns": list,
                "success_rate": float
            },
            "free_kicks": {
                "total": int,
                "direct_shots": int,
                "crosses": int,
                "success_rate": float
            }
        }
    }
}

WEATHER_SCHEMA = {
    "weather_data": {
        "status": "success/error",
        "current": {
            "temperature": float,
            "humidity": float,
            "wind_speed": float,
            "precipitation": float,
            "condition": str
        },
        "forecast": {
            "hourly": [
                {
                    "time": str,
                    "temperature": float,
                    "humidity": float,
                    "wind_speed": float,
                    "precipitation": float,
                    "condition": str
                }
            ]
        },
        "match_impact": {
            "playing_conditions": str,
            "risk_factors": list,
            "recommendations": list
        }
    }
}

# Estructura completa para un equipo
TEAM_DATA_SCHEMA = {
    "team_info": {
        "name": str,
        "league": str,
        "season": str
    },
    "understat_data": UNDERSTAT_SCHEMA,
    "injury_data": INJURY_SCHEMA,
    "physical_data": PHYSICAL_SCHEMA,
    "tactical_data": TACTICAL_SCHEMA,
    "weather_data": WEATHER_SCHEMA,
    "metadata": {
        "last_updated": str,
        "data_quality": {
            "completeness": float,
            "reliability": float
        }
    }
}
