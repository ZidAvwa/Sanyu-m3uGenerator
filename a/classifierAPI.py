import os
import json
import time
from google import genai
from google.genai import types

def get_gemini_batch_classification(tracks_list, mode="genre"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
        
    client = genai.Client(api_key=api_key)
    
    # Trimmed down payload: Only send what is strictly necessary to calculate the name
    input_data = []
    for item in tracks_list:
        input_data.append({
            "id": item["id"],
            "a": item["artist"], # Shorthand keys to save token space
            "t": item["title"]
        })
        
    if mode == "genre":
        system_instruction = (
            "You are a music organization assistant specializing in Japanese music, Anime soundtracks, Vocaloid, and J-Pop. "
            "Categorize each song into a single descriptive genre/vibe (e.g., Orchestral, Dramatic, Electronic, Cinematic, Rock, Classical, J-Pop).\n"
            "Respond with a JSON object mapping the song ID to its categorized string: {\"1\": \"Orchestral\"}\n"
            "If completely unrecognizable, use 'UNKNOWN'."
        )
    else:
        system_instruction = (
            "You are a music metadata engine specializing in Japanese artists, VTubers, Utaite, units, and cover singers.\n"
            "Your job is to extract, clean, and standardize the PRIMARY ARTISTS name for filesystem folders.\n"
            "Rules:\n"
            "1. If multiple artists or a group unit (e.g., 'After the Rain', 'そらる×まふまふ'), separate individual primary names with a COMMA (e.g., 'そらる, まふまふ').\n"
            "2. If a track is a cover, extract the name of the person WHO COVERED IT. Look for 'cover', '【歌ってみた】', '/ Artist'.\n"
            "3. Keep the name in its primary recognizable form (Japanese or English characters).\n"
            "4. Strip out track numbers, bitrates (e.g., MP3_320K), and generic phrases like 'Music Video' or 'Lyrics'.\n"
            "5. Respond with a JSON object mapping ID to clean artist: {\"1\": \"そらる, まふまふ\", \"2\": \"Lucia\"}\n"
            "6. If no discernible human artist or cover singer, map to 'UNKNOWN'."
        )

    max_retries = 5
    flat_delay = 5
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=json.dumps(input_data),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                return json.loads(response.text.strip())
            return {}
            
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                print(f"\n [Server Snag] Burst limit hit. Re-trying batch in {flat_delay}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(flat_delay)
            else:
                print(f"\n[CRITICAL API ERROR]: {e}")
                return {}
                
    print("\n[BATCH POSTPONED]: Moving batch forward to fallback queue.")
    return {}