import glob, os
from celery import Celery, group, chord
import requests 
import json 
import time

RESULT = []

ENDPOINT = "https://ranking.glassdollar.com/graphql"

CORPBYIDQUERY = '''
query ($id: String!) {
  corporate(id: $id) {
    id
    name
    description
    logo_url
    hq_city
    hq_country
    website_url
    linkedin_url
    twitter_url
    startup_partners_count
    startup_partners {
      master_startup_id
      company_name
      logo_url: logo
      city
      website
      country
      theme_gd
      __typename
    }
    startup_themes
    startup_friendly_badge
    __typename
  }
}
'''

LISTCORPQUERY = """
query ExampleQuery($filters: CorporateFilters, $page: Int, $sortBy: String) {
  corporates(filters: $filters, page: $page, sortBy: $sortBy) {
    rows {
      id
    }
  }
}
"""

LISTCORPPAYLOAD = {
    "variables": {
        "filters": {
            "hq_city": [],
            "industry": []
        },
        "page": 27
    },
    'query': LISTCORPQUERY
}

CORPBYIDPAYLOAD = {
    'query': CORPBYIDQUERY,
    'variables': {
        'id': '8483fc50-b82d-5ffa-5f92-6c72ac4bdaff',
    }
}

app = Celery('tasks', broker=os.getenv('BROKER'), backend=os.getenv('BACKEND'))

@app.task
def get_corp_list(page):
    '''
    get a list of the corporate ids of the page 
    create a group of get_corp tasks to retrieve data 
    '''
    LISTCORPPAYLOAD['variables']['page'] = page
    response = requests.post(ENDPOINT, json=LISTCORPPAYLOAD)
    if response.status_code == 200: 
        data = response.json()
        corp_ids = data['data']['corporates']['rows']
        
        grp = chord((get_corp.s(id['id']) for id in corp_ids), collect.s(page))()
        return grp.id
    else: 
        raise ValueError(f"Failed to list corp ids. Status code: {response.status_code}")

@app.task 
def get_corp(id):
    '''
    get corporate data using its id
    '''
    CORPBYIDPAYLOAD['variables']['id'] = id 
    response = requests.post(ENDPOINT, json=CORPBYIDPAYLOAD)
    if response.status_code == 200:
        data = response.json()
        return data['data']['corporate']
    else: 
        raise ValueError(f"Failed to get corp by id. Status code {response.status_code}")

@app.task 
def collect(corp_data_list, page):
    '''
    callback to a group of get_corp tasks 
    combine the data into a single json file with its page number
    '''
    result_json = json.dumps(corp_data_list, indent=2)
    filename = 'corp_data_' + str(page) + '.json'
    with open(filename, 'w') as f:
        f.write(result_json)

@app.task 
def write_all():
    '''
    combines corp_data_page.json files into a single corp_data.json file
    deletes them afterwards
    '''

    data = []
    for i in range(1, 28):  # loop to go through all 27 pages
        filename = 'corp_data_' + str(i) + '.json'
        with open(filename, 'r') as f:
            page_data = json.load(f)
        data.extend(page_data)
    with open('corp_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    for f in glob.glob("corp_data_*.json"):
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error deleting file {f}: {e}")


@app.task 
def main_task():
    '''
    Gets all the data, and combines it to a single corp_data.json
    I didnt use group here specifically, 
     - the result tend to not differ, even faster this way 
     - calling .ready() on group obj returns true as soon as group starts executing subtasks 
    '''

    for i in range(1, 28): 
       grp = get_corp_list.delay(i)
       while not grp.ready(): 
           time.sleep(1)
    write_all() 


