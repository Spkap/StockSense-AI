from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, Feed, Market
from typing import List
from dotenv import load_dotenv
import os


load_dotenv()

client = WebSocketClient(
	api_key=os.getenv("POLYGON_API_KEY"),
	feed=Feed.Delayed,
	market=Market.Stocks
	)

def get_stock_data(ticker: str) -> List[WebSocketMessage]:
    
    client.subscribe(f"AM.{ticker}")
    def handle_message(msgs: List[WebSocketMessage]):
        for m in msgs:
            print(m)
    client.run(handle_message)

        


if __name__ == "__main__":
    get_stock_data("AAPL")