# main.py
import os
from dotenv import load_dotenv   

from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get the key from the environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Make sure it's in your .env file.")

# Initialise client
client = OpenAI(api_key=api_key)

# Conversation history
history = [
    {"role": "system", "content": "You are Dachikou, a warm, patient elderly companion."}
]

print("Chat started. Type 'exit' to quit.\n")

while True:
    try:
        user_msg = input("You: ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        history.append({"role": "user", "content": user_msg})

        response = client.responses.create(
            model="gpt-5-nano",
            input=history
        )

        assistant_reply = response.output_text.strip()
        print(f"Dachikou: {assistant_reply}\n")

        history.append({"role": "assistant", "content": assistant_reply})

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        break
    except Exception as e:
        print(f"[Error] {e}")
        break