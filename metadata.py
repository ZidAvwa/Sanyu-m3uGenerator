import os
import re
from tinytag import TinyTag

def clean_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    # Remove leading track numbers
    cleaned = re.sub(r'^\d+[\s._-]*', '', name_without_ext)
    return cleaned.strip()

def parse_audio_file(file_path):
    try:
        tag = TinyTag.get(file_path)
        artist = tag.artist.strip() if tag.artist else None
        title = tag.title.strip() if tag.title else None
        
        if artist and title:
            return artist, title
    except Exception:
        pass

    filename = os.path.basename(file_path)
    cleaned = clean_filename(filename)
    
    # Smart split: Handles " - ", "   -   ", " -", "- ", or double underscores "__"
    parts = re.split(r'\s*-\s*|\s*__\s*', cleaned, maxsplit=1)
    
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
        
    return "UNKNOWN", cleaned