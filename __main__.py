"""
SevenBit v10
Able to upload to lovedjeans website
JSON file containing upload and translation data
"""
import multiprocessing
from app import App

multiprocessing.freeze_support()   # Fixes issues with threading in the .exe file
App().run()
