"""
Tests for handling binary data (e.g., msgpack from Django Channels).
"""
import redis
from .base import RedisTestCase


class TestBinaryData(RedisTestCase):
    """Test cases for binary data handling."""
    
    def test_binary_string_value(self):
        """Test that binary string values are displayed as base64."""
        # Create a binary value that can't be decoded as UTF-8
        binary_value = b'\x83\xa4type\xafgeneral_message\xa4html\xb2<p>Hello World</p>'
        
        # Store it directly using redis-py without decode_responses
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.set('test:binary:msgpack', binary_value)
        
        # Try to retrieve it using the panel utils
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:binary:msgpack')
        
        # The value should be successfully retrieved and displayed as base64
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'string')
        self.assertIn('[binary data: base64]', key_data['value'])
        
        # Clean up
        conn.delete('test:binary:msgpack')
    
    def test_utf8_string_value(self):
        """Test that UTF-8 string values are still displayed normally."""
        # Store a normal UTF-8 value
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.set('test:utf8:string', 'Hello World')
        
        # Try to retrieve it using the panel utils
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:utf8:string')
        
        # The value should be successfully retrieved and displayed as normal string
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'string')
        self.assertEqual(key_data['value'], 'Hello World')
        
        # Clean up
        conn.delete('test:utf8:string')
    
    def test_binary_list_values(self):
        """Test that binary values in lists are handled correctly."""
        binary_value = b'\xd3\x15\xc0Jo\xaev\xca\x8e\xbf\xff'
        
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.delete('test:binary:list')
        conn.lpush('test:binary:list', binary_value)
        conn.lpush('test:binary:list', 'normal string')
        
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:binary:list')
        
        # Both values should be retrieved
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'list')
        self.assertEqual(len(key_data['value']), 2)
        
        # One should be normal string, one should be base64
        self.assertEqual(key_data['value'][0], 'normal string')
        self.assertIn('[binary data: base64]', key_data['value'][1])
        
        # Clean up
        conn.delete('test:binary:list')
    
    def test_binary_hash_values(self):
        """Test that binary values in hashes are handled correctly."""
        binary_value = b'\x83\xa4type\xafgeneral'
        
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.delete('test:binary:hash')
        conn.hset('test:binary:hash', 'binary_field', binary_value)
        conn.hset('test:binary:hash', 'normal_field', 'normal value')
        
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:binary:hash')
        
        # Both values should be retrieved
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'hash')
        self.assertEqual(len(key_data['value']), 2)
        
        # One should be normal string, one should be base64
        self.assertEqual(key_data['value']['normal_field'], 'normal value')
        self.assertIn('[binary data: base64]', key_data['value']['binary_field'])
        
        # Clean up
        conn.delete('test:binary:hash')
    
    def test_binary_set_values(self):
        """Test that binary values in sets are handled correctly."""
        binary_value = b'\xd3\x15\xc0Jo\xae'
        
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.delete('test:binary:set')
        conn.sadd('test:binary:set', binary_value)
        conn.sadd('test:binary:set', 'normal member')
        
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:binary:set')
        
        # Both values should be retrieved
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'set')
        self.assertEqual(len(key_data['value']), 2)
        
        # Clean up
        conn.delete('test:binary:set')
    
    def test_binary_zset_values(self):
        """Test that binary values in sorted sets are handled correctly."""
        binary_value = b'\xd3\x15\xc0Jo'
        
        conn = redis.Redis(host='127.0.0.1', port=6379, db=15, decode_responses=False)
        conn.delete('test:binary:zset')
        conn.zadd('test:binary:zset', {binary_value: 1.0})
        conn.zadd('test:binary:zset', {'normal member': 2.0})
        
        from dj_redis_panel.redis_utils import RedisPanelUtils
        
        key_data = RedisPanelUtils.get_key_data('test_redis', 15, 'test:binary:zset')
        
        # Both values should be retrieved
        self.assertTrue(key_data['exists'])
        self.assertEqual(key_data['type'], 'zset')
        self.assertEqual(len(key_data['value']), 2)
        
        # Values should be tuples of (member, score)
        # Clean up
        conn.delete('test:binary:zset')
