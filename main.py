#!/usr/bin/env python
"""
https://github.com/jantman/prometheus-security-spy-exporter

MIT License

Copyright (c) 2023 Jason Antman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import os
import argparse
import logging
import socket
from typing import Generator, Dict, Optional

import requests
import xmltodict
from wsgiref.simple_server import make_server, WSGIServer
from prometheus_client.core import REGISTRY, GaugeMetricFamily, Metric
from prometheus_client.exposition import make_wsgi_app, _SilentHandler
from prometheus_client.samples import Sample

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


class LabeledGaugeMetricFamily(Metric):
    """Not sure why the upstream one doesn't allow labels..."""

    def __init__(
        self,
        name: str,
        documentation: str,
        value: Optional[float] = None,
        labels: Dict[str, str] = None,
        unit: str = '',
    ):
        Metric.__init__(self, name, documentation, 'gauge', unit)
        if labels is None:
            labels = {}
        self._labels = labels
        if value is not None:
            self.add_metric(labels, value)

    def add_metric(self, labels: Dict[str, str], value: float) -> None:
        """Add a metric to the metric family.
        Args:
          labels: A dictionary of labels
          value: A float
        """
        self.samples.append(
            Sample(self.name, dict(labels | self._labels), value, None)
        )


class WeatherGooseCollector:

    def _env_or_err(self, name: str) -> str:
        s: str = os.environ.get(name)
        if not s:
            raise RuntimeError(
                f'ERROR: You must set the "{name}" environment variable.'
            )
        return s

    def __init__(self):
        logger.debug('Instantiating WeatherGooseCollector')
        self.url: str = self._env_or_err('WEATHERGOOSE_XML_URL')

    def _get_data(self) -> dict:
        r = requests.get(self.url)
        r.raise_for_status()
        return xmltodict.parse(r.content)

    def collect(self) -> Generator[Metric, None, None]:
        sysinfo: dict = self._get_data()
        for field in sysinfo['server']['devices']['device']['field']:
            yield GaugeMetricFamily(
                f'weathergoose_{field["@key"]}', field["@key"],
                value=float(field['@value'])
            )


def _get_best_family(address, port):
    """
    Automatically select address family depending on address
    copied from prometheus_client.exposition.start_http_server
    """
    # HTTPServer defaults to AF_INET, which will not start properly if
    # binding an ipv6 address is requested.
    # This function is based on what upstream python did for http.server
    # in https://github.com/python/cpython/pull/11767
    infos = socket.getaddrinfo(address, port)
    family, _, _, _, sockaddr = next(iter(infos))
    return family, sockaddr[0]


def serve_exporter(port: int, addr: str = '0.0.0.0'):
    """
    Copied from prometheus_client.exposition.start_http_server, but doesn't run
    in a thread because we're just a proxy.
    """

    class TmpServer(WSGIServer):
        """Copy of WSGIServer to update address_family locally"""

    TmpServer.address_family, addr = _get_best_family(addr, port)
    app = make_wsgi_app(REGISTRY)
    httpd = make_server(
        addr, port, app, TmpServer, handler_class=_SilentHandler
    )
    httpd.serve_forever()


def parse_args(argv):
    p = argparse.ArgumentParser(description='Prometheus WeatherGoose exporter')
    p.add_argument(
        '-v', '--verbose', dest='verbose', action='count', default=0,
        help='verbose output. specify twice for debug-level output.'
    )
    PORT_DEF = int(os.environ.get('PORT', '8080'))
    p.add_argument(
        '-p', '--port', dest='port', action='store', type=int,
        default=PORT_DEF, help=f'Port to listen on (default: {PORT_DEF})'
    )
    args = p.parse_args(argv)
    return args


def set_log_info():
    set_log_level_format(
        logging.INFO, '%(asctime)s %(levelname)s:%(name)s:%(message)s'
    )


def set_log_debug():
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level: int, format: str):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()
    REGISTRY.register(WeatherGooseCollector())
    logger.info('Starting HTTP server on port %d', args.port)
    serve_exporter(args.port)
