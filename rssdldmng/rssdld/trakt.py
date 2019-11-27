import re
import logging
import time

log = logging.getLogger(__name__)
logging.getLogger("trakt.core").setLevel(logging.WARNING)


# login to trakt first
# python -c "import trakt; trakt.init(store=True)"

class Trakt():

    def __init__(self, config):
        assert(config)
        assert('username' in config)

        self.username = config['username']

        self.client_id = config.get('clientid', None)
        self.client_secret = config.get('clientsecret', None)
        self.report_progress = config.get('reportprogress', False)
        self.device_code = None
        self.user_code = None
        self.interval = 0
        self.auth_start = None
        self.auth_check = None
        self.verification_url = None
        self.authenticated = None
        self.cancel = False

        try:
            import trakt.users
            trakt.users.User(self.username)
            self.authenticated = True
        except:
            self.authenticated = False
            pass

    def is_authenticated(self):
        return self.authenticated

    def get_user_code(self):
        if not self.authenticated:
            return self.user_code
        return None

    def authenticate(self, client_id = None, client_secret = None):
        if client_id:
            self.client_id = client_id
        if client_secret:
            self.client_secret = client_secret

        self._authenticate()

    def cancel_authentication(self):
        self.cancel = True

    def _authenticate(self):
        if self.is_authenticated():
            return

        log.info("STARTING TRAKT AUTHENTICATION")
        assert(self.client_id and self.client_secret), "invalid trakt id or secret"
        if self.start_authentication():
            log.info("USER CODE: {}. URL: {}".format(self.user_code, self.verification_url))
            log.info("WILL BLOCK UNTILL AUTH IS SUCCESSFULL")
            while not self.check_authentication():
                time.sleep(1)
            log.info("TRAKT AUTHENTICATION SUCCESSFULL")
        else:
            raise Exception("FAILED to start Trakt authentication")

    def start_authentication(self):
        import trakt.core
        try:
            #trakt.core.device_auth(client_id=self.clientid, client_secret=clientsecret, store=True)
            response = trakt.core.get_device_code(client_id=self.client_id,
                                                  client_secret=self.client_secret)
            self.authenticated = False
            self.device_code = response.get('device_code')
            self.user_code = response.get('user_code')
            self.interval = response.get('interval')
            self.auth_start = response.get('requested')
            self.verification_url = response.get('verification_url')
            return True
        except Exception as e:
            log.warn('cannot start trakt authentication [{}]'.format(e))
            return False

    def check_authentication(self):
        error_messages = {
            404: 'Invalid device_code',
            409: 'You already approved this code',
            410: 'The tokens have expired, restart the process',
            418: 'You explicitly denied this code',
        }

        if self.cancel:
            raise Exception("Trakt authentication canceled")

        if not self.auth_start:
            raise Exception("Trakt authentication not started")

        if not self.auth_check:
            self.auth_check = self.auth_start

        if self.auth_check + self.interval > time.time():
            #log.debug("interval constraint not reached [{} + {} < {}]".format(self.auth_check, self.interval, time.time()))
            return None

        self.auth_check = time.time()
        import trakt.core
        try:
            response = trakt.core.get_device_token(self.device_code, self.client_id, self.client_secret, store=True)

            if response.status_code == 200:
                log.info("Trakt authentication successfull")
                self.authenticated = True
                self.auth_start = None
                self.auth_check = None
                self.inteval = 0
                self.device_code = None
                self.user_code = None
                return response
            elif response.status_code == 429:  # slow down
                self.interval *= 2
                log.info("slow down checking authentication [interval {}]".format(self.interval))
                return None
            elif response.status_code != 400:  # not pending
                log.error(error_messages.get(response.status_code, response.reason))
                raise Exception(error_messages.get(response.status_code, response.reason))
                return None

        except Exception as e:
            log.warn('cannot authenticate to trakt [{}]'.format(e))

        return None

    #@_authenticate
    def getTvShows(self, list):
        if not self.is_authenticated():
            log.warn('Not authenticated to Trakt')
            return []

        shows = []
        import trakt.users
        try:
            if list and list.lower() != 'watchlist':
                slist = trakt.users.User(self.username).get_list(list)
            else:
                slist = trakt.users.User(self.username).watchlist_shows
            for s in slist:
                if type(s) is trakt.tv.TVShow:
                    shows.append(re.sub('[\\/:"*?<>|]+', '', s.title))
        except trakt.errors.TraktException as te:
            log.warn('connect to trakt exception [{te}]')
        except Exception as e:
            log.warn('cannot get trakt list {list} for user {self.username} [{e}]')
            shows = []
        return shows

    #@_authenticate
    def setCollected(self, showname, season, episode):
        if not self.is_authenticated():
            log.warn('Not authenticated to Trakt')
            return []

        if not self.report_progress:
            return True
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.add_to_collection()
        except (trakt.errors.NotFoundException, Exception) as e:
            print('WRN: cannot set collected {:s} S{:02d}E{:02d} [{:}]'.format(showname, season, episode, e))
            return False
        return True

    #@_authenticate
    def setWatched(self, showname, season, episode):
        if not self.is_authenticated():
            log.warn('Not authenticated to Trakt')
            return []

        if not self.report_progress:
            return True
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.mark_as_seen()
        except (trakt.errors.NotFoundException, Exception) as e:
            print('WRN: cannot set watched {:s} S{:02d}E{:02d} [{:}]'.format(showname, season, episode, e))
            return False
        return True
