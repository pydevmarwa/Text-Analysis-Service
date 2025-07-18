# Text Analysis Service

Welcome to the Text Analysis Service! This lightweight microservice demonstrates 
how to process large volumes of text data asynchronously using RabbitMQ and MongoDB.

## What's Inside

- **app/**  
  Contains the main service code:
  - `__init__.py` — package marker  
  - `config.py` — central configuration (queues, database, thresholds)  
  - `consumer.py` — RabbitMQ consumer  
  - `processor.py` — main business logic: analyzes the text and prepares enriched output (calls utils) 
  - `db.py` — handles MongoDB upserts/deletions  
  - `publisher.py` — publishes enriched messages back to RabbitMQ  
  - `utils.py` —  helper functions used by the processor, like simulated delays or scoring stubs, 
     can easily be replaced later with real business logic or machine learning models. 
  - `main.py` — entry point to start the service  

- **functional_tests/**  
  End-to-end scripts for manual and batch testing:
  - `batch_test.py` — sends 500 messages, waits for processing, peeks all results  
  - `send_test_message.py` — send individual test messages  
  - `receive_test_message.py` — consume and print from the output queue  

- **tests/**  
  Unit tests for core components:
  - `__init__.py` — adds `app/` to path for pytest  
  - `test_consumer.py` — Unit test for the consumer logic  
  - `test_db.py` — Unit tests for database methods  
  - `test_processor.py` — Unit tests for text processing logic  

- **Dockerfile**  
  Builds a slim Python 3.11 image with dependencies installed.

- **docker-compose.yml**  
  Brings up RabbitMQ, MongoDB, and the service together.

- **requirements.txt**  
  Python dependencies list.

- **README.md**  
  This file, explaining how to run and test the project.

---

## Prerequisites

- Docker & Docker Compose  
- Python 3.11+  
- (Optional) `pip` for local development  

## Quick Start with Docker

1. **Clone the repo**  
   ```bash
   git clone <your-github-url>
   cd text_analysis_service
   ```

2. **Build and start**  
   ```bash
   docker-compose up --build
   ```
   - RabbitMQ management UI will be available at [http://localhost:15672](http://localhost:15672) (`guest`/`guest`).  
   - MongoDB listens on port 27017.  

3. **Check logs**  
   ```bash
   docker-compose logs -f app
   ```

---

## Running Locally

1. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

2. Start RabbitMQ and MongoDB (if not using Docker):  
   ```bash
   docker-compose up -d rabbitmq mongo
   ```

3. Run the service:  
   ```bash
   python -m app.main
   ```

---

## Testing

### Unit Tests

Run all unit tests:
```bash
pytest tests
```

### Functional Tests

- **Batch Test**  
  ```bash
  python functional_tests/batch_test.py
  ```
  Sends 500 messages (400 updates, 100 deletes), waits for processing and prints every result.

- **Single Message Test**  
  ```bash
  python functional_tests/send_test_message.py
  ```
  Modify the `batch` list in the script to send custom messages.

- **Receive Processed**  
  ```bash
  python functional_tests/receive_test_message.py
  ```
  Reads and prints messages from the `processed_texts` queue.

---

## How It Works

1. The **consumer** listens on `incoming_texts`.  
2. On each message, **processor** simulates a heavy task, scores toxicity, and reformats data.  
3. **db** module upserts or deletes records in MongoDB by message `id`.  
4. **publisher** sends enriched messages to `processed_texts`.  
5. Downstream services (or our tests) read from `processed_texts`.

---

Feel free to explore, adapt thresholds in `config.py`, or replace the simulated 
processor with a real NLP model. Good luck!


## Author

**Marwa Amri**  
Email: amri.marwa9999@gmail.com  