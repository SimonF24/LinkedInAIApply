# AI Settings
ai = dict(
    api_key = "lm-studio", # API key for the AI model
    logging = True, # Whether to log all interactions with the ai model
    model = "whichever-is-loaded-in-lm-studio", # The AI model to use
    retries = 3, # int denoting how many times to try if the ai model isn't giving us an answer we want (e.g. yes or no)
    system_prompt = "You are an agent helping a user apply for jobs", # The system prompt to use with the AI model
    url = "http://localhost:1234/v1" # The url for the AI model you're using
)

# Search Settings
search = dict(
    applied_jobs_json_filename = "applied_jobs.json", # Filename for a json file containing jobs you've already applied to
    browser = "chrome", # Which browser to use during the search, one of ["chrome", "edge", "firefox", "safari"]
    locations = [ # Locations where you want to find a job
        "San Francisco Bay Area"
    ],
    matched_jobs_json_filename = "matched_jobs.json", # Filename for a JSON file containing jobs you've been matched with
    max_search_time = 60*60, # Maximum search time in seconds, the search will finish the page it's on when this time runs out
    remote_ok = True, # Whether you're ok with remote work
    save_results_every_x_pages = 1, # After how many pages (25 jobs) to save the search results to our file
    search_terms = [ # Searches you want the agent to make
        "machine learning",
        "artificial intelligence"
    ],
    skip_previously_viewed = True # Whether or not to skip jobs that LinkedIn marks as previously viewed
)

# User Settings
user = dict(
    address = dict( # Street address
        city = "Washington", # City
        country = "United States of America", # Country for your address
        street = "1600 Pennsylvania Avenue NW", # Street name for your address
        street_line_2 = "", # Suite, apt number, etc.
        state = "District of Columbia", # State for your address
        zip_code = "20500" # ZIP code for your address
    ),
    blacklist_companies = "None", # Are there any companies you don't want to apply to?
    certify_information_accuracy = "Yes", # Do you certify that all information you have entered is accurate?
    disability = "No", # Do you have any disabilities
    email = "example@gmail.com", # The email you'd like to use for job applications
    hispanic_or_latino = "No", # Whether you're hispanic or latino
    job_interests = "machine learning, AI", # What you're looking for in a job
    languages = "English - Native speaker", # Please list all languages you speak/write and how fluent you are with them
    linkedin_email_or_phone = "",
    # The email or phone number you use to login to LinkedIn (make sure you keep this secret and don't commit to version control)
    # This is optional, you can login manually if you would like to instead
    linkedin_password = "",
    # The password you use to login to LinkedIn (make sure you keep this secret and don't commit to version control)
    # This is optional, you can login manually if you'd like
    linkedin_profile = "https://www.linkedin.com/in/reidhoffman/", # The link to your LinkedIn profile
    name = "John Doe", # Your name
    type_of_role = ("I am looking for a full-time position. I would be "
                    "interested in a contract position if there was a possibility "
                    "of converting to a full-time role. I would not be interested in an internship."), # Whether or not you are interested in contract roles
    open_to_relocation = "Yes I am looking to relocate to the San Francisco Bay Area", # Whether or not you are willing to relocation for a job
    phone_number = "+12484345508", # Your phone number including the country code
    phone_type = "Mobile", # The type of phone the above number is for
    race = "White", # Your race
    remote_work_preference = "I am open to remote, hybrid, and in-person positions", # Whether you are open to remote, in-person or hybrid positions
    resume_path = "C:/path/to/your/Resume.pdf", # The path to your resume
    salary_range = "Over $100,000 per year", # Your expected salary range
    us_citizen = "Yes", # Whether or not you are a US citizen
    us_require_sponsorship = "No", # Whether or not you would require sponsorship to work in the US
    us_security_clearance_level = "None", # The active level of US security clearance you have
    us_work_authorization = "Authorized to work for any employer", # Your work authorization status
    veteran_status = "I am not a protected veteran" # Your veteran status
)