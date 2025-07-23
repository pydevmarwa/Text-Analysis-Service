import os
import logging

# Base dir = dossier racine du projet dans le conteneur => /app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'service.log')

logger = logging.getLogger("text_analysis_service")
logger.setLevel(logging.INFO)

# Clear handlers pour éviter les doublons
if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

# Console handler
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# File handler
fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(formatter)
logger.addHandler(fh)
