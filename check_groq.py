import os
import sys

from dotenv import load_dotenv
from groq import Groq, GroqError


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")

    if not api_key or not model:
        print("Connectivity check not run: GROQ_API_KEY and GROQ_MODEL must be set in .env.")
        return 1

    try:
        response = Groq(api_key=api_key).chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with READY only"}],
            temperature=0,
            max_tokens=128,
        )
    except GroqError as error:
        print(f"Groq request failed ({type(error).__name__}): {error}")
        return 1

    choice = response.choices[0]
    content = choice.message.content
    print(f"Model: {model}")
    print("Status: request completed")
    print(f"Finish reason: {choice.finish_reason}")
    print(f"Response: {content!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
