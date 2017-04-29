import logging
import sys
import time

import requests
import dicttoxml

from xml.dom.minidom import parseString
import pprint

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree


def configure_logger(log_level=logging.WARN):
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    try:
        sa = logging.StreamHandler(stream=sys.stdout)
    except TypeError:
        sa = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    sa.setFormatter(formatter)
    logger.addHandler(sa)
    return logger

log = configure_logger()


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

    def __init__(self, response_format='json', time_zone='utc'):
        """  
        :param response_format: optional, they dont supported xml
        :param time_zone: optional, they have only gmt?
        """
        if response_format.lower() not in self._FORMATS:
            raise ValueError(
                'Unknown response format: "{}", supported formats are {}'.format(response_format,
                                                                                 ', '.join(self._FORMATS))
            )
        if time_zone.lower() not in self._TIME_ZONES:
            raise ValueError(
                'Unknown time zone: {}, supported time zones are {}'.format(time_zone,
                                                                            ', '.join(self._TIME_ZONES))
            )
        self.time_settings = time_zone.lower()
        self.response_format = response_format.lower()

    def places(self, **params):
        """
        Get request with params to api.skypicker.com/places
        :param params: extra parameters = (
            'id',
            'term',
            'locale',
            'zoomLevelThreshold',
            'bounds',
            'v'
        )
        :return: Json of skypicker api ids
        """
        service_url = "{API_HOST}/places".format(API_HOST=self.API_HOST)
        return self.make_request(service_url, **params)

    def make_request(self, service_url, method='get', headers=None, data=None, callback=None, **params):
        if callback is None:
            callback = self._default_callback

        request = getattr(requests, method.lower())

        log.debug('* Request URL: %s' % service_url)
        log.debug('* Request method: %s' % method)
        log.debug('* Request query params: %s' % params)
        log.debug('* Request headers: %s' % headers)

        r = request(service_url, headers=headers, data=data, params=params)
        try:
            r.raise_for_status()
            return callback(r)
        except Exception as e:
            return self._error_handling(e)

    # @staticmethod
    # def _params_maker(params, extra_keys):
    #     """
    #     :param params:
    #     :param extra_keys:
    #     :return:
    #     """
    #     for (key, value) in params.items():
    #         if key == 'bounds':
    #             params[key] = requests.utils.quote(value)
    #     params_path = list(
    #         (key + '=' + value) for (key, value) in params.items()
    #         if key in extra_keys
    #     )
    #     return '?' + '&'.join(params_path)

    @staticmethod
    def _parse_response(response, response_format):
        """
        if response_format == 'xml':
            return dicttoxml.dicttoxml(response.json())
        else:
            return response.json()
        """
        response.parsed = dicttoxml.dicttoxml(response.json()) if response_format == 'xml' else response.json()
        return response

    @staticmethod
    def _error_handling():
        pass

    def _default_callback(self, response):
        if not response or not response.content:
            raise EmptyResponse('Response has no content.')
        parsed_resp = self._parse_response(response, self.response_format)
        return parsed_resp


class Search(Transport):
    """
    Search Class
    """
    def search_flights(self, partner='picky', **params):
        pass


class Booking(Transport):
    """
    Booking Class
    """
    pass

if __name__ == '__main__':
    response_type = 'json'
    s = Transport(response_format=response_type)
    res = s.places(id='SK', term='br', bounds='lat_lo,lat_hi')
    if response_type == 'xml':
        print(parseString(res).toprettyxml())
    else:
        print(pprint.pformat(res))
