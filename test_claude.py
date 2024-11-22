import os
from anthropic import Anthropic
from dotenv import load_dotenv

def test_claude_api():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("CLAUDE_API_KEY")
    
    print("\n=== Claude API Test ===\n")
    
    if not api_key:
        print("Error: CLAUDE_API_KEY not found in environment variables")
        print("Please add your API key to the .env file")
        return
        
    print(f"API key found: {api_key[:15]}...")
    
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        
        print("\nSending test message to Claude...")
        
        # Make test request
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ]
        )
        
        print("\nSuccess! Claude's response:")
        print(response.content[0].text)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nPlease verify:")
        print("1. Your API key is correct")
        print("2. You have installed the anthropic package (pip install anthropic)")
        print("3. You have sufficient API credits")

if __name__ == "__main__":
    test_claude_api()