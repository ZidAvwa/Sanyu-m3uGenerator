import os
import re
import time
from collections import defaultdict
from metadata import parse_audio_file
from a.classifierAPIgroq import get_gemini_classification

def clean_playlist_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def append_to_m3u(file_path, tracks):
    file_exists = os.path.exists(file_path)
    with open(file_path, "a", encoding="utf-8") as f:
        if not file_exists:
            f.write("#EXTM3U\n")
        for track in tracks:
            f.write(f"{track}\n")

def redo_unknown_tracks(unknown_m3u_path, output_dir="./playlists", sort_by="artist"):
    if not os.path.exists(unknown_m3u_path):
        print(f"❌ Error: Could not find '{unknown_m3u_path}'.")
        return

    print(f"🔍 Reading tracks from {unknown_m3u_path}...")
    tracks_to_process = []
    
    with open(unknown_m3u_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if os.path.exists(line):
                tracks_to_process.append(line)

    total_songs = len(tracks_to_process)
    if total_songs == 0:
        print("🎉 No tracks found inside UNKNOWN_TRACKS.m3u to process!")
        return

    print(f"🚀 Found {total_songs} tracks to re-process via Groq (Sorting by: {sort_by})...")
    print("-" * 70)

    successfully_processed = defaultdict(list)
    cover_playlist = []
    still_unknown = []

    for index, full_path in enumerate(tracks_to_process, start=1):
        artist, title = parse_audio_file(full_path)
        filename = os.path.basename(full_path)
        
        print(f" [{index}/{total_songs}] Re-processing: {filename}...")
        
        assigned_value = get_gemini_classification(artist, title, mode=sort_by)
        assigned_value = assigned_value.replace('"', '').replace("'", "").strip()
        
        if assigned_value.upper() == "UNKNOWN" or not assigned_value:
            print(f"  -> ❌ Still UNKNOWN")
            still_unknown.append(full_path)
        else:
            if sort_by == "artist":
                is_cover = False
                clean_value = assigned_value
                if assigned_value.upper().startswith("COVER:"):
                    is_cover = True
                    cover_playlist.append(full_path)
                    clean_value = assigned_value[6:].strip()

                individual_artists = [a.strip() for a in clean_value.split(",") if a.strip()]
                if is_cover:
                    print(f"  -> 🎤 [Cover] Cleaned Artists: {', '.join(individual_artists)} -> Added to Cover.m3u")
                else:
                    print(f"  -> ✅ Cleaned Artists: {', '.join(individual_artists)}")
                
                for individual_artist in individual_artists:
                    successfully_processed[individual_artist].append(full_path)
            else:
                print(f"  -> ✅ Success! Genre: {assigned_value}")
                successfully_processed[assigned_value].append(full_path)
                
        time.sleep(0.1)

    print("-" * 70)
    print("💾 Updating playlist files on disk...")

    for group_name, tracks in successfully_processed.items():
        safe_name = clean_playlist_name(group_name)
        target_path = os.path.join(output_dir, f"{sort_by}_{safe_name}.m3u")
        append_to_m3u(target_path, tracks)

    if cover_playlist:
        append_to_m3u(os.path.join(output_dir, "Cover.m3u"), cover_playlist)
        print(f"  -> Appended {len(cover_playlist)} track(s) to Cover.m3u")

    unknown_file_path = os.path.abspath(unknown_m3u_path)
    if still_unknown:
        with open(unknown_file_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for track in still_unknown:
                f.write(f"{track}\n")
        print(f"📝 Updated UNKNOWN_TRACKS.m3u: {len(still_unknown)} tracks left.")
    else:
        if os.path.exists(unknown_file_path):
            os.remove(unknown_file_path)
        print("🔥 All unknown tracks successfully sorted!")

if __name__ == "__main__":
    UNKNOWN_M3U = r"./playlists/UNKNOWN_TRACKS.m3u"
    SORTING_MODE = "artist" 
    
    redo_unknown_tracks(UNKNOWN_M3U, sort_by=SORTING_MODE)