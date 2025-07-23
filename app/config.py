import os

"""
Centralized configuration for the text analysis service.
Reads environment variables (Docker Compose) or uses defaults.
"""

RABBITMQ = {
    'HOST': os.getenv('RABBITMQ_HOST', 'localhost'),
    'PORT': int(os.getenv('RABBITMQ_PORT', 5672)),
    'USER': os.getenv('RABBITMQ_USER', 'guest'),
    'PASSWORD': os.getenv('RABBITMQ_PASSWORD', 'guest'),
    'INPUT_QUEUE': os.getenv('RABBITMQ_INPUT_QUEUE', 'incoming_texts'),
    'OUTPUT_QUEUE': os.getenv('RABBITMQ_OUTPUT_QUEUE', 'processed_texts'),
}

MONGO = {
    'URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017'),
    'DB_NAME': os.getenv('MONGO_DB_NAME', 'text_analysis'),
    'COLLECTION': os.getenv('MONGO_COLLECTION', 'processed_messages'),
}

PROCESSING = {
    'MIN_PROCESSING_TIME': float(os.getenv('MIN_PROCESSING_TIME', 2)),
    'MAX_PROCESSING_TIME': float(os.getenv('MAX_PROCESSING_TIME', 15)),
    'TOXICITY_THRESHOLD': int(os.getenv('TOXICITY_THRESHOLD', 70)),
}
