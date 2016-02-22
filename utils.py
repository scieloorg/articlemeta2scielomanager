# coding: utf-8
import os
import re
import logging
import weakref
from ConfigParser import ConfigParser

from thrift import clients


logger = logging.getLogger(__name__)


REGEX_ISSN = re.compile(r"^[0-9]{4}-[0-9]{3}[0-9xX]$")


class SingletonMixin(object):
    """
    Adds a singleton behaviour to an existing class.
    weakrefs are used in order to keep a low memory footprint.
    As a result, args and kwargs passed to classes initializers
    must be of weakly refereable types.
    """
    _instances = weakref.WeakValueDictionary()

    def __new__(cls, *args, **kwargs):
        key = (cls, args, tuple(kwargs.items()))

        if key in cls._instances:
            return cls._instances[key]

        try:
            new_instance = super(type(cls), cls).__new__(cls, *args, **kwargs)
        except TypeError:
            new_instance = super(type(cls), cls).__new__(cls, **kwargs)

        cls._instances[key] = new_instance

        return new_instance


class Configuration(SingletonMixin):
    """
    Acts as a proxy to the ConfigParser module
    """
    def __init__(self, fp, parser_dep=ConfigParser):
        self.conf = parser_dep()

        try:
            self.conf.read_file(fp)
        except AttributeError:
            self.conf.readfp(fp)

    @classmethod
    def from_env(cls):
        try:
            filepath = os.environ['ARTICLEMETA2SCIELOMANAGER_SETTINGS_FILE']
        except KeyError:
            raise ValueError('missing env variable ARTICLEMETA2SCIELOMANAGER_SETTINGS_FILE')

        return cls.from_file(filepath)

    @classmethod
    def from_file(cls, filepath):
        """
        Returns an instance of Configuration
        ``filepath`` is a text string.
        """
        fp = open(filepath, 'r')

        return cls(fp)

    def __getattr__(self, attr):
        return getattr(self.conf, attr)

    def items(self):
        """Settings as key-value pair.
        """
        return [(section, dict(self.conf.items(section, raw=True))) for \
            section in [section for section in self.conf.sections()]]


config = Configuration.from_env()
settings = dict(config.items())


def ckeck_given_issns(issns):
    valid_issns = []

    for issn in issns:
        if not REGEX_ISSN.match(issn):
            continue
        valid_issns.append(issn)

    return valid_issns


def articlemeta_server():
    try:
        server = settings['app:main']['articlemeta_thriftserver'].split(':')
        host = server[0]
        port = int(server[1])
    except:
        logger.warning('Error defining Article Meta thrift server, assuming default server articlemeta.scielo.org:11720')
        host = 'articlemeta.scielo.org'
        port = 11720

    return clients.ArticleMeta(host, port)


def scielomanager_server():
    try:
        server = settings['app:main']['scielomanager_thriftserver'].split(':')
        host = server[0]
        port = int(server[1])
    except:
        logger.warning('Error defining SciELO Managerthrift server, assuming default server manager.scielo.org:11720')
        host = 'scielomanager.scielo.org'
        port = 11720

    return clients.ScieloManager(host, port)