We are Team Foxtrot making Station-Fall, a space station exploration rougelike!

Team Motto: "It's Magic, Don't Ask!"

## Running the Game

### Requirements
- Python **3.11+**
- `pygame`
- `pygbag` (only required for web build)

---

## Local Run (Desktop)

### First-time setup
Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv station_fall_venv
source station_fall_venv/bin/activate
pip install -r requirements.txt

To run: python3 -m src.main

## Web build (pygbag)
# First time only
chmod +x run_web.sh

To launch: ./run_web.sh
# open http://localhost:8000

