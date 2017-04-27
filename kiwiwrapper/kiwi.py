import logging
import sys
import time

import requests

import pprint

from kiwiwrapper import session

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

    """
    @staticmethod
    def _params_maker(params, req_keys, extra_keys=None):
        try:
            params_list = [params.pop(key) for key in req_keys]
        except KeyError as e:
            raise ExpectedParameter('Missing request parameter: '
                                    '{}'.format(e))
        if extra_keys:
            params_list.extend([params.pop(key) for key in params])
        return '&'.join(str(par) for par in params_list)
    """

    @staticmethod
    def _params_maker(params, extra_keys):
        """
        Beta solution
        :param params: 
        :param extra_keys: 
        :return: 
        """
        params_path = ''
        if params:
            for (key, value) in params.items():
                if key not in extra_keys:
                    raise UnexpectedParameter(
                        'Method get wrong parameters: "{}", '.format(key) +
                        'supported parameters are: {}'.format(', '.join(extra_keys))
                    )
                params_part = key + '=' + value
                params_path = params_path + params_part + '&'
            params_path = '?' + params_path[:-1]
        return params_path

    @staticmethod
    def _parse_response(response, response_format):
        if response_format == 'xml':
            response.parsed = etree.fromstring(response.content)
            return response.parsed
        else:
            return response.json()

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
        response = session.get(path, headers=headers)
        return self._parse_response(response, self.response_format)

    def flights(self, **params):
        pass


if __name__ == '__main__':
    s = Search()
#    print(Search._params_maker(pr, rq))
    print(pprint.pformat(s.places(id='SK', term='br', headers={'Accept': 'application/json'})))
