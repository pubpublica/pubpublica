config = {
    "BUILD": {"LOCAL_CONFIG_PATH": "config/"},
    "PROVISION": {
        "DEPENDENCIES": [
            "python3",
            "python3-pip",
            "python3-venv",
            "pkg-config",
            "libsystemd-dev",
            "redis-server",
            "nginx",
        ]
    },
    "DEPLOY": {
        "USER": "pubpublica",
        "GROUP": "pubpublica",
        "APP_PATH": "/srv/pubpublica",
        "PRODUCTION_PATH": "/var/www/pubpublica",
        "SOCKET_PATH": "/var/run/pubpublica/pubpublica.sock",
        "INCLUDES": [
            "__version__.py",
            "requirements.txt",
            "gunicorn.py",
            "uwsgi.ini",
            "wsgi.py",
            "publications/",
            "pubpublica/",
        ],
        "DEPLOYED_ID_FILE": ".deployed",
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
