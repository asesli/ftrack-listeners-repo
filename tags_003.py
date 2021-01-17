#import requests.packages.urllib3
#requests.packages.urllib3.disable_warnings()

#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()

# VERSION 2
import sys,os

import logging
logging.basicConfig()
logger = logging.getLogger('logger')

import urllib3
urllib3.disable_warnings()

sys.path.insert(0,"X:/apps/Scripts/FTRACK/python-lib/lib")
sys.path.insert(0,"X:/apps/Scripts/FTRACK/python-lib/lib/site-packages")

import ftrack_api

# setup environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"] = credentials.server_url
    os.environ["FTRACK_API_USER"] = credentials.api_user
    #os.environ["LOGNAME"] = credentials.api_user
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")



'''

def tags(event):

    update = False 

    for entity in event['data'].get('entities', []):

        entityId = entity['entityId']

        changes = entity.get('changes')

        keys =  changes.keys()

        detect = ['statusid']

        if len(list(set(keys) & set(detect))) > 0:
            
            session = ftrack_api.Session()

            sel = session.query('select custom_attributes, status.name from Task where id is "{0}"'.format(entityId)).first()
                
            if sel['status']['name'] == 'Internal Review':

                sel['custom_attributes']['review_counter'] = sel['custom_attributes']['review_counter'] + 1

                session.commit()
'''

def read_repo():
    repo = r"L:\HAL\LIVEAPPS\apps\Scripts\FTRACK\ftrack_events\resources\tags_repo.txt"
    content = []
    with open(repo) as f:
        content = f.readlines()


    content = [x.strip() for x in content] 
    content = list(set(content))
    content = sorted(content)
    return content

def tags(event):

    changes = event['data']['recordData'].get('changes', {})
    attributeName = event['data']['attributeName']
    output = []
    if attributeName == 'tags':

        items = read_repo()

        #items = ['Furniture', 'Car']

        output = []
        #print items
        for i in items:
            item = {
                        'name': i,
                        'value': i
                    }
            output.append(item)

    return output


# Subscribe to events with the update topic.

session = ftrack_api.Session()
#expand the topic to be more specific.... like 
session.event_hub.subscribe('topic=ftrack.dynamic-enumerator', tags)
session.event_hub.wait()#duration=60)
