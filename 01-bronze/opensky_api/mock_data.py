"""Mock data for OpenSky API — based on real API response structure"""

MOCK_DEPARTURES = [
    {
        "icao24": "3c56f0",
        "firstSeen": 1778598961,
        "estDepartureAirport": "EDDB",
        "lastSeen": 1778604722,
        "estArrivalAirport": "EDDM",
        "callsign": "EWG1R   ",
        "estDepartureAirportHorizDistance": 4135,
        "estDepartureAirportVertDistance": 264,
        "estArrivalAirportHorizDistance": 1823,
        "estArrivalAirportVertDistance": 158,
        "departureAirportCandidatesCount": 1,
        "arrivalAirportCandidatesCount": 1
    },
    {
        "icao24": "3c6444",
        "firstSeen": 1778601200,
        "estDepartureAirport": "EDDB",
        "lastSeen": 1778608500,
        "estArrivalAirport": "LEMD",
        "callsign": "DLH456  ",
        "estDepartureAirportHorizDistance": 2100,
        "estDepartureAirportVertDistance": 180,
        "estArrivalAirportHorizDistance": 3200,
        "estArrivalAirportVertDistance": 210,
        "departureAirportCandidatesCount": 1,
        "arrivalAirportCandidatesCount": 1
    },
    {
        "icao24": "406a42",
        "firstSeen": 1778603000,
        "estDepartureAirport": "EDDB",
        "lastSeen": 1778607800,
        "estArrivalAirport": "EGLL",
        "callsign": "BAW982  ",
        "estDepartureAirportHorizDistance": 3500,
        "estDepartureAirportVertDistance": 220,
        "estArrivalAirportHorizDistance": 4100,
        "estArrivalAirportVertDistance": 190,
        "departureAirportCandidatesCount": 1,
        "arrivalAirportCandidatesCount": 2
    }
]

MOCK_ARRIVALS = [
    {
        "icao24": "4ca5a1",
        "firstSeen": 1778590000,
        "estDepartureAirport": "EIDW",
        "lastSeen": 1778601000,
        "estArrivalAirport": "EDDB",
        "callsign": "RYR5432 ",
        "estDepartureAirportHorizDistance": 2800,
        "estDepartureAirportVertDistance": 195,
        "estArrivalAirportHorizDistance": 1950,
        "estArrivalAirportVertDistance": 145,
        "departureAirportCandidatesCount": 1,
        "arrivalAirportCandidatesCount": 1
    },
    {
        "icao24": "3c4b4c",
        "firstSeen": 1778592000,
        "estDepartureAirport": "EDDM",
        "lastSeen": 1778598000,
        "estArrivalAirport": "EDDB",
        "callsign": "DLH789  ",
        "estDepartureAirportHorizDistance": 1600,
        "estDepartureAirportVertDistance": 130,
        "estArrivalAirportHorizDistance": 2200,
        "estArrivalAirportVertDistance": 160,
        "departureAirportCandidatesCount": 1,
        "arrivalAirportCandidatesCount": 1
    }
]


def get_mock_departures(airport: str = "EDDB") -> list:
    return [f for f in MOCK_DEPARTURES if f["estDepartureAirport"] == airport]


def get_mock_arrivals(airport: str = "EDDB") -> list:
    return [f for f in MOCK_ARRIVALS if f["estArrivalAirport"] == airport]
