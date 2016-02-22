# coding: utf-8
import os
from celery import Celery
import logging
import time

import thriftpy
from thriftpy.rpc import make_client

import utils

logger = logging.getLogger(__name__)

scielomanager_thrift = thriftpy.load(
    os.path.join(os.path.dirname(__file__))+'/thrift/scielomanager.thrift')

celery_broker = utils.settings.get('celery', 'amqp://guest@localhost//')
app = Celery('tasks', broker=celery_broker)


@app.task
def check_registry_status(
        scielomanger_thrift_server,
        articlemeta_thrift_server,
        data,
        xml):
    '''
    Esta função é uma Celery Task que controla os eventos de registro de um
    XML no SciELO Manager.
    Em caso de sucesso o AID é registrado no Article Meta para referência.
    '''

    status = [
        'PENDING',
        'STARTED',
        'RETRY',
        'FAILURE',
        'SUCCESS'
    ]

    task_id = scielomanger_thrift_server.client.addArticle(xml)

    while True:
        result = scielomanger_thrift_server.client.getTaskResult(task_id)

        if result.status in [0, 1, 2]:
            logger.warning('XML loading status is %s for %s' % (status[result.status], data.publisher_id))
            time.sleep(1)
            continue

        if result.status == 4:
            logger.info('XML loading status is %s for %s' % (status[result.status], data.publisher_id))

            articlemeta_thrift_server.client.set_aid(
                data.publisher_id, data.collection_acronym, result.value)
            break

        logger.warning('XML loading status is %s for %s (%s)' % (status[result.status], data.publisher_id, result.value))
        break
