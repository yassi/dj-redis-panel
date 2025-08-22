"""
Tests for the Django Redis Panel collection member delete functionality.

This module tests the ability to delete individual members from Redis collections
(lists, sets, sorted sets, and hashes) through the key detail view.
"""
import redis
from django.urls import reverse
from .base import RedisTestCase


class TestCollectionMemberDelete(RedisTestCase):
    """Test cases for deleting individual members from Redis collections."""
    
    def test_delete_list_item_success(self):
        """Test successful deletion of a list item by index."""
        # Create a test list
        list_key = 'test:delete_list'
        self.redis_conn.rpush(list_key, 'item0', 'item1', 'item2', 'item3')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Delete item at index 1
        response = self.client.post(url, {
            'action': 'delete_list_item',
            'index': '1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "List item deleted successfully")
        
        # Verify the item was deleted from Redis
        remaining_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(remaining_items, ['item0', 'item2', 'item3'])
        self.assertEqual(len(remaining_items), 3)
    
    def test_delete_list_item_invalid_index(self):
        """Test deletion with invalid list index."""
        # Create a test list with 3 items
        list_key = 'test:delete_list_invalid'
        self.redis_conn.rpush(list_key, 'item0', 'item1', 'item2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Try to delete item at index 5 (out of range)
        response = self.client.post(url, {
            'action': 'delete_list_item',
            'index': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Index 5 is out of range", response.context['error_message'])
        
        # Verify no items were deleted
        remaining_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(remaining_items), 3)
    
    def test_delete_list_item_non_numeric_index(self):
        """Test deletion with non-numeric index."""
        # Create a test list
        list_key = 'test:delete_list_non_numeric'
        self.redis_conn.rpush(list_key, 'item0', 'item1')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        
        # Try to delete with non-numeric index
        response = self.client.post(url, {
            'action': 'delete_list_item',
            'index': 'invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Invalid index provided")
        
        # Verify no items were deleted
        remaining_items = self.redis_conn.lrange(list_key, 0, -1)
        self.assertEqual(len(remaining_items), 2)
    
    def test_delete_list_item_disabled(self):
        """Test list item deletion when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        list_key = 'test:delete_list_disabled'
        conn_14.rpush(list_key, 'item0', 'item1', 'item2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, list_key])
        response = self.client.post(url, {
            'action': 'delete_list_item',
            'index': '1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no items were deleted
        remaining_items = conn_14.lrange(list_key, 0, -1)
        self.assertEqual(len(remaining_items), 3)
        
        # Cleanup
        conn_14.delete(list_key)
    
    def test_delete_set_member_success(self):
        """Test successful deletion of a set member."""
        # Create a test set
        set_key = 'test:delete_set'
        self.redis_conn.sadd(set_key, 'member1', 'member2', 'member3')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Delete member2
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'member2'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Set member deleted successfully")
        
        # Verify the member was deleted from Redis
        remaining_members = self.redis_conn.smembers(set_key)
        self.assertEqual(remaining_members, {'member1', 'member3'})
        self.assertEqual(len(remaining_members), 2)
    
    def test_delete_set_member_nonexistent(self):
        """Test deletion of non-existent set member."""
        # Create a test set
        set_key = 'test:delete_set_nonexistent'
        self.redis_conn.sadd(set_key, 'member1', 'member2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        
        # Try to delete non-existent member
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'nonexistent'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Member does not exist in set")
        
        # Verify no members were deleted
        remaining_members = self.redis_conn.smembers(set_key)
        self.assertEqual(len(remaining_members), 2)
    
    def test_delete_set_member_disabled(self):
        """Test set member deletion when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        set_key = 'test:delete_set_disabled'
        conn_14.sadd(set_key, 'member1', 'member2')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, set_key])
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'member1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no members were deleted
        remaining_members = conn_14.smembers(set_key)
        self.assertEqual(len(remaining_members), 2)
        
        # Cleanup
        conn_14.delete(set_key)
    
    def test_delete_zset_member_success(self):
        """Test successful deletion of a sorted set member."""
        # Create a test sorted set
        zset_key = 'test:delete_zset'
        self.redis_conn.zadd(zset_key, {'member1': 1.0, 'member2': 2.0, 'member3': 3.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Delete member2
        response = self.client.post(url, {
            'action': 'delete_zset_member',
            'member': 'member2'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Sorted set member deleted successfully")
        
        # Verify the member was deleted from Redis
        remaining_members = self.redis_conn.zrange(zset_key, 0, -1, withscores=True)
        expected_members = [('member1', 1.0), ('member3', 3.0)]
        self.assertEqual(remaining_members, expected_members)
        self.assertEqual(len(remaining_members), 2)
    
    def test_delete_zset_member_nonexistent(self):
        """Test deletion of non-existent sorted set member."""
        # Create a test sorted set
        zset_key = 'test:delete_zset_nonexistent'
        self.redis_conn.zadd(zset_key, {'member1': 1.0, 'member2': 2.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        
        # Try to delete non-existent member
        response = self.client.post(url, {
            'action': 'delete_zset_member',
            'member': 'nonexistent'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Member does not exist in sorted set")
        
        # Verify no members were deleted
        remaining_members = self.redis_conn.zrange(zset_key, 0, -1)
        self.assertEqual(len(remaining_members), 2)
    
    def test_delete_zset_member_disabled(self):
        """Test sorted set member deletion when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        zset_key = 'test:delete_zset_disabled'
        conn_14.zadd(zset_key, {'member1': 1.0, 'member2': 2.0})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, zset_key])
        response = self.client.post(url, {
            'action': 'delete_zset_member',
            'member': 'member1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no members were deleted
        remaining_members = conn_14.zrange(zset_key, 0, -1)
        self.assertEqual(len(remaining_members), 2)
        
        # Cleanup
        conn_14.delete(zset_key)
    
    def test_delete_hash_field_success(self):
        """Test successful deletion of a hash field."""
        # Create a test hash
        hash_key = 'test:delete_hash'
        self.redis_conn.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2', 'field3': 'value3'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Delete field2
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'field2'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field deleted successfully")
        
        # Verify the field was deleted from Redis
        remaining_fields = self.redis_conn.hgetall(hash_key)
        expected_fields = {'field1': 'value1', 'field3': 'value3'}
        self.assertEqual(remaining_fields, expected_fields)
        self.assertEqual(len(remaining_fields), 2)
    
    def test_delete_hash_field_nonexistent(self):
        """Test deletion of non-existent hash field."""
        # Create a test hash
        hash_key = 'test:delete_hash_nonexistent'
        self.redis_conn.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        
        # Try to delete non-existent field
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'nonexistent'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Field does not exist in hash")
        
        # Verify no fields were deleted
        remaining_fields = self.redis_conn.hgetall(hash_key)
        self.assertEqual(len(remaining_fields), 2)
    
    def test_delete_hash_field_disabled(self):
        """Test hash field deletion when editing is disabled."""
        # Create key in test database 14 (no_features instance)
        conn_14 = redis.Redis(host='127.0.0.1', port=6379, db=14, decode_responses=True)
        hash_key = 'test:delete_hash_disabled'
        conn_14.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2'})
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis_no_features', 14, hash_key])
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'field1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], "Key editing is disabled for this instance")
        
        # Verify no fields were deleted
        remaining_fields = conn_14.hgetall(hash_key)
        self.assertEqual(len(remaining_fields), 2)
        
        # Cleanup
        conn_14.delete(hash_key)
    
    def test_delete_member_wrong_key_type(self):
        """Test deletion operations on wrong key types."""
        # Create different key types
        string_key = 'test:wrong_type_string'
        list_key = 'test:wrong_type_list'
        
        self.redis_conn.set(string_key, 'string_value')
        self.redis_conn.rpush(list_key, 'item1', 'item2')
        
        # Try to delete set member from a string key
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, string_key])
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'anything'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("is not a set", response.context['error_message'])
        
        # Try to delete hash field from a list key
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'anything'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("is not a hash", response.context['error_message'])
    
    def test_delete_member_nonexistent_key(self):
        """Test deletion operations on non-existent keys."""
        nonexistent_key = 'test:nonexistent_key'
        
        # Ensure the key doesn't exist
        self.redis_conn.delete(nonexistent_key)
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, nonexistent_key])
        
        # Try to delete from non-existent key - should get 404
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'anything'
        })
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_member_with_pagination(self):
        """Test deletion of members in paginated collections."""
        # Create a large list to trigger pagination
        large_list_key = 'test:delete_paginated_list'
        for i in range(150):
            self.redis_conn.rpush(large_list_key, f'item_{i:03d}')
        
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, large_list_key])
        
        # Go to second page and delete an item
        response = self.client.post(url + '?page=2&per_page=50', {
            'action': 'delete_list_item',
            'index': '75'  # Item at position 75
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.context['success_message'])
        
        # Verify the item was deleted
        remaining_items = self.redis_conn.lrange(large_list_key, 0, -1)
        self.assertEqual(len(remaining_items), 149)
        self.assertNotIn('item_075', remaining_items)
        
        # Verify pagination context is maintained
        self.assertTrue(response.context['is_paginated'])
    
    def test_delete_member_special_characters(self):
        """Test deletion of members with special characters."""
        # Create collections with special character members
        set_key = 'test:delete_special_chars'
        hash_key = 'test:delete_special_hash'
        
        special_members = ['member with spaces', 'member@with#symbols', 'member:with:colons', 'member\nwith\nnewlines']
        
        # Add to set
        for member in special_members:
            self.redis_conn.sadd(set_key, member)
        
        # Add to hash
        for i, member in enumerate(special_members):
            self.redis_conn.hset(hash_key, member, f'value_{i}')
        
        # Test deleting from set
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'member with spaces'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Set member deleted successfully")
        
        # Verify deletion
        remaining_members = self.redis_conn.smembers(set_key)
        self.assertNotIn('member with spaces', remaining_members)
        self.assertEqual(len(remaining_members), 3)
        
        # Test deleting from hash
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'member@with#symbols'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field deleted successfully")
        
        # Verify deletion
        remaining_fields = self.redis_conn.hgetall(hash_key)
        self.assertNotIn('member@with#symbols', remaining_fields)
        self.assertEqual(len(remaining_fields), 3)
    
    def test_delete_member_empty_collection_after_deletion(self):
        """Test deletion that results in empty collection."""
        # Create collections with single items
        set_key = 'test:delete_to_empty_set'
        hash_key = 'test:delete_to_empty_hash'
        list_key = 'test:delete_to_empty_list'
        zset_key = 'test:delete_to_empty_zset'
        
        self.redis_conn.sadd(set_key, 'only_member')
        self.redis_conn.hset(hash_key, 'only_field', 'only_value')
        self.redis_conn.rpush(list_key, 'only_item')
        self.redis_conn.zadd(zset_key, {'only_member': 1.0})
        
        # Delete from set
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, set_key])
        response = self.client.post(url, {
            'action': 'delete_set_member',
            'member': 'only_member'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Set member deleted successfully")
        self.assertEqual(self.redis_conn.scard(set_key), 0)
        
        # Delete from hash
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, hash_key])
        response = self.client.post(url, {
            'action': 'delete_hash_field',
            'field': 'only_field'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Hash field deleted successfully")
        self.assertEqual(self.redis_conn.hlen(hash_key), 0)
        
        # Delete from list
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, list_key])
        response = self.client.post(url, {
            'action': 'delete_list_item',
            'index': '0'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "List item deleted successfully")
        self.assertEqual(self.redis_conn.llen(list_key), 0)
        
        # Delete from sorted set
        url = reverse('dj_redis_panel:key_detail', args=['test_redis', 15, zset_key])
        response = self.client.post(url, {
            'action': 'delete_zset_member',
            'member': 'only_member'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success_message'], "Sorted set member deleted successfully")
        self.assertEqual(self.redis_conn.zcard(zset_key), 0)
