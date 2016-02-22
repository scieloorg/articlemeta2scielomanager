# coding: utf-8
import os
import argparse
import logging
import time
import json
import codecs
from io import StringIO

import lxml
import packtools
from packtools.catalogs import XML_CATALOG

import utils
from tasks import check_registry_status

os.environ['XML_CATALOG_FILES'] = XML_CATALOG

logger = logging.getLogger(__name__)


def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)

    return logger


def summarize(validator):

    def _make_err_message(err):
        """ An error message is comprised of the message itself and the
        element sourceline.
        """
        err_msg = {'message': err.message}

        try:
            err_element = err.get_apparent_element(validator.lxml)
        except ValueError:
            logger.info('Could not locate the element name in: %s' % err.message)
            err_element = None

        if err_element is not None:
            err_msg['apparent_line'] = err_element.sourceline
        else:
            err_msg['apparent_line'] = None

        return err_msg

    dtd_is_valid, dtd_errors = validator.validate()
    sps_is_valid, sps_errors = validator.validate_style()

    summary = {
        'dtd_errors': [_make_err_message(err) for err in dtd_errors],
        'sps_errors': [_make_err_message(err) for err in sps_errors],
    }

    summary['dtd_is_valid'] = validator.validate()[0]
    summary['sps_is_valid'] = validator.validate_style()[0]
    summary['is_valid'] = bool(validator.validate()[0] and validator.validate_style()[0])

    return summary


def analyze_xml(xml, document):
    """Analyzes `file` against packtools' XMLValidator.
    """

    f = StringIO(xml)

    try:
        xml = packtools.XMLValidator(f, sps_version='sps-1.1')
    except:
        logger.error('Could not read file %s' % document.publisher_id)
        summary = {}
        summary['dtd_is_valid'] = False
        summary['sps_is_valid'] = False
        summary['is_valid'] = False
        summary['parsing_error'] = True
        return summary
    else:
        summary = summarize(xml)
        return summary


class Export(object):

    def __init__(self, collection, issns=None, full=False, xml_parsing_report=None):

        self._articlemeta = utils.articlemeta_server()
        self._scielomanager = utils.scielomanager_server()
        self.collection = collection
        self.issns = issns
        self.full = full
        self.xml_parsing_report = codecs.open(xml_parsing_report, 'w', encoding='utf-8') if xml_parsing_report else xml_parsing_report

    def _write(self, line):
        self.xml_parsing_report.write('%s\r\n' % line)

    def _fmt_json(self, data, xml_result):

        fmt = {}

        fmt['code'] = data.publisher_id
        fmt['collection'] = data.collection_acronym
        fmt['id'] = '_'.join([data.collection_acronym, data.publisher_id])
        fmt['document_type'] = data.document_type
        fmt['publication_year'] = data.publication_date[0:4]
        fmt['document_type'] = data.document_type
        fmt['data_version'] = 'legacy' if data.data_model_version == 'html' else 'xml'
        fmt.update(xml_result)

        return json.dumps(fmt)

    def run(self):
        '''
            This method registry Celery tasks for each document.
        '''
        for xylose_article, xml in self.items():

            logger.info('Registering %s, %s' % (
                xylose_article.publisher_id,
                xylose_article.collection_acronym))

            check_registry_status.delay(
                self._scielomanager,
                self._articlemeta,
                xylose_article,
                xml
            )

        logger.info('Export finished')

    def items(self):

        extra_filter = json.dumps({"version": 'html'})

        if not self.full:
            extra_filter['aid': {'$exists': 0}]

        if not self.issns:
            self.issns = [None]

        for issn in self.issns:
            for data in self._articlemeta.documents(
                    collection=self.collection,
                    issn=issn,
                    extra_filter=extra_filter):

                logger.info('Reading document: %s' % data.publisher_id)

                xml = self._articlemeta.document(
                    data.publisher_id, data.collection_acronym, fmt='xmlrsps')

                checked_xml = analyze_xml(xml, data)

                if not checked_xml['is_valid'] and self.xml_parsing_report:

                    self._write(self._fmt_json(data, checked_xml))

                if not checked_xml['dtd_is_valid']:
                    logger.warning('Invalid XML for: %s, %s' % (
                        data.publisher_id, data.collection_acronym))
                    continue

                yield (data, xml)


def main():

    parser = argparse.ArgumentParser(
        description='Exporta XML\'s SciELO PS do Article Meta para o SciELO Manager'
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
        '--full',
        '-f',
        action='store_true',
        help="Apply submission to all files including those that have already been sent and already has an AID"
    )

    parser.add_argument(
        '--logging_file',
        '-o',
        help='Full path to the log file'
    )

    parser.add_argument(
        '--xml_parsing_report',
        '-x',
        help='Full path to the xml parsing report file. If not specified, no report will be produced'
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

    export = Export(
        args.collection, issns, full=args.full, xml_parsing_report=args.xml_parsing_report)

    export.run()
