import os
import time
from pathlib import Path

# Configuration
PDF_DIR = "./research_papers"
LOG_FILE = "download_log.txt"
TARGET = 500

def get_progress():
    # 1. Count files
    if os.path.exists(PDF_DIR):
        files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
        count = len(files)
    else:
        count = 0
    
    # 2. Parse log for status
    last_topic = "Starting..."
    candidates = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "Searching topic:" in line:
                    last_topic = line.split("'")[1]
                    break
            for line in reversed(lines):
                if "Found" in line and "candidates" in line:
                    try:
                        candidates = int(line.split("Found")[1].split("new")[0].strip())
                        break
                    except:
                        pass
    
    return count, last_topic, candidates

def draw_bar(count, total, length=40):
    percent = min(100, (count / total) * 100)
    filled = int(length * count // total)
    bar = "█" * filled + "░" * (length - filled)
    return f"|{bar}| {percent:.1f}% ({count}/{total})"

def main():
    try:
        while True:
            count, topic, cands = get_progress()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 60)
            print("       ScholarAI v3: Pre-AI Corpus Collection Progress")
            print("=" * 60)
            print(f"\nTarget: {TARGET} Research Papers (2000-2015)")
            print(f"Status: {draw_bar(count, TARGET)}")
            print(f"\nCurrent Topic:  {topic}")
            print(f"Last Discovery: Found {cands} candidates")
            print("\n" + "-" * 60)
            print("Press Ctrl+C to exit monitoring.")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
