We are Team Foxtrot making Station-Fall, a space station exploration rougelike!

Team Motto: "It's Magic, Don't Ask!"

## Running the Game

### Requirements
- Python **3.11+**
- `pygame`
- `pygbag` (only required for web build)

---

## Testing (TDD Workflow)

We follow Test-Driven Development principles to collect evidence of the system's value Running Test Cases

To run the automated test suite for the camera and background modules, navigate to the src directory and use unittest discover:
'''bash
#Navigate to source directory

cd src

### Run all tests in the test_cases folder

python3 -m unittest discover test_cases

'''

#### Why we test

- Evidence Collection: Testing provides technical information about the quality of our components.

- Beck's Rules: We only write new business code when an automated test has failed and always eliminate duplication.

- Organic Development: Our highly cohesive, loosely coupled components make testing and maintenance easier.

#### Summary of what these tests verify:

- Camera: Validates the translation of world coordinates to screen coordinates and smooth centering logic.

- Background: Verifies the generation of parallax star layers, including star density and movement speeds.

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