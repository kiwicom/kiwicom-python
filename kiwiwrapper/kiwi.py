import logging
import sys
import time

import requests
import dicttoxml

from kiwiwrapper import session

from xml.dom.minidom import parseString
import pprint

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree


def logger():
    pass


class UnexpectedParameter(KeyError):
    pass


class ExpectedParameter(KeyError):
    pass


class Search(object):
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

    @staticmethod
    def _params_maker(params, extra_keys):
        """
        :param params: 
        :param extra_keys: 
        :return: 
        """
        for (key, value) in params.items():
            if key == 'bounds':
                params[key] = requests.utils.quote(value)
        params_path = list(
            (key + '=' + value) for (key, value) in params.items()
            if key in extra_keys
        )
        return '?' + '&'.join(params_path)

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

    def places(self, headers=None, **params):
        """
        Get request with params to api.skypicker.com/places
        :param headers: headers={'x-test': 'true'}
        :param params: extra parameters
        :return: Json of skypicker api ids
        """
        extra_keys = (
            'id',
            'term',
            'locale',
            'zoomLevelThreshold',
            'bounds',
            'v'
        )
        path = '{api_host}/places{params_path}'.format(api_host=self.API_HOST,
                                                       params_path=self._params_maker(params, extra_keys))
        print(path)
        response = session.get(path, headers=headers)
        return self._parse_response(response, self.response_format)

    def search_flights(self, partner='picky', **params):
        pass
        # if self.response_format == 'xml'
        #     params[xml] = 1

if __name__ == '__main__':
    response_type = 'json'
    s = Search(response_format=response_type)
    res = s.places(id='SK', term='br', bounds='lat_lo,lat_hi')
    if response_type == 'xml':
        print(parseString(res.parsed).toprettyxml())
    else:
        print(pprint.pformat(res.json()))
