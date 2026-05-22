import os
from groq import Groq

def get_gemini_classification(artist, title, mode="artist"):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
        
    client = Groq(api_key=api_key)
    
    if mode == "genre":
        system_instruction = (
            "You are a music organization assistant specializing in Japanese music. "
            "Categorize the song into a single descriptive genre/vibe (e.g., Orchestral, Electronic, Rock, Classical, J-Pop). "
            "Respond with ONLY the genre name. If unsure, reply 'UNKNOWN'."
        )
        prompt = f"Artist: {artist}, Title: {title}"
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=20
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            return "UNKNOWN"

    # --- MODE: ARTIST (DUAL-LAYER CHECK) ---
    raw_text = f"Artist field: {artist} | Title field: {title}"
    
    # Layer 1: Aggressive Cover Detection
    is_cover = False
    cover_instruction = (
        "You are a verification system. Look at the text and determine if this is a cover song or '歌ってみた'. "
        "Look for indicators like 'Cover by', '(Cover)', '【Cover】', or artist names acting as cover units.\n"
        "Reply with exactly 'YES' or 'NO'. Absolutely nothing else."
    )
    
    try:
        cover_check = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": cover_instruction},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.0,
            max_tokens=5
        )
        if "YES" in cover_check.choices[0].message.content.upper():
            is_cover = True
    except Exception:
        pass

    # Layer 2: Clean Name Extraction
    name_instruction = (
        "You are a music metadata cleaning engine. Extract ONLY the primary singer or channel covering the track.\n"
        "Rules:\n"
        "1. If a cover artist is explicitly named (e.g. 'Cover by Alia Adelia', 'Keroro Suika 【Cover】'), extract THAT person's name (e.g. 'Alia Adelia', 'Keroro Suika').\n"
        "2. Keep first and last names together as one string (e.g., 'Alia Adelia'). Do not use a comma inside a single person's name.\n"
        "3. Only use a comma to separate completely different people or independent duos (e.g. 'そらる, まふまふ').\n"
        "4. Strip out track numbers, bitrates (MP3_160K), descriptors like 'Lagu Jepang Sedih', and generic text.\n"
        "5. CRITICAL: Your response must contain ONLY the names or the word 'UNKNOWN'. Never explain your answer or write sentences like 'No primary artist found'.\n"
        "Respond with ONLY the cleaned string value."
    )

    try:
        name_clean = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": name_instruction},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.0,
            max_tokens=30
        )
        
        final_name = name_clean.choices[0].message.content.strip()
        
        # Catch conversational hallucinations
        if "FOUND" in final_name.upper() or "NOT" in final_name.upper() or "UNKNOWN" in final_name.upper():
            return "UNKNOWN"
            
        if is_cover and final_name:
            return f"COVER: {final_name}"
            
        return final_name if final_name else "UNKNOWN"
        
    except Exception as e:
        print(f"\n[Groq API Error]: {e}")
        return "UNKNOWN"