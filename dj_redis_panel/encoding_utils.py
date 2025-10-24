from typing import Dict, List, Union


class RedisValueDecoder:
    """
    Handles decoding of Redis values using a configurable encoder.
    Falls back to raw byte string representation when encoding fails.
    """

    def __init__(self, encoder: str = "utf-8"):
        """
        Initialize decoder with encoder setting.

        Args:
            encoder: Primary encoding to use (defaults to 'utf-8')
        """
        self.encoder = encoder

    def decode_value(self, value: Union[bytes, str, None]) -> Union[str, None]:
        """
        Decode a Redis value using the configured encoder.

        Args:
            value: The value to decode (bytes, str, or None)

        Returns:
            Decoded string or None if input was None
        """
        if value is None:
            return None

        # If already a string, return as-is
        if isinstance(value, str):
            return value

        # If bytes, try to decode with the configured encoder
        if isinstance(value, bytes):
            try:
                return value.decode(self.encoder)
            except (UnicodeDecodeError, LookupError):
                # If encoding fails, return raw byte string representation with b'' prefix
                # This clearly indicates to the user that this is binary data
                return repr(value)  # Keep the full b'...' representation

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

    def encode_for_redis(self, value: str) -> Union[str, bytes]:
        """
        Convert a decoded string back to the format expected by Redis.

        This handles the case where binary data was decoded to a string representation
        (like b'\\x80\\x04\\x95...') and needs to be converted back to bytes for Redis operations.

        Args:
            value: The decoded string value from the UI

        Returns:
            Either the original string (if it's valid UTF-8) or bytes (if it's a binary representation)
        """
        if not isinstance(value, str):
            return value

        # Check if this looks like a bytes literal representation
        # repr() can output either b'...' or b"..." depending on the content
        is_bytes_repr = (value.startswith("b'") and value.endswith("'")) or (
            value.startswith('b"') and value.endswith('"')
        )

        if is_bytes_repr:
            try:
                # Use ast.literal_eval to safely parse the bytes literal
                import ast

                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # If ast.literal_eval fails, don't attempt lossy fallback parsing
                # Return the original value to avoid data corruption
                return value

        # For regular strings, try to encode with the configured encoder
        try:
            return value.encode(self.encoder)
        except (UnicodeEncodeError, LookupError):
            # If encoding fails, return as string
            return value
