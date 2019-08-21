import pytest

from . import validate


def test_currency():
    assert validate.currency('bitcoin') is True
    assert validate.currency('bitcoincash') is True
    assert validate.currency('ethereum') is True
    assert validate.currency('litecoin') is True
    with pytest.raises(ValueError):
        validate.currency('othercoin')
    with pytest.raises(ValueError):
        validate.currency('btc')
