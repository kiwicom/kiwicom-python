import arrow
import requests


def search_flight(payload):
    return requests.get('https://api.skypicker.com/flights', params=payload)


def test_search_flight():
    prg_to_lgw = {
        'flyFrom': 'PRG',
        'to': 'LGW',
        'dateFrom': arrow.utcnow().replace(day=10).format('DD/MM/YYYY'),
        'dateTo': arrow.utcnow().replace(day=20).format('DD/MM/YYYY'),
        'partner': 'picky'
    }

    api_result = search_flight(prg_to_lgw)
    assert 'currency' in api_result.json()
    assert 'data' in api_result.json()
