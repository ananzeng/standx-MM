import logging

from client import StandXClient
from strategy import MakerStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    client = StandXClient()
    strategy = MakerStrategy(client)
    strategy.run()
