"user strict"
/**
 * This is a simple interface for using two amazing nodejs libraries
 * (google-play-scraper and app-store) in Python.
 * It uses zerorpc to communicate using a Unix socket.
 *
 * If you find the server is stuck (that is python scrapper is stuck),
 * probably you have to remove the unix_socket /tmp/ipv-spyware.sock.
 *
 */
const process = require("process");
const zerorpc = require("zerorpc");
const gplay = require('google-play-scraper')
const appstore = require('app-store-scraper')
const fs = require('fs')

var LANG = 'it'
var COUNTRY = 'it'

var all_apis = {
    hello: function(name, reply) {
        reply(null, "Hello, " + name, false);
    }
};

function convert_to_ascii(query) {
    ['price', 'appId', 'country', 'lang', 'term'].forEach(
        function (key) {
            if (query[key]){
                query[key] = query[key].toString('ascii');
            }
        }
    );
    if(!query['cache'])
        query['cache'] = true;
}

function create_reply(name, api) {
    all_apis[name] = function (query, reply) {
        convert_to_ascii(query)
        console.log(name, query);
        api(query)
            .then((res) => {
                reply(null, res, false);
            })
            .catch((err) => { // if there is an error, just send something
                console.log(err);
                reply(null, [], false);
            });
    }
}

var ios_api_dict = {
    app: appstore.app,
    list: appstore.list,
    search: appstore.search,
    suggest: appstore.suggest,
    similar: appstore.similar,
    reviews: appstore.reviews,
    // permissions: appstore.permissions,
    // developer: appstore.developer     # appstore does not provide these two
}

var android_api_dict = {
    app: gplay.app,  // details about the app
    list: gplay.list,  // list the apps of a particular catagory
    suggest: gplay.suggest, // suggest similar apps
    similar: gplay.similar, // suggest similar query term
    search: gplay.search,  // search for apps given a query term
    reviews: gplay.reviews, // get reviews of an app given app-id
    permissions: gplay.permissions, // get permissions of an app given app-id
    developer: gplay.developer// other apps by the same developer given dev-id.
}

// update the all_apis dictionary for registering with zerorpc server
// in future.
switch (process.argv[2]) {
case "android":
    Object.keys(android_api_dict).forEach(
        key => create_reply('android_' + key, android_api_dict[key])
    );
    break;
case "ios":
    Object.keys(ios_api_dict).forEach(
        key => create_reply('ios_' + key, ios_api_dict[key])
    );
    break;
default:
    console.log("No store provided " + process.argv +". Should be");
    console.log("$ node server.js [android|ios]");
    process.exit(1);
}

console.log(all_apis);

var server = new zerorpc.Server(all_apis);
// server.bind("tcp://0.0.0.0:4242");
var sock_path = "/tmp/ipv-spyware_" + process.argv[2] + ".sock";
if (fs.existsSync(sock_path)) {
    throw("File already exists...kill running server and/or delete the sock file. " + sock_path);
}

function clean_die() {
    console.log('Dyingggg!!!');
    fs.unlinkSync(sock_path);
    console.log(fs.existsSync(sock_path));
    server.close();
    process.exit(0);
}

server.bind("ipc://" + sock_path);
server.on('close', clean_die);
server.on('error', clean_die);
process.on('SIGINT', clean_die);
process.on('SIGTERM', clean_die);
