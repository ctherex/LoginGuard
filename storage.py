
import json
import os
import time
import uuid

import redis


MAX_FAILURES = 5
TIME_WINDOW = 60
LOCKOUT_DURATION = 60
MAX_EVENTS = 100

client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

# Atomically record a failure in a rolling time window.
# KEYS[1] = failure sorted set
# ARGV[1] = current timestamp
# ARGV[2] = unique event ID
# ARGV[3] = window length
FAILURE_SCRIPT = client.register_script("""
local key = KEYS[1]
local now = tonumber(ARGV[1])
local member = ARGV[2]
local window = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE',
           key, '-inf', now - window)
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, math.ceil(window) + 2)

return redis.call('ZCARD', key)
""")

# Account failures and lockout activation happen atomically.
# Returns {failure_count, lockout_started, remaining_seconds}.
ACCOUNT_SCRIPT = client.register_script("""
local failures = KEYS[1]
local lockout = KEYS[2]

local now = tonumber(ARGV[1])
local member = ARGV[2]
local window = tonumber(ARGV[3])
local threshold = tonumber(ARGV[4])
local duration = tonumber(ARGV[5])

local remaining = redis.call('TTL', lockout)
if remaining > 0 then
    return {0, 0, remaining}
end

redis.call('ZREMRANGEBYSCORE',
           failures, '-inf', now - window)
redis.call('ZADD', failures, now, member)
redis.call('EXPIRE', failures, math.ceil(window) + 2)

local count = redis.call('ZCARD', failures)

if count >= threshold then
    redis.call('SET', lockout, '1', 'EX', duration)
    redis.call('DEL', failures)
    return {count, 1, duration}
end

return {count, 0, 0}
""")


def failure_key(ip):
    return f"loginguard:ip:{ip}:failures"


def account_failure_key(username):
    return f"loginguard:account:{username}:failures"


def lockout_key(username):
    return f"loginguard:lockout:{username}"


def record_ip_failure(ip):
    return int(FAILURE_SCRIPT(
        keys=[failure_key(ip)],
        args=[time.time(), uuid.uuid4().hex, TIME_WINDOW]
    ))


def get_ip_failure_count(ip):
    key = failure_key(ip)
    now = time.time()

    with client.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(key, "-inf", now - TIME_WINDOW)
        pipe.zcard(key)
        results = pipe.execute()

    return int(results[1])


def record_account_failure(username):
    count, locked, remaining = ACCOUNT_SCRIPT(
        keys=[
            account_failure_key(username),
            lockout_key(username)
        ],
        args=[
            time.time(),
            uuid.uuid4().hex,
            TIME_WINDOW,
            MAX_FAILURES,
            LOCKOUT_DURATION
        ]
    )

    return {
        "count": int(count),
        "locked": bool(locked),
        "remaining_seconds": int(remaining)
    }


def get_lockout_remaining(username):
    remaining = client.ttl(lockout_key(username))
    return max(0, remaining)


def reset_account_failures(username):
    client.delete(account_failure_key(username))


def get_locked_accounts(usernames):
    accounts = []

    for username in usernames:
        remaining = get_lockout_remaining(username)

        if remaining > 0:
            accounts.append({
                "username": username,
                "remaining_seconds": remaining
            })

    return accounts


def save_event(event):
    serialized = json.dumps(event)

    with client.pipeline(transaction=True) as pipe:
        pipe.lpush("loginguard:events", serialized)
        pipe.ltrim("loginguard:events", 0, MAX_EVENTS - 1)
        pipe.execute()


def get_events():
    entries = client.lrange(
        "loginguard:events", 0, MAX_EVENTS - 1
    )

    # Return oldest first, matching the original app.
    return [json.loads(entry) for entry in reversed(entries)]


def redis_healthy():
    return bool(client.ping())
