from kiwiwrapper import *
import cerberus


def test_places_info():
    """
    Test an API call to get a Skypicker api ids
    """
    schema = {
        'id': {'type': 'string'},
        'lat': {},
        'lng': {},
        'numberOfAirports': {'type': 'integer'},
        'parentId': {},
        'population': {},
        'rank': {},
        'sp_score': {},
        'type': {},
        'value': {},
        'zoomLevelThreshold': {}
    }
    v = cerberus.Validator(schema)

    s = Search()
    res = s.search_places(id='SK', term='br', bounds='lat_lo,lat_hi', locale='cs', limits='5')
    assert v.validate(res.json())
