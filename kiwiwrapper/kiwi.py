import datetime
import logging
import sys
import os
import io

from structlog import get_logger
from structlog import configure
from structlog import processors
from structlog import stdlib
import requests
from pythonjsonlogger import jsonlogger

import settings


def configure_logger(log_level='DEBUG', log_file='logs.log'):
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

    def __init__(self, time_zone='gmt'):
        """ 
        :param time_zone: 
        """
        if time_zone.lower() not in self._TIME_ZONES:
            raise ValueError(
                'Unknown time zone: {}, '
                'supported time zones are {}'.format(time_zone, self._TIME_ZONES)
            )
        self.time_zone = time_zone.lower()
        self.API_HOSTS = (os.environ.get("API_SEARCH"), os.environ.get("API_BOOKING"))

    def make_request(self, service_url, params, method='get', callback=None,
                     data=None, json_data=None, request_args=None):
        """
        :param request_args: 
        :param json_data:  
        :param service_url: 
        :param method:  
        :param data: 
        :param callback: 
        :param params: 
        :return: 
        """
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
    def _params_maker(params, req_params=None):
        for (key, value) in params.items():
            req_params[key] = value
        return req_params

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

    def _params_checker(self, params, params_payload, service_url, request_args):
        if params and params_payload:
            raise UnexpectedParameter(
                'Params and params_payload were taken, only one can be'
            )
        elif params_payload and not params:
            return self.make_request(service_url,
                                     params=params_payload,
                                     request_args=request_args)
        else:
            return self.make_request(service_url,
                                     params=params,
                                     request_args=request_args)


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
        service_url = "{API_HOST}/places".format(API_HOST=self.API_HOSTS[0])
        return self._params_checker(params=params,
                                    params_payload=params_payload,
                                    service_url=service_url,
                                    request_args=request_args)

    def search_flights(self, request_args=None, params_payload=None, **params):
        """  
        :param params_payload:
        :param request_args:  
        :param fly_from: Skypicker api id of the departure destination. 
                Accepts multiple values separated by comma, 
                these values might be airport codes, city IDs, two letter country codes, 
                metropolitan codes and radiuses. Radius needs to be in form lat-lon-xkm. 
                E.g. -23.24--47.86-500km for places around Sao Paulo, LON - checks every airport in London, 
                LHR - checks flights from London Heathrow, UK - flights from United Kingdom 
                Example: CZ.
                [String]
        :param partner_market: Market from which the request is coming from. 
                Example: us.
                [String]
        :param date_from: search flights from this date (dd/mm/YYYY). 
                Use parameters dateFrom and dateTo as a date range 
                for the flight departure. Parameter dateFrom 01/05/2016 and dateTo 30/05/2016 means, 
                that the departure can be anytime between those dates. For the dates of the return flights, 
                use the returnTo&returnFrom or daysInDestinationFrom & daysInDestinationTo parameters 
                Example: 08/08/2017.
                [String]
        :param date_to: search flights until this date (dd/mm/YYYY) 
                Example: 08/09/2017.
                [String]
        :param partner: partner ID. 
                If present, in the result will be also a link to a specific trip directly 
                to kiwi.com, with the affiliate id included (use picky partner ID for testing) 
                Example: picky.
                [String]
        :param params: all other extra params
        :return: response with JSON or XML content
        """
        service_url = "{API_HOST}/flights".format(API_HOST=self.API_HOSTS[0])
        return self._params_checker(params=params,
                                    params_payload=params_payload,
                                    service_url=service_url,
                                    request_args=request_args)

    def search_flights_multi(self, json_data=None, data=None, request_args=None, **params):
        """
        
        :param request_args: 
        :param json_data: 
        :param data: 
        :param params:
        :required_data: 
        (
            affilid: Your partner ID, for testing use 'picky'
        )
        :return: 
        """
        service_url = "{API_HOST}/flights_multi".format(API_HOST=self.API_HOSTS[0])
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
    def __init__(self, api_key, time_zone='gmt'):
        super().__init__(time_zone)
        self.api_key = api_key


if __name__ == '__main__':
    from pprint import pprint
    import arrow
    s = Search()
    payload = {
        'id': 'SK',
        'term': 'br',
        'bounds': 'lat_lo,lat_hi',
        'locale': 'cs'
    }
    # res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs')
    res = s.search_places(params_payload=payload)
    prg_to_lgw = {
        'flyFrom': 'PRG',
        'to': 'LGW',
        'dateFrom': arrow.utcnow().format('DD/MM/YYYY'),
        'dateTo': arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
        'partner': 'picky'
    }
    # res1 = s.search_flights(flyFrom='PRG', to='LGW', dateFrom=arrow.utcnow().format('DD/MM/YYYY'),
    #                         dateTo=arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'), partner='picky')
    # res1 = s.search_flights(params_payload=prg_to_lgw)
    # pprint(res1.url)

    date_from_1 = arrow.utcnow().format('DD/MM/YYYY')
    date_to_1 = arrow.utcnow().shift(weeks=+1).format('DD/MM/YYYY')
    date_from_2 = arrow.utcnow().shift(weeks=+2).format('DD/MM/YYYY')
    date_to_2 = arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY')
    payload = {
        "requests": [
            {"to": "AMS", "flyFrom": "PRG", "directFlights": 0, "dateFrom": date_from_1, date_to_1: "28/06/2017"},
            {"to": "OSL", "flyFrom": "AMS", "directFlights": 0, "dateFrom": date_from_2, date_to_2: "11/07/2017"}
        ]}
    # res2 = s.search_flights_multi(json_data=payload)
    # pprint(res2.json())
