from smtplib import SMTP
import sqlite3
import threading
from email.message import EmailMessage
import time
import os
import passwords
import sys
import random

def mk_msg(city):
    return f'''Hello,

    I am {NAMES[random.randint(0, len(NAMES) - 1)]}, a volunteer with the student-run COVID Networks. We are reaching out because we are interested in working with the city of {city} to expand our community impact and further our mission in alleviating loneliness caused by social isolation amongst both students and seniors.

    Regarding our organization, we have designed a free virtual service where senior citizens can request to hold online video sessions one-on-one with students and other young citizens. In addition, we prepare fun events and activities for seniors that will help them find a community during this pandemic. These include interactive yoga meditation sessions, book clubs, trivia/online games, live music performances and artwork sessions, and more! We are currently a 501-c national nonprofit recognized by the government. Our 300+ volunteers have worked with over 3000 seniors and 30 senior centers!

    Notably, we partnered with San Francisco Center for Jewish Living and StoryCorps Connect to embark on a national project documenting some of the interviews we have had with their seniors. More details can be found at https://storycorps.org/participate/storycorps-connect/. Our work has been featured by prominent local news platforms, including KCBS, SF Examiner, and The Mercury News.

    With the flu-season setting in, we are aware that the pandemic’s severe effects and quarantine measures are far from over. We would like to partner with {city} as we believe that we can make a tangible impact in the community with our passionate volunteers, and hope to have your support in our outreach efforts. Check out more information on our website at Covidnetworks.org, and feel free to reach out to us for further questions and information.

    Thank you so much for your time and consideration.
    '''
with open('names.txt') as handle:
    NAMES = handle.readlines()
NAMES = map(str.strip, NAMES)
EMAIL_ADDRESS = passwords.username
EMAIL_PASSWORD = passwords.password
mailed = list()
failed = False
count = 0

def send_mail(email):
    msg = EmailMessage()
    msg['Subject'] = 'Online Senior-Student Connection Platform'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email[2]
    msg.set_content(mk_msg(email[1]))

    try:
        with SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            #smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            #smtp.send_message(msg)
            #mailed.append(email[0])
    except:
        print('message failed')
        global failed
        failed = True
    print(f'sent to: {email[2]} in: {email[1]} id: {email[0]}')

def mailer():
    c.execute('''SELECT id FROM websites WHERE used = 0 AND searched = 1 LIMIT 1;''')
    id = c.fetchall()[0][0]
    c.execute(f'''SELECT emails.id, websites.city, emails.email
                 FROM emails LEFT JOIN websites ON emails.city = websites.id
                 WHERE emails.used = 0 AND websites.id = {id};''')
    que = c.fetchall()
    que = eledgeble(que, id)
    print(f'total length is: {len(que)}.')
    time.sleep(2)
    threads = list()
    for _ in range(3):
        for _ in range(3): # send 99 mails before 5 min break for google
            for _ in range(33):
                if not que:
                    for t in threads:
                        t.join()
                    save()
                    global failed
                    if failed:
                        failed = False
                        print('non-failed complete')
                        print('waiting on failed...')
                        #time.sleep(5*60)
                        mailer()
                    set_site_used(id)
                    print('city complete')
                    return id
                while threading.active_count() > 5:
                    time.sleep(1)

                t = threading.Thread(target=send_mail, args=(que.pop(),), daemon=True)
                t.start()
                threads.append(t)
        time.sleep(5*60)
    for t in threads:
        t.join()
    save()
    print('reached mailing limit')

def save():
    global count
    global mailed
    count += len(mailed)
    print(f'sent: {len(mailed)}. total = {count}')
    for i in mailed:
        c.execute(f'UPDATE emails SET used = 1 WHERE id = {i};')
        mailed = list()
    conn.commit()

def eledgeble(emails, id):
    bad_words = ['court', 'report', 'police', 'fire', 'policy', 'emergency', 'finance', 'complaint', 'staff', 'inspect', 'treasury', 'election', 'deputy', 'transit', 'airport', 'prosecutor', 'customerservice','stormwater', 'housing', 'safety', 'hotline', 'parking', 'development', 'license', 'admin', 'webhelp', 'property', 'closure', 'records', 'plan']
    bad_ids = list()
    good_emails = list()
    if not emails:
        print(f'{id} had no emails')
        set_site_used(id)
        mailer()
    while emails:
        email = emails.pop()
        for j in bad_words:
            if j in email[2]:
                bad_ids.append(email[0])
                break
        if not email[0] in bad_ids:
            good_emails.append(email)
    for i in bad_ids:
        c.execute(f'UPDATE emails SET used = 2 WHERE id = {i}')
    return good_emails

def set_site_used(id):
    c.execute(f'UPDATE websites SET used = 1 WHERE id = {id}')
    print('used city:', id)
    conn.commit()

if __name__ == '__main__':
    conn = sqlite3.connect(f'{os.getcwd()}\\CovidNet.db')
    c = conn.cursor()
    mailer()
    conn.close()
