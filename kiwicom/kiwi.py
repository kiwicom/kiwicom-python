import logging
import datetime
from urllib.parse import urljoin

from structlog import (
    get_logger, configure,
    processors, stdlib
)
import requests
from pythonjsonlogger import jsonlogger


class UnexpectedParameter(KeyError):
    pass


class EmptyResponse(Exception):
    pass


class Logger(object):
    def __init__(self, log_level='WARNING', log_file='kiwicom_wrap.log'):
        self.log_level = log_level
        self.log_file = log_file
        self.log = self.configure_logger()

    def configure_logger(self):
        lvl = getattr(logging, self.log_level.upper())
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
        handler = logging.FileHandler(filename=self.log_file)
        handler.setFormatter(jsonlogger.JsonFormatter(
            '%(asctime)s %(filename)s %(lineno)d %(message)s'
        ))
        logger = get_logger('kiwiwrap')
        logger.propagate = False
        logger.setLevel(lvl)
        logger.addHandler(handler)
        return logger


class Kiwicom(object):
    """
    Parent class for initialisation
    """
    _TIME_ZONES = 'gmt'
    API_HOST = {
        'search': 'https://api.skypicker.com/',
        'booking': 'https://booking-api.skypicker.com/api/v0.1/',
        'location': 'https://locations.skypicker.com/',
        'zooz_sandbox': 'https://sandbox.zooz.co/mobile/ZooZPaymentAPI/',
        'zooz': 'Need to add'
    }

    def __init__(self, time_zone='gmt', sandbox=True):
        if time_zone.lower() not in self._TIME_ZONES:
            raise ValueError(
                'Unknown time zone: {}, '
                'supported time zones are {}'.format(time_zone, self._TIME_ZONES)
            )
        self.time_zone = time_zone.lower()
        self.sandbox = sandbox
        self.log = get_logger('kiwiwrap')

    def make_request(self, service_url, method='get', data=None,
                     json_data=None, request_args=None, headers=None, **params):

        self.log.debug('Request', URL=service_url, method=method.upper(), params=params, request_args=request_args)

        request = getattr(requests, method.lower())
        try:
            response = request(service_url, params=params, data=data, json=json_data, headers=headers, **request_args)
        except TypeError as err:
            response = request(service_url, params=params, data=data, json=json_data, headers=headers)
            if request_args:
                self.log.warning(err, request_args=request_args)

        try:
            response.raise_for_status()
            return response
        except Exception as e:
            return self._error_handling(response, e)

    def _error_handling(self, response, error):
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
            self.log.error(error)
            return response

    # @staticmethod
    # def _make_request_params(params, req_params):
    #     return {key: value for key, value in req_params.items() if key not in params.keys()}

    @staticmethod
    def _validate_date(dt):
        try:
            datetime.datetime.strptime(str(dt), '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _reformat_date(self, params):
        """
        Reformatting datetime.datetime and YYYY-mm-dd to dd/mm/YYYY
        :param params: takes dict with parameters
        :return: dict with reformatted date
        """
        for (k, v) in params.items():
            if k in ('dateFrom', 'dateTo'):
                if isinstance(v, datetime.date):
                    params[k] = datetime.date.strftime(v, "%d/%m/%Y")
                elif self._validate_date(v):
                    params[k] = datetime.datetime.strptime(v, "%Y-%m-%d")\
                        .strftime("%d/%m/%Y")
        return params


class Search(Kiwicom):
    """
    Search Class
    """
    def search_places(self, headers=None, request_args=None, **params):
        """
        Get request with parameters
        :param headers: headers
        :param request_args: extra args to requests.get
        :param params: parameters for request
        :return: response
        """
        service_url = urljoin(self.API_HOST['search'], 'places')
        return self.make_request(service_url,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)

    def search_flights(self, headers=None, request_args=None, **params):
        """  
        :param headers: headers
        :param request_args: extra args to requests.get
        :param params: parameters for request
        :return: response
        """
        # params.update(self._make_request_params(params, req_params))
        self._reformat_date(params)

        service_url = urljoin(self.API_HOST['search'], 'flights')
        return self.make_request(service_url,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)

    def search_flights_multi(self, json_data=None, data=None, headers=None, request_args=None, **params):
        """
        Sending post request
        :param json_data: takes post data dict
        :param data: takes json formatted data
        :param headers: headres
        :param request_args: extra args to requests.get
        :param params: parameters for request
        :return: response
        """
        if json_data:
            for item in json_data['requests']:
                json_data.update(self._reformat_date(item))
        if data:
            for item in data['requests']:
                data.update(self._reformat_date(item))

        service_url = urljoin(self.API_HOST['search'], 'flights_multi')
        return self.make_request(service_url,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)


class Booking(Kiwicom):
    """
    Booking Class
    """
    def check_flights(self, headers=None, request_args=None, **params):
        service_url = urljoin(self.API_HOST['booking'], 'check_flights')
        return self.make_request(service_url,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)

    def save_booking(self, json_data=None, data=None, headers=None, request_args=None, **params):
        service_url = urljoin(self.API_HOST['booking'], 'save_booking')
        return self.make_request(service_url,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)

    def pay_via_zooz(self, json_data=None, data=None, headers=None, request_args=None, **params):
        service_url = self.API_HOST['zooz_sandbox'] if self.sandbox else self.API_HOST['zooz']
        return self.make_request(service_url,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)

    def confirm_payment(self, json_data=None, data=None, headers=None, request_args=None, *params):
        service_url = urljoin(self.API_HOST['booking'], 'confirm_payment')
        return self.make_request(service_url,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)


class Locations(Kiwicom):
    def get_locations(self, headers=None, request_args=None, **params):
        service_url = self.API_HOST['location']
        return self.make_request(service_url,
                                 headers=headers,
                                 request_args=request_args,
                                 **params)
