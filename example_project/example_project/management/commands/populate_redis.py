from django.core.management.base import BaseCommand
from dj_redis_panel.redis_utils import RedisPanelUtils
import json
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Populate Redis instances with test data for testing"

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

        for instance_alias in target_instances:
            if instance_alias not in instances:
                self.stdout.write(
                    self.style.ERROR(
                        f'Instance "{instance_alias}" not found in configuration.'
                    )
                )
                continue

            self.stdout.write(f"Populating Redis instance: {instance_alias}")
            self.populate_instance(instance_alias, options["clear"])

        self.stdout.write(
            self.style.SUCCESS("Successfully populated Redis instances with test data!")
        )

    def populate_instance(self, instance_alias, clear_first=False):
        try:
            redis_conn = RedisPanelUtils.get_redis_connection(instance_alias)

            # Test multiple databases
            for db in [0, 1, 2]:
                redis_conn.select(db)

                if clear_first:
                    redis_conn.flushdb()
                    self.stdout.write(f"  Cleared database {db}")

                self.stdout.write(f"  Populating database {db}...")
                self.create_test_data(redis_conn, db)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error populating {instance_alias}: {str(e)}")
            )

    def create_test_data(self, redis_conn, db_num):
        # String values with various prefixes
        string_data = {
            f"user:{i}:profile": json.dumps(
                {
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "active": random.choice([True, False]),
                    "created": datetime.now().isoformat(),
                }
            )
            for i in range(1, 21)
        }

        # Session keys
        session_data = {
            f"session:{random.randint(100000, 999999)}": json.dumps(
                {
                    "user_id": random.randint(1, 100),
                    "login_time": datetime.now().isoformat(),
                    "ip_address": f"192.168.1.{random.randint(1, 255)}",
                }
            )
            for _ in range(15)
        }

        # Cache keys with different patterns
        cache_data = {
            f"cache:product:{i}": json.dumps(
                {
                    "id": i,
                    "name": f"Product {i}",
                    "price": round(random.uniform(10.0, 1000.0), 2),
                    "in_stock": random.randint(0, 100),
                }
            )
            for i in range(1, 31)
        }

        # API cache keys
        api_cache_data = {
            f"api:weather:{city}": json.dumps(
                {
                    "city": city,
                    "temperature": random.randint(-10, 35),
                    "humidity": random.randint(30, 90),
                    "last_updated": datetime.now().isoformat(),
                }
            )
            for city in [
                "london",
                "paris",
                "tokyo",
                "newyork",
                "sydney",
                "berlin",
                "moscow",
            ]
        }

        # Set all string values
        for key, value in {
            **string_data,
            **session_data,
            **cache_data,
            **api_cache_data,
        }.items():
            redis_conn.set(key, value)

        # Create lists
        for i in range(1, 6):
            list_key = f"list:queue:{i}"
            redis_conn.delete(list_key)  # Clear existing
            for j in range(random.randint(5, 15)):
                redis_conn.lpush(list_key, f"task_{i}_{j}")

        # Create sets
        for category in ["tags", "categories", "skills"]:
            set_key = f"set:{category}"
            redis_conn.delete(set_key)  # Clear existing
            items = [f"{category}_{i}" for i in range(1, random.randint(5, 12))]
            redis_conn.sadd(set_key, *items)

        # Create hashes
        for i in range(1, 8):
            hash_key = f"hash:stats:{i}"
            redis_conn.delete(hash_key)  # Clear existing
            hash_data = {
                "views": random.randint(100, 10000),
                "likes": random.randint(10, 1000),
                "shares": random.randint(1, 100),
                "last_updated": str(int(datetime.now().timestamp())),
            }
            redis_conn.hset(hash_key, mapping=hash_data)

        # Create sorted sets (leaderboards)
        for board in ["users", "games", "scores"]:
            zset_key = f"zset:leaderboard:{board}"
            redis_conn.delete(zset_key)  # Clear existing
            for i in range(1, 11):
                redis_conn.zadd(
                    zset_key, {f"{board}_player_{i}": random.randint(100, 9999)}
                )

        # Create keys with TTL (expiration)
        ttl_data = {
            f"temp:token:{random.randint(1000, 9999)}": "temporary_access_token",
            f"temp:otp:{random.randint(100000, 999999)}": "one_time_password",
            f"temp:reset:{random.randint(1, 100)}": "password_reset_token",
        }

        for key, value in ttl_data.items():
            redis_conn.setex(key, random.randint(300, 3600), value)  # 5min to 1hour TTL

        # Some keys with specific patterns for testing
        test_patterns = {
            "config:app:database_url": "postgres://localhost:5432/myapp",
            "config:app:debug_mode": "true",
            "config:redis:max_connections": "100",
            "counter:page_views": str(random.randint(10000, 50000)),
            "counter:api_calls": str(random.randint(1000, 5000)),
            "lock:user:123": "processing",
            "lock:order:456": "payment_processing",
            "feature:new_ui:enabled": "true",
            "feature:beta_access:users": json.dumps([1, 5, 10, 23, 45]),
        }

        for key, value in test_patterns.items():
            redis_conn.set(key, value)

        # Log what was created
        key_count = len(
            {
                **string_data,
                **session_data,
                **cache_data,
                **api_cache_data,
                **ttl_data,
                **test_patterns,
            }
        )
        self.stdout.write(f"    Created {key_count} string keys")
        self.stdout.write(f"    Created 5 lists")
        self.stdout.write(f"    Created 3 sets")
        self.stdout.write(f"    Created 7 hashes")
        self.stdout.write(f"    Created 3 sorted sets")
        self.stdout.write(f"    Created {len(ttl_data)} keys with TTL")
