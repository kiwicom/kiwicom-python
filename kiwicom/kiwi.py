import logging
import datetime

from structlog import (
    get_logger, configure,
    processors, stdlib
)
import requests
from pythonjsonlogger import jsonlogger


def configure_logger(log_level='WARNING', log_file='kiwicom_wrap.log'):
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
        'search': 'https://api.skypicker.com',
        'booking': 'https://booking-api.skypicker.com/api/v0.1',
        'location': 'https://locations.skypicker.com',
        'zooz_sandbox': 'https://sandbox.zooz.co/mobile/ZooZPaymentAPI',
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

    def make_request(self, service_url, params, method='get', callback=None,
                     data=None, json_data=None, request_args=None, headers=None):
        if callback is None:
            callback = self._default_callback

        log.debug('Request', URL=service_url, method=method.upper(),
                  params=params, request_args=request_args)

        request = getattr(requests, method.lower())
        try:
            r = request(service_url, params=params, data=data, json=json_data,
                        headers=headers, **request_args)
        except TypeError as err:
            r = request(service_url, params=params, data=data, json=json_data,
                        headers=headers)
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

    def _validate_params(self, service_url, params, params_payload,
                         request_args, headers):
        if params and params_payload:
            raise UnexpectedParameter(
                'Params and params_payload were taken, only one can be'
            )
        else:
            return self.make_request(service_url,
                                     params=params or params_payload,
                                     headers=headers,
                                     request_args=request_args)

    @staticmethod
    def _default_params(params, req_params):
        for (key, value) in req_params.items():
            if key not in params:
                params[key] = value
        return params

    @staticmethod
    def _validate_date(dt):
        try:
            datetime.datetime.strptime(str(dt), '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _reformat_date(self, params):
        # Need to correct
        if 'requests' in params.keys():
            for item in params['requests']:
                for (k, v) in item.items():
                    if k in ('dateFrom', 'dateTo'):
                        if isinstance(v, datetime.date):
                            item[k] = datetime.date.strftime(v, "%d/%m/%Y")
                        elif self._validate_date(v):
                            item[k] = datetime.datetime.strptime(v, "%Y-%m-%d")\
                                .strftime("%d/%m/%Y")
        else:
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
    def search_places(self, params_payload=None, headers=None,
                      request_args=None, **params):
        """
        Get request with parameters
        :param headers: headers
        :param request_args: extra args to requests.get
        :param params: parameters for request
        :param params_payload: takes payload with params for request
        :return: response
        """
        service_url = "{}/places".format(self.API_HOST['search'])
        return self._validate_params(service_url,
                                     params=params,
                                     params_payload=params_payload,
                                     headers=headers,
                                     request_args=request_args)

    def search_flights(self, params_payload=None, headers=None,
                       request_args=None, **params):
        """  
        :param headers: headers
        :param params_payload: takes payload with params for request
        :param request_args: extra args to requests.get
        :param params: parameters for request
        :return: response
        """
        # rand_from = randint(10, 50)
        # a = arrow.utcnow().shift(days=+rand_from).format('DD/MM/YYYY')
        # req_params = {
        #     'flyFrom': 'PRG',
        #     'dateFrom': a,
        # }
        if params:
            self._reformat_date(params)
        elif params_payload:
            self._reformat_date(params_payload)
        # else:
        #     params = {}
        #     params.update(req_params)

        service_url = "{}/flights".format(self.API_HOST['search'])
        return self._validate_params(service_url,
                                     params_payload=params_payload,
                                     params=params,
                                     headers=headers,
                                     request_args=request_args)

    def search_flights_multi(self, json_data=None, data=None,
                             headers=None, request_args=None, **params):
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
            json_data.update(self._reformat_date(json_data))
        if data:
            data.update(self._reformat_date(data))

        service_url = "{}/flights_multi".format(self.API_HOST['search'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args)


class Booking(Kiwicom):
    """
    Booking Class
    """
    def check_flights(self, params_payload=None, headers=None,
                      request_args=None, **params):
        service_url = "{}/check_flights".format(self.API_HOST['booking'])
        return self._validate_params(service_url,
                                     params_payload=params_payload,
                                     headers=headers,
                                     params=params,
                                     request_args=request_args)

    def save_booking(self, json_data=None, data=None, headers=None,
                     request_args=None, **params):
        service_url = "{}/save_booking".format(self.API_HOST['booking'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args)

    def pay_via_zooz(self, json_data=None, data=None, headers=None,
                     request_args=None, **params):
        service_url = self.API_HOST['zooz_sandbox'] if self.sandbox else self.API_HOST['zooz']
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args)

    def confirm_payment(self, json_data=None, data=None, headers=None,
                        request_args=None, *params):
        service_url = "{}/confirm_payment".format(self.API_HOST['booking'])
        return self.make_request(service_url,
                                 params=params,
                                 method='post',
                                 json_data=json_data,
                                 data=data,
                                 headers=headers,
                                 request_args=request_args)


class Location(Kiwicom):
    def get_location(self, params_payload=None, headers=None,
                     request_args=None, **params):
        service_url = self.API_HOST['location']
        return self._validate_params(service_url,
                                     params_payload=params_payload,
                                     headers=headers,
                                     request_args=request_args,
                                     params=params)
