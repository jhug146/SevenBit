"""
SevenBit v10
Able to upload to lovedjeans website
JSON file containing upload and translation data
"""
import multiprocessing

USE_WEB_UI = False

multiprocessing.freeze_support()   # Fixes issues with threading in the .exe file

if USE_WEB_UI:
    from ui.website.web_app import WebApp
    WebApp().run()
else:
    from app import App
    App().run()
