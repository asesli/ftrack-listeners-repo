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


def auto_update_paths(event):

    update = False 

    for entity in event['data'].get('entities', []):

        entityType = entity.get('entityType')
        if str(entityType).lower() not in ['project', 'episode', 'sequence', 'shot', 'task']:
            continue

        if entity.get('action') == 'remove':
            continue

        entityId = entity.get('entityId')
        if not entityId:
            continue

        changes = entity.get('changes')
        if not changes:
            continue

        parents = entity.get('parents')

        #more specific

        keys =  changes.keys()

        detect = ['parent_id', 'name', 'typeid']

        if len(list(set(keys) & set(detect))) > 0:
            
            session = ftrack_api.Session()
            #items = session.query('select custom_attributes, object_type.name, type.name, parent.name, link, name from TypedContext where ancestors.id is "{0}" or project_id is "{0}"'.format(entityId)).all()

            sel = session.query('select custom_attributes, project_id, object_type.name, type.name, parent.name, ancestors, link, name from TypedContext where id is "{0}"'.format(entityId)).first()

            if sel == None:
                #print 'sel was none yo'
                sel = session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(entityId)).first()
                proj = sel

            else:
                proj = session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(sel['project_id'])).first()

            if proj != sel:
                x = '{} > {}'.format(sel['parent']['name'], sel['name'])
                print x

            #episodes are found from Projet Looking downwards instead of finding it in the items iterator.
            #would be more efficient if we look at ancestors?

            episodes = session.query('select name from Episode where project_id is "{0}"'.format(proj['id'])).all()

            episode_names = [e['name'] for e in episodes]

            #print episode_names

            project_path = proj['custom_attributes']['Project_Path']
            project_name = proj['full_name']


            if sel == proj:

                base_path = '{project_path}{project_name}/'.format(project_path=project_path, project_name=project_name)

                if proj['custom_attributes']['base_path'] != base_path:
                    proj['custom_attributes']['base_path'] = base_path
                    update = True

                if proj['custom_attributes']['resolution'] in ['', None]:
                    proj['custom_attributes']['resolution'] = 'HD1080 1920 x 1080'
                    update = True

                if update:
                    session.commit()
                    

            else:
                i = sel

                episode = ''

                if i['object_type']['name'] == 'Episode':

                    episode = i['name']

                else:

                    episode = [ x['name'] for x in i['ancestors'] if x['name'] in episode_names ]

                    if len(episode)>0: 

                        episode = episode[0]

                    else:

                        episode = ''

                base_path = '{project_path}{project_name}/{episode}/'.format(project_path=project_path, project_name=project_name, episode=episode).replace('//','/')

                if i['custom_attributes']['base_path'] != base_path:
                    i['custom_attributes']['base_path'] = base_path
                    update = True


                if i['object_type']['name'] == 'Sequence':
                    base_cis = '{base_path}09_QT/EDITORIAL/_base_cis/'.format(base_path=base_path)
                    if i['custom_attributes']['base_cis'] != base_cis:
                        i['custom_attributes']['base_cis'] = base_cis
                        update = True
                        
                    base_edl = '{base_path}09_QT/EDITORIAL/EDL/'.format(base_path=base_path)
                    if i['custom_attributes']['base_edl'] != base_edl:
                        i['custom_attributes']['base_edl'] = base_edl
                        update = True

                if i['object_type']['name'] == 'Task':

                    shot_name = i['parent']['name'] #this may break when it comes to asset builds since they are not nested under a shot..
                    task_type = i['type']['name']
                    task_name = i['name']

                    path = ''#base_path
                    out_path = ''#base_path

                    if task_type.lower() in ['compositing', 'precomp', 'cleanplate', 'retime', 'rotoscoping', 'paintout']:

                        comp_out_dir = '02_OUTPUT/03_comp'

                        if task_type.lower() != task_name.lower():
                            comp_out_dir = '02_OUTPUT/01_precomp/{task_name}'.format(task_name=task_name)
                        
                        path     = '{base_path}{dept_name}/{shot_name}/'.format(base_path=base_path,shot_name=shot_name,dept_name='05_COMP')
                        out_path = '{base_path}{dept_name}/{shot_name}/{comp_out_dir}/'.format(base_path=base_path,shot_name=shot_name,dept_name='05_COMP',comp_out_dir=comp_out_dir)

                    if task_type.lower() in ['matchmove', 'tracking']:

                        path = '{base_path}{dept_name}/scenes/{shot_name}/tracking/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                        out_path = '{base_path}{dept_name}/{shot_name}/TRAC/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                    if task_type.lower() in ['animation']:

                        path = '{base_path}{dept_name}/scenes/{shot_name}/anim/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                        out_path = '{base_path}{dept_name}/{shot_name}/ANIM/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                    if task_type.lower() in ['layout']:

                        path = '{base_path}{dept_name}/scenes/{shot_name}/layout/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                        out_path = '{base_path}{dept_name}/{shot_name}/LYT/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                    if task_type.lower() in ['lighting']:

                        path = '{base_path}{dept_name}/scenes/{shot_name}/lighting/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                        out_path = '{base_path}{dept_name}/{shot_name}/FINL/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                    if task_type.lower() in ['fx']:

                        path = '{base_path}{dept_name}/scenes/{shot_name}/fx/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                        out_path = '{base_path}{dept_name}/{shot_name}/FX/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                    path = path.replace('//', '/')
                    out_path = out_path.replace('//', '/')

                    if i['custom_attributes']['path']!= path: #only make changes if they dont already exist
                        i['custom_attributes']['path'] = path
                        update = True

                    if i['custom_attributes']['out_path'] != out_path: #only make changes if they dont already exist
                        i['custom_attributes']['out_path'] = out_path
                        update = True


                #We could expand this so it browses the directorty for the most applicable plate... for now, run it at plate level, and let get_version choose _O vs _R
                if i['object_type']['name'] == 'Shot':
                    shot_name = i['name']
                    #print shot_name
                    out_path = '{base_path}01_PLATES/{shot_name}/PLATE/'.format(base_path=base_path, shot_name=shot_name)
                    #plate_path = out_path

                    #plate_path = plate_path.replace('//', '/')
                    out_path = out_path.replace('//', '/')

                    if i['custom_attributes']['out_path'] != out_path: #only make changes if they dont already exist
                        i['custom_attributes']['out_path'] = out_path
                        update = True

        if update:
            session.commit()


# Subscribe to events with the update topic.

session = ftrack_api.Session()
#expand the topic to be more specific.... like 
session.event_hub.subscribe('topic=ftrack.update', auto_update_paths)
session.event_hub.wait()#duration=60)
