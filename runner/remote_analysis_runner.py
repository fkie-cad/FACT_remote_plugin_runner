# -*- coding: utf-8 -*-
import base64
import json
import pickle
import time

import pika

RABBIT_HOST = 'localhost'
RABBIT_IN_EXCHANGE = 'task_out'
RABBIT_OUT_EXCHANGE = 'task_write_back'


class RemoteAnalysisRunner:
    def __init__(self, name, version):
        self._name = name
        self._version = version

        self._in_connection, self._in_channel, self._in_queue = self._set_up_in_channel()

        self._out_connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
        self._out_channel = self._out_connection.channel()
        self._out_channel.exchange_declare(exchange=RABBIT_OUT_EXCHANGE, exchange_type='direct')

    def _set_up_in_channel(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=RABBIT_IN_EXCHANGE, exchange_type='topic')

        queue = channel.queue_declare()
        channel.queue_bind(
            exchange=RABBIT_IN_EXCHANGE,
            queue=queue.method.queue,
            routing_key=self._get_topic()
        )

        return connection, channel, queue

    def _process_task(self, task_message):
        file_object = task_message.pop('file_object')
        self.process_object(file_object)
        self._add_result_metadata(file_object)
        self._send_task_result(file_object, task_message)

    def _add_result_metadata(self, file_object):
        file_object.processed_analysis[self._name]['analysis_date'] = time.time()
        file_object.processed_analysis[self._name]['plugin_version'] = self._version

    def _send_task_result(self, file_object, task_message: dict):
        task_message['timestamp'] = time.time()
        task_message['analysis'] = file_object.processed_analysis[self._name]
        task_message['analysis_system'] = self._name
        task_message['object_uid'] = file_object.get_uid()
        self._out_channel.basic_publish(exchange='task_write_back', routing_key='tasks', body=json.dumps(task_message))

    def run(self) -> int:
        self._in_channel.basic_qos(prefetch_count=1)
        self._in_channel.basic_consume(self._task_in_callback, queue=self._in_queue.method.queue)

        try:
            while True:
                self._in_channel.start_consuming()
        except KeyboardInterrupt:
            print('Shutting down gracefully ..')

        self._in_connection.close()
        self._out_connection.close()

        return 0

    def _task_in_callback(self, ch: pika.adapters.blocking_connection.BlockingChannel, method: pika.spec.Basic.Deliver, properties: pika.BasicProperties, body: bytes):
        print('[INFO] Processing a task')
        task_message = pickle.loads(base64.standard_b64decode(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        self._process_task(task_message)

    def _get_topic(self) -> str:
        return 'analysis.{}.normal'.format(self._name)

    def process_object(self, binary, dependend_analysis):
        pass
