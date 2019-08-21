#!/usr/bin/python3

__version__ = '0.0.4'

# API documentation: https://www.privcoin.io/api/

import logging
from time import sleep
from random import randint

import aaargh
import requests
import pyqrcode

from . import validate


CLEARNET_ENDPOINT = 'https://www.privcoin.io'
TOR_ENDPOINT = 'http://tr5ods7ncr6eznny.onion'

DEFAULT_ENDPOINT = TOR_ENDPOINT

# Sets a random fee between 2.1 and 2.9.
DEFAULT_FEE = float('2.{}'.format(randint(1, 9)))
DEFAULT_AFFILIATE = 'b69f11b'
DEFAULT_DELAY = 1
DEFAULT_RETRY = False
DEFAULT_TIMEOUT = 60

cli = aaargh.App()

USE_TOR_PROXY = 'auto'
TOR_PROXY = 'socks5h://127.0.0.1:9050'
# For requests module
TOR_PROXY_REQUESTS = {'http': TOR_PROXY, 'https': TOR_PROXY}

cli = aaargh.App()

logging.basicConfig(level=logging.WARNING)


def validate_use_tor_proxy(use_tor_proxy):
    if isinstance(use_tor_proxy, bool):
        return True
    if isinstance(use_tor_proxy, str):
        if use_tor_proxy == 'auto':
            return True

    raise ValueError('use_tor_proxy must be True, False, or "auto"')


def is_onion_url(url):
    """
    returns True/False depending on if a URL looks like a Tor hidden service
    (.onion) or not.
    This is designed to false as non-onion just to be on the safe-ish side,
    depending on your view point. It requires URLs like: http://domain.tld/,
    not http://domain.tld or domain.tld/.

    This can be optimized a lot.
    """
    try:
        url_parts = url.split('/')
        domain = url_parts[2]
        tld = domain.split('.')[-1]
        if tld == 'onion':
            return True
    except Exception:
        pass
    return False


def api_request(url,
                get_params=None,
                retry=DEFAULT_RETRY,
                timeout=DEFAULT_TIMEOUT,
                use_tor_proxy=USE_TOR_PROXY):
    validate_use_tor_proxy(use_tor_proxy)
    proxies = {}
    if use_tor_proxy is True:
        proxies = TOR_PROXY_REQUESTS
    elif use_tor_proxy == 'auto':
        if is_onion_url(url) is True:
            msg = 'use_tor_proxy is "auto" and we have a .onion url, '
            msg += 'using local Tor SOCKS proxy.'
            logging.debug(msg)
            proxies = TOR_PROXY_REQUESTS

    try:
        request = requests.get(url,
                               params=get_params,
                               timeout=timeout,
                               proxies=proxies)
    except Exception as e:
        if retry is True:
            logging.warning('Got an error, but retrying: {}'.format(e))
            sleep(5)
            # Try again.
            return api_request(url,
                               get_params=get_params,
                               retry=retry,
                               use_tor_proxy=use_tor_proxy)
        else:
            raise

    status_code_first_digit = request.status_code // 100
    if status_code_first_digit == 2:
        try:
            request_dict = request.json()
            return request_dict
        except Exception:
            return request.content
    elif status_code_first_digit == 4:
        raise ValueError(request.content)
    elif status_code_first_digit == 5:
        if retry is True:
            logging.warning(request.content)
            logging.warning('Got a 500, retrying in 5 seconds...')
            sleep(5)
            # Try again if we get a 500
            return api_request(url,
                               get_params=get_params,
                               retry=retry,
                               use_tor_proxy=use_tor_proxy)
        else:
            raise Exception(request.content)
    else:
        # Not sure why we'd get this.
        request.raise_for_status()
        raise Exception('Stuff broke strangely.')


@cli.cmd(name='mix')
@cli.cmd_arg('--currency', type=str, required=True)
@cli.cmd_arg('--output_address', type=str, required=True)
@cli.cmd_arg('--endpoint', type=str, default=DEFAULT_ENDPOINT)
def _mix_terminal(currency, output_address, endpoint=DEFAULT_ENDPOINT):
    output = mix(currency=currency,
                 output_address=output_address,
                 endpoint=endpoint)
    uri = '{}:{}'.format(currency, output['address'])
    qr = pyqrcode.create(uri).terminal(module_color='black',
                                       background='white',
                                       quiet_zone=1)
    letter = letter_of_guarantee(output['id'], endpoint=endpoint)
    msg = '{}\n{}\nMinimum: {} Maximum: {} Bitcode: {}\n{}'
    terminal_output = msg.format(qr,
                                 uri,
                                 output['minimum'],
                                 output['maximum'],
                                 output['id'],
                                 letter)
    return terminal_output


def mix(currency,
        output_address,
        endpoint=DEFAULT_ENDPOINT,
        fee=DEFAULT_FEE,
        affiliate=DEFAULT_AFFILIATE,
        delay=DEFAULT_DELAY,
        retry=DEFAULT_RETRY):
    """
    currency must be one of: bitcoin, bitcoincash, ethereum, litecoin
    output_address is destination for mixed coins.
    affiliate is None or string.

    Output is a dict containing id, address, minimum, and maximum.
    """
    validate.currency(currency)

    get_params = {'addr1': output_address,
                  'pr1': 100,
                  'time1': delay,
                  'fee': fee,
                  'affiliate': affiliate}

    base_url = '{}/{}/api/'.format(endpoint, currency)
    url = '{}/api/'.format(base_url)
    output = api_request(url=url, get_params=get_params, retry=retry)
    if not isinstance(output, dict):
        raise ValueError(output)
    if 'status' not in output:
        logging.debug(output)
        raise ValueError('status not in JSON output from privcoin?')
    if output['status'] != 'success':
        raise ValueError(output['message'])
    output_dict = {'id': output['bitcode'],
                   'address': output['address'],
                   'minimum': output['minamount'],
                   'maximum': output['maxamount']}
    return output_dict


@cli.cmd
@cli.cmd_arg('bitcode', type=str)
@cli.cmd_arg('--endpoint', type=str, default=DEFAULT_ENDPOINT)
def check(bitcode,
          endpoint=DEFAULT_ENDPOINT,
          retry=DEFAULT_RETRY):
    """
    Checks status of a mix.
    """
    url = '{}/status/'.format(endpoint)
    get_params = {'id': bitcode}
    output = api_request(url, get_params=get_params)
    return output


@cli.cmd
@cli.cmd_arg('bitcode', type=str)
@cli.cmd_arg('--endpoint', type=str, default=DEFAULT_ENDPOINT)
def letter_of_guarantee(bitcode,
                        endpoint=DEFAULT_ENDPOINT,
                        retry=DEFAULT_RETRY):
    """
    Checks status of a mix.
    """
    url = '{}/signature/'.format(endpoint)
    get_params = {'id': bitcode,
                  'api': True}
    output = api_request(url, get_params=get_params)
    return output


def main():
    output = cli.run()
    if output is True:
        exit(0)
    elif output is False:
        exit(1)
    else:
        print(output)
        exit(0)


if __name__ == '__main__':
    main
