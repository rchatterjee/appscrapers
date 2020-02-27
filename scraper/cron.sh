#!/bin/bash
DIR="$(cd "$( dirname "${BASH_SOURCE[0]}")" && pwd)"
cd $(dirname $DIR)
pwd
dropbox stop
python -m scraper.pyscrapper --crawl --prod --appstore ios &>> /tmp/pyscrapper.log &
python -m scraper.pyscrapper --crawl --prod --appstore android &>> /tmp/pyscrapper.log && fg
dropbox start
    
