from urllib import parse
from selenium.webdriver import Chrome, ChromeOptions
from pyvirtualdisplay import Display
import pandas as pd
from util import get_engine, get_upload_url
from urllib.parse import urlparse
from random import randint, shuffle, choice
from time import time
import requests
from shutil import make_archive
from argparse import ArgumentParser
from datetime import datetime
import os

def main():
    # parse arguments
    args = parse_args()
    category = args.category
    profile_path = f'profiles/{category}'

    start_time = datetime.now()

    # get URLs
    urls = get_urls(category)

    # check url length
    if len(urls) == 0:
        print("No urls found for", category)
        return

    # init virtual display
    Display(size=(1920,1080)).start()
    
    # init driver
    options = ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument(f'--user-data-dir={profile_path}')

    driver = Chrome(options=options)
    driver.implicitly_wait(30)

    # walkthrough URLs and loiter
    for url in urls:
        try:
            driver.get(f'https://{url}')
            loiter(driver, how_long=400)
        except Exception as e:
            print(e)

    # save end time
    end_time = datetime.now()

    # save browser profile
    archive = make_archive(category, 'zip', profile_path, '.')

    # upload profile to server
    filename = upload(archive, end_time)

    # save info to database
    row = {
        'Category': category,
        'StartTime': start_time,
        'EndTime': end_time,
        'Filename': filename
    }
    pd.DataFrame([row]).to_sql('crawls', con=get_engine(), if_exists='append', index=False)

    # close webdriver
    driver.close()


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('category')
    args = parser.parse_args()
    return args

def get_urls(category):
    sw = pd.read_sql('similarweb', con=get_engine())
    sw = sw[sw['Category'] == category]
    return sw.sort_values(by='Rank')['URL']

def get_random_text():
    with open('topics.txt') as f:
        texts = f.read().split('\n')
        return choice(texts)[:30].strip()                

def get_filename(archive, timestamp):
    basename = os.path.basename(archive)
    name, ext = os.path.splitext(basename)
    ts = datetime.strftime(timestamp, '%Y%m%d%H%M%S')
    return f'{name}-{ts}{ext}'

def upload(archive, timestamp):
    url = get_upload_url()
    files = {'file': open(archive, 'rb')}
    name = get_filename(archive, timestamp)
    r = requests.post(url,data={'key': 'from_haroon', 'filename': name}, files=files)
    if 'success' in r.text:
        return name
    raise Exception(r.text)

def loiter(driver, how_long=300):
    start_time = time()
    
    # spend the required time around the site
    while (time() - start_time) < how_long:
        
        try:
            action = randint(0, 5)
            if action == 0:
                # execute a random scroll
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight * Math.random())", "");
            elif action == 1:
                # get domain name
                dom = urlparse(driver.current_url).netloc
                # get all `a` links
                linkEls = driver.find_elements_by_tag_name('a')
                # shuffle links so random is clicked
                shuffle(linkEls)

                for link in linkEls[:5]:
                    href = link.get_attribute('href')
                    # for each link, check for non-empty href to same domain
                    if href is not None and href.strip() != '' and dom == urlparse(href).netloc:
                        # click the link
                        try:
                            link.click()
                            break
                        except:
                            pass
            elif action == 2:
                # get all `input` fields
                inputEls = driver.find_elements_by_tag_name('input')
                # shuffle fields so random is selected
                shuffle(inputEls)

                text = get_random_text()
                for inputt in inputEls[:5]:
                    try:
                        inputt.send_keys(text + '\n')
                        break
                    except:
                        pass
            else:
                pass
        except:
            pass

if __name__ == '__main__':
    main()
