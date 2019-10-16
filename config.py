config = {
    "LOCAL_CONFIG_PATH": "config/",
    "PUBLICATIONS_PATH": "publications/",
    "PROVISION": {},
    "DEPLOY": {
        "USER": "pubpublica",
        "GROUP": "pubpublica",
        "APP_PATH": "/var/www/pubpublica/",
    },
    "FLASK": {"FLASK_SECRET_KEY_PATH": "cayenne/flask/key"},
    "REDIS": {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD_PATH": "cayenne/redis/key",
    },
}
