config = {
    "BUILD": {"LOCAL_CONFIG_PATH": "config/"},
    "PROVISION": {
        "DEPENDENCIES": [
            "python3",
            "python3-pip",
            "python3-venv",
            "redis-server",
            "nginx",
        ]
    },
    "DEPLOY": {
        "USER": "pubpublica",
        "GROUP": "pubpublica",
        "APP_PATH": "pubpublica/",
        "INCLUDES": [
            "__version__.py",
            "requirements.txt",
            "pubpublica.ini",
            "wsgi.py",
            "publications/",
            "pubpublica/",
        ],
    },
    "PUBPUBLICA": {
        "PUBPUBLICA_CONFIG_FILE": ".pubpublica",
        "PUBLICATIONS_PATH": "publications/",
    },
    "FLASK": {
        "FLASK_CONFIG_FILE": ".flask",
        "FLASK_SECRET_KEY_PATH": "cayenne/flask/key",
    },
    "REDIS": {
        "REDIS_CONFIG_FILE": ".redis",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD_PATH": "cayenne/redis/key",
    },
}
