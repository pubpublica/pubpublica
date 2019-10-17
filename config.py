config = {
    "BUILD": {
        "LOCAL_CONFIG_PATH": "config/",
        "DEPENDENCIES": [
            "python3",
            "python3-pip",
            "python3-venv",
            "redis-server",
            "nginx",
        ],
    },
    "PROVISION": {},
    "DEPLOY": {
        "USER": "pubpublica",
        "GROUP": "pubpublica",
        "APP_PATH": "pubpublica/",
    },
    "PUBPUBLICA": {"PUBLICATIONS_PATH": "publications/"},
    "FLASK": {"FLASK_SECRET_KEY_PATH": "cayenne/flask/key"},
    "REDIS": {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD_PATH": "cayenne/redis/key",
    },
}
