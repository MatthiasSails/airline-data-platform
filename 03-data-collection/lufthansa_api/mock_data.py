"""Mock data for development - mimics Lufthansa API responses"""

MOCK_AIRPORTS = {
    "ResourceResponse": {
        "Airport": [
            {
                "AirportCode": "BER",
                "Position": {
                    "Coordinate": {
                        "Latitude": 52.364,
                        "Longitude": 13.502
                    }
                },
                "CityCode": "BER",
                "CountryCode": "DE",
                "LocationType": "Airport",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Berlin Brandenburg"
                        },
                        {
                            "@LanguageCode": "de",
                            "$": "Berlin Brandenburg"
                        }
                    ]
                }
            },
            {
                "AirportCode": "TXL",
                "Position": {
                    "Coordinate": {
                        "Latitude": 52.562,
                        "Longitude": 13.288
                    }
                },
                "CityCode": "BER",
                "CountryCode": "DE",
                "LocationType": "Airport",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Berlin Tegel"
                        }
                    ]
                }
            },
            {
                "AirportCode": "CDG",
                "Position": {
                    "Coordinate": {
                        "Latitude": 49.009,
                        "Longitude": 2.548
                    }
                },
                "CityCode": "PAR",
                "CountryCode": "FR",
                "LocationType": "Airport",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Paris Charles de Gaulle"
                        }
                    ]
                }
            },
            {
                "AirportCode": "FCO",
                "Position": {
                    "Coordinate": {
                        "Latitude": 41.800,
                        "Longitude": 12.239
                    }
                },
                "CityCode": "ROM",
                "CountryCode": "IT",
                "LocationType": "Airport",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Rome Fiumicino"
                        }
                    ]
                }
            },
            {
                "AirportCode": "MAD",
                "Position": {
                    "Coordinate": {
                        "Latitude": 40.472,
                        "Longitude": -3.361
                    }
                },
                "CityCode": "MAD",
                "CountryCode": "ES",
                "LocationType": "Airport",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Madrid-Barajas"
                        }
                    ]
                }
            }
        ]
    }
}

MOCK_AIRLINES = {
    "ResourceResponse": {
        "Airline": [
            {
                "AirlineCode": "LH",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Lufthansa"
                        },
                        {
                            "@LanguageCode": "de",
                            "$": "Lufthansa"
                        }
                    ]
                }
            },
            {
                "AirlineCode": "BA",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "British Airways"
                        }
                    ]
                }
            },
            {
                "AirlineCode": "AF",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Air France"
                        }
                    ]
                }
            },
            {
                "AirlineCode": "IB",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Iberia"
                        }
                    ]
                }
            },
            {
                "AirlineCode": "AZ",
                "Names": {
                    "Name": [
                        {
                            "@LanguageCode": "en",
                            "$": "Alitalia"
                        }
                    ]
                }
            }
        ]
    }
}


def get_mock_airports(limit: int = 20, offset: int = 0):
    """Return mock airports response"""
    airports = MOCK_AIRPORTS["ResourceResponse"]["Airport"]
    return {
        "ResourceResponse": {
            "Airport": airports[offset : offset + limit]
        }
    }


def get_mock_airlines(limit: int = 20, offset: int = 0):
    """Return mock airlines response"""
    airlines = MOCK_AIRLINES["ResourceResponse"]["Airline"]
    return {
        "ResourceResponse": {
            "Airline": airlines[offset : offset + limit]
        }
    }
