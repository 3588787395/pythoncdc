# Source Generated with Decompyle++ (Python version)
# File: mq_connector.pyc (Python 3.11)

import abc
import six
import pika
class AbstractMQConnector(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError
    @abc.abstractmethod
    def bind(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def consume(self, *args, **kwargs):
        raise NotImplementedError
    @abc.abstractmethod
    def publish(self, *args, **kwargs):
        raise NotImplementedError
class RabbitMQConnector(AbstractMQConnector):
    __doc__ = """
    RabbitMQ工具类
    """
    def __init__(self, host, port, username, password):
        """
        :param host:
        :param port:
        :param username:
        :param password:
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._connection = None
        self._channel = None
    def connect(self):
        """

        :return:
        """
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port, credentials=pika.PlainCredentials(self._username, self._password)))
        self._channel = self._connection.channel()
    def bind(self, exchange, queue, route):
        """

        :param exchange:
        :param queue:
        :param route:
        :return:
        """
        self._channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)
        self._channel.queue_declare(queue=queue, durable=True)
        self._channel.queue_bind(exchange=exchange, queue=queue, routing_key=route)
    def consume(self, func, queue):
        """

        :param func:
        :param queue:
        :return:
        """
        self._channel.basic_consume(queue, func)
        self._channel.start_consuming()
    def publish(self, exchange, queue, messages):
        """

        :param queue:
        :param messages:
        :return:
        """
        self._channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)
        self._channel.queue_declare(queue=queue, durable=True)
        self._channel.basic_publish(exchange=exchange, routing_key=queue, body=messages)
    def close(self):
        self._connection.close()
