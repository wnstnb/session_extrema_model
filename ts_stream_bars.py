import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API credentials
CLIENT_ID = os.getenv('TRADESTATION_KEY')
CLIENT_SECRET = os.getenv('TRADESTATION_SECRET')
REDIRECT_URI = os.getenv('TRADESTATION_REDIRECT_URI')
ACCESS_TOKEN = os.getenv('TRADESTATION_ACCESS_TOKEN')

# API endpoint
BASE_URL = "https://api.tradestation.com/v3/marketdata/stream/barcharts"

def stream_bars(symbol, interval='1', unit='Minute', session='USEQPreAndPost'):
  url = f"{BASE_URL}/{symbol}"
  
  headers = {
      "Authorization": f"Bearer {ACCESS_TOKEN}",
      "Content-Type": "application/json"
  }
  
  params = {
      "interval": interval,
      "unit": unit,
      "session": session
  }
  
  try:
      with requests.get(url, headers=headers, params=params, stream=True) as response:
          if response.status_code == 200:
              for line in response.iter_lines():
                  if line:
                      bar_data = json.loads(line)
                      print(f"Received bar for {symbol} at {datetime.now()}:")
                      print(json.dumps(bar_data, indent=2))
                      print("-" * 50)
          else:
              print(f"Error: Received status code {response.status_code}")
              print(response.text)
  except requests.exceptions.RequestException as e:
      print(f"An error occurred: {e}")

if __name__ == "__main__":
  symbol = input("Enter the symbol to stream (e.g., AAPL): ")
  interval = input("Enter the interval (default is 1): ") or "1"
  unit = input("Enter the unit (Minute, Daily, Weekly, Monthly; default is Minute): ") or "Minute"
  session = input("Enter the session (USEQPreAndPost, USEQPost, USEQPre, USEQ; default is USEQPreAndPost): ") or "USEQPreAndPost"
  
  print(f"Streaming bars for {symbol}...")
  stream_bars(symbol, interval, unit, session)