from sqlalchemy import create_engine
import json
import os
import gzip
import pandas as pd

def get_engine():
    creds = search_for('db-creds.json')
    with open(creds) as f:
        credentials = json.load(f)
        return create_engine(f"mysql+pymysql://{credentials['USER']}:{credentials['PASS']}@{credentials['HOST']}/{credentials['DB']}")

def load_data_from_json(table):
    data_file = search_for('data/%s.json.gz' % table)
    with gzip.open(data_file, 'rb') as f:
        js = json.load(f)
        return pd.DataFrame(js)
        
def search_for(f):
    tree = (os.getcwd(), None)
    while tree[0] != '/':
        cwd = tree[0]
        file_p = os.path.join(cwd, f)
        
        # if config found, return
        if os.path.exists(file_p):
            return file_p
        
        # go to parent dir
        tree = os.path.split(tree[0])
    
    raise Exception('File %s not found!' % f)

def get_upload_url():
    return 'UPLOAD_URL'