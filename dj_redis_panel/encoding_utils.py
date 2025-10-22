from typing import Dict, List, Union


class RedisValueDecoder:
    """
    Handles decoding of Redis values using a configurable pipeline of encodings.
    Falls back to raw byte string representation when all encodings fail.
    """

    def __init__(self, encoding_pipeline: List[str] = None):
        """
        Initialize decoder with encoding pipeline.
        """

        self.encoding_pipeline = encoding_pipeline or ["utf-8"]

    def decode_value(self, value: Union[bytes, str, None]) -> Union[str, None]:
        """
        Decode a Redis value using the encoding pipeline. This is for string or bytes
        only.
        """
        if value is None:
            return None

        # If already a string, return as-is
        if isinstance(value, str):
            return value

        # If bytes, try each encoding in the pipeline
        if isinstance(value, bytes):
            for encoding in self.encoding_pipeline:
                try:
                    return value.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    continue

            # If all encodings fail, return raw byte string representation
            # Using repr() to get a readable string representation of the bytes
            return repr(value)[2:-1]  # Remove b' and ' from repr output

        # For other types, convert to string
        return str(value)

    def decode_list(
        self, values: List[Union[bytes, str, None]]
    ) -> List[Union[str, None]]:
        """
        Decode a list of Redis values.
        """
        return [self.decode_value(value) for value in values]

    def decode_dict(
        self, values: Dict[Union[bytes, str], Union[bytes, str, None]]
    ) -> Dict[str, Union[str, None]]:
        """
        Decode a dictionary of Redis values (for hashes).
        """
        return {
            self.decode_value(key): self.decode_value(value)
            for key, value in values.items()
        }

    def decode_zset_list(self, values: List[tuple]) -> List[tuple]:
        """
        Decode a list of (member, score) tuples from a sorted set.
        """
        return [(self.decode_value(member), score) for member, score in values]
