import pytest

from . import validate

def test_currency():
    assert validate.currency('bitcoin') == True
    assert validate.currency('bitcoincash') == True
    assert validate.currency('ethereum') == True
    assert validate.currency('litecoin') == True
    with pytest.raises(ValueError):
        validate.currency('othercoin')
    with pytest.raises(ValueError):
        validate.currency('btc')
