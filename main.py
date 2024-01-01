from tasks import main_task
from fastapi import FastAPI 
from group import write_results
import os
import json 

CORP_DATA_PATH = 'corp_data.json'
app = FastAPI()

@app.get("/scrape")
def scrape():
    if os.path.exists(CORP_DATA_PATH):
        return {'status': 'corp_data.json already exists. delete the old one.'}
    else:
        main_task.delay()
        return {'status': 'task submitted'}

