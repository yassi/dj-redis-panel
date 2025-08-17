from django.core.management.base import BaseCommand
from dj_redis_panel.redis_utils import RedisPanelUtils
import json
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Populate Redis instances with test data for testing, including support for very large collections"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing keys before populating",
        )
        parser.add_argument(
            "--instance",
            type=str,
            help="Specific Redis instance to populate (default: all)",
        )
        parser.add_argument(
            "--db",
            type=int,
            nargs="+",
            help="Specific database numbers to populate (e.g., --db 0 1 2)",
        )
        parser.add_argument(
            "--all-dbs",
            action="store_true",
            help="Populate all available databases (0-15)",
        )
        parser.add_argument(
            "--keys",
            type=int,
            default=100,
            help="Number of keys to create (default: 100)",
        )
        parser.add_argument(
            "--large-collections",
            action="store_true",
            help="Create some collections with very large numbers of members (hundreds to thousands)",
        )
        parser.add_argument(
            "--large-collection-count",
            type=int,
            default=5,
            help="Number of large collections to create per database (default: 5)",
        )
        parser.add_argument(
            "--max-collection-size",
            type=int,
            default=1000,
            help="Maximum size for large collections (default: 1000)",
        )

    def handle(self, *args, **options):
        instances = RedisPanelUtils.get_instances()

        if not instances:
            self.stdout.write(
                self.style.ERROR(
                    "No Redis instances configured. Please check DJ_REDIS_PANEL_SETTINGS."
                )
            )
            return

        target_instances = (
            [options["instance"]] if options["instance"] else instances.keys()
        )

        # Determine which databases to populate
        if options["all_dbs"]:
            target_dbs = list(range(16))  # All Redis databases (0-15)
        elif options["db"]:
            target_dbs = options["db"]
            # Validate database numbers
            invalid_dbs = [db for db in target_dbs if db < 0 or db > 15]
            if invalid_dbs:
                self.stdout.write(
                    self.style.ERROR(
                        f"Invalid database numbers: {invalid_dbs}. Must be between 0-15."
                    )
                )
                return
        else:
            target_dbs = [0, 1, 2]  # Default databases

        for instance_alias in target_instances:
            if instance_alias not in instances:
                self.stdout.write(
                    self.style.ERROR(
                        f'Instance "{instance_alias}" not found in configuration.'
                    )
                )
                continue

            self.stdout.write(f"Populating Redis instance: {instance_alias}")
            if len(target_dbs) == 16:
                self.stdout.write("  Target: All databases (0-15)")
            else:
                self.stdout.write(f"  Target databases: {sorted(target_dbs)}")
            self.stdout.write(f"  Keys to create: {options['keys']}")
            if options["large_collections"]:
                self.stdout.write(f"  Large collections: {options['large_collection_count']} per database")
                self.stdout.write(f"  Max collection size: {options['max_collection_size']}")
            self.populate_instance(
                instance_alias, options["clear"], target_dbs, options["keys"], options
            )

        self.stdout.write(
            self.style.SUCCESS("Successfully populated Redis instances with test data!")
        )

    def populate_instance(
        self, instance_alias, clear_first=False, target_dbs=None, key_count=100, options=None
    ):
        if target_dbs is None:
            target_dbs = [0, 1, 2]

        try:
            redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)

            # Populate specified databases
            for db in target_dbs:
                try:
                    redis_conn.select(db)

                    if clear_first:
                        redis_conn.flushdb()
                        self.stdout.write(f"  Cleared database {db}")

                    self.stdout.write(f"  Populating database {db}...")
                    self.create_test_data(redis_conn, db, key_count, options)
                except Exception as db_error:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Could not access database {db}: {str(db_error)}"
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error populating {instance_alias}: {str(e)}")
            )

    def create_test_data(self, redis_conn, db_num, key_count=100, options=None):
        """Create random test data up to the specified key count"""
        if options is None:
            options = {}

        # Key type distribution (percentages)
        string_ratio = 0.70  # 70% strings
        list_ratio = 0.10  # 10% lists
        set_ratio = 0.08  # 8% sets
        hash_ratio = 0.08  # 8% hashes
        zset_ratio = 0.04  # 4% sorted sets

        # Calculate counts for each type
        string_count = int(key_count * string_ratio)
        list_count = int(key_count * list_ratio)
        set_count = int(key_count * set_ratio)
        hash_count = int(key_count * hash_ratio)
        zset_count = int(key_count * zset_ratio)

        # Lets add some string keys in case we are short on keys
        total_allocated = sum(
            [string_count, list_count, set_count, hash_count, zset_count]
        )
        if total_allocated < key_count:
            string_count += key_count - total_allocated

        created_keys = 0
        ttl_keys = 0

        # Create string keys with various patterns
        key_patterns = [
            "user:{id}:profile",
            "session:{id}",
            "cache:product:{id}",
            "api:weather:{city}",
            "config:app:{setting}",
            "counter:{metric}",
            "lock:user:{id}",
            "feature:{name}:enabled",
            "temp:token:{id}",
            "temp:otp:{id}",
        ]

        cities = [
            "london",
            "paris",
            "tokyo",
            "newyork",
            "sydney",
            "berlin",
            "moscow",
            "madrid",
            "rome",
            "vienna",
        ]
        settings = [
            "database_url",
            "debug_mode",
            "max_connections",
            "timeout",
            "cache_ttl",
        ]
        metrics = ["page_views", "api_calls", "downloads", "uploads", "errors"]
        features = ["new_ui", "beta_access", "dark_mode", "notifications", "analytics"]

        for i in range(string_count):
            pattern = random.choice(key_patterns)

            if "{city}" in pattern:
                key = pattern.format(city=random.choice(cities))
                value = json.dumps(
                    {
                        "city": random.choice(cities),
                        "temperature": random.randint(-10, 35),
                        "humidity": random.randint(30, 90),
                        "last_updated": datetime.now().isoformat(),
                    }
                )
            elif "user:" in pattern and ":profile" in pattern:
                user_id = random.randint(1, 10000)
                key = pattern.format(id=user_id)
                value = json.dumps(
                    {
                        "name": f"User {user_id}",
                        "email": f"user{user_id}@example.com",
                        "active": random.choice([True, False]),
                        "created": datetime.now().isoformat(),
                    }
                )
            elif "session:" in pattern:
                key = pattern.format(id=random.randint(100000, 999999))
                value = json.dumps(
                    {
                        "user_id": random.randint(1, 100),
                        "login_time": datetime.now().isoformat(),
                        "ip_address": f"192.168.1.{random.randint(1, 255)}",
                    }
                )
            elif "product:" in pattern:
                product_id = random.randint(1, 1000)
                key = pattern.format(id=product_id)
                value = json.dumps(
                    {
                        "id": product_id,
                        "name": f"Product {product_id}",
                        "price": round(random.uniform(10.0, 1000.0), 2),
                        "in_stock": random.randint(0, 100),
                    }
                )
            elif "config:" in pattern:
                key = pattern.format(setting=random.choice(settings))
                value = random.choice(
                    ["true", "false", "postgres://localhost:5432/myapp", "100", "3600"]
                )
            elif "counter:" in pattern:
                key = pattern.format(metric=random.choice(metrics))
                value = str(random.randint(1000, 50000))
            elif "lock:" in pattern:
                key = pattern.format(id=random.randint(1, 1000))
                value = random.choice(["processing", "completed", "failed", "pending"])
            elif "feature:" in pattern:
                key = pattern.format(name=random.choice(features))
                value = random.choice(["true", "false"])
            elif "temp:" in pattern:
                key = pattern.format(id=random.randint(1000, 999999))
                value = f"temporary_value_{random.randint(1, 1000)}"
            else:
                key = f"key:{i}:db{db_num}"
                value = f"value_{i}_{random.randint(1, 1000)}"

            # Some keys get TTL
            if "temp:" in key and random.random() < 0.8:  # 80% of temp keys get TTL
                redis_conn.setex(key, random.randint(300, 3600), value)
                ttl_keys += 1
            else:
                redis_conn.set(key, value)

            created_keys += 1

        # Create lists
        for i in range(list_count):
            list_key = f"list:queue:{i}:db{db_num}"
            redis_conn.delete(list_key)  # Clear existing
            for j in range(random.randint(3, 10)):
                redis_conn.lpush(list_key, f"task_{i}_{j}_{random.randint(1, 1000)}")
            created_keys += 1

        # Create sets
        categories = ["tags", "categories", "skills", "permissions", "roles", "groups"]
        for i in range(set_count):
            category = random.choice(categories)
            set_key = f"set:{category}:{i}:db{db_num}"
            redis_conn.delete(set_key)  # Clear existing
            items = [
                f"{category}_{j}_{random.randint(1, 100)}"
                for j in range(random.randint(3, 15))
            ]
            redis_conn.sadd(set_key, *items)
            created_keys += 1

        # Create hashes
        for i in range(hash_count):
            hash_key = f"hash:stats:{i}:db{db_num}"
            redis_conn.delete(hash_key)  # Clear existing
            hash_data = {
                "views": random.randint(100, 10000),
                "likes": random.randint(10, 1000),
                "shares": random.randint(1, 100),
                "comments": random.randint(0, 500),
                "last_updated": str(int(datetime.now().timestamp())),
            }
            redis_conn.hset(hash_key, mapping=hash_data)
            created_keys += 1

        # Create sorted sets (leaderboards)
        boards = ["users", "games", "scores", "points", "rankings"]
        for i in range(zset_count):
            board = random.choice(boards)
            zset_key = f"zset:leaderboard:{board}:{i}:db{db_num}"
            redis_conn.delete(zset_key)  # Clear existing
            for j in range(random.randint(5, 20)):
                redis_conn.zadd(
                    zset_key,
                    {
                        f"{board}_player_{j}_{random.randint(1, 1000)}": random.randint(
                            100, 9999
                        )
                    },
                )
            created_keys += 1

        # Create large collections if requested
        large_collections_created = 0
        if options.get("large_collections", False):
            large_collection_count = options.get("large_collection_count", 5)
            max_collection_size = options.get("max_collection_size", 1000)
            large_collections_created = self.create_large_collections(
                redis_conn, db_num, large_collection_count, max_collection_size
            )
            created_keys += large_collections_created

        # Log what was created
        self.stdout.write(f"    Created {created_keys} total keys:")
        self.stdout.write(f"      - {string_count} string keys")
        self.stdout.write(f"      - {list_count} lists")
        self.stdout.write(f"      - {set_count} sets")
        self.stdout.write(f"      - {hash_count} hashes")
        self.stdout.write(f"      - {zset_count} sorted sets")
        if large_collections_created > 0:
            self.stdout.write(f"      - {large_collections_created} large collections")
        if ttl_keys > 0:
            self.stdout.write(f"      - {ttl_keys} keys with TTL")

    def create_large_collections(self, redis_conn, db_num, collection_count, max_size):
        """Create large collections with hundreds to thousands of members"""
        created_count = 0
        
        # Distribute collection types
        collection_types = ['list', 'set', 'hash', 'zset']
        collections_per_type = max(1, collection_count // len(collection_types))
        remaining = collection_count % len(collection_types)
        
        for collection_type in collection_types:
            type_count = collections_per_type + (1 if remaining > 0 else 0)
            remaining -= 1
            
            for i in range(type_count):
                size = random.randint(max(100, max_size // 10), max_size)
                
                if collection_type == 'list':
                    created_count += self.create_large_list(redis_conn, db_num, i, size)
                elif collection_type == 'set':
                    created_count += self.create_large_set(redis_conn, db_num, i, size)
                elif collection_type == 'hash':
                    created_count += self.create_large_hash(redis_conn, db_num, i, size)
                elif collection_type == 'zset':
                    created_count += self.create_large_zset(redis_conn, db_num, i, size)
        
        return created_count

    def create_large_list(self, redis_conn, db_num, index, size):
        """Create a large list with many items"""
        list_key = f"large:list:events:{index}:db{db_num}"
        redis_conn.delete(list_key)  # Clear existing
        
        # Use pipeline for better performance
        pipe = redis_conn.pipeline()
        
        # Create realistic event log entries
        event_types = ['login', 'logout', 'purchase', 'view', 'click', 'search', 'error', 'warning']
        user_agents = ['Chrome/91.0', 'Firefox/89.0', 'Safari/14.1', 'Edge/91.0']
        
        for i in range(size):
            event_data = {
                'timestamp': (datetime.now() - timedelta(seconds=random.randint(0, 86400))).isoformat(),
                'event_type': random.choice(event_types),
                'user_id': random.randint(1, 10000),
                'session_id': f"sess_{random.randint(100000, 999999)}",
                'ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'user_agent': random.choice(user_agents),
                'page': f"/page/{random.randint(1, 100)}"
            }
            pipe.lpush(list_key, json.dumps(event_data))
            
            # Execute in batches for memory efficiency
            if i % 1000 == 0:
                pipe.execute()
                pipe = redis_conn.pipeline()
        
        # Execute remaining commands
        pipe.execute()
        
        self.stdout.write(f"      Created large list '{list_key}' with {size} events")
        return 1

    def create_large_set(self, redis_conn, db_num, index, size):
        """Create a large set with many unique items"""
        set_key = f"large:set:unique_visitors:{index}:db{db_num}"
        redis_conn.delete(set_key)  # Clear existing
        
        # Use pipeline for better performance
        pipe = redis_conn.pipeline()
        
        # Generate unique visitor IDs
        batch_size = 1000
        for i in range(0, size, batch_size):
            batch_items = []
            for j in range(min(batch_size, size - i)):
                visitor_id = f"visitor_{random.randint(1, 1000000)}_{i}_{j}"
                batch_items.append(visitor_id)
            
            if batch_items:
                pipe.sadd(set_key, *batch_items)
                pipe.execute()
                pipe = redis_conn.pipeline()
        
        self.stdout.write(f"      Created large set '{set_key}' with {size} unique visitors")
        return 1

    def create_large_hash(self, redis_conn, db_num, index, size):
        """Create a large hash with many fields"""
        hash_key = f"large:hash:user_metrics:{index}:db{db_num}"
        redis_conn.delete(hash_key)  # Clear existing
        
        # Use pipeline for better performance
        pipe = redis_conn.pipeline()
        
        # Create user metrics
        batch_size = 1000
        for i in range(0, size, batch_size):
            batch_data = {}
            for j in range(min(batch_size, size - i)):
                user_id = f"user_{i}_{j}"
                batch_data[f"{user_id}:views"] = random.randint(1, 1000)
                batch_data[f"{user_id}:clicks"] = random.randint(1, 100)
                batch_data[f"{user_id}:time_spent"] = random.randint(60, 7200)
                batch_data[f"{user_id}:last_seen"] = str(int(datetime.now().timestamp()))
            
            if batch_data:
                pipe.hset(hash_key, mapping=batch_data)
                pipe.execute()
                pipe = redis_conn.pipeline()
        
        self.stdout.write(f"      Created large hash '{hash_key}' with {size * 4} fields")
        return 1

    def create_large_zset(self, redis_conn, db_num, index, size):
        """Create a large sorted set with many scored items"""
        zset_key = f"large:zset:global_leaderboard:{index}:db{db_num}"
        redis_conn.delete(zset_key)  # Clear existing
        
        # Use pipeline for better performance
        pipe = redis_conn.pipeline()
        
        # Create global leaderboard
        batch_size = 1000
        for i in range(0, size, batch_size):
            batch_data = {}
            for j in range(min(batch_size, size - i)):
                player_name = f"player_{i}_{j}_{random.randint(1000, 9999)}"
                score = random.randint(1, 1000000)
                batch_data[player_name] = score
            
            if batch_data:
                pipe.zadd(zset_key, batch_data)
                pipe.execute()
                pipe = redis_conn.pipeline()
        
        self.stdout.write(f"      Created large sorted set '{zset_key}' with {size} players")
        return 1
