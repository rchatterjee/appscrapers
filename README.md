# appscrapers
A collection of scrapers for Android and iOS apps on different stores

# Scrapper scripts 
## For scrping search engines
```bash
$ python scraper.search_engines <language> <country> <query>
# Or, default language=US, country=EN
$ python scraper.search_engines <query>
# E.g.,
$ python scraper.search_engines "Amy I being tracked"
$ python scraper.search_engines bn bn "আমাকে কি track করা হচ্ছে"
```

<!---
```python
if __name__ == "__main__":
    import sys
    if len(sys.argv)>3:
        HL = sys.argv[1]
        CR = sys.argv[2]
        q = sys.argv[3]
        print(google_suggest(q))
    elif len(sys.argv) == 1:
        q = sys.argv[1]
        print(google_suggest(q))
    else:
        print("""
$ python scraper.search_engines <language> <country> <query>
# Or, default language=US, country=EN
$ python scraper.search_engines <query>
# E.g.,
$ python scraper.search_engines "Amy I being tracked"
$ python scraper.search_engines bn bn "আমাকে কি track করা হচ্ছে"
""")
```    
-->


## For scraping Play Store and iTune App store

The main calling script is [`pyscrapper.py`](pyscrapper.py).
Checkout `cron.sh` for how to run the scripts. You have to run from 
the top level directory of the project. 

### Required
* `node.js (version 10)` See how to install `node` and `npm` from https://nodejs.org/en/download/package-manager/
* `sqlite3`
* Python requirements are listed in `scraper/requirement.txt`, which can be installed
  with `pip` (`pip install -U -r requirements.txt`).
* Node requirements are listed in `scraper/package.json`

```bash
$ cd scraper/
$ pip install -r requirement.txt
$ npm i .  ## If no package.json run the following command
$ npm i process zerorpc google-play-scraper app-store-scraper fs
```


## How to run?  ##

This uses the nodejs module called
[`google-play-scraper`](https://github.com/facundoolano/google-play-scraper) and
[`app-store-scraper`](https://github.com/facundoolano/app-store-scraper).

I am too lazy to learn node.js, so created a node.js server using `zerorpc` and
use it to communicate from `python`.


```bash
$ python -m scraper.pyscrapper -h
usage: pyscrapper.py [-h]
                     [--appstore {android,ios,google-related,google-comp,bing}]
                     [--reviews] [--apps APPS [APPS ...]] [--appdetails]
                     [--crawl] [--test] [--qs] [--fresh] [--prod]
                     [--search SEARCH] [--similarapps]

A scraping tool to perform query snowballing, downloading metadata from Play
Store and iTuenes App store.

optional arguments:
  -h, --help            show this help message and exit
  --appstore {android,ios,google-related,google-comp,bing}
                        Which app store to target. options: android, ios
  --reviews             Download comments. Only valid if--download flag is
                        given
  --apps APPS [APPS ...]
                        List of appIds to download
  --appdetails          Action: download app(s).
  --crawl               Start crawling. Start fresh. Run it everyday at 10am
                        EST.
  --test                Run test
  --qs                  Perform query snowballing on the app store
  --fresh               Start the node server server.js so that we are not
                        hitting the same cache
  --prod                Stores in databse only if this is true
  --search SEARCH       Search apps with this query
  --similarapps         Get closure of apps of the given appIds in --apps
```

### To download details of apps
```bash
$ python -m scraper.pyscrapper --appdetails --apps com.dxco.pandavszombies --appstore android [--fresh]
```

`--apps` takes a list of apps as argument, so if you have only a few apps to download this is the easiest. If there are
many apps to download, put those in a file, say called `app-lists.txt` and run the same command replacing the appid(s) with
`@app-lists.txt` as follows

The downloaded app details goes to `data/apps_test.db`. 

```bash
$ python -m scraper.pyscrapper --appdetails --apps @app-lists.txt --appstore android [--fresh]
```

Adding a `--reviews` will download the reviews of those apps too. Number of reviews to download is controlled by `scraper/config.py` file 
`NUM_COMMENTS_TO_DOWNLOAD = 200 # Max 200 comments to download`



### Watch live scraping ###
`tail -f /tmp/jsserver.log` 
This command will continuously pull the file, keeps updating if anything changes
Note that node.js actually does the scraping. Python is used to control scraping and store data in sqlite.

### Crawling ###

```bash
python -m scraper.pyscrapper --crawl --prod --appstore android &>> /tmp/pyscrapper.log && fg
```

This is the actual command:
```bash
python -m scraper.pyscrapper --crawl --prod --appstore android 
```

After the `&>>` (redirect):
	`&>> /tmp/pyscrapper.log && fg`
redirects both the standard output and the standard error, stdout and stderr, into the file `/tmp/pyscrapper.log`. 

`&& fg` brings the command into the foreground, because it would otherwise run in the background. 
Now, both will be run in the same shell together.
The `fg` is not necessary if you're running only one command.  
Thus, if you're only running the android script, you can just use:
```bash
python -m scraper.pyscrapper --crawl --prod --appstore android &>> /tmp/pyscrapper.log &
```
### Set Language and Country ###

If you want to set the `LANG` and `COUNTRY`, use `APP_LANG` and `APP_COUNTRY` bash environment 
variables. The following command will execute for Italian in Italy. 

```bash
$ APP_LANG=it APP_COUNTRY=it python -m scraper.pyscrapper --crawl --prod --appstore android &>> /tmp/pyscrapper.log &
```



### Read Data ###
In `./data` folder, find data in `crawled_apps.db` `sqlite3`
crawled_`apps.db`. **Note**: Data is not stored in `data/apps_test.db`. Data
will be stored in `data/crawled_apps.db`. 

Once you crawl, you can get list of apps you want to use to train a model. 
All data is stored in sqlite. 
Dump from sqlite to .csv, put into Google sheet, level out things, then download .csv file. 
For training, just care about appid and relevance level from data. appid is necessary, is the way to key.





