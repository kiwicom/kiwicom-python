import logging
import os
import datetime

from structlog import get_logger
from structlog import configure
from structlog import processors
from structlog import stdlib
import requests
from pythonjsonlogger import jsonlogger
import arrow

import settings


def configure_logger(log_level='WARNING', log_file='logs.log'):
    lvl = getattr(logging, log_level.upper())
    configure(
        processors=[
            stdlib.filter_by_level,
            stdlib.add_logger_name,
            stdlib.add_log_level,
            stdlib.PositionalArgumentsFormatter(),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=stdlib.LoggerFactory(),
        wrapper_class=stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    handler = logging.FileHandler(filename=log_file)
    handler.setFormatter(jsonlogger.JsonFormatter(
        '%(asctime)s %(filename)s %(lineno)d %(message)s'
    ))
    logger = get_logger(__name__)
    logger.setLevel(lvl)
    logger.addHandler(handler)
    return logger


log = configure_logger()


class UnexpectedParameter(KeyError):
    pass


class EmptyResponse(Exception):
    pass


class Kiwicom(object):
    """
    Parent class for initialisation
    """
    _TIME_ZONES = 'gmt'
    API_HOST = {
        'search': os.environ.get('API_SEARCH'),
        'booking': '{0}/api/v0.1'.format(os.environ.get('API_BOOKING')),
    }

    def __init__(self, time_zone='gmt'):
        if time_zone.lower() not in self._TIME_ZONES:
            raise ValueError(
                'Unknown time zone: {}, '
                'supported time zones are {}'.format(time_zone, self._TIME_ZONES)
            )
        self.time_zone = time_zone.lower()

    def make_request(self, service_url, params, method='get', callback=None,
                     data=None, json_data=None, request_args=None):
        if callback is None:
            callback = self._default_callback

        log.debug('Request', URL=service_url, method=method.upper(),
                  params=params, request_args=request_args)

        request = getattr(requests, method.lower())
        try:
            r = request(service_url, params=params, data=data, json=json_data, **request_args)
        except TypeError as err:
            r = request(service_url, params=params, data=data, json=json_data)
            if request_args is not None:
                log.warning(err)

        try:
            r.raise_for_status()
            return callback(r)
        except Exception as e:
            return self._error_handling(r, e)

    @staticmethod
    def _error_handling(response, error):
        if isinstance(error, requests.HTTPError):
            if response.status_code == 400:
                error = requests.HTTPError(
                    '%s: Request parameters were rejected by the server'
                    % error, response=response
                )
            elif response.status_code == 429:
                error = requests.HTTPError(
                    '%s: Too many requests in the last minute'
                    % error, response=response
                )
            raise error
        else:
            log.error(error)
            return response

    @staticmethod
    def _default_callback(response):
        if not response or not response.content:
            raise EmptyResponse('Response has no content.')
        return response

    def _validate_params(self, params, params_payload, service_url, request_args):
        if params and params_payload:
            raise UnexpectedParameter(
                'Params and params_payload were taken, only one can be'
            )
        else:
            return self.make_request(service_url,
                                     params=params or params_payload,
                                     request_args=request_args)

    # @staticmethod
    # def _default_params(params, **req_params):
    #     # if params_payload:
    #     #     params_dict = params_payload.copy()
    #     # else:
    #     #     params_dict = params.copy()
    #
    #     for (key, value) in req_params.items():
    #         # if key not in (params or params_payload):
    #         if key not in params:
    #             params[key] = value
    #     return params

    @staticmethod
    def _validate_date(date):
        try:
            datetime.datetime.strptime(str(date), '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _reformat_date(self, params):
        for (key, value) in params.items():

            if key == ('dateFrom' or 'dateTo'):
                dtemp = params[key]
                if isinstance(params[key], datetime.date):
                    params[key] = datetime.date.strftime(dtemp, "%d/%m/%Y")
                if self._validate_date(dtemp) and isinstance(dtemp, str):
                    a = arrow.get(dtemp, 'YYYY-MM-DD').date()
                    params[key] = datetime.date.strftime(a, "%d/%m/%Y")

            if key == 'requests':
                for item in params['requests']:
                    for (k, v) in item.items():
                        if k == ('dateFrom' or 'dateTo'):
                            dtemp = item[k]
                            if isinstance(item[k], datetime.date):
                                item[k] = datetime.date.strftime(dtemp, "%d/%m/%Y")
                            if self._validate_date(dtemp) and isinstance(dtemp, str):
                                a = arrow.get(dtemp, 'YYYY-MM-DD').date()
                                item[k] = datetime.date.strftime(a, "%d/%m/%Y")
        return params


class Search(Kiwicom):
    """
    Search Class
    """
    def search_places(self, params_payload=None, request_args=None, **params):
        """
        Get request with parameters
        :param request_args: extra args to requests.get
        :param params: extra parameters: 
        (
            'id',
            'term',
            'locale',
            'zoomLevelThreshold',
            'bounds',
            'v'
        )
        :param params_payload: takes payload with params
        :return: Json of skypicker api ids
        """
        # if params and 'zoom_level_threshold' in params:
        #     v = params.pop('zoom_level_threshold')
        #     new_dict = {'zoomLevelThreshold': v}
        #     params.update(new_dict)
        # if params_payload and 'zoom_level_threshold' in params_payload:
        #     v = params_payload.pop('zoom_level_threshold')
        #     new_dict = {'zoomLevelThreshold': v}
        #     params_payload.update(new_dict)

        service_url = "{API_HOST}/places".format(API_HOST=self.API_HOST['search'])
        return self._validate_params(params=params,
                                     params_payload=params_payload,
                                     service_url=service_url,
                                     request_args=request_args)

    def search_flights(self, params_payload=None, request_args=None, **params):
        """  
        :param params_payload:
        :param request_args:
        :param params: all other extra params
        :return: response with JSON or XML content
        """
        if params:
            params.update(self._reformat_date(params))
        if params_payload:
            params_payload.update(self._reformat_date(params_payload))

        service_url = "{API_HOST}/flights".format(API_HOST=self.API_HOST['search'])
        return self._validate_params(params=params,
                                     params_payload=params_payload,
                                     service_url=service_url,
                                     request_args=request_args)

    def search_flights_multi(self, json_data=None, data=None, request_args=None, **params):
        if json_data:
            json_data.update(self._reformat_date(json_data))
        if data:
            data.update(self._reformat_date(data))

        service_url = "{API_HOST}/flights_multi".format(API_HOST=self.API_HOST['search'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 request_args=request_args)


class Booking(Kiwicom):
    """
    Booking Class
    """
    def check_flights(self, params_payload=None, request_args=None, **params):
        # p, pp = self._default_params(params,
        #                              params_payload,
        #                              v=2,
        #                              affily='otto_{market}')
        # if params:
        #     params.update(p)
        # if params_payload:
        #     params_payload.update(pp)

        service_url = "{API_HOST}/check_flights".format(API_HOST=self.API_HOST['booking'])
        return self._validate_params(params=params,
                                     params_payload=params_payload,
                                     service_url=service_url,
                                     request_args=request_args)

    def save_booking(self, json_data=None, data=None, request_args=None, **params):
        service_url = "{API_HOST}/save_booking".format(API_HOST=self.API_HOST['booking'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 request_args=request_args)

    def confirm_payment(self, json_data=None, data=None, request_args=None, *params):
        service_url = "{API_HOST}/confirm_payment".format(API_HOST=self.API_HOST['booking'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 request_args=request_args)


if __name__ == '__main__':
    from pprint import pprint

    logging.basicConfig(level='DEBUG')

    s = Search()
    payload_place = {
        'id': 'SK',
        'term': 'br',
        'bounds': 'lat_lo,lat_hi',
        'locale': 'cs',
        'zoom_level_threshold': 7
    }
    payload_flights = {
        'flyFrom': 'LGW',
        'to': 'PRG',
        'dateFrom': arrow.utcnow().format('DD/MM/YYYY'),
        'dateTo': arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
        'partner': 'picky'
    }
    prg_to_lgw = {
        'flyFrom': 'PRG',
        'to': 'LGW',
        'dateFrom': '13/07/2017',
        'dateTo': '19/07/2017',
        'partner': 'picky'
    }
    payload_flights_multi = {
        "requests": [
            {
                "to": "AMS",
                "flyFrom": "PRG",
                "directFlights": 0,
                "dateFrom": datetime.date.today(),
                "dateTo": arrow.utcnow().shift(weeks=+1).format('DD/MM/YYYY'),
            },
            {
                "to": "OSL",
                "flyFrom": "AMS",
                "directFlights": 0,
                "dateFrom": arrow.utcnow().shift(weeks=+2).format('DD/MM/YYYY'),
                "dateTo": arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
            }

        ]
    }

    # pprint(s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs', zoom_level_threshold=7).url)
    # pprint(s.search_places(params_payload=payload).url)

    d = str(datetime.date(2017, 7, 11))
    pprint(s.search_flights(to='LGW', dateFrom=datetime.date.today()))
    pprint(s.search_flights(to='LGW', dateFrom='2017-06-18'))
    pprint(s.search_flights(to='LGW'))
    pprint(s.search_flights(params_payload=payload_flights))

    pprint(s.search_flights_multi(json_data=payload_flights_multi))

    b = Booking()
    check_payload = {
        'v': 2,
        'booking_token': s.search_flights(params_payload=prg_to_lgw).json()['data'][0]['booking_token'],
        'pnum': 1,
        'bnum': 0,
        'affily': 'otto_{market}',
        'currency': 'USD',
        'visitor_uniqid': '90a12afc-e240-11e6-bf01-fe55135034f3',
    }
    save_book_payload = {
        "lang": "en",
        "bags": 0,
        "passengers": [
            {
                'surname': 'test',
                'name': 'test dont book',
                'title': 'mr',
                'birthday': 631152000,
                'nationality': 'cz',
                'insurance': 'none',
                'cardno': None,
                'expiration': None,
                'email': 'test@skypicker.com',
                'phone': '+421902123456'
            }
        ],
        'price': 00.0,
        "currency": "czk",
        'customerLoginID': 'unknown',
        'customerLoginName': 'unknown',
        "booking_token": b.check_flights(params_payload=check_payload).json()['booking_token'],
        "affily": "sp_test",
        'visitor_uniqid': '90a12afc-e240-11e6-bf01-fe55135034f3',
        'payment_gateway': 'zooz',
        'override_duplicate_booking_warning': True,
        'immediate_confirmation': False,
        'use_credits': False,
    }

    # pprint(b.check_flights(params_payload=check_payload).json())
    # pprint(b.save_booking(json_data=save_book_payload).json())
