# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from gunicorn.http.message import Request
from gunicorn.http.unreader import SocketUnreader, IterUnreader


class Parser(object):
    glog = None
    mesg_class = None

    def __init__(self, cfg, source):
        self.cfg = cfg
        if hasattr(source, "recv"):
            self.unreader = SocketUnreader(source)
        else:
            self.unreader = IterUnreader(source)
        self.mesg = None

        # request counter (for keepalive connetions)
        self.req_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        # Stop if HTTP dictates a stop.
        if self.mesg and self.mesg.should_close():
            self.glog.debug("BG: parser: stopIteration top")
            raise StopIteration()

        # Discard any unread body of the previous message
        if self.mesg:
            self.glog.debug("BG:  parser: have mesg, reading data for {}".format(self.mesg.path))
            data = self.mesg.body.read(8192)
            while data:
                data = self.mesg.body.read(8192)
            try:
                self.glog.debug("BG: parser: discarded data: {}".format(data))
            except Exception:
                pass
        else:
            self.glog.debug("BG: parser: no mesg")

        # Parse the next request
        self.req_count += 1
        self.mesg = self.mesg_class(self.cfg, self.unreader, self.req_count)

        if not self.mesg:
            self.glog.debug("BG:  parser: stop iteration bottom")
            raise StopIteration()

        self.glog.debug("BG: parser: returning mesg = {}".format(self.mesg))
        return self.mesg

    next = __next__


class RequestParser(Parser):

    mesg_class = Request
