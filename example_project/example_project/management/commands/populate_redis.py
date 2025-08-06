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
            self.populate_instance(
                instance_alias, options["clear"], target_dbs, options["keys"]
            )

        self.stdout.write(
            self.style.SUCCESS("Successfully populated Redis instances with test data!")
        )

    def populate_instance(
        self, instance_alias, clear_first=False, target_dbs=None, key_count=100
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
                    self.create_test_data(redis_conn, db, key_count)
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

    def create_test_data(self, redis_conn, db_num, key_count=100):
        """Create random test data up to the specified key count"""

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

        # Log what was created
        self.stdout.write(f"    Created {created_keys} total keys:")
        self.stdout.write(f"      - {string_count} string keys")
        self.stdout.write(f"      - {list_count} lists")
        self.stdout.write(f"      - {set_count} sets")
        self.stdout.write(f"      - {hash_count} hashes")
        self.stdout.write(f"      - {zset_count} sorted sets")
        if ttl_keys > 0:
            self.stdout.write(f"      - {ttl_keys} keys with TTL")
