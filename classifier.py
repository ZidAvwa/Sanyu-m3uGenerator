import os
import json
import time
from groq import Groq
import ollama

def get_gemini_classification(artist, title, mode="artist", backend="local"):
    """
    Metadata engine that supports switching between 'local' (Ollama) and 'groq' (API).
    """
    if mode == "genre":
        system_instruction = (
            "You are a music assistant. Categorize the track into a single descriptive vibe "
            "(e.g., Orchestral, Electronic, Cinematic, Rock, Classical, J-Pop). "
            "Respond with ONLY the category name. If unsure, reply 'UNKNOWN'."
        )
        prompt = f"Artist: {artist}, Title: {title}"
    else:
        system_instruction = (
            "You are a music metadata cleaning engine. Extract ONLY the primary singer or channel covering the track.\n"
            "Rules:\n"
            "1. If a cover artist is explicitly named (e.g. 'Cover by Alia Adelia'), extract THAT person's name.\n"
            "2. Keep first and last names together as one string (e.g., 'Alia Adelia'). Do not use a comma inside a single person's name.\n"
            "3. Only use a comma to separate completely different people or independent duos (e.g. 'そらる, まふまふ').\n"
            "4. Strip out track numbers, bitrates (MP3_160K), descriptions like 'Lagu Jepang Sedih', and generic text.\n"
            "5. CRITICAL: Your response must contain ONLY the names or the word 'UNKNOWN'. Never explain your answer.\n"
            "Respond with ONLY the cleaned string value."
        )
        prompt = f"Artist field: {artist} | Title field: {title}"

    # --- ROUTE TO GROQ ---
    if backend.lower() == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set.")
        client = Groq(api_key=api_key)
        
        # Groq specific logic (including binary cover gate)
        if mode == "artist":
            is_cover = False
            cover_instruction = (
                "You are a verification system. Determine if this is a cover song or '歌ってみた'. "
                "Reply with exactly 'YES' or 'NO'. Absolutely nothing else."
            )
            try:
                cover_check = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": cover_instruction}, {"role": "user", "content": prompt}],
                    temperature=0.0, max_tokens=5
                )
                if "YES" in cover_check.choices[0].message.content.upper():
                    is_cover = True
            except Exception:
                pass

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}],
                temperature=0.0, max_tokens=30
            )
            final_name = completion.choices[0].message.content.strip()
            if "FOUND" in final_name.upper() or "NOT" in final_name.upper() or "UNKNOWN" in final_name.upper():
                return "UNKNOWN"
            if mode == "artist" and is_cover and final_name:
                return f"COVER: {final_name}"
            return final_name if final_name else "UNKNOWN"
        except Exception as e:
            print(f"\n[Groq API Error]: {e}")
            return "UNKNOWN"

    # --- ROUTE TO LOCAL OLLAMA ---
    else:
        if mode == "artist":
            is_cover = False
            cover_instruction = (
                "You are a verification system. Determine if this is a cover song or '歌ってみた'. "
                "Reply with exactly 'YES' or 'NO'. Absolutely nothing else."
            )
            try:
                cover_check = ollama.generate(
                    model='llama3.2', system=cover_instruction, prompt=prompt, options={'temperature': 0.0}
                )
                if "YES" in cover_check['response'].upper():
                    is_cover = True
            except Exception:
                pass

        try:
            name_clean = ollama.generate(
                model='llama3.2', system=system_instruction, prompt=prompt, options={'temperature': 0.0}
            )
            final_name = name_clean['response'].strip()
            if "FOUND" in final_name.upper() or "NOT" in final_name.upper() or "UNKNOWN" in final_name.upper():
                return "UNKNOWN"
            if mode == "artist" and is_cover and final_name:
                return f"COVER: {final_name}"
            return final_name if final_name else "UNKNOWN"
        except Exception as e:
            print(f"\n[Local GPU Engine Error]: {e}")
            return "UNKNOWN"