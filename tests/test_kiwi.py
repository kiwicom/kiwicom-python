from pytest import fixture
from kiwiwrapper import Search


@fixture
def place_keys():
    return ['id', 'term', 'locale', 'zoomLevelThreshold', 'bounds', 'v']


def test_places_info(place_keys):
    """
    Test an API call to get a Skypicker api ids
    """
    """
    place_instance = Search('xml')
    response = place_instance.places()

    assert isinstance(response, dict)
    assert set(place_keys).issubset(response.keys())
    """
