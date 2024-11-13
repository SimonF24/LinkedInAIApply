# LinkedInAIApply
A really simple AI agent to search LinkedIn for jobs that match your experience level, interests, and preferences.

The agent searches LinkedIn for matching jobs then saves them to a JSON file (config.search['matched_jobs_json_filename']) as a list of URL strings for you to do what you please with. You could run this script overnight, watch the JSON file for changes and email yourself a message with new matched jobs, manually apply to them, or do anything else you want with the information.

The eventual goal is for this agent to be to automatically apply to matched jobs, we'll see how that goes.

## Usage
1. Clone or download the repo
2. Create a config.py file either by renaming example.config.py file or creating a new one yourself. Make sure all the fields are filled out appropriately including the AI model fields, which determine which LLM will be used (I've personally been using Llama 3.1 8B locally with LM studio but any OpenAI compatible model should work). Also make sure that the browser you want to use (config.search['browser']) is installed on your system.
3. Optionally create and activate a virtual environment (recommended, I personally use venv in a .venv folder in the same directory)
4. Run pip install -r requirements.txt
5. Run agent.py
6. Login to LinkedIn/complete FFA
7. Don't interfere with the agent while it's running the job search. The agent's browser needs to remain open, closing the browser will result in an error. The browser can be minimized, in the background or on a secondary monitor though. Your computer going to sleep will result in the script throwing an error so set your settings accoringly if you want to run the script for an extended period of time.
8. If manually applying for jobs simply apply for the job that pops up in a second tab of the browser. Once finished close the tab that popped up and another job will open. You can open and close other tabs as you like without any issue, a new job will open when you close the tab that opened with the last job application page. If you close the browser you are assumed to be done applying for jobs for now and your progress will be saved so you can apply for more by running the script again.