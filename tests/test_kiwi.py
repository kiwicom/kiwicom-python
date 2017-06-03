from kiwiwrapper.kiwi import Search
import cerberus
import arrow
import os


API_HOST = api_host = '{0}'.format(os.environ.get("API_SEARCH"))


class TestUrl(object):
    def test_places_url(self):
        # payload = {
        #     'id': 'SK',
        #     'term': 'br',
        #     'bounds': 'lat_lo,lat_hi',
        #     'locale': 'cs'
        # }
        req_url = '{0}/places?id=SK&term=br&bounds=lat_lo%2Clat_hi&locale=cs'\
            .format(API_HOST)

        s = Search()
        # api_res = requests.get('{0}/places'.format(API_HOST), params=payload)
        res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs')
        assert res.url == req_url

    def test_flights_url(self):
        # payload = {
        #     'flyFrom': 'PRG',
        #     'dateFrom': '01/06/2017',
        #     'dateTo': '01/07/2017',
        #     'partner': 'picky',
        # }
        req_url = '{0}/flights?flyFrom=PRG&dateFrom=01%2F06%2F2017&dateTo=01%2F07%2F2017&partner=picky'\
            .format(API_HOST)

        s = Search()
        # api_res = requests.get('{0}/flights'.format(API_HOST), params=payload)
        res = s.search_flights(flyFrom='PRG',
                               dateFrom='01/06/2017',
                               dateTo='01/07/2017',
                               partner='picky')
        assert res.url == req_url


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
        for item in res.json():
            assert v.validate(item)
            break

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

        res = s.search_flights(flyFrom='PRG',
                               dateFrom=arrow.utcnow().format('DD/MM/YYYY'),
                               dateTo=arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
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

        date_from_1 = arrow.utcnow().format('DD/MM/YYYY')
        date_to_1 = arrow.utcnow().shift(weeks=+1).format('DD/MM/YYYY')
        date_from_2 = arrow.utcnow().shift(weeks=+2).format('DD/MM/YYYY')
        date_to_2 = arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY')
        payload = {
            "requests": [
                {"to": "AMS", "flyFrom": "PRG", "directFlights": 0, "dateFrom": date_from_1, date_to_1: "28/06/2017"},
                {"to": "OSL", "flyFrom": "AMS", "directFlights": 0, "dateFrom": date_from_2, date_to_2: "11/07/2017"}
            ]}
        # payload = {
        #     "requests": [
        #         {
        #             "affilid": "picky",
        #             "flyFrom": "BRQ",
        #             "to": "BCN",
        #             "featureName": "results",
        #             "dateFrom": date_from_1,
        #             "dateTo": date_to_1,
        #             "typeFlight": "oneway",
        #             "adults": 1
        #         },
        #         {
        #
        #             "affilid": "picky",
        #             "flyFrom": "BCN",
        #             "to": "ZAG",
        #             "featureName": "results",
        #             "dateFrom": date_from_2,
        #             "dateTo": date_to_2,
        #             "typeFlight": "oneway",
        #             "adults": 1
        #         }
        #     ],
        # }

        v = cerberus.Validator(schema)
        s = Search()

        res = s.search_flights_multi(json_data=payload)

        v.allow_unknown = True
        for item in res.json():
            assert v.validate(item)
            break
