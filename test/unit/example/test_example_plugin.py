import pytest

from example.example_plugin import AnalysisPlugin


@pytest.fixture(scope='function')
def stub_plugin():
    return AnalysisPlugin()


def test_process_object_success(stub_plugin: AnalysisPlugin):
    padded_binary = b'\xAB\xCD' + b'\xFF' * 200 + b'END'
    result = stub_plugin.process_object(padded_binary, {})

    assert result and 'summary' in result
    assert '0xff' == result['summary'][0]


def test_process_object_failed(stub_plugin: AnalysisPlugin):
    not_padded_binary = b'\xAB\xCD' + b'\xFF' * 100 + b'END'
    result = stub_plugin.process_object(not_padded_binary, {})

    assert not result['summary']


def test_find_run_of_byte(stub_plugin: AnalysisPlugin):
    assert not stub_plugin.find_run_of_byte(b'', 0)
    assert not stub_plugin.find_run_of_byte(b'\xFF', 0)
    assert not stub_plugin.find_run_of_byte(b'\xFF' * 33 + b'\x00' * 100, 0)
    assert stub_plugin.find_run_of_byte(b'\x00', 0)


def test_test_for_padding(stub_plugin: AnalysisPlugin):
    binary = b'\xAB\xCD' + b'\xFF' * 200 + b'END'
    good_offset, bad_offset = 0, 200
    byte_value = 255

    assert stub_plugin.test_for_padding(binary, good_offset, byte_value)
    assert not stub_plugin.test_for_padding(binary, bad_offset, byte_value)


def test_detect_padding_for_specific_byte(stub_plugin: AnalysisPlugin):
    binary = b'\xAB\xCD' + b'\xFF' * 200 + b'END'
    bad_byte_value, good_byte_value = 0, 255

    assert stub_plugin._detect_padding_for_specific_byte(binary, good_byte_value)
    assert not stub_plugin._detect_padding_for_specific_byte(binary, bad_byte_value)
