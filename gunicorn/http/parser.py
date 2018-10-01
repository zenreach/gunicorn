# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from gunicorn.http.message import Request
from gunicorn.http.unreader import SocketUnreader, IterUnreader

glog = None


def log_no_die(base, *args):
    try:
        if args:
            glog.debug(base.format(args))
        else:
            glog.debug(base)

    except Exception:
        glog("BG: log_no_die died :( ")


class Parser(object):

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
            log_no_die("BG: parser: stopIteration top")
            raise StopIteration()

        # Discard any unread body of the previous message
        if self.mesg:
            data = self.mesg.body.read(8192)
            while data:
                data = self.mesg.body.read(8192)
            log_no_die("BG: parser.data: {}", data)

        # Parse the next request
        self.req_count += 1
        self.mesg = self.mesg_class(self.cfg, self.unreader, self.req_count)

        log_no_die("BG: parser.mesg: {}", self.mesg)

        if not self.mesg:
            log_no_die("BG: parser: stopIteration bottom")
            raise StopIteration()

        return self.mesg

    next = __next__


class RequestParser(Parser):

    mesg_class = Request
