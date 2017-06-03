# Kiwi.com wrapper
[Kiwi.com (Skypicker.com)](https://www.kiwi.com) API Wrapper

- For more information read [Kiwi.com documentation](http://docs.skypickerpublicapi.apiary.io)

## Search module:
To use this module, firstly, you should create an a config file `.env` and put it into root directory:

    API_SEARCH='API_SEARCH_HOST'
    API_BOOKING='API_BOOKING_HOST'
Where `API_SEARCH_HOST` and `API_BOOKING_HOST` is Search and Booking API URLs

Then, create an object

    import kiwi

    s = Search()
##### SEARCH PLACES:

    res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi')
Also, you can send this parameters in payload:

    payload = {
        'id': 'SK',
        'term': 'br',
        'bounds': 'lat_lo,lat_hi',
        'locale': 'cs'
    }

    res = s.search_places(params_payload=payload)
##### SEARCH FLIGHTS:

    res = s.search_flights(flyFrom='CZ', dateFrom='26/05/2017', dateTo='5/06/2017', partner='picky')
Also, you can send this parameters in payload:

    import arrow

    payload = {
        'flyFrom': 'PRG',
        'to': 'LGW',
        'dateFrom': arrow.utcnow().format('DD/MM/YYYY'),
        'dateTo': arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
        'partner': 'picky'
    }

    res = s.search_flights(params_payload=payload)


##### SEARCH FLIGHTS MULTI:
Firstly, you should create payload

    payload = {
        "requests": [
            {"to": "AMS", "flyFrom": "PRG", "directFlights": 0, "dateFrom": "11/06/2017", "dateTo": "28/06/2017"},
            {"to": "OSL", "flyFrom": "AMS", "directFlights": 0, "dateFrom": "01/07/2017", "dateTo": "11/07/2017"}
        ]}

Then use it in search_flights_multi method

    res = s.search_flights_multi(json_data=payload)
***
All search methods accept `request_args` as an argument to send some extra parameters to request directly

(For more information about request args read [requests documentation](http://docs.python-requests.org/en/master))

If you want to add some extra params to request like **Headers** you should create some dictionary like:

    request_args = {
        'headers': {'Content-type': 'application/xml'}
    }

And add it to some search method as an argument

    res = s.search_flights_multi(json_data=payload, request_args=request_args)

For parsing use `res.json()`

Also you can configure logger(alpha)

    configure_logger(log_level='debug')

### API WRAPPER IN PROGRESS...
