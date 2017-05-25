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
# Just for pretty printing
from xml.dom.minidom import parseString
import pprint


def configure_logger(log_level='debug', log_file='logs.log'):
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


class ExpectedParameter(KeyError):
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


class Search(Kiwicom):
    """
    Search Class
    """

    def search_places(self, request_args=None, **params):
        """
        Get request with params to api.skypicker.com/places
        :param request_args: 
        :param params: extra parameters: 
        (
            'id',
            'term',
            'locale',
            'zoomLevelThreshold',
            'bounds',
            'v'
        )
        :return: Json of skypicker api ids
        """
        service_url = "{API_HOST}/places".format(API_HOST=self.API_HOSTS[0])
        return self.make_request(service_url,
                                 params=params,
                                 request_args=request_args)

    def search_flights(self, fly_from=None, partner_market=None, date_from=None, date_to=None,
                       partner='picky', request_args=None, **params):
        """  
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
        required_params = {
            'flyFrom': fly_from,
            'dateFrom': date_from,
            'dateTo': date_to,
            'partner': partner,
            'partner_market': partner_market
        }

        service_url = "{API_HOST}/flights".format(API_HOST=self.API_HOSTS[0])
        return self.make_request(service_url,
                                 params=self._params_maker(params=params,
                                                           req_params=required_params),
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
    # configure_logger(log_level='debug')
    s = Search()
    request_args = {
        'headers': {'Content-type': 'application/xml'},
        'cookies': {'cookies_are': 'worked'}
    }
    res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs')
    # res1 = s.search_flights(fly_from='CZ', date_from='26/05/2017', date_to='5/06/2017', partner_market='US')
    prg_to_lgw = {
        'flyFrom': 'PRG',
        'to': 'LGW',
        'dateFrom': '26/05/2017',  # arrow.utcnow().replace(day=10).format('DD/MM/YYYY'),
        'dateTo': '5/06/2017',  # arrow.utcnow().replace(day=20).format('DD/MM/YYYY'),
        'partner': 'picky'
    }
    # res1 = s.search_flights(params=prg_to_lgw)
    v = {"requests": [
        {"v": 2, "sort": "duration", "asc": 1, "locale": "en", "daysInDestinationFrom": "", "daysInDestinationTo": "",
         "affilid": "picky", "children": 0, "infants": 0, "flyFrom": "BRQ", "to": "BCN", "featureName": "results",
         "dateFrom": "09/05/2017", "dateTo": "09/06/2017", "typeFlight": "oneway", "returnFrom": "", "returnTo": "",
         "one_per_date": 0, "oneforcity": 0, "wait_for_refresh": 0, "adults": 1},
        {"v": 2, "sort": "duration", "asc": 1, "locale": "en", "daysInDestinationFrom": "", "daysInDestinationTo": "",
         "affilid": "picky", "children": 0, "infants": 0, "flyFrom": "BCN", "to": "ZAG", "featureName": "results",
         "dateFrom": "12/06/2017", "dateTo": "15/06/2017", "typeFlight": "oneway", "returnFrom": "", "returnTo": "",
         "one_per_date": 0, "oneforcity": 0, "wait_for_refresh": 0, "adults": 1}], "limit": 45}
    # res2 = s.search_flights_multi(json_data=v)
    # print(parseString(res1).toprettyxml())
    # pprint.pprint(res2.json())
    pprint.pprint(res.json())
