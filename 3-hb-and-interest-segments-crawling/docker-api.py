from util import get_engine
import pandas as pd
from argparse import ArgumentParser
import docker

IMAGE_NAME = 'ecs289m/testing'

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--build', action="store_true", help='Build docker images')
    parser.add_argument('--runAll', action="store_true", help='Run all docker containers')
    args = parser.parse_args()
    return args, parser

def build_image():
    # get docker client and build image
    client = docker.from_env()
    client.images.build(path='.', tag=IMAGE_NAME, rm=True)

def run_containers():
    # get docker client
    client = docker.from_env()

    # get db connection
    engine = get_engine()

    # fetch channels and queries from db
    crawls = pd.read_sql('crawls', con=engine)

    for crawl in crawls.itertuples():
        client.containers.run(IMAGE_NAME, ['python', 'hb-testing.py', crawl.Filename, crawl.Category], shm_size="512M", remove=True, detach=True)

def main():

    args, parser = parse_args()

    if args.build:
        print("Starting docker build...")
        build_image()
        print("Build complete!")
    
    if args.runAll:
        print("Starting containers...")
        run_containers()
        print("Started!")

    if not args.build and not args.runAll:
        parser.print_help()


if __name__ == '__main__':
    main()
