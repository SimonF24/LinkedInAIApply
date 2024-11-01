# LinkedInAIApply
A really simple AI agent to search LinkedIn for jobs that match your experience level, interests, and preferences.

The agent searches LinkedIn for matching jobs then saves them to a JSON file (config.search['matched_jobs_json_filename']) as a list of URL strings for you to do what you please with. You could run this script overnight, watch the JSON file for changes and email yourself a message with new matched jobs, manually apply to them, or do anything else you want with the information.

The eventual goal is for this agent to be to automatically apply to matched jobs, we'll see how that goes. There are some functions in the code that are currently commented out looking towards this goal. These functions don't really work right now, have not been thoroughly tested and include dangerous functionality like directly running AI generated code. If you choose to uncomment and run those lines you do so at your own risk.

## Usage
1. Clone or download the repo
2. Create a config.py file either by renaming example.config.py file or creating a new one yourself. Make sure all the fields are filled out appropriately including the AI model fields, which determine which LLM will be used (I've personally been using Llama 3.1 8B locally with LM studio but any OpenAI compatible model should work). Also make sure that the browser you want to use (config.search['browser']) is installed on your system.
3a. Optionally create and activate a virtual environment (recommended, I personally use venv in a .venv folder in the same directory)
3b. Run pip install -r requirements.txt
4. Run agent.py
5. Login to LinkedIn/complete FFA
6. Don't interfere with the agent while it's running. The agent's browser needs to remain open, closing the browser will result in an error. The browser can be minimized, in the background or on a secondary monitor though.