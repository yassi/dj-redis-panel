"""
Tests for the Django Redis Panel collection member edit functionality.

This module tests the ability to edit individual members in Redis collections
(lists, hashes, and sorted sets) through the key detail view.
"""
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestCollectionMemberEdit(RedisTestCase):
    """Test cases for editing individual members in Redis collections."""
    
    def test_update_list_item_success(self):
        """Test successful update of a list item by index."""
        # Create a test list
        list_key = 'test:edit_list'
        self.redis_conn.rpush(list_key, 'original_item_0', 'original_item_1', 'original_item_2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Update item at index 1
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '1',
            'new_value': 'updated_item_1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "List item updated successfully")
        
        # Verify the item was updated in Redis
        updated_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(updated_items, ['original_item_0', 'updated_item_1', 'original_item_2'])
    
    def test_update_list_item_invalid_index(self):
        """Test update with invalid list index."""
        # Create a test list with 3 items
        list_key = 'test:edit_list_invalid'
        self.redis_conn.rpush(list_key, 'item0', 'item1', 'item2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Try to update item at index 5 (out of range)
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '5',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Index 5 is out of range", response.context['error_message'])
        
        # Verify no items were changed
        original_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(original_items, ['item0', 'item1', 'item2'])
    
    def test_update_list_item_non_numeric_index(self):
        """Test update with non-numeric index."""
        # Create a test list
        list_key = 'test:edit_list_non_numeric'
        self.redis_conn.rpush(list_key, 'item0', 'item1')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Try to update with non-numeric index
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': 'invalid',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Invalid index provided")
        
        # Verify no items were changed
        original_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(original_items), 2)
    
    def test_update_list_item_disabled(self):
        """Test list item update when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        list_key = 'test:edit_list_disabled'
        conn_14.rpush(list_key, 'item0', 'item1', 'item2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, list_key])
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '1',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no items were changed
        original_items = conn_14.lrange(list_key, 0, -1)
        self.assertEqual(original_items, ['item0', 'item1', 'item2'])
        
        # Cleanup
        conn_14.delete(list_key)
    
    def test_update_hash_field_value_success(self):
        """Test successful update of a hash field value."""
        # Create a test hash
        hash_key = 'test:edit_hash'
        self.redis_conn.hset(hash_key, mapping={'field1': 'original_value1', 'field2': 'original_value2', 'field3': 'original_value3'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Update field2 value
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'field2',
            'new_value': 'updated_value2'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field value updated successfully")
        
        # Verify the field value was updated in Redis
        updated_hash = self.redis_conn.hgetall(hash_key)
        expected_hash = {'field1': 'original_value1', 'field2': 'updated_value2', 'field3': 'original_value3'}
        self.assertEqual(updated_hash, expected_hash)
    
    def test_update_hash_field_value_nonexistent_field(self):
        """Test update of non-existent hash field."""
        # Create a test hash
        hash_key = 'test:edit_hash_nonexistent'
        self.redis_conn.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Try to update non-existent field
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'nonexistent',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("does not exist in hash", response.context['error_message'])
        
        # Verify no fields were changed
        original_hash = self.redis_conn.hgetall(hash_key)
        self.assertEqual(len(original_hash), 2)
    
    def test_update_hash_field_value_disabled(self):
        """Test hash field value update when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        hash_key = 'test:edit_hash_disabled'
        conn_14.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, hash_key])
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'field1',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no fields were changed
        original_hash = conn_14.hgetall(hash_key)
        self.assertEqual(original_hash, {'field1': 'value1', 'field2': 'value2'})
        
        # Cleanup
        conn_14.delete(hash_key)
    
    def test_update_zset_member_score_success(self):
        """Test successful update of a sorted set member score."""
        # Create a test sorted set
        zset_key = 'test:edit_zset'
        self.redis_conn.zadd(zset_key, {'member1': 1.0, 'member2': 2.0, 'member3': 3.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Update member2 score
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'member2',
            'new_score': '5.5'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Sorted set member score updated successfully")
        
        # Verify the member score was updated in Redis (and reordered)
        updated_zset = self.redis_conn.zrange(zset_key, 0, -1, withscores=True)
        expected_zset = [('member1', 1.0), ('member3', 3.0), ('member2', 5.5)]
        self.assertEqual(updated_zset, expected_zset)
    
    def test_update_zset_member_score_nonexistent_member(self):
        """Test update of non-existent sorted set member."""
        # Create a test sorted set
        zset_key = 'test:edit_zset_nonexistent'
        self.redis_conn.zadd(zset_key, {'member1': 1.0, 'member2': 2.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Try to update non-existent member
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'nonexistent',
            'new_score': '10.0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("does not exist in sorted set", response.context['error_message'])
        
        # Verify no members were changed
        original_zset = self.redis_conn.zrange(zset_key, 0, -1, withscores=True)
        self.assertEqual(len(original_zset), 2)
    
    def test_update_zset_member_score_invalid_score(self):
        """Test update with invalid score value."""
        # Create a test sorted set
        zset_key = 'test:edit_zset_invalid_score'
        self.redis_conn.zadd(zset_key, {'member1': 1.0, 'member2': 2.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Try to update with invalid score
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'member1',
            'new_score': 'invalid_score'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Invalid score provided. Score must be a number.")
        
        # Verify no members were changed
        original_zset = self.redis_conn.zrange(zset_key, 0, -1, withscores=True)
        self.assertEqual(original_zset, [('member1', 1.0), ('member2', 2.0)])
    
    def test_update_zset_member_score_disabled(self):
        """Test sorted set member score update when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        zset_key = 'test:edit_zset_disabled'
        conn_14.zadd(zset_key, {'member1': 1.0, 'member2': 2.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, zset_key])
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'member1',
            'new_score': '10.0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no members were changed
        original_zset = conn_14.zrange(zset_key, 0, -1, withscores=True)
        self.assertEqual(original_zset, [('member1', 1.0), ('member2', 2.0)])
        
        # Cleanup
        conn_14.delete(zset_key)
    
    def test_update_member_wrong_key_type(self):
        """Test update operations on wrong key types."""
        # Create different key types
        string_key = 'test:wrong_type_string'
        list_key = 'test:wrong_type_list'
        
        self.redis_conn.set(string_key, 'string_value')
        self.redis_conn.rpush(list_key, 'item1', 'item2')
        
        # Try to update hash field on a string key
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, string_key])
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'anything',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("is not a hash", response.context['error_message'])
        
        # Try to update zset member score on a list key
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'anything',
            'new_score': '1.0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("is not a sorted set", response.context['error_message'])
    
    def test_update_member_nonexistent_key(self):
        """Test update operations on non-existent keys."""
        nonexistent_key = 'test:nonexistent_key'
        
        # Ensure the key doesn't exist
        self.redis_conn.delete(nonexistent_key)
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, nonexistent_key])
        
        # Try to update from non-existent key - should get 404
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'anything',
            'new_value': 'should_fail'
        })
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_member_with_pagination(self):
        """Test update of members in paginated collections."""
        # Create a large list to trigger pagination
        large_list_key = 'test:edit_paginated_list'
        for i in range(150):
            self.redis_conn.rpush(large_list_key, f'item_{i:03d}')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
        
        # Go to second page and update an item
        response = self.client.post(url + '?page=2&per_page=50', {
            'action': 'update_list_item',
            'index': '75',  # Item at position 75
            'new_value': 'updated_item_075'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated successfully", response.context['success_message'])
        
        # Verify the item was updated
        updated_items = self.redis_conn.lrange(large_list_key, 0, -1)
        self.assertEqual(len(updated_items), 150)
        self.assertEqual(updated_items[75], 'updated_item_075')
        
        # Verify pagination context is maintained
        self.assertTrue(response.context['is_paginated'])
    
    def test_update_member_special_characters(self):
        """Test update of members with special characters."""
        # Create collections with special character values
        hash_key = 'test:edit_special_hash'
        list_key = 'test:edit_special_list'
        
        # Hash with special character field names and values
        self.redis_conn.hset(hash_key, mapping={
            'field with spaces': 'value with spaces',
            'field@with#symbols': 'value@with#symbols',
            'field:with:colons': 'value:with:colons'
        })
        
        # List with special character values
        special_items = ['item with spaces', 'item@with#symbols', 'item:with:colons']
        for item in special_items:
            self.redis_conn.rpush(list_key, item)
        
        # Test updating hash field value with special characters
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'field with spaces',
            'new_value': 'updated value with spaces'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field value updated successfully")
        
        # Verify update
        updated_hash = self.redis_conn.hgetall(hash_key)
        self.assertEqual(updated_hash['field with spaces'], 'updated value with spaces')
        
        # Test updating list item with special characters
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '1',
            'new_value': 'updated item@with#symbols'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "List item updated successfully")
        
        # Verify update
        updated_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(updated_items[1], 'updated item@with#symbols')
    
    def test_update_member_empty_values(self):
        """Test update of members with empty values."""
        # Create test collections
        hash_key = 'test:edit_empty_hash'
        list_key = 'test:edit_empty_list'
        zset_key = 'test:edit_empty_zset'
        
        self.redis_conn.hset(hash_key, 'field1', 'original_value')
        self.redis_conn.rpush(list_key, 'original_item')
        self.redis_conn.zadd(zset_key, {'member1': 1.0})
        
        # Test updating hash field to empty value
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'field1',
            'new_value': ''  # Empty value
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field value updated successfully")
        self.assertEqual(self.redis_conn.hget(hash_key, 'field1'), '')
        
        # Test updating list item to empty value
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '0',
            'new_value': ''  # Empty value
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "List item updated successfully")
        self.assertEqual(self.redis_conn.lindex(list_key, 0), '')
        
        # Test updating zset member score to zero
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'member1',
            'new_score': '0'  # Zero score
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Sorted set member score updated successfully")
        self.assertEqual(self.redis_conn.zscore(zset_key, 'member1'), 0.0)
    
    def test_update_member_numeric_values(self):
        """Test update of members with various numeric values."""
        # Create test collections
        hash_key = 'test:edit_numeric_hash'
        list_key = 'test:edit_numeric_list'
        zset_key = 'test:edit_numeric_zset'
        
        self.redis_conn.hset(hash_key, 'numeric_field', '123')
        self.redis_conn.rpush(list_key, '456')
        self.redis_conn.zadd(zset_key, {'numeric_member': 1.0})
        
        # Test updating hash field with numeric value
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        response = self.client.post(url, {
            'action': 'update_hash_field_value',
            'field': 'numeric_field',
            'new_value': '999.5'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.redis_conn.hget(hash_key, 'numeric_field'), '999.5')
        
        # Test updating list item with numeric value
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'update_list_item',
            'index': '0',
            'new_value': '-123.456'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.redis_conn.lindex(list_key, 0), '-123.456')
        
        # Test updating zset member with negative score
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        response = self.client.post(url, {
            'action': 'update_zset_member_score',
            'member': 'numeric_member',
            'new_score': '-5.75'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.redis_conn.zscore(zset_key, 'numeric_member'), -5.75)
