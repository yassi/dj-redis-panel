"""
Tests for the Django Redis Panel collection member add functionality.

This module tests the ability to add new members to Redis collections
(lists, sets, sorted sets, and hashes) through the key detail view.
"""
import os
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestCollectionMemberAdd(RedisTestCase):
    """Test cases for adding new members to Redis collections."""
    
    def test_add_list_item_success_end_position(self):
        """Test successful addition of list item at end position."""
        # Create existing list
        list_key = 'test:add_list_end'
        self.redis_conn.rpush(list_key, 'existing_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Add item to end (default position)
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': 'new_item',
            'position': 'end'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("end of list", response.context['success_message'])
        
        # Verify item was added to the end
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(items, ['existing_item', 'new_item'])
    
    def test_add_list_item_success_start_position(self):
        """Test successful addition of list item at start position."""
        # Create existing list
        list_key = 'test:add_list_start'
        self.redis_conn.rpush(list_key, 'existing_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Add item to start
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': 'new_first_item',
            'position': 'start'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("beginning of list", response.context['success_message'])
        
        # Verify item was added to the beginning
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(items, ['new_first_item', 'existing_item'])
    
    def test_add_list_item_wrong_key_type_error(self):
        """Test add_list_item when key exists but is not a list."""
        # Create a string key first
        string_key = 'test:wrong_type_for_list'
        self.redis_conn.set(string_key, 'existing_string_value')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, string_key])
        
        # Try to add list item to a string key
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': 'should_fail',
            'position': 'end'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("exists but is not a list", response.context['error_message'])
        
        # Verify the original string value is unchanged
        self.assertEqual(self.redis_conn.get(string_key), 'existing_string_value')
    
    def test_add_list_item_disabled(self):
        """Test add_list_item when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        list_key = 'test:add_list_disabled'
        conn_14.rpush(list_key, 'existing_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, list_key])
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': 'should_fail',
            'position': 'end'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no items were added
        original_items = conn_14.lrange(list_key, 0, -1)
        self.assertEqual(original_items, ['existing_item'])
        
        # Cleanup
        conn_14.delete(list_key)
    
    def test_add_set_member_success_new_member(self):
        """Test successful addition of new set member."""
        # Create set with one member first
        set_key = 'test:add_set_new'
        self.redis_conn.sadd(set_key, 'existing_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Add new member
        response = self.client.post(url, {
            'action': 'add_set_member',
            'new_member': 'new_member'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("added to set", response.context['success_message'])
        
        # Verify member was added
        members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(members), 2)
        self.assertIn('new_member', members)
        self.assertIn('existing_member', members)
    
    def test_add_set_member_duplicate_member(self):
        """Test add_set_member when member already exists."""
        # Create set with existing member
        set_key = 'test:add_set_duplicate'
        self.redis_conn.sadd(set_key, 'existing_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Try to add the same member again
        response = self.client.post(url, {
            'action': 'add_set_member',
            'new_member': 'existing_member'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists in set", response.context['success_message'])
        
        # Verify set still has only one member
        members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(members), 1)
        self.assertIn('existing_member', members)
    
    def test_add_set_member_wrong_key_type_error(self):
        """Test add_set_member when key exists but is not a set."""
        # Create a hash key first
        hash_key = 'test:wrong_type_for_set'
        self.redis_conn.hset(hash_key, 'field1', 'value1')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Try to add set member to a hash key
        response = self.client.post(url, {
            'action': 'add_set_member',
            'new_member': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("exists but is not a set", response.context['error_message'])
        
        # Verify the original hash is unchanged
        self.assertEqual(self.redis_conn.hget(hash_key, 'field1'), 'value1')
    
    def test_add_set_member_disabled(self):
        """Test add_set_member when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        set_key = 'test:add_set_disabled'
        conn_14.sadd(set_key, 'existing_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, set_key])
        response = self.client.post(url, {
            'action': 'add_set_member',
            'new_member': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no members were added
        original_members = conn_14.smembers(set_key)
        self.assertEqual(len(original_members), 1)
        self.assertIn('existing_member', original_members)
        
        # Cleanup
        conn_14.delete(set_key)
    
    def test_add_zset_member_success_new_member(self):
        """Test successful addition of new sorted set member."""
        # Create sorted set with one member first
        zset_key = 'test:add_zset_new'
        self.redis_conn.zadd(zset_key, {'existing_member': 1.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Add new member
        response = self.client.post(url, {
            'action': 'add_zset_member',
            'new_member': 'new_member',
            'new_score': '3.5'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("added to sorted set", response.context['success_message'])
        
        # Verify member was added with correct score
        score = self.redis_conn.zscore(zset_key, 'new_member')
        self.assertEqual(score, 3.5)
        
        # Verify both members exist
        members = self.redis_conn.zrange(zset_key, 0, -1, withscores=True)
        self.assertEqual(len(members), 2)
    
    def test_add_zset_member_update_existing_score(self):
        """Test add_zset_member when updating existing member score."""
        # Create sorted set with existing member
        zset_key = 'test:add_zset_update'
        self.redis_conn.zadd(zset_key, {'existing_member': 1.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Update the score of existing member
        response = self.client.post(url, {
            'action': 'add_zset_member',
            'new_member': 'existing_member',
            'new_score': '2.5'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("score updated in sorted set", response.context['success_message'])
        
        # Verify score was updated
        score = self.redis_conn.zscore(zset_key, 'existing_member')
        self.assertEqual(score, 2.5)
    
    def test_add_zset_member_wrong_key_type_error(self):
        """Test add_zset_member when key exists but is not a sorted set."""
        # Create a list key first
        list_key = 'test:wrong_type_for_zset'
        self.redis_conn.rpush(list_key, 'existing_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Try to add zset member to a list key
        response = self.client.post(url, {
            'action': 'add_zset_member',
            'new_member': 'should_fail',
            'new_score': '1.0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("exists but is not a sorted set", response.context['error_message'])
        
        # Verify the original list is unchanged
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(items, ['existing_item'])
    
    def test_add_zset_member_invalid_score(self):
        """Test add_zset_member with invalid score."""
        # Create sorted set
        zset_key = 'test:add_zset_invalid_score'
        self.redis_conn.zadd(zset_key, {'existing_member': 1.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Try to add member with invalid score
        response = self.client.post(url, {
            'action': 'add_zset_member',
            'new_member': 'new_member',
            'new_score': 'invalid_score'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Invalid score provided. Score must be a number.")
        
        # Verify no new members were added
        members = self.redis_conn.zrange(zset_key, 0, -1)
        self.assertEqual(len(members), 1)
    
    def test_add_zset_member_disabled(self):
        """Test add_zset_member when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        zset_key = 'test:add_zset_disabled'
        conn_14.zadd(zset_key, {'existing_member': 1.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, zset_key])
        response = self.client.post(url, {
            'action': 'add_zset_member',
            'new_member': 'should_fail',
            'new_score': '2.0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no members were added
        original_members = conn_14.zrange(zset_key, 0, -1, withscores=True)
        self.assertEqual(len(original_members), 1)
        self.assertEqual(original_members[0], ('existing_member', 1.0))
        
        # Cleanup
        conn_14.delete(zset_key)
    
    def test_add_hash_field_success_new_field(self):
        """Test successful addition of new hash field."""
        # Create hash with one field first
        hash_key = 'test:add_hash_new'
        self.redis_conn.hset(hash_key, 'existing_field', 'existing_value')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Add new field
        response = self.client.post(url, {
            'action': 'add_hash_field',
            'new_field': 'new_field',
            'new_value': 'new_value'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("added to hash", response.context['success_message'])
        
        # Verify field was added
        value = self.redis_conn.hget(hash_key, 'new_field')
        self.assertEqual(value, 'new_value')
        
        # Verify both fields exist
        all_fields = self.redis_conn.hgetall(hash_key)
        self.assertEqual(len(all_fields), 2)
        self.assertEqual(all_fields['existing_field'], 'existing_value')
        self.assertEqual(all_fields['new_field'], 'new_value')
    
    def test_add_hash_field_update_existing_field(self):
        """Test add_hash_field when updating existing field."""
        # Create hash with existing field
        hash_key = 'test:add_hash_update'
        self.redis_conn.hset(hash_key, 'existing_field', 'original_value')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Update the existing field
        response = self.client.post(url, {
            'action': 'add_hash_field',
            'new_field': 'existing_field',
            'new_value': 'updated_value'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated in hash", response.context['success_message'])
        
        # Verify field was updated
        value = self.redis_conn.hget(hash_key, 'existing_field')
        self.assertEqual(value, 'updated_value')
    
    def test_add_hash_field_wrong_key_type_error(self):
        """Test add_hash_field when key exists but is not a hash."""
        # Create a set key first
        set_key = 'test:wrong_type_for_hash'
        self.redis_conn.sadd(set_key, 'existing_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Try to add hash field to a set key
        response = self.client.post(url, {
            'action': 'add_hash_field',
            'new_field': 'should_fail',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("exists but is not a hash", response.context['error_message'])
        
        # Verify the original set is unchanged
        members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(members), 1)
        self.assertIn('existing_member', members)
    
    def test_add_hash_field_disabled(self):
        """Test add_hash_field when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=14, decode_responses=True)
        hash_key = 'test:add_hash_disabled'
        conn_14.hset(hash_key, 'existing_field', 'existing_value')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, hash_key])
        response = self.client.post(url, {
            'action': 'add_hash_field',
            'new_field': 'should_fail',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no fields were added
        original_fields = conn_14.hgetall(hash_key)
        self.assertEqual(len(original_fields), 1)
        self.assertEqual(original_fields['existing_field'], 'existing_value')
        
        # Cleanup
        conn_14.delete(hash_key)
    
    def test_add_operations_with_empty_values(self):
        """Test add operations with empty values."""
        # Test adding empty string to list
        list_key = 'test:add_empty_list'
        self.redis_conn.rpush(list_key, 'initial_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': '',  # Empty value
            'position': 'end'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('success_message', response.context)
        
        # Verify empty string was added
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1], '')
        
        # Test adding empty member to set
        set_key = 'test:add_empty_set'
        self.redis_conn.sadd(set_key, 'initial_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        response = self.client.post(url, {
            'action': 'add_set_member',
            'new_member': ''  # Empty member
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('success_message', response.context)
        
        # Verify empty string was added to set
        members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(members), 2)
        self.assertIn('', members)
    
    def test_add_operations_with_special_characters(self):
        """Test add operations with special characters in values."""
        # Test list with special characters
        list_key = 'test:add_special_list'
        self.redis_conn.rpush(list_key, 'initial_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        special_values = [
            'value with spaces',
            'value@with#symbols',
            'value:with:colons',
            'value\nwith\nnewlines',
            'value"with"quotes',
            "value'with'apostrophes"
        ]
        
        for value in special_values:
            response = self.client.post(url, {
                'action': 'add_list_item',
                'new_value': value,
                'position': 'end'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('success_message', response.context)
        
        # Verify all values were added
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(items), len(special_values) + 1)  # +1 for initial_item
        for value in special_values:
            self.assertIn(value, items)
    
    def test_add_operations_with_numeric_values(self):
        """Test add operations with numeric string values."""
        # Test adding numeric strings to hash
        hash_key = 'test:add_numeric_hash'
        self.redis_conn.hset(hash_key, 'initial_field', 'initial_value')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        numeric_values = ['123', '-456', '78.9', '0', '999999999']
        
        for i, value in enumerate(numeric_values):
            response = self.client.post(url, {
                'action': 'add_hash_field',
                'new_field': f'field_{i}',
                'new_value': value
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('success_message', response.context)
        
        # Verify all numeric values were stored as strings
        for i, value in enumerate(numeric_values):
            stored_value = self.redis_conn.hget(hash_key, f'field_{i}')
            self.assertEqual(stored_value, value)
    
    def test_add_operations_with_large_values(self):
        """Test add operations with large values."""
        # Test adding large string to list
        list_key = 'test:add_large_list'
        self.redis_conn.rpush(list_key, 'initial_item')
        large_value = 'x' * 10000  # 10KB string
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'add_list_item',
            'new_value': large_value,
            'position': 'end'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('success_message', response.context)
        
        # Verify large value was added
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(items), 2)  # initial_item + large_value
        self.assertEqual(items[1], large_value)
        self.assertEqual(len(items[1]), 10000)
    
    def test_add_operations_multiple_items(self):
        """Test add operations with multiple items to ensure proper behavior."""
        # Test adding multiple items to list
        list_key = 'test:add_multiple_list'
        self.redis_conn.rpush(list_key, 'initial_item')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Add multiple items
        for i in range(3):
            response = self.client.post(url, {
                'action': 'add_list_item',
                'new_value': f'item_{i}',
                'position': 'end'
            })
            self.assertEqual(response.status_code, 200)
        
        # Verify all items were added
        items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(items), 4)  # initial + 3 new items
        self.assertEqual(items[0], 'initial_item')
        
        # Test adding multiple members to set
        set_key = 'test:add_multiple_set'
        self.redis_conn.sadd(set_key, 'initial_member')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Add multiple members
        for i in range(3):
            response = self.client.post(url, {
                'action': 'add_set_member',
                'new_member': f'member_{i}'
            })
            self.assertEqual(response.status_code, 200)
        
        # Verify all members were added
        members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(members), 4)  # initial + 3 new members
