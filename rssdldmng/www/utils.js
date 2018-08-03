
class Log {
  constructor(DEBUG) {
    if (DEBUG) {
      this.debugLog = console.log.bind(window.console, 'DBG: ');
      this.errorLog = console.log.bind(window.console, 'ERR: ');
    }
    else {
      this.debugLog = function () { };
      this.errorLog = function () { };
    }
  }
  d(msg) {
    this.debugLog(msg);
  }
  e(msg) {
    this.errorLog(msg);
  }
};
var log = new Log(true);

class RssdldmngService {
    constructor(props) {
        this.props = props;
        this.shows = [];
    }
    get(url, onResponseCb = null) {
        $.ajax({
            url: 'http://' + this.props.host + ':' + this.props.port + '/api' + url,
            type: 'GET',
            success: function(response) { 
                if (onResponseCb && typeof onResponseCb == "function")
                    onResponseCb(response);
            }
        });
    }
    put(url, data = null) {
        $.ajax({
            url: 'http://' + this.props.host + ':' + this.props.port + '/api' + url,
            type: 'PUT',
            data: JSON.stringify(data), // or $('#myform').serializeArray()
            success: function() { log.d('PUT completed'); }
        });
    }

};

class KodiWSService {
  constructor(props) {
    this.props = props;
    var kodi_ws_url = 'ws://' + props.host + ':' + props.port;
    var that = this;
    log.d('init KodiWSService [connecting to: ' + kodi_ws_url + ']');

    this.ws = new WebSocket(kodi_ws_url);
    
    this.ws.onopen = function () {
      log.d('Connected to Kodi Web Socket');
    };

    this.ws.onerror = function () {
      log.d('Socket error');
        that.showNotificationError('Socket error');
    };
    
    this.ws.onclose = function (event) {
      log.d('Closing socket [' + event.code + ']');
    };
  }

  waitForConnection (callback, attempt) {
    var service = this;
    setTimeout(function () {
      if (service.ws.readyState !== WebSocket.OPEN) {
        if (attempt > 0 && service.ws.readyState != WebSocket.CLOSED) {
          log.d('Wait for connection...');
          service.waitForConnection(callback, attempt - 1);
        } else {
          log.e('Could not connect to Kodi!');
          if (service.onerror && typeof service.onerror == "function")
            service.onerror('Could not connect to Kodi!');
        }
      } else {
        callback(service);
      }
    }, this.props.timeout * 1000);
  }

  send (method, params, onResponseCb = null) {
    this.waitForConnection(function (service) {
      var id = Math.floor((Math.random() * 100) + 1);
      log.d('send method:' + method + ', params: ' + JSON.stringify(params));
      service.ws.send(JSON.stringify({ jsonrpc: '2.0', id: id, method: method, params: params }));
      service.ws.onmessage = function (message) {
        //log.d(message.data);
        var response = JSON.parse(message.data);
        //log.d('response: ' + message.data); 
        if (response.id === id) {
          if (response.error !== undefined) {
            var error = response.error;
            log.d(method + ' : ' + error.message);
          }
          if (service.onmessage && typeof service.onmessage == "function")
            service.onmessage(response.result);
          if (onResponseCb && typeof onResponseCb == "function")
             onResponseCb(response.result);
        }
      };
    }, 10);
  }
}