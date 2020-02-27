CREATE TABLE ios_terms (
	term VARCHAR(255) NOT NULL, terms TEXT, apps TEXT, time TEXT, 
	PRIMARY KEY (term)
);
CREATE TABLE ios_reviews (
	id VARCHAR(255) NOT NULL, date TEXT, "userName" TEXT, "userUrl" TEXT, version TEXT, score INTEGER, title TEXT, text TEXT, url TEXT, "appId" TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE android_reviews (
	id VARCHAR(255) NOT NULL, "userName" TEXT, "userImage" TEXT, date TEXT, url TEXT, score INTEGER, title TEXT, text TEXT, "replyDate" TEXT, "replyText" TEXT, "appId" TEXT, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_ios_terms_2a4c3b84009d0ba2 ON ios_terms (term);
CREATE INDEX ix_ios_reviews_25e70e52969f978b ON ios_reviews ("appId");
CREATE INDEX ix_android_reviews_25e70e52969f978b ON android_reviews ("appId");
CREATE TABLE "android_apps" (
	id INTEGER NOT NULL, "appId" TEXT, version TEXT, "contentRating" TEXT, "offersIAP" BOOLEAN, "descriptionHTML" TEXT, video TEXT, "androidVersionText" TEXT, size TEXT, title TEXT, screenshots TEXT, description TEXT, "maxInstalls" INTEGER, comments TEXT, score FLOAT, "developerEmail" TEXT, "familyGenre" TEXT, "genreId" TEXT, developer TEXT, "androidVersion" TEXT, "recentChanges" TEXT, updated TEXT, "developerWebsite" TEXT, "adSupported" BOOLEAN, price TEXT, free BOOLEAN, histogram TEXT, "familyGenreId" TEXT, genre TEXT, icon TEXT, url TEXT, similar TEXT, preregister BOOLEAN, summary TEXT, reviews TEXT, time TEXT, permissions TEXT, "minInstalls" INTEGER, relevant TEXT, "developerId" TEXT, discontinued TEXT, anti_spy_relevant VARCHAR(2), 
	PRIMARY KEY (id)
);
CREATE TABLE "ios_apps" (
	id INTEGER NOT NULL, "appId" TEXT, title TEXT, url TEXT, description TEXT, icon TEXT, genres TEXT, "genreIds" TEXT, "primaryGenre" TEXT, "primaryGenreId" INTEGER, "contentRating" TEXT, languages TEXT, size TEXT, "requiredOsVersion" TEXT, released TEXT, updated TEXT, "releaseNotes" TEXT, version TEXT, price FLOAT, currency TEXT, free BOOLEAN, "developerId" INTEGER, developer TEXT, "developerUrl" TEXT, "developerWebsite" TEXT, score TEXT, reviews TEXT, "currentVersionScore" TEXT, "currentVersionReviews" TEXT, screenshots TEXT, "ipadScreenshots" TEXT, "appletvScreenshots" TEXT, "supportedDevices" TEXT, similar TEXT, permissions TEXT, time TEXT, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_android_apps_25e70e52969f978b ON android_apps ("appId");
CREATE TABLE android_desc (
	id INTEGER NOT NULL, "appId" TEXT, time TEXT, description TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE android_terms_old(
  term TEXT,
  terms TEXT,
  apps TEXT,
  time TEXT
);
CREATE TABLE android_terms (
	term VARCHAR(255) NOT NULL, terms TEXT, apps TEXT, time TEXT, 
	PRIMARY KEY (term)
);
CREATE INDEX ix_android_terms_2a4c3b84009d0ba2 ON android_terms (term);
CREATE TABLE configs (
	id INTEGER NOT NULL, "key" TEXT, value TEXT, 
	PRIMARY KEY (id)
);
