import os
import re
import time
from collections import defaultdict
from metadata import parse_audio_file
from classifier import get_gemini_classification 

def clean_playlist_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def write_m3u(file_path, tracks):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for track in tracks:
            f.write(f"{track}\n")

def run_playlist_generator(music_dir, sort_by="artist"):
    # FIX: Playlists are now saved directly INSIDE your music folder for universal phone compatibility
    output_dir = os.path.join(music_dir, "Playlists")
    os.makedirs(output_dir, exist_ok=True)
    
    playlists = defaultdict(list)
    unknown_playlist = []
    cover_playlist = []
    
    valid_extensions = ('.mp3', '.m4a', '.flac', '.wav', '.ogg')
    
    print(" [1/3] Scanning directory for audio files...")
    all_files = []
    for root, _, files in os.walk(music_dir):
        # Prevent the script from scanning its own generated playlist folder recursively
        if "Playlists" in root:
            continue
        for file in files:
            if file.lower().endswith(valid_extensions):
                all_files.append((root, file))
                
    total_songs = len(all_files)
    print(f" Found {total_songs} songs to process.\n")
    print(f" [2/3] Processing tracks (Sorting by: {sort_by})...")
    print("-" * 70)

    for index, (root_dir, filename) in enumerate(all_files, start=1):
        full_path = os.path.join(root_dir, filename)
        artist, title = parse_audio_file(full_path)
        
        print(f" [{index}/{total_songs}] Processing: {filename}...")
        
        assigned_value = get_gemini_classification(artist, title, mode=sort_by)
        assigned_value = assigned_value.replace('"', '').replace("'", "").strip()
        
        # FIX: We use relative path references so both Android and Windows can read it
        # If your music is flat in one folder, this becomes just the filename.
        # If you have subfolders, it computes the universal relative jump step.
        relative_path = os.path.relpath(full_path, start=output_dir)
        
        if assigned_value.upper() == "UNKNOWN" or not assigned_value:
            print(f"  -> Moved to UNKNOWN_TRACKS")
            unknown_playlist.append(relative_path)
        else:
            if sort_by == "artist":
                is_cover = False
                clean_value = assigned_value
                if assigned_value.upper().startswith("COVER:"):
                    is_cover = True
                    cover_playlist.append(relative_path)
                    clean_value = assigned_value[6:].strip()

                individual_artists = [a.strip() for a in clean_value.split(",") if a.strip()]
                
                if is_cover:
                    print(f"  -> 🎤 [Cover] Cleaned Artists: {', '.join(individual_artists)} -> Added to Cover.m3u")
                else:
                    print(f"  -> Cleaned Artists: {', '.join(individual_artists)}")
                
                for individual_artist in individual_artists:
                    playlists[individual_artist].append(relative_path)
            else:
                print(f"  -> Genre: {assigned_value}")
                playlists[assigned_value].append(relative_path)
                
        time.sleep(0.1)

    print("-" * 70)
    print(" [3/3] Saving universal .m3u playlist files to disk...")
    
    for group_name, tracks in playlists.items():
        safe_name = clean_playlist_name(group_name)
        target_path = os.path.join(output_dir, f"{sort_by}_{safe_name}.m3u")
        write_m3u(target_path, tracks)
        
    if cover_playlist:
        write_m3u(os.path.join(output_dir, "Cover.m3u"), cover_playlist)
        print(f" Saved Cover.m3u with {len(cover_playlist)} tracks.")
        
    if unknown_playlist:
        write_m3u(os.path.join(output_dir, "UNKNOWN_TRACKS.m3u"), unknown_playlist)
        print(f" Saved UNKNOWN_TRACKS.m3u with {len(unknown_playlist)} tracks.")

    print(f"\n Done! Playlists generated natively inside your music directory.")

if __name__ == "__main__":
    TARGET_MUSIC_FOLDER = r"E:\Music" 
    SORTING_MODE = "artist"  
    
    run_playlist_generator(TARGET_MUSIC_FOLDER, sort_by=SORTING_MODE)