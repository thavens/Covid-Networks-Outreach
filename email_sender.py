from smtplib import SMTP
import sqlite3
import threading
from email.message import EmailMessage
import time
import os
import passwords

def mk_msg(city):
    return f'''Hello,

    I am {NAME}, a volunteer with the student-run COVID Networks. We are reaching out because we are interested in working with the city of {city} to expand our community impact and further our mission in alleviating loneliness caused by social isolation amongst both students and seniors.

    Regarding our organization, we have designed a free virtual service where senior citizens can request to hold online video sessions one-on-one with students and other young citizens. In addition, we prepare fun events and activities for seniors that will help them find a community during this pandemic. These include interactive yoga meditation sessions, book clubs, trivia/online games, live music performances and artwork sessions, and more! We are currently a 501-c national nonprofit recognized by the government. Our 300+ volunteers have worked with over 3000 seniors and 30 senior centers!

    Notably, we partnered with San Francisco Center for Jewish Living and StoryCorps Connect to embark on a national project documenting some of the interviews we have had with their seniors. More details can be found at https://storycorps.org/participate/storycorps-connect/. Our work has been featured by prominent local news platforms, including KCBS, SF Examiner, and The Mercury News.

    With the flu-season setting in, we are aware that the pandemic’s severe effects and quarantine measures are far from over. We would like to partner with {city} as we believe that we can make a tangible impact in the community with our passionate volunteers, and hope to have your support in our outreach efforts. Check out more information on our website at Covidnetworks.org, and feel free to reach out to us for further questions and information.

    Thank you so much for your time and consideration.
    '''

EMAIL_ADDRESS = passwords.username
EMAIL_PASSWORD = passwords.password
NAME = 'Mike'
mailed = list()
count = 0

def multi(email):
    msg = EmailMessage()
    msg['Subject'] = 'Online Senior-Student Connection Platform'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email[2]
    msg.set_content(mk_msg(email[1]))

    with SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    mailed.append(email[0])
    print(f'sent to: {email[2]} in: {email[1]} id: {email[0]}')


if __name__ == '__main__':
    conn = sqlite3.connect(f'{os.getcwd()}\\CovidNet.db')
    c = conn.cursor()
    for _ in range(20):
        c.execute('''SELECT emails.id, websites.city, emails.email
                    FROM emails LEFT JOIN websites ON emails.city = websites.id
                    WHERE emails.used = 0
                    LIMIT 30;''')
        que = c.fetchall()
        print(que)
        if not que:
            break
        time.sleep(5)
        threads = list()
        for email in que:
            while threading.active_count() > 5:
                time.sleep(2)

            if '.com' in email[2]:
                mailed.append(email[0])
                continue

            t = threading.Thread(target=multi, args=(email,), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        count += len(mailed)
        print(f'sent: {len(mailed)}. total: {count}')
        for id in mailed:
            c.execute(f'UPDATE emails SET used = 1 WHERE id = {id}')
            mailed = list()
        conn.commit()
    conn.close()
