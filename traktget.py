import sys, argparse, json
import trakt
import logging

# do auth: (will create a file ~/pytrakt.json)
# get info from https://trakt.tv/ -> Settings -> Your API Apps
# python -c "import trakt; trakt.init(store=True)"

from rssdldmng.const import (
    __version__,
)

def get_arguments():
    parser = argparse.ArgumentParser(
        description="RSS Downloader - Trakt utility")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-l', '--login', action='store_true', default=False, help='Login to trakt')
    parser.add_argument('-u', '--user', metavar='username', default='', help='Trakt username')
    parser.add_argument('--list', metavar='list', default='', help='Get specified list from trakt (default is watchlist)')

    arguments = parser.parse_args()
    return arguments

def get_trakt_tvlist(username, listname):
    shows = []
    import trakt.users
    from trakt.errors import NotFoundException
    try:
        if listname and listname.lower() != 'watchlist':
            slist = trakt.users.User(username).get_list(listname)
        else:
            slist = trakt.users.User(username).watchlist_shows
    except NotFoundException:
        print ('list {0} for user {1} not found'.format(listname, username))
        return []
    for s in slist:
        if type(s) is trakt.tv.TVShow:
            shows.append(s.title)
    return shows


def main():

    args = get_arguments()

    if not args.user:
        print ('No username provided')
        sys.exit(1)

    if args.login:
        import trakt
        trakt.init(store=True)

    shows = get_trakt_tvlist(args.user, args.list)
    if len(shows) > 0:
        print ('Trakt watchlist ({0} items):'.format(len(shows)))
        print (json.dumps(shows, sort_keys=True, indent=4))

if __name__ == "__main__":
    sys.exit(main())