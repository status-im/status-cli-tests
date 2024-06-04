import os
from dotenv import load_dotenv

load_dotenv()  # This will load environment variables from a .env file if it exists


def get_env_var(var_name, default=None):
    env_var = os.getenv(var_name, default)
    if env_var in [None, ""]:
        print(f"{var_name} is not set; using default value: {default}")
        env_var = default
    print(f"{var_name}: {env_var}")
    return env_var


# Configuration constants. Need to be upercase to appear in reports
NUM_MESSAGES = get_env_var("NUM_MESSAGES", 1)
DELAY_BETWEEN_MESSAGES = get_env_var("DELAY_BETWEEN_MESSAGES", 2)
RUNNING_IN_CI = get_env_var("CI")
