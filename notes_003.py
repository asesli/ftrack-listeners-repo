import sys,os
import re


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging
logging.basicConfig()
logger = logging.getLogger('logger')

import urllib3
urllib3.disable_warnings()

sys.path.insert(0,"X:/apps/Scripts/FTRACK/python-lib/lib")
sys.path.insert(0,"X:/apps/Scripts/FTRACK/python-lib/lib/site-packages")
import ftrack_api


import smtplib, ssl


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

def notes(event):

    for entity in event['data'].get('entities', []):

        entityType = entity.get('entityType')
        if entityType != 'note': 
            continue

        changes = entity.get('changes')
        if not changes:
            continue

        if changes.get('text'):

            text = changes['text'].get('new')
            if text :
                text = str(text.encode('utf-8'))
            else:
                text = 'None'

            if '@' not in text:
                continue

            old_text = str(changes['text'].get('old'))
            tags = re.findall(r"(@[a-zA-Z]+)", text)
            new_tags = tags

            #Delete this part if you want to email tagged users every time there is a change in that note. 
            old_tags = []
            if '@' in old_text:
                old_tags = re.findall(r"(@[a-zA-Z]+)", old_text)
            new_tags = [tag for tag in tags if tag not in old_tags]

            if not new_tags:
                continue

            new_tags = [tag.replace('@','').lower() for tag in tags]
            default_body = 'You were tagged in a note on Ftrack.\n\n{link_text}\n{dash_url}\n\n{note}'

            user_id = changes['userid']['new']

            session = ftrack_api.Session()

            active_users = session.query('select custom_attributes, first_name, last_name, username, email, id from User where is_active is True').all()

            related_users = []

            author = None

            parents = entity.get('parents')
            if parents:
                parents = parents[::-1]



            parent_ids_lst = [str(p['entityId']) for p in parents]
            parent_ids = tuple(parent_ids_lst)
            #print parent_ids

            parents = session.query("select name, id from Context where id in {}".format( parent_ids )).all()

            #print 'entity: ', entity.keys()
            #print
            #print 'entity.changes: ', changes.keys()
            #print
            #print 'entity.parents: ', parents[0].keys()
            #print
            #print [i['name'] for i in parents]

            parents =  sorted(parents,key=lambda x:parent_ids_lst.index(x['id']))

           
            dash_p_url = "https://domain.ftrackapp.com/#slideEntityId={id}&slideEntityType=task&itemId=home".format(id=parents[-1]['id'])
            dash_h_url  = '<a href="{url}">Go to the Noted item</a>'.format(url=dash_p_url)

            link_p_text = ' / '.join([i['name'] for i in parents])

            a = '<a href="https://domain.ftrackapp.com/#slideEntityId={id}&amp;slideEntityType=task&amp;itemId=home" target="_blank" rel="noopener">{name}</a>'
            link_h_text = ' / '.join([ a.format(id=i['id'], name=i['name'])  for i in parents])

            title = ' / '.join([i['name'] for i in parents[-2::]])
            #print title
            #print link_text
            #print dash_p_url

            #a = ""
            #continue

            for user in active_users:
                user_dict = {}
                user_dict['first_name'] = user['first_name']
                user_dict['last_name'] = user['last_name']
                user_dict['username'] = user['username']
                user_dict['nicknames'] = user['custom_attributes']['nicknames']
                user_dict['id'] = user['id']
                user_dict['first_last_name'] = str(user_dict['first_name'])+str(user_dict['last_name'])
                names = user_dict['nicknames'].replace(' ',',').split(',')
                names = [n for n in names if n != '']
                names += [user_dict['first_name']]+[user_dict['username']]+[user_dict['first_last_name']]
                names = [n.lower() for n in names]
                user_dict['names'] = names

                related = [tag for tag in new_tags if tag in names]
                if related:
                    user_dict['email'] = user['email']
                    related_users.append(user_dict)

                if user_dict['id'] == user_id:
                    author = user_dict

            user_emails = [user['email'] for user in related_users]
            user_txt = ','.join(user_emails)
            #title = 'ShotCodeTask'
            subject = 'Note on ' + title


            '''
            body = default_body.format(
                    note=text,
                    link_text=link_p_text,
                    dash_url=dash_p_url

                    )
            '''

            #The mail addresses and password

            sender_address = 'luxvfx.notifications@gmail.com'
            sender_pass = '8 or more'

            receiver_address = user_emails


            #msg = 'Subject: {}\n\n{}'.format(subject, body)

            
            msg = MIMEMultipart()
            #msg['Subject'] = '{}\n\n{}'.format(subject, body)#body
            msg['Subject'] = subject
            msg['From'] = sender_address#author['email']
            msg['To'] = user_txt
            msg["Bcc"] = user_txt


            plain = """\
{note}


{link_text}
{dash_url}""".format(
    link_text=link_p_text,
    dash_url=dash_p_url,
    note=text
    )

            html = """\
<html>
    <body>
        <p>{note}<br>
            <br>
            <br>
            {link_text}<br>
            {dash_url}<br>
            <br>
        </p>
    </body>
</html>
""".format(
    link_text=link_h_text,
    dash_url=dash_h_url,
    note=text
    )
            msg.attach(MIMEText(plain, 'plain'))
            #msg.attach(MIMEText(html, 'html'))
            #msg.attach(MIMEText(body, 'plain'))
            
            #print html
            #
            try:
                # Create a secure SSL context
                #ssl_context = ssl.create_default_context()

                #Create SMTP session for sending the mail
                stmp_session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
                stmp_session.ehlo()
                #stmp_session.starttls(context=ssl_context) #enable security
                stmp_session.starttls()
                stmp_session.ehlo()
                stmp_session.login(sender_address, sender_pass) #login with mail_id and password
                stmp_session.sendmail(sender_address, receiver_address, msg.as_string())
                #print msg.as_string()
                print('Mail Sent to {}'.format(user_txt))
            except Exception as e:
                # Print any error messages to stdout
                print(e)
            finally:
                stmp_session.quit() 

            pass
            

# Subscribe to events with the update topic.
session = ftrack_api.Session()
session.event_hub.subscribe('topic=ftrack.update', notes)
session.event_hub.wait()
