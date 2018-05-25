from entropy import shannon_entropy

from runner.remote_analysis_runner import RemoteAnalysisRunner

BLOCK_SIZE = 32
MINIMAL_PADDING_BYTES = 128


class AnalysisPlugin(RemoteAnalysisRunner):
    '''
    Do useless - or is it? ; ) - analysis
    '''
    NAME = 'example_plugin'
    VERSION = '0.1'

    def __init__(self):
        super().__init__(self.NAME, self.VERSION)

    def process_object(self, binary: bytes, dependent_analysis: dict) -> dict:
        result = dict(summary=list())

        for value in [0, 255]:
            result[hex(value)] = 'Padding found' if self._detect_padding_for_specific_byte(binary, value) else 'No padding found'
        for key, value in result.items():
            if value == 'Padding found':
                result['summary'].append(key)

        return result

    def _detect_padding_for_specific_byte(self, binary: bytes, byte_value: int):
        offset = 0

        block = binary[offset:offset+BLOCK_SIZE]
        while len(block) > 0:
            if shannon_entropy(block) < 0.1:
                padding = self.test_for_padding(binary, offset, byte_value)
                if padding:
                    return True
            offset += BLOCK_SIZE
            block = binary[offset:offset+BLOCK_SIZE]

        return False

    def test_for_padding(self, binary: bytes, offset: int, byte_value : int):
        block = binary[offset:offset + MINIMAL_PADDING_BYTES]

        if not byte_value in block:
            return False
        else:
            if not shannon_entropy(block) < 0.1:
                return False
            else:
                return self.find_run_of_byte(block, byte_value)

    @staticmethod
    def find_run_of_byte(block: bytes, byte_value: int):
        first = block.find(byte_value)
        if first > BLOCK_SIZE:
            return False
        for item in block[first:]:
            if item != byte_value:
                return False
        return True if block else False


if __name__ == '__main__':
    plugin = AnalysisPlugin()
    exit(plugin.run())
