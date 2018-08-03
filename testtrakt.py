import sys
import trakt
import logging

FORMAT = '%(asctime)-15s %(levelname)-7s %(name)-30s %(message)s'
#logging.basicConfig(format=FORMAT, level=logging.DEBUG)

# do auth: (will create a file ~/pytrakt.json)
# python -c "import trakt; trakt.init(store=True)"

import trakt.users
u = trakt.users.User('payne_xl')
#print (u.show_collection)
shows = []
for s in u.watchlist_shows:
    if type(s) is trakt.tv.TVShow:
        shows.append(s.title)

print (shows)
#print (u.get_list("FavShows"))
#print (u.get_list("Watchlist"))
        #trakt.init('payne_xl', client_id="06964c04c5c35ad9dbdfc361aad436eeb6b64cf758398e4563497e4de97eda2f", client_secret="7535f8ba9c563efd484341b0b118893a0ed59ea6cfbabaa65dd837bcef26fb55", store=True)

