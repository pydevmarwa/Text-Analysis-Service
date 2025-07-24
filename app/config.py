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
    'PREFETCH_COUNT': int(os.getenv('RABBITMQ_PREFETCH_COUNT', 20)),
    'MAX_RETRIES': int(os.getenv('RABBITMQ_MAX_RETRIES', 3)),
    'DLX_EXCHANGE': os.getenv('RABBITMQ_DLX_EXCHANGE', 'dlx_exchange'),
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
    'MAX_CONCURRENT_TASKS': int(os.getenv('MAX_CONCURRENT_TASKS', 10))  # adapt based on load and machine

}
