#!/bin/bash
DIR=$(dirname "$(cd "$( dirname "${BASH_SOURCE[0]}")" && pwd)")
cd $DIR
sqlite3 -header -csv ./data/crawled_apps.db 'select appId, count(*) c from android_reviews group by appId' > t_done
python -m scraper.pyscrapper --apps t --reviews --prod
