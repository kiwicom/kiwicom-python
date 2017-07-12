from kiwicom.kiwi import Search
import cerberus
import arrow
import requests
from random import randint
from urllib.parse import urljoin


class TestUrl(object):
    def test_places_url(self):
        payload = {
            'id': 'SK',
            'term': 'br',
            'bounds': 'lat_lo,lat_hi',
            'locale': 'cs',
            'zoomLevelThreshold': 7
        }

        s = Search()
        service_url = urljoin(s.API_HOST['search'], 'places')
        api_res = requests.get(service_url, params=payload)
        res = s.search_places(params_payload=payload)
        assert res.url == api_res.url

    def test_flights_url(self):
        payload = {
            'to': 'LGW',
            'flyFrom': 'PRG',
            'dateFrom': arrow.utcnow().format('DD/MM/YYYY'),
            'dateTo': arrow.utcnow().shift(weeks=+1).format('DD/MM/YYYY'),
            'partner': 'picky',
        }

        s = Search()
        service_url = urljoin(s.API_HOST['search'], 'flights')
        api_res = requests.get(service_url, params=payload)
        res = s.search_flights(params_payload=payload)
        assert res.url == api_res.url


class TestApiResp(object):
    def test_places_info(self):
        schema = {
            'zoomLevelThreshold': {'type': 'integer'},
            'numberOfAirports': {'type': 'integer'},
            'sp_score': {'nullable': True},
            'value': {'type': 'string'},
            'rank': {'type': 'integer'},
            'parentId': {'type': 'string'},
            'lat': {'type': 'number'},
            'lng': {'type': 'number'},
            'type': {'type': 'integer'},
            'id': {'type': 'string'},
            'population': {'type': 'integer'}
        }
        v = cerberus.Validator(schema)
        s = Search()

        res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs')

        v.allow_unknown = True
        assert v.validate(res.json()[0])

    def test_flights_info(self):
        schema = {
            '_results': {'type': 'integer'},
            'all_airlines': {'type': 'list'},
            'all_stopover_airports': {'type': 'list'},
            'connections': {'type': 'list'},
            'currency': {'type': 'string'},
            'currency_rate': {'type': 'number'},
            'data': {'type': 'list'},
            'del': {'nullable': True},
            'ref_tasks': {'type': 'dict'},
            'refresh': {'type': 'list'},
            'search_params': {
                'type': 'dict',
                'schema': {
                    'flyFrom_type': {'type': 'string'},
                    'seats': {
                        'type': 'dict',
                        'schema': {
                            'adults': {'type': 'integer'},
                            'children': {'type': 'integer'},
                            'infants': {'type': 'integer'},
                            'passengers': {'type': 'integer'}
                        }
                    },
                    'to_type': {'type': 'string'}
                }
            },
            'time': {'type': 'number'}
        }

        v = cerberus.Validator(schema)
        s = Search()
        rand_from = randint(10, 50)
        res = s.search_flights(flyFrom='PRG',
                               dateFrom=arrow.utcnow().format('DD/MM/YYYY'),
                               dateTo=arrow.utcnow().shift(days=+rand_from).format('DD/MM/YYYY'),
                               partner='picky')

        v.allow_unknown = True
        assert v.validate(res.json())

    def test_flights_multi_info(self):
        schema = {
            'price': {'type': 'number'},
            'deep_link': {'type': 'string'},
            'booking_token': {'type': 'string'},
            'route': {
                'type': 'list',
                'schema': {
                    'type': 'dict'
                }
            },
        }
        payload = {
            "requests": [
                {
                    "to": "AMS",
                    "flyFrom": "PRG",
                    "directFlights": 0,
                    "dateFrom": arrow.utcnow().shift(days=+randint(0, 5)).format('DD/MM/YYYY'),
                    "dateTo": arrow.utcnow().shift(days=+randint(6, 11)).format('DD/MM/YYYY'),
                },
                {
                    "to": "OSL",
                    "flyFrom": "AMS",
                    "directFlights": 0,
                    "dateFrom": arrow.utcnow().shift(days=+randint(12, 17)).format('DD/MM/YYYY'),
                    "dateTo": arrow.utcnow().shift(days=+randint(18, 23)).format('DD/MM/YYYY'),
                }

            ]
        }

        v = cerberus.Validator(schema)
        s = Search()

        res = s.search_flights_multi(json_data=payload)

        v.allow_unknown = True
        assert v.validate(res.json()[0])
