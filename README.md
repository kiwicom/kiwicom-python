# Kiwi.com wrapper
[Kiwi.com (Skypicker.com)](https://www.kiwi.com) API Wrapper

- For more information read [Kiwi.com documentation](http://docs.skypickerpublicapi.apiary.io)

## Search module:
To use this module, firstly, you should create an a config file `.env` and put it into root directory:

    API_SEARCH='API_SEARCH_HOST'
    API_BOOKING='API_BOOKING_HOST'
Where `API_SEARCH_HOST` and `API_BOOKING_HOST` is Search and Booking API URLs
Then, create an object

    s = Search()
##### Search places:

    res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi')
##### Search flights:

    res = s.search_flights(fly_from='CZ', date_from='26/05/2017', date_to='5/06/2017', partner_market='US')
##### Search flights_multi:
Firstly, you should create payload

    payload = {"requests": [
        {"v": 2, "sort": "duration", "asc": 1, "locale": "en", "daysInDestinationFrom": "", "daysInDestinationTo": "",
         "affilid": "picky", "children": 0, "infants": 0, "flyFrom": "BRQ", "to": "BCN", "featureName": "results",
         "dateFrom": "09/05/2017", "dateTo": "09/06/2017", "typeFlight": "oneway", "returnFrom": "", "returnTo": "",
         "one_per_date": 0, "oneforcity": 0, "wait_for_refresh": 0, "adults": 1},
        {"v": 2, "sort": "duration", "asc": 1, "locale": "en", "daysInDestinationFrom": "", "daysInDestinationTo": "",
         "affilid": "picky", "children": 0, "infants": 0, "flyFrom": "BCN", "to": "ZAG", "featureName": "results",
         "dateFrom": "12/06/2017", "dateTo": "15/06/2017", "typeFlight": "oneway", "returnFrom": "", "returnTo": "",
         "one_per_date": 0, "oneforcity": 0, "wait_for_refresh": 0, "adults": 1}], "limit": 45}

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
