#!/usr/bin/python3

__version__ = '0.0.2'

# API documentation: https://www.privcoin.io/api/

import logging
from time import sleep

import aaargh
import requests
import pyqrcode

from . import validate


DEFAULT_ENDPOINT = 'https://www.privcoin.io'
# Tor endpoint
# DEFAULT_ENDPOINT = 'http://tr5ods7ncr6eznny.onion'

DEFAULT_AFFILIATE = 'b69f11b'
DEFAULT_FEE = 2.5
DEFAULT_RETRY = False
DEFAULT_DELAY = 1

cli = aaargh.App()


def api_request(url, json_params=None, get_params=None, retry=False):
    try:
        if json_params is None:
            request = requests.get(url, params=get_params, timeout=30)
        else:
            request = requests.post(url, json=json_params, timeout=30)
    except Exception as e:
        if retry is True:
            logging.warning('Got an error, but retrying: {}'.format(e))
            sleep(5)
            # Try again.
            return api_request(url,
                               json_params=json_params,
                               get_params=get_params,
                               retry=retry)
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
                               json_params=json_params,
                               get_params=get_params,
                               retry=retry)
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
    letter = letter_of_guarantee(output['bitcode'])
    msg = '{}\n{}\nMinimum: {} Maximum: {} Bitcode: {}\n{}'
    terminal_output = msg.format(qr,
                                 uri,
                                 output['minamount'],
                                 output['maxamount'],
                                 output['bitcode'],
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
    return output


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
