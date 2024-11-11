import config
from dataclasses import dataclass
import json
from openai import OpenAI
from pathlib import Path
from prompt_helpers import (
    selenium_driver_location_documentation,
    selenium_driver_navigation_documentation,
    selenium_driver_wait_documentation
)
from pypdf import PdfReader
import re
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from types import ModuleType
from typing import List


linkedin_page_size = 25


class Agent:
    def __init__(self, config: ModuleType=config):
        self.ai_client = OpenAI(base_url=config.ai['url'], api_key=config.ai['api_key'])
        user = config.user
        match config.search['browser']:
            case "chrome":
                self.driver = webdriver.Chrome()
            case "edge":
                self.driver = webdriver.Edge()
            case "firefox":
                self.driver = webdriver.Firefox()
            case "safari":
                self.driver = webdriver.Safari()
            case _:
                raise Exception("Unrecognized browser. Please change config.search['browser'] to be one of ['chrome', 'edge', 'firefox', 'safari']")
        self.driver.maximize_window()
        self.actions = ActionChains(self.driver)
        self.config = config
        self.applied_jobs = []
        self.matched_jobs = []
        reader = PdfReader(user['resume_path'])
        resume_text = ""
        for i in range(len(reader.pages)):
            resume_text += reader.pages[i].extract_text(0)
            # We only look for text oriented vertically, if your resume has text that isn't vertical that's a you problem
        self.resume_text = resume_text
        self.user_profile_text = (
            f"Here is how the user answered some questions:\n"
            f"Are you a US citizen? {user['us_citizen']}\n"
            f"Are you legally authorized to work in the US for any employer? {user['us_work_authorization']}\n"
            f"Will you now or in the future require sponsorship to work in the US? {user['us_require_sponsorship']}\n"
            f"What is the highest level of active US security clearance you possess? {user['us_security_clearance_level']}\n"
            f"What is your race? {user['race']}\n"
            f"Are you hispanic or latino? {user['hispanic_or_latino']}\n"
            f"Do you have any disabilities? {user['disability']}\n"
            f"Are you a protected veteran? {user['veteran_status']}\n"
            f"Are you open to relocation? {user['open_to_relocation']}\n"
            f"What is your preference regarding remote work? {user['remote_work_preference']}\n"
            f"What type of role are you looking for? {user['type_of_role']}\n"
            f"Are there any companies you don't want to apply to? {user['blacklist_companies']}\n"
            f"What languages do you speak and write? {user['languages']}\n"
            f"What is your expected salary range? {user['salary_range']}\n"
            f"How did you hear about this job? Linkedin\n"
            f"Do you certify that all information you have entered is accurate? {user['certify_information_accuracy']}\n"
            f"What is your name: {user['name']}\n"
            f"What is your email? {user['email']}\n"
            f"What is your phone number? {user['phone_number']}\n"
            f"What is your address? "
            f"{user['address']['street']} {user['address']['street_line_2']} {user['address']['city']}"
            f"{user['address']['state']} {user['address']['zip_code']} {user['address']['country']}\n"
            f"What are your job interests? {user['job_interests']}\n" 
            f"The user has this resume:\n{resume_text}\n"
        )
    
    def __del__(self):
        self.driver.quit()
    
    def manually_apply_to_jobs(self):
        """
        Iterates through the list of matched jobs and takes the user to the page for them to apply themselves.
        Goes to the the next job when the tab with the open job is closed by the user. Ends if the user closes the
        selenium browser
        """
        i = 0
        original_window = self.driver.current_window_handle
        for job in self.matched_jobs:
            self.driver.switch_to.new_window('tab')
            self.driver.get(job)
            job_window = self.driver.current_window_handle
            user_closed = False
            while job_window in self.driver.window_handles:
                time.sleep(1)
                try:
                    self.driver.window_handles
                except:
                    user_closed = True
                    break
            if user_closed:
                break
            self.applied_jobs.append(job)
            self.driver.switch_to.window(original_window) 
            i += 1
        self.matched_jobs = self.matched_jobs[i:]
    
    def login_to_linkedin(self):
        """
        Logs in to LinkedIn with the provided credentials or waits for the user to login.
        The user may need to complete 2FA
        """
        self.driver.get('https://linkedin.com/login')
        if ('linkedin_email_or_phone' in self.config.user and self.config.user['linkedin_email_or_phone'] != ''
            and 'linkedin_password' in self.config.user and self.config.user['linkedin_password'] != ''):
            try:
                email_or_phone_number_element = self.driver.find_element(By.ID, 'username')
            except NoSuchElementException:
                raise Exception('Failed to find the email or phone number field')
            email_or_phone_number_element.send_keys(self.config.user['linkedin_email_or_phone'])
            try:
                password_element = self.driver.find_element(By.ID, 'password')
            except NoSuchElementException:
                raise Exception('Failed to find the password element')
            password_element.send_keys(self.config.user['linkedin_password'])
            button_elements = self.driver.find_elements(By.TAG_NAME, 'button')
            success = False
            for button_element in button_elements:
                if button_element.text == 'Sign in':
                    button_element.click()
                    success = True
                    break
            if not success:
                print("We weren't able to find the submit button, please complete sign-in manually")
        while 'feed' not in self.driver.current_url:
            print('Waiting for the user to login/complete 2FA')
            time.sleep(5)
        
    def search_for_jobs(self) -> None:
        """
        Searches for jobs on LinkedIn from the given search terms and locations
        then adds them to the jobs list
        """
        applied_job_set = set(self.applied_jobs)
        matched_job_set = set(self.matched_jobs)
        for search_term in self.config.search['search_terms']:
            search_term_start_time = time.time()
            for search_location in self.config.search['locations']:
                base_url = "https://www.linkedin.com/jobs/search/"
                page_num = 0
                breakout = False
                while True: # We go until there's no next page and save the matched jobs after every page
                    try:
                        self.driver.get(f"{base_url}?keywords={search_term.replace(" ", "%20")}"
                                        f"&location={search_location.replace(" ", "%20")}&start={linkedin_page_size*page_num}")
                        try:
                            self.driver.find_element(By.CLASS_NAME, "jobs-search-no-results-banner")
                            # No jobs were found for that search
                            continue
                        except NoSuchElementException:
                            pass
                        # We have to scroll to the bottom of the job list to load all the elements
                        job_element_container = self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
                        previous_scroll_position = -1
                        new_scroll_position = self.driver.execute_script("return arguments[0].scrollTop", job_element_container)
                        while previous_scroll_position != new_scroll_position:
                            previous_scroll_position = new_scroll_position
                            new_scroll_position = self.driver.execute_script(
                                "arguments[0].scrollTop = arguments[0].scrollHeight; return arguments[0].scrollTop", job_element_container)
                        job_elements = self.driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
                        while len(job_elements) < linkedin_page_size:
                            time.sleep(1)
                            job_elements = self.driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
                        try: # Close a message pop up window if one exists
                            self.driver.find_element(
                                By.CLASS_NAME, "msg-overlay-conversation-bubble--is-active"
                                ).find_elements(By.CLASS_NAME, "msg-overlay-bubble-header__control")[1].click()
                        except NoSuchElementException:
                            pass
                    except NoSuchElementException:
                        break
                    for job_element in job_elements:
                        
                        # If the job element is an inline suggestion ignore it and continue on to the next element
                        try:
                            job_element.find_element(By.CLASS_NAME, 'jobs-search-inline-suggestions-card')
                            continue
                        except NoSuchElementException:
                            pass
                        
                        # If the user wants to skip previously viewed jobs and this job is marked as viewed, skip it
                        try:
                            if (self.config.search['skip_previously_viewed']
                                and 'Viewed' in job_element.find_element(By.CLASS_NAME, "job-card-container__footer-wrapper").text):
                                continue
                        except NoSuchElementException:
                            pass
                        
                        # Parse the job and ask the model if it's a good match
                        self.actions.move_to_element(job_element).perform()
                        job_element.click()
                        try:
                            selected_job_element = self.driver.find_element(By.CLASS_NAME, 'jobs-details')
                        except NoSuchElementException:
                            continue
                        try:
                            company_name = selected_job_element.find_element(
                                By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text
                        except NoSuchElementException:
                            continue
                        try:
                            description_text = selected_job_element.find_element(
                                By.CLASS_NAME, "jobs-description-content__text").text
                        except NoSuchElementException:
                            continue
                        try:
                            job_title_element = selected_job_element.find_element(
                                By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title"
                            ).find_element(By.XPATH, "//div/h1/a")
                            job_title = job_title_element.text
                            linkedin_job_url = job_title_element.get_attribute('href')
                        except NoSuchElementException:
                            continue
                        try:
                            apply_button_element = selected_job_element.find_element(
                                By.CLASS_NAME, "jobs-apply-button")
                            if apply_button_element.text == "Easy Apply":
                                easy_apply = True
                            elif apply_button_element.text == "Apply":
                                easy_apply = False
                            else:
                                continue
                        except NoSuchElementException:
                            continue
                        job_match_questionaire_prompt = self.create_job_match_questionaire_prompt(
                            company_name, description_text, search_location, job_title)
                        success = False
                        for i in range(config.ai['retries']):
                            questionaire = self.get_ai_response(job_match_questionaire_prompt)
                            questionaire_answer_prompt = self.create_job_match_questionaire_answer_prompt(questionaire)
                            questionaire_answer = self.get_ai_response(questionaire_answer_prompt)
                            if re.compile(r'\b[Nn]o\b').search(questionaire_answer):
                                # We check for no first since most models seem to be "yes" happy
                                break
                            elif re.compile(r'\b[Yy]es\b').search(questionaire_answer):
                                success = True
                                break
                        if not success:
                            continue
                        if easy_apply:
                            job_url = linkedin_job_url
                        else:
                            original_window = self.driver.current_window_handle
                            apply_button_element.click()
                            # Get the url from clicking on the button and going to the new tab it opens
                            wait = WebDriverWait(self.driver, 30)
                            try:
                                wait.until(EC.number_of_windows_to_be(2))
                            except TimeoutException:
                                try: # Close the modal
                                    modal_element = self.driver.find_element(By.CLASS_NAME, 'artdeco-modal')
                                    modal_element.find_element(By.CLASS_NAME, 'artdeco-button--circle').click()
                                    apply_button_element = selected_job_element.find_element(
                                        By.CLASS_NAME, "jobs-apply-button")
                                    apply_button_element.click()
                                except NoSuchElementException:
                                    pass
                            for window_handle in self.driver.window_handles:
                                if window_handle != original_window:
                                    self.driver.switch_to.window(window_handle)
                                    break
                            if self.driver.current_window_handle != original_window:
                                job_url = self.driver.current_url
                                # Close to window and switch back to the original window
                                self.driver.close()
                                self.driver.switch_to.window(original_window)
                            else:
                                continue
                        if job_url not in applied_job_set and job_url not in matched_job_set:
                            self.matched_jobs.append(job_url)
                            matched_job_set.add(job_url)
                    
                        if time.time() - search_term_start_time > self.config.search['max_search_time'] / len(self.config.search['search_terms']):
                            breakout = True
                            break
                        
                    if breakout:
                        break

                    if page_num % self.config.search['save_results_every_x_pages'] == 0:
                        self.save_matched_jobs()
                    page_num += 1
        self.save_matched_jobs()

    def get_ai_response(self, prompt: str) -> str:
        """
        Queries the LLM for a response
        """
        completion = self.ai_client.chat.completions.create(
            messages = [
                {
                    "role": "system",
                    "content": self.config.ai['system_prompt']
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.config.ai['model'],
            temperature = 0.7
        )
        return completion.choices[0].message.content
    
    def get_ai_chat(self, messages: List[dict]) -> List[dict]:
        """
        Queries the LLM for a response to the given messages and returns the entire message history
        """
        completion = self.ai_client.chat.completions.create(
            messages = messages,
            model=self.config.ai['model'],
            temperature = 0.7
        )
        response_dict = {"role": "assistant", "content": completion.choices[0].message.content}
        return messages + [response_dict]
        
    def create_job_match_questionaire_prompt(self, company: str, description: str, location: str, title: str) -> str:
        """
        Creates a prompt to ask the LLM to answer a series of questions about whether or not a job is a good
        fit for the user
        """
        return (
            f"Is a job with this title: \"{title}\"\n"
            f"Working for this company: \"{company}\"\n"
            f"With this job description:\n\"{description}\"\n"
            f"At this location: \"{location}\"\n"
            f"a good match for a user with this profile? \n\"{self.user_profile_text}\"\n"
            "To answer that question please respond with answers to the following questions:"
            "Does the user have an appropriate amount of relevant experience for this position?\n"
            "Does the user have a citizenship and work authorization status that makes them eligible for the job?\n"
            "Does the job sound like something the user would be interested in?\n"
            "Does the type of role match the user's preferences?\n"
            "Is this job likely to match the user's salary expectations?\n"
            "Does this job require an active security clearance? "
            "If so does the user have/can the user acquire the appropriate clearance in an appropriate time frame?\n"
            "If there are any other questions you think would also be relevant to determining if the "
            "job is a good match for the user please include those as well."
        )
    
    def create_job_match_questionaire_answer_prompt(self, questionaire: str):
        """
        Returns a prompt asking the ai model to respond to the questionaire prompt provided
        """
        return (
            f"Here is a set of questions and answers:\n{questionaire}\n"
            "Based on these questions is the job a good match for the user? "
            "Please answer only with \"yes\" or \"no\""
        )
        
    def load_applied_jobs(self):
        """
        Loads applied jobs from a file (config.search['applied_jobs_json_filename'])
        """
        if Path(self.config.search['applied_jobs_json_filename']).is_file():
            with open(self.config.search['applied_jobs_json_filename'], 'r') as file:
                self.applied_jobs = json.load(file)
        
    def load_matched_jobs(self):
        """
        Loads matched jobs from a file (config.search['matched_jobs_json_filename'])
        """
        if Path(self.config.search['matched_jobs_json_filename']).is_file():
            with open(self.config.search['matched_jobs_json_filename'], 'r') as file:
                self.matched_jobs = json.load(file)
                
    def save_applied_jobs(self):
        """
        Saves the applied jobs to a file (config.search['applied_jobs_json_filename']).
        This overwrites the previous save so you're expected to run load_applied_jobs()
        first if you want to preserve previous entries.
        """
        with open(self.config.search['applied_jobs_json_filename'], 'w') as file:
            json.dump(self.applied_jobs, file)
        
    def save_matched_jobs(self, overwrite=False):
        """
        Saves matched jobs to a file (config.search['matched_jobs_json_filename'])
        """
        if Path(self.config.search['matched_jobs_json_filename']).is_file() and not overwrite:
            applied_job_set = set(self.applied_jobs)
            with open(self.config.search['matched_jobs_json_filename'], 'r') as file:
                previous_jobs = json.load(file)
            # Ensuring no duplicate jobs exist in the file
            previous_job_set = set(previous_jobs)
            new_jobs = []
            for job in self.matched_jobs:
                if job not in previous_job_set and job not in applied_job_set:
                    new_jobs.append(job)
            with open(self.config.search['matched_jobs_json_filename'], 'w') as file: # There's maybe a way to append here
                json.dump(previous_jobs + new_jobs, file)
        else:
            with open(self.config.search['matched_jobs_json_filename'], 'w') as file:
                json.dump(self.matched_jobs, file)

if __name__ == "__main__":
    agent = Agent(config=config)
    agent.load_applied_jobs()
    agent.load_matched_jobs()
    agent.login_to_linkedin()
    print('Searching for jobs')
    agent.search_for_jobs()
    agent.save_applied_jobs()
    agent.save_matched_jobs()
    print('Finished searching for jobs!')
    print('Starting manual job applications')
    agent.manually_apply_to_jobs()
    agent.save_applied_jobs()
    agent.save_matched_jobs(overwrite=True)
    print('Done!')