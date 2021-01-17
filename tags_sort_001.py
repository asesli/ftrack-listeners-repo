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


def tag_sort(event):

    for entity in event['data'].get('entities', []):

        #if entity.get('action') == 'remove':
        #    continue

        changes = entity.get('changes')
        if not changes:
            continue

        if changes.get('tags'):

            entityId = entity.get('entityId')
            if not entityId:
                continue

            entityType = entity.get('entityType')
            if str(entityType).lower() not in ['shot','task']:#<--shots are tasks?? hmm.. 
                continue

            tags = changes['tags'].get('new')
            if not tags:
                continue
                
            tags =  tags.split(', ')
            tags = sorted(list(set(tags)))
            tags = ', '.join(tags)
            #print tags
            session = ftrack_api.Session()
            sel = session.query('select custom_attributes from Shot where id is "{0}"'.format(entityId)).first()
            if sel:
                if sel['custom_attributes']['tags'] != tags:
                    sel['custom_attributes']['tags'] = tags
                    session.commit()

# Subscribe to events with the update topic.

session = ftrack_api.Session()
#expand the topic to be more specific.... like 
session.event_hub.subscribe('topic=ftrack.update', tag_sort)
session.event_hub.wait()#duration=60)
