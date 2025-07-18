import asyncio
import random
from app.config import PROCESSING

async def simulate_heavy_processing() -> float:
    """
    Simulates a heavy CPU-bound task via async sleep.

    Returns:
        float: Simulated processing duration in seconds.
    """
    delay = random.uniform(
        PROCESSING['MIN_PROCESSING_TIME'],
        PROCESSING['MAX_PROCESSING_TIME']
    )
    await asyncio.sleep(delay)
    return delay

async def calculate_toxicity_score(text: str) -> int:
    """
    Simulate toxicity scoring (placeholder for a real NLP model).

    Args:
        text (str): Text to score.

    Returns:
        int: Toxicity score between 0 and 100.
    """
    await asyncio.sleep(0)  # Keep async signature
    return random.randint(0, 100)
