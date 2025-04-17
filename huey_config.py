# huey_config.py
from huey import RedisHuey

HUEY = RedisHuey(
    'room', 
    host='localhost', 
    port=6379
)
