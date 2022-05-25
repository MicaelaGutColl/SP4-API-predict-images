import os

# We will store images uploaded by the user on this folder
UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# REDIS
# Queue name
REDIS_QUEUE = 'queue'
# Port
REDIS_PORT = 6379
# DB Id
REDIS_DB_ID = 1
# Host IP
REDIS_IP = '0.0.0.0'
# Sleep parameters which manages the
# interval between requests to our redis queue
SERVER_SLEEP = 0.05
