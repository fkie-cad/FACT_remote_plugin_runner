# -*- coding: utf-8 -*-
import base64
import pickle
import time

import pika

RABBIT_HOST = 'localhost'
RABBIT_IN_EXCHANGE = 'task_out'
RABBIT_OUT_EXCHANGE = 'task_write_back'
WRITE_BACK_KEY = 'tasks'


class RemoteAnalysisRunner:
    def __init__(self, name: str, version: str):
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

    def _process_task(self, task_message: dict):
        binary = task_message.pop('binary')
        dependent_analysis = task_message.pop('dependencies')

        result = self.process_object(binary=binary, dependent_analysis=dependent_analysis)
        self._add_result_metadata(result)
        self._send_task_result(result, task_message)

    def _add_result_metadata(self, result: dict):
        result['analysis_date'] = time.time()
        result['plugin_version'] = self._version

    def _send_task_result(self, result: dict, task_message: dict):
        task_message['timestamp'] = time.time()
        task_message['analysis'] = result
        task_message['analysis_system'] = self._name
        self._out_channel.basic_publish(exchange=RABBIT_OUT_EXCHANGE, routing_key=WRITE_BACK_KEY, body=self.serialize(task_message))

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
        print('[{}][INFO] Processing a task'.format(int(time.time())))
        task_message = self.deserialize(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        self._process_task(task_message)

    def _get_topic(self) -> str:
        return 'analysis.{}.normal'.format(self._name)

    def process_object(self, binary: bytes, dependent_analysis: dict) -> dict:
        pass

    @staticmethod
    def serialize(item: dict) -> str:
        return base64.standard_b64encode(pickle.dumps(item)).decode()

    @staticmethod
    def deserialize(item: bytes) -> dict:
        return pickle.loads(base64.standard_b64decode(item))
