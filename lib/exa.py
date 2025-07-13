from dotenv import load_dotenv

load_dotenv()

import os

from exa_py import Exa

# Initializations
exa = Exa(api_key=os.getenv("EXA_API_KEY"))
