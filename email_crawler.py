import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
import requests.exceptions
from collections import deque
import re
import lxml
import multiprocessing as mp
import random
import sys
import traceback

def create_email_table(c):
    sql_create = '''CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city INTEGER,
                    email TEXT UNIQUE NOT NULL,
                    used TINYINT
                    ); '''
    c.execute(sql_create)

def slash_freq(str):
    count = 0
    for s in str:
        if s == '/':
            count += 1
    return count

def extract(lst):
    return [item[0] for item in lst]

def scrape(url, di, emails):
    # extract base url to resolve relative links
    parts = urlsplit(url)
    base = '{0.netloc}'.format(parts)
    strip_base = base.replace('www.', '')
    base_url = '{0.scheme}://{0.netloc}'.format(parts)

    # a queue of urls to be crawled
    url = url[len(base_url):]
    new_urls = deque([url])

    # a set of urls that we have already been processed
    processed_urls = set()
    # a set of domains inside the target website
    local_urls = set()


    # process urls one by one until we exhaust the queue
    while len(new_urls):
        # move next url from the queue to the set of processed urls
        url = new_urls.popleft()
        processed_urls.add(url)
        # get url's content
        try:
            response = requests.get(base_url + url)
            time.sleep(5)
        except (requests.exceptions.MissingSchema,
                requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL,
                requests.exceptions.InvalidSchema):
            print(',', end='')
            continue
        except Exception as err:
            print('Response error', end='')
            continue

        for i in re.findall(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.gov', response.text, re.I):
            emails.put([i.lower(), di])
            print('|', end='')

        # create a beutiful soup for the html document
        soup = BeautifulSoup(response.text, 'lxml')

        for link in soup.find_all('a'):
            # extract link url from the anchor
            anchor = link.attrs['href'] if 'href' in link.attrs else ''

            if anchor.startswith('/') and slash_freq(anchor) < 3:
                if len(anchor) < 25:
                    local_urls.add(anchor)
            elif strip_base in anchor and slash_freq(anchor) < 5:
                anchor = anchor[len(base_url):]
                if len(anchor) < 25:
                    local_urls.add(anchor)
            elif 'mailto:' in anchor:
                match = re.search(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.gov', anchor)
                if match:
                    emails.put([match.group().lower(), di])
                print('|', end='')
        for i in local_urls:
            if not i in new_urls and not i in processed_urls:
                new_urls.append(i)

        local_urls = set()
        print('.', end='')
        if random.randint(0, 100) == 100:
            print('Status: %d | Processed: %s' % (response.status_code, base_url + url))
        sys.stdout.flush()

def run(site, done, emails):
    print('\nScraping: %s at %s\t' % (site[2], site[1]), end='')
    sys.stdout.flush()
    scrape(site[1], site[0], emails)
    done.put(site[0])
    print('\nCompleted: %s' % (site[2]))

def used_city(c, done):
    while not done.empty():
        c.execute(f'''UPDATE websites
                    SET searched = 1
                    WHERE id = {done.get()}''')

def insert_new_emails(c, emails):
    while not emails.empty():
        e = emails.get()
        print(e[0])
        c.execute(f'''INSERT OR IGNORE INTO emails(city, email, used)
                     VALUES({e[1]}, \"{e[0]}\", 0);''')

if __name__ == '__main__':
    emails = mp.SimpleQueue()
    done = mp.SimpleQueue()

    conn = sqlite3.connect(r'D:/Programming/CovidNet/CovidNet.db')
    c = conn.cursor()
    create_email_table(c)
    c.execute('SELECT id, url, city FROM websites WHERE searched == 0 AND health == 1')
    sites = [list(i) for i in c.fetchall()]
    print(sites)

    while sites:
        site = sites.pop()
        _ = mp.Process(target=run, args=(site, done, emails), name=site[2], daemon=True)
        _.start()

        while len(mp.active_children()) >= mp.cpu_count() * 4 or (not sites and mp.active_children()):
            if (not done.empty()) or (not emails.empty()):
                used_city(c, done)
                insert_new_emails(c, emails)
                conn.commit()
            time.sleep(60)

    conn.close()
