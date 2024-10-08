

import os
import google.generativeai as genai
from dotenv import find_dotenv, load_dotenv
from decimal import Decimal
import json
import pickle
from datetime import datetime

# Load environment variables from .env file
load_dotenv(find_dotenv())
key = os.getenv('GOOGLE_API_KEY')
import google.generativeai as genai

genai.configure(api_key=key)


import yfinance as yf

def get_stock_price(symbol: str):
    """Get the most recent price of a stock."""
    stock = yf.Ticker(symbol)
    price = stock.history(period="1d")['Close'].iloc[-1]
    print(f"TRADEBOT: Most recent price of {symbol} is ${price:.2f}")
    return price

def buy_stock(symbol: str, quantity: int):
    """Buy a specified quantity of a stock."""
    price = get_stock_price(symbol)
    total_cost = price * quantity
    print(f"TRADEBOT: Bought {quantity} shares of {symbol} at ${price:.2f} each. Total cost: ${total_cost:.2f}")
    return {"quantity": quantity, "price": price, "total_cost": total_cost}

def buy_stock_with_usd(symbol: str, usd_amount: float, price: float):
    """Buy as many shares as possible with a given USD amount."""
    # price = get_stock_price(symbol)
    quantity = int(usd_amount // price)
    total_cost = price * quantity
    print(f"TRADEBOT: With ${usd_amount:.2f}, you can buy {quantity} shares of {symbol} at ${price:.2f} each. Total cost: ${total_cost:.2f}")
    return {"quantity": quantity, "price": price, "total_cost": total_cost}

def sell_stock(symbol: str, quantity: int):
    """Sell a specified quantity of a stock."""
    price = get_stock_price(symbol)
    total_value = price * quantity
    print(f"TRADEBOT: Sold {quantity} shares of {symbol} at ${price:.2f} each. Total value: ${total_value:.2f}")
    return {"quantity": quantity, "price": price, "total_value": total_value}

def sell_stock_with_usd(symbol: str, usd_amount: float, price: float):
    """Sell as many shares as possible with a given USD amount."""
    # price = get_stock_price(symbol)
    quantity = int(usd_amount // price)
    total_value = price * quantity
    print(f"TRADEBOT: With ${usd_amount:.2f}, you can sell {quantity} shares of {symbol} at ${price:.2f} each. Total value: ${total_value:.2f}")
    return {"quantity": quantity, "price": price, "total_value": total_value}


trading_controls = [get_stock_price, buy_stock, sell_stock, buy_stock_with_usd, sell_stock_with_usd]
instruction = """You are a helpful trading bot. 
                You can get stock prices, buy stocks, and sell stocks based on yfinance data. 
                You can also buy and sell stocks with a given USD amount. 
                Do not perform any other tasks."""

model = genai.GenerativeModel(
    "models/gemini-1.5-flash", tools=trading_controls, system_instruction=instruction
)

chat = model.start_chat()

from google.generativeai.types import content_types
from collections.abc import Iterable


def tool_config_from_mode(mode: str, fns: Iterable[str] = ()):
    """Create a tool config with the specified function calling mode."""
    return content_types.to_tool_config(
        {"function_calling_config": {"mode": mode, "allowed_function_names": fns}}
    )


tool_config = tool_config_from_mode("auto")

def save_chat_session(chat_history):
    """Save the chat session to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_session_{timestamp}.pkl"
    with open(filename, 'wb') as f:
        pickle.dump(chat_history, f)
    print(f"Chat session saved to {filename}")

def load_chat_session(filename):
    """Load a chat session from a file."""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def handle_stock_request(user_message, chat_history):
    """Handles user requests related to stock trading."""
    tool_config = tool_config_from_mode("auto")
    response = chat.send_message(user_message, tool_config=tool_config)
    
    # Add the user message and response to chat history
    chat_history.append({"user": user_message, "model": response})
    
    if response.parts[0].function_call:
        function_name = response.parts[0].function_call.name
        args = response.parts[0].function_call.args
        
        # Mapping function names to actual functions
        function_map = {
            "get_stock_price": get_stock_price,
            "sell_stock": sell_stock,
            "buy_stock": buy_stock,
            "buy_stock_with_usd": buy_stock_with_usd,
            "sell_stock_with_usd": sell_stock_with_usd
        }
        
        # Call the corresponding function if it exists in the map
        func = function_map.get(function_name)
        if func:
            result = func(**args)
            # Inform the chatbot about the function result
            chat.send_message(f"Function {function_name} returned: {result}")
            return result, chat_history
        else:
            return "Unknown function called.", chat_history
    else:
        return "No function call detected in the response.", chat_history

# # Usage example:
chat_history = []
# Load the previous chat session
filename = "chat_session_20240929_115811.pkl"
chat_history = load_chat_session(filename)
print(chat_history)
print(f"Loaded chat session from {filename}")

while True:
    user_input = input("Enter your stock-related request (or 'quit' to exit): ")
    if user_input.lower() == 'quit':
        save_chat_session(chat_history)
        break
    result, chat_history = handle_stock_request(user_input, chat_history)
    print(result)

# To load a previous chat session:
# filename = "chat_session_YYYYMMDD_HHMMSS.pkl"
# chat_history = load_chat_session(filename)