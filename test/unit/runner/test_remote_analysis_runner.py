import os
import time
from multiprocessing import Process
from signal import SIGKILL

import pytest

from runner.remote_analysis_runner import RemoteAnalysisRunner


@pytest.fixture(scope='function')
def stub_runner():
    return RemoteAnalysisRunner(name='stub', version='0.1')


def test_serialization(stub_runner: RemoteAnalysisRunner) -> None:
    item = {'a_dict': ['with', b'a', 'list']}
    result = stub_runner.deserialize(stub_runner.serialize(item).encode())
    assert item == result


def test_get_topic(stub_runner: RemoteAnalysisRunner) -> None:
    assert stub_runner._get_topic() == 'analysis.stub.normal'


def test_process_object(stub_runner: RemoteAnalysisRunner) -> None:
    assert not stub_runner.process_object(b'', dict())


def test_run(stub_runner: RemoteAnalysisRunner) -> None:
    process = Process(target=stub_runner.run)
    process.start()
    time.sleep(0.5)
    os.kill(process.pid, SIGKILL)
    process.join()
    assert True


def test_process_task(stub_runner: RemoteAnalysisRunner) -> None:
    a = time.time()
    stub_runner.process_object = lambda **kwargs: dict()
    message = dict(binary=b'', dependencies={})
    stub_runner._process_task(message)

    assert message['analysis']['plugin_version'] == '0.1'

    b = time.time()
    assert a < message['analysis']['analysis_date'] < b
