import logging
import sys
import time

import requests
import dicttoxml

# Just for pretty printing
from xml.dom.minidom import parseString
import pprint

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class UnexpectedParameter(KeyError):
    pass


class ExpectedParameter(KeyError):
    pass


class EmptyResponse(Exception):
    pass


class Transport(object):
    """
    Parent class for initialisation
    """
    API_HOST = 'https://api.skypicker.com'
    _FORMATS = ('json', 'xml')
    _TIME_ZONES = ('utc', 'gmt')
    _LOG_FORMATS = ('DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL')

    def __init__(self, log='WARN', log_file='logs.log', time_zone='utc'):
        """
        :param log: 
        :param log_file: 
        :param time_zone: 
        """
        # if response_format.lower() not in self._FORMATS:
        #     raise ValueError(
        #         'Unknown response format: "{}", supported formats are {}'.format(response_format,
        #                                                                          ', '.join(self._FORMATS))
        #     )
        if time_zone.lower() not in self._TIME_ZONES:
            raise ValueError(
                'Unknown time zone: {}, supported time zones are {}'.format(time_zone,
                                                                            ', '.join(self._TIME_ZONES))
            )
        if log.upper() not in self._LOG_FORMATS:
            raise ValueError(
                'Unknown log format: {}, supported log formats are {}'.format(log,
                                                                              ', '.join(self._LOG_FORMATS))
            )
        self.time_settings = time_zone.lower()
        # self.response_format = response_format.lower()
        self.log = getattr(logging, log.upper())
        self.log_file = log_file

    def configure_logger(self, log_level=logging.WARN):
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
        # Setup console logging
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        # Setup file logging
        fh = logging.FileHandler(filename=self.log_file, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def make_request(self, service_url, params, method='get', headers=None, data=None, callback=None):
        """
        :param service_url: 
        :param method: 
        :param headers: 
        :param data: 
        :param callback: 
        :param params: 
        :return: 
        """
        if callback is None:
            callback = self._default_callback

        request = getattr(requests, method.lower())

        log = self.configure_logger(log_level=self.log)
        log.debug('| Request URL: %s' % service_url)
        log.debug('| Request method: %s' % method.upper())
        log.debug('| Request query params: %s' % params)
        log.debug('| Request headers: %s' % headers)

        r = request(service_url, headers=headers, data=data, params=params)
        log.info('| Full Request URL: %s' % r.url)
        try:
            r.raise_for_status()
            return callback(r)
        except Exception as e:
            return self._error_handling(e)

    # @staticmethod
    # def _params_maker(params, extra_keys):
    #     for (key, value) in params.items():
    #         if key == 'bounds':
    #             params[key] = requests.utils.quote(value)
    #     params_path = list(
    #         (key + '=' + value) for (key, value) in params.items()
    #         if key in extra_keys
    #     )
    #     return '?' + '&'.join(params_path)

    # @staticmethod
    # def _parse_response(response, response_format):
    #     if response_format == 'xml':
    #         # response.parsed = etree.fromstring(response.content)
    #         return response
    #     else:
    #         response.parsed = response.json()
    #         return response

    @staticmethod
    def _error_handling():
        pass

    @staticmethod
    def _default_callback(response):
        if not response or not response.content:
            raise EmptyResponse('Response has no content.')
        # parsed_resp = self._parse_response(response, self.response_format)
        return response


class Search(Transport):
    """
    Search Class
    """
    def places(self, **params):
        """
        Get request with params to api.skypicker.com/places
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
        required_params = {}
        for (key, value) in params.items():
            required_params[key] = value
        service_url = "{API_HOST}/places".format(API_HOST=self.API_HOST)
        return self.make_request(service_url, params=required_params)

    def search_flights(self, flyFrom, partner_market, dateFrom, dateTo, partner='picky', **params):
        """  
        :param flyFrom: Skypicker api id of the departure destination. Accepts multiple values separated by comma, 
                these values might be airport codes, city IDs, two letter country codes, 
                metropolitan codes and radiuses. Radius needs to be in form lat-lon-xkm. 
                E.g. -23.24--47.86-500km for places around Sao Paulo, LON - checks every airport in London, 
                LHR - checks flights from London Heathrow, UK - flights from United Kingdom 
                Example: CZ.
                [String]
        :param partner_market: Market from which the request is coming from. 
                Example: us.
                [String]
        :param dateFrom: search flights from this date (dd/mm/YYYY). Use parameters dateFrom and dateTo as a date range 
                for the flight departure. Parameter dateFrom 01/05/2016 and dateTo 30/05/2016 means, 
                that the departure can be anytime between those dates. For the dates of the return flights, 
                use the returnTo&returnFrom or daysInDestinationFrom & daysInDestinationTo parameters 
                Example: 08/08/2017.
                [String]
        :param dateTo: search flights until this date (dd/mm/YYYY) 
                Example: 08/09/2017.
                [String]
        :param partner: partner ID. If present, in the result will be also a link to a specific trip directly 
                to kiwi.com, with the affiliate id included (use picky partner ID for testing) 
                Example: picky.
                [String]
        :param params: all other extra params
        :return: response with JSON or XML content
        """
        required_params = {
            'flyFrom': flyFrom,
            'dateFrom': dateFrom,
            'dateTo': dateTo,
            'partner': partner,
            'partner_market': partner_market
        }
        for (key, value) in params.items():
            required_params[key] = value
        service_url = "{API_HOST}/flights".format(API_HOST=self.API_HOST)
        return self.make_request(service_url, params=required_params)


class Booking(Transport):
    """
    Booking Class
    """
    pass

if __name__ == '__main__':
    s = Search(log='info', log_file='info.log')
    # res = s.places(id='SK', term='br', bounds='lat_lo,lat_hi')
    res1 = s.search_flights(flyFrom='CZ', dateFrom='03/05/2017', dateTo='13/05/2017', partner_market='US')
    # print(parseString(res1).toprettyxml())
    pprint.pprint(res1.json())
