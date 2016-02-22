# coding: utf-8
import argparse
import logging
import json

import utils


logger = logging.getLogger(__name__)


def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)

    return logger


class Export(object):

    def __init__(self, collection, issns=None, output_file=None):

        self._articlemeta = utils.articlemeta_server()
        self._scielomanager = utils.scielomanager_server()
        self.collection = collection
        self.issns = issns

    def run(self):

        for item in self.items():
            if not item.doi:
                continue
            aid = self._scielomanager.retrieve_aid_from_doi(item.doi)
            if aid:

                logger.debug('AID (%s) found for DOI (%s) and PID (%s)' % (
                    aid,
                    item.doi,
                    item.publisher_id)
                )
                self._articlemeta.client.set_aid(
                    item.publisher_id, item.collection_acronym, aid)

        logger.info('Export finished')

    def items(self):

        extra_filter = json.dumps({"aid": {'$exists': 0}})

        if not self.issns:
            self.issns = [None]

        for issn in self.issns:
            for data in self._articlemeta.documents(
                    collection=self.collection,
                    issn=issn,
                    extra_filter=extra_filter):
                logger.debug('Reading document: %s' % data.publisher_id)
                yield data


def main():

    parser = argparse.ArgumentParser(
        description='Carrega AID de documentos no Article Meta'
    )

    parser.add_argument(
        'issns',
        nargs='*',
        help='ISSN\'s separated by spaces'
    )

    parser.add_argument(
        '--collection',
        '-c',
        help='Collection Acronym'
    )

    parser.add_argument(
        '--logging_file',
        '-o',
        help='Full path to the log file'
    )

    parser.add_argument(
        '--logging_level',
        '-l',
        default='DEBUG',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logggin level'
    )

    args = parser.parse_args()
    _config_logging(args.logging_level, args.logging_file)
    logger.info('Dumping data for: %s' % args.collection)

    issns = None
    if len(args.issns) > 0:
        issns = utils.ckeck_given_issns(args.issns)

    export = Export(args.collection, issns)

    export.run()
