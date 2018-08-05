import sys, os, time, threading
from threading import Thread

class ServiceThread(Thread):

    def __init__(self, service=None):
        self.__is_stopped = threading.Event()
        self.__stop_request = False

        self.service = service
        if "serve_forever" in dir(service):
            Thread.__init__(self, target=self.service.serve_forever)
        else:
            Thread.__init__(self, target=self.serve_forever)
        self.daemon = True


    def is_stopped(self):
        return self.__is_stopped.is_set()

    def start(self):
        Thread.start(self)

    def stop(self):
        self.__stop_request = True
        self.__is_stopped.wait()
        Thread.join(self)

    def serve_starting(self):
        raise NotImplementedError("Please Implement this method")

    def serve(self):
        raise NotImplementedError("Please Implement this method")

    def serve_stopped(self):
        raise NotImplementedError("Please Implement this method")

    def serve_forever(self, poll_interval=0.5):
        self.__is_stopped.clear()
        self.serve_starting()
        try:
            while not self.__stop_request:
                self.serve()
                time.sleep(poll_interval)
        finally:
            self.__stop_request = False
            self.__is_stopped.set()
            self.serve_stopped()
