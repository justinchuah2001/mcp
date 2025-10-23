import asyncio
from fastmcp import Client
from google import genai

client = Client("http://localhost:8000/mcp")
## Replace your api_key value with your actual API key.
gemini_client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

async def get_user_input_async(prompt: str) -> str:
    """Non-blocking function to get user input."""
    # This runs the built-in input() in a separate thread so it doesn't block the event loop.
    return await asyncio.to_thread(input, prompt)

async def main():
    async with client:
        chat = gemini_client.aio.chats.create(
            model="gemini-2.5-flash",
            config=genai.types.GenerateContentConfig(
                temperature=0,
                tools=[client.session], 
            ),
        )

        while True:
            try:
                user_prompt = await get_user_input_async("\nYou:\n")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting chat.")
                break

            print("Generating...")
            try:
                response = await chat.send_message(user_prompt)

                print(f"Response: {response.text}")
            except Exception as e:
                print(f"Error during message generation: {e}")
        
        print("Chat session ended.")

asyncio.run(main())