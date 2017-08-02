from kiwicom import kiwi

import cerberus
import arrow
import requests

import datetime
from datetime import timedelta
from random import randint


class TestDateValidation(object):
    def test_date_formatting(self):
        rand_to = randint(1, 10)
        payload = {
            'dateFrom': datetime.datetime.today(),
            'dateTo': datetime.date.today() + timedelta(days=rand_to),
        }

        p = kiwi.Search()._reformat_date(payload)

        assert isinstance(p, dict)
        assert datetime.datetime.strptime(p['dateFrom'], '%d/%m/%Y')
        assert datetime.datetime.strptime(p['dateTo'], '%d/%m/%Y')


class TestSearchResponse(object):
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
        s = kiwi.Search()

        res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs')

        v.allow_unknown = True
        assert res.status_code == requests.codes.ok
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
        s = kiwi.Search()
        rand_from = randint(10, 50)
        res = s.search_flights(flyFrom='PRG',
                               dateFrom=arrow.utcnow().format('DD/MM/YYYY'),
                               dateTo=arrow.utcnow().shift(days=+rand_from).format('DD/MM/YYYY'),
                               partner='picky')

        v.allow_unknown = True
        assert res.status_code == requests.codes.ok
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
        s = kiwi.Search()

        res = s.search_flights_multi(json_data=payload)

        v.allow_unknown = True
        assert res.status_code == requests.codes.ok
        assert v.validate(res.json()[0])


class TestBookingResponse(object):
    def test_save_booking_info(self):
        s = kiwi.Search()
        b = kiwi.Booking()

        prg_to_lgw = {
            'flyFrom': 'PRG',
            'to': 'LGW',
            'dateFrom': datetime.datetime.today(),
            'dateTo': arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
            'partner': 'picky',
            'typeFlight': 'oneway'
        }
        check_payload = {
            'v': 2,
            'pnum': 1,
            'booking_token': s.search_flights(**prg_to_lgw).json()['data'][0]['booking_token'],
            'bnum': 0,
            'affily': 'otto_{market}',
            'currency': 'USD',
            'visitor_uniqid': '90a12afc-e240-11e6-bf01-fe55135034f3',
        }
        check_resp = b.check_flights(**check_payload).json()
        booking_token = check_resp['booking_token']
        price = check_resp['eur_payment_price']
        save_book_payload = {
            "lang": "en",
            "bags": 0,
            "passengers": [
                {
                    'surname': 'test',
                    'name': 'test dont book',
                    'title': 'mr',
                    'birthday': 631152000,
                    'nationality': 'test',
                    'insurance': 'none',
                    'cardno': None,
                    'expiration': None,
                    'email': 'test@test.com',
                    'phone': '+421902123456'
                }
            ],
            'price': price,
            "currency": "czk",
            'customerLoginID': 'unknown',
            'customerLoginName': 'unknown',
            "booking_token": booking_token,
            "affily": "sp_test",
            'visitor_uniqid': '90a12afc-e240-11e6-bf01-fe55135034f3',
            'payment_gateway': 'zooz',
            'override_duplicate_booking_warning': True,
            'immediate_confirmation': False,
            'use_credits': False,
        }
        booking_response = b.save_booking(json_data=save_book_payload)
        json_response = booking_response.json()
        assert booking_response.status_code == requests.codes.ok
        assert 'success' in json_response['status']
        assert 'zooz_token' in json_response
        assert 'booking_id' in json_response
