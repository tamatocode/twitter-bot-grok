import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import time

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)


def clean_text(text: str) -> str:
    """Clean text: remove URLs, extra spaces."""
    if not text:
        return ""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_reply(tweet_text: str) -> str:
    """Generate a cool, human-like Web3/AI KOL-style, reply using Gemini."""
    tweet_text = clean_text(tweet_text)

    if not tweet_text:
        raise ValueError("Tweet text is empty")

    # Very direct prompt - no extra words
    prompt = f"""
        You are a cool, influential tech person — a Key Opinion Leader (KOL) known , thoughtful, and human replies about AI, Web3, blockchain, and tech culture, you give replies that adds some insights to the post instead of just agreeing to it.

        Make sure to:
        - Keep replies as short as possible keeping in mind that they sound human under 1 - 10 words.
        - Be authentic, conversational, and natural — sound as if a human is writing and when you give replies that adds some insights to the post instead of just agreeing to it.
        - Mix intelligence, humor, or curiosity based on context and write in a way that showcases human emotions and not something that an LLM would write.
        - Reply with a developer and programmer mindset and don't moonlight any achievement of anyone
        - If tweet is serious → reply thoughtfully but then again the consideration should be that human intelligence should be mimcked.
        - If tweet is about tech or crypto → reply with insight or optimism. 
        - Never use hashtags, links, or emojis unless natural.

        Tweet:
            "{tweet_text}"

            Now write your reply:
            """

    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}/{max_retries}")
            
            # Create model with system instruction to avoid thinking tokens
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction="Reply to tweets in 3-25 words. Be casual and authentic. No explanations, just the reply."
            )
            
            # No token limits - let the model generate freely
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    candidate_count=1,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            print(f"Response received. Candidates: {len(response.candidates)}")
            
            if not response.candidates:
                print("No candidates returned")
                time.sleep(1)
                continue
            
            candidate = response.candidates[0]
            print(f"Finish reason: {candidate.finish_reason}")
            print(f"Has content: {candidate.content is not None}")
            
            if candidate.content:
                print(f"Has parts: {candidate.content.parts is not None}")
                print(f"Parts length: {len(candidate.content.parts) if candidate.content.parts else 0}")
            
            # Extract reply
            if candidate.content and candidate.content.parts:
                reply_text = ""
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        reply_text += part.text
                
                if reply_text:
                    reply_text = clean_text(reply_text)
                    print(f"✓ Generated reply: '{reply_text}'")
                    return reply_text
                else:
                    print("Parts exist but no text found")
            else:
                print("No content.parts available")
            
            # If we got here, generation failed - wait and retry
            print(f"Generation failed, retrying in {attempt + 1} seconds...")
            time.sleep(attempt + 1)
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(attempt + 1)
            else:
                raise
    
    raise RuntimeError(f"Failed to generate reply after {max_retries} attempts. The API may be experiencing issues or your API key may have restrictions.")


# Example usage
if __name__ == "__main__":
    test_tweets = [
        "Have a blessed day",
        "What memecoin will have a god candle soon?",
        "Can't believe how fast this year went by 😭"
    ]
    
    print(f"Using API Key: {GEMINI_API_KEY[:10]}...")
    print(f"Using Model: {GEMINI_MODEL}\n")
    
    for tweet in test_tweets:
        print(f"\n{'='*70}")
        print(f"Tweet: {tweet}")
        try:
            reply = generate_reply(tweet)
            print(f"✓ Final Reply: '{reply}'")
        except Exception as e:
            print(f"✗ Failed: {e}")
        print(f"{'='*70}")