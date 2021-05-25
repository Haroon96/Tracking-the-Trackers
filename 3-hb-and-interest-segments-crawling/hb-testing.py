from util import get_engine, get_upload_url
import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions
from pyvirtualdisplay import Display
import os
import requests
from shutil import unpack_archive, rmtree
import json
from datetime import datetime
from time import sleep
from argparse import ArgumentParser

def main():
    # parse arguments
    args = parse_args()
    crawl = args.crawl
    crawl_category = args.crawl_category

    # init virtual display
    Display(size=(1920,1080)).start()
    
    # get list of header bidding sites
    hb_sites = pd.read_sql('SELECT DISTINCT sw.URL, Category FROM similarweb sw JOIN `header-bidding-sites` hb ON sw.URL = hb.URL', con=get_engine())
    
    # organize sites by category
    sites = hb_sites[hb_sites['Category'] == crawl_category]['URL'].to_list() + hb_sites[hb_sites['Category'] != crawl_category]['URL'].to_list()
    
    hb_responses = []
    
    for site in sites:
        try:
            hb_responses.append(getHBInfo(crawl, site))
        except Exception as e:
            print(e)

    with open('columns.txt') as f:
        cols = f.read().strip().split('\n')
        df = pd.DataFrame(hb_responses, columns=cols)
        df['Time'] = datetime.now()
        try:
            df.to_sql('header-bidding-responses', con=get_engine(), index=False, if_exists='append')
        except Exception as e:
            print(e)
            df.to_json('header-bidding-response.json')

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('crawl')
    parser.add_argument('crawl_category')
    args = parser.parse_args()
    return args

def getHBInfo(profile_name, site=None):
    driver = load_driver(profile_name, headless=False)
    driver.get('https://%s' % site)
    
    # sleep for 30s for auction to happen
    sleep(30)

    row = {
        'Profile': profile_name,
        'HB_URL': site
    }
    # find pbjs var
    pbjsGlobal = driver.execute_script('return _pbjsGlobals')[0]
    # find methods for pbjs
    methods = driver.execute_script('return Object.keys(%s).filter(x => typeof(%s[x]) == "function")' % (pbjsGlobal, pbjsGlobal))
    # store each methods response
    for method in methods:
        try:
            row[method] = json.dumps(driver.execute_script('return %s.%s()' % (pbjsGlobal, method)))
        except:
            pass

    driver.close()
    return row


def download_profile(profile_name, bp='profiles'):
    # determine output directory
    name, ext = os.path.splitext(profile_name)
    profile_path = os.path.join(bp, name) 
    
    # create directory
    os.makedirs(bp, exist_ok=True)
    
    # download profile zip
    url = f'{get_upload_url()}/{profile_name}'
    out = os.path.join(bp, profile_name)

    # download if not exist
    if not os.path.exists(out):
        r = requests.get(url)
        with open(out, 'wb') as f:
            f.write(r.content)
        
    # extract profile zip
    unpack_archive(out, profile_path)
    
    # return path to profile
    return profile_path

def load_driver(profile_name=None, headless=False):
    # download profile from server
    options = ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    
    if headless:
        options.add_argument('--headless')
    
    if profile_name is not None:
        user_data_dir = download_profile(profile_name)
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
    driver = Chrome(options=options)
    driver.implicitly_wait(30)
    return driver

if __name__ == '__main__':
    main()
