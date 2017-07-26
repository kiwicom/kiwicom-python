# Kiwi.com Python Wrapper
[Kiwi.com](https://www.kiwi.com) API Wrapper

- Search API Documentaiton http://docs.skypickerpublicapi.apiary.io
- Booking API Documentaiton http://docs.skypickerbookingapi1.apiary.io
- Locations API Documentaiton http://docs.locations10.apiary.io/

# Search module:

Create an object

    from kiwicom import kiwi

    s = kiwi.Search()

## search_places:

    res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi')
Also, you can send this parameters in payload:

    payload = {
        'id': 'SK',
        'term': 'br',
        'bounds': 'lat_lo,lat_hi',
        'locale': 'cs',
        'zoomLevelThreshold': 7
    }

    res = s.search_places(**payload)

## search_flights:

    res = s.search_flights(flyFrom='CZ', dateFrom='26/05/2017', dateTo='5/06/2017', partner='picky')
Also, you can send this parameters in payload:

    import arrow

    payload = {
        'flyFrom': 'PRG', # default value is 'PRG'
        'to': 'LGW',
        'dateFrom': arrow.utcnow().format('DD/MM/YYYY'),
        'dateTo': arrow.utcnow().shift(weeks=+3).format('DD/MM/YYYY'),
        'partner': 'picky' # default value is 'picky' use it for testing
    }

    res = s.search_flights(**payload)

You can use `datetime.date` for `dateFrom` and `dateTo` parameters

## search_flights_multi:
Put payload into method

    payload = {
        "requests": [
            {"to": "AMS", "flyFrom": "PRG", "directFlights": 0, "dateFrom": "11/06/2017", "dateTo": "28/06/2017"},
            {"to": "OSL", "flyFrom": "AMS", "directFlights": 0, "dateFrom": "01/07/2017", "dateTo": "11/07/2017"}
        ]}

    res = s.search_flights_multi(json_data=payload)

# Booking module:
    from kiwicom import kiwi

    b = kiwi.Booking()

## check_flights:
    booking_token = s.search_flights(**payload).json()['data'][0]['booking_token']
    check_payload = {
            'v': 2,
            'booking_token': booking_token,
            'pnum': 1,
            'bnum': 0,
            'affily': 'otto_{market}',
            'currency': 'USD',
            'visitor_uniqid': '90a12afc-e240-11e6-bf01-fe55135034f3',
        }

    res = b.check_flights(**check_payload)

## save_booking:
    b.save_booking(json_data=save_book_payload)

## pay_via_zooz
    pay_via_zooz()  # only sandbox mode

## confirm_payment:
    confirm_payment()

# Locations module:

## get_locations:
    get_locations()

---
All methods accept `request_args` as an argument to send some extra parameters to request directly

(For more information about request args read [requests documentation](http://docs.python-requests.org/en/master))

Also all methods accept `headers` as an argument

    headers = {
        'some': 'headers'
    }

    s.search_flights(parms_payload=payload, headers=headers)


# Setup Logger
    l = Logger(log_level='DEBUG', log_file='log.log')

### API WRAPPER IN PROGRESS...
