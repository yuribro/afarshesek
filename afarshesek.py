# coding=utf-8

import httplib
import urllib

import datetime
import json

from private import GAPI_KEY, LOCATION

import bottle

###########

ARTISTS = []

###########

GOOGLE_CAL_NAME = "afarkeseth@gmail.com"

###########

######################
# Google Calandar 
######################

def format_time(d):
    return d.isoformat().split('.')[0] + "z"

def get_show_list(days=30):
    params = {}

    now = datetime.datetime.now()
    params["timeMin"] = format_time(now)
    params["timeMax"] = format_time(now + datetime.timedelta(days=days))
    params["key"] = GAPI_KEY

    con = httplib.HTTPSConnection("www.googleapis.com")
    url = "/calendar/v3/calendars/%s/events?%s" % (GOOGLE_CAL_NAME, urllib.urlencode(params))
    con.request("GET", url)
    res = con.getresponse()
    
    if (res.status != 200):
        print "Failed querying google: %d %s" % (res.status, res.reason)
        return

    raw_data = res.read()
    data = json.loads(raw_data)

    shows = []
    
    for event in data["items"]:
        show = {}
        try:
            show["loc"] = event["location"]
            show["name"] = event["summary"]
            onlydate, tz = event["start"]["dateTime"].split("+")
            show["time"] = datetime.datetime.strptime(onlydate, "%Y-%m-%dT%H:%M:%S")  # 2013-10-21T23:00:00+03:00
            show["tz"] = tz

            shows.append(show)

        except KeyError:
            print "bad event: ", repr(event)
    
    return shows

def filter_by_artist(s):
    for art in ARTISTS:
        if art in s["name"]:
            print "match:", art, " ~ ", s["name"]
            return True

    return False

def filter_by_location(s):
    return True

def print_show(s):
    print "ARTIST = ", s["name"]
    print "WHERE: ", s["loc"]
    print "WHEN: ", s["time"]
    print

def dump_show_html(s):
    return u'''
    <br />
    <p>
    אומן: %(name)s     <br /> 
    מקום: %(loc)s    <br /> 
    זמן: %(time)s    <br /> 
    </p>
    <br /> 
    <br />
    ''' % s
    
def get_filtered_show_list(days=30):
    shows = get_show_list(days=days)
    shows = filter(filter_by_artist, shows)
    shows = filter(filter_by_location, shows)
    return u'\n'.join(map(dump_show_html, shows))


######################
# Web Interface 
######################


@bottle.get('/') 
def root_page():
    return bottle.static_file("query.html", root="html/")

@bottle.route('/css/<filename>')
def serve_css(filename):
    return bottle.static_file(filename, root="css/")
        

@bottle.post('/search') 
def do_search():
    try:
        days = int(bottle.request.forms.get('days'))
    except ValueError:
        days = 14

    names = bottle.request.forms.get('names').split('\n')
    names = map(lambda x: x.strip(), names)
    names = map(lambda x: x.decode("utf-8"), names)

    global ARTISTS
    ARTISTS = names[:]

    page = u'''
    <div dir="rtl">
    <h2> האמנים שנבחרו: </h2> <br /> 
    <ul>
    '''

    for art in ARTISTS:
        page += u"<li> %s </li> " % (art, )
    
    page += u"</ul>"

    page += u"<h2> הופעות מתאימות: </h2>"

    page += get_filtered_show_list(days=days)
    page += u"</div>"

    return page




######################
# Main
######################

def main():
    bottle.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == "__main__":
    main()
