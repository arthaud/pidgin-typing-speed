#!/usr/bin/env python
import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop
import time
import re

DEBUG = False

# use glib loop as default loop
DBusGMainLoop(set_as_default=True)

# dbus session
bus = dbus.SessionBus()


def debug(message):
    if DEBUG:
        print(message)


class User:
    def __init__(self, name):
        self.name = name
        self.timer = None
        self.wrong = False # in case he stops typing without sending message

        self.sum_elapsed = 0.0
        self.sum_words = 0

    def start_typing(self):
        if self.timer: # should not happen
            self.wrong = True

        self.timer = time.time()

    def stop_typing(self):
        if self.timer:
            self.wrong = True

        self.timer = None

    def received_message(self, message):
        if self.timer and not self.wrong:
            elapsed = time.time() - self.timer

            if elapsed < 0.4 or elapsed > 20.0 or len(message) == 0: # seems strange, doesn't count
                debug('STRANGE: %s: "%s" in %f secs' % (self.name, message, elapsed))
            else:
                self.sum_elapsed += elapsed
                self.sum_words += len(re.findall(r'\w+', message))
                debug('OK: %s: "%s" in %f secs' % (self.name, message, elapsed))
                print('%s: %f words/minute' % (self.name, self.sum_words / self.sum_elapsed * 60.0))
        else:
            debug('WRONG: %s: "%s"' % (self.name, message))

        self.timer = None
        self.wrong = False


users = {}


def buddy_typing(account, username):
    if username not in users:
        users[username] = User(username)

    users[username].start_typing()


def buddy_typing_stopped(account, username):
    if username not in users:
        users[username] = User(username)

    users[username].stop_typing()


def received_message(account, username, message, conversation, flags):
    if username not in users:
        users[username] = User(username)

    users[username].received_message(message)


bus.add_signal_receiver(buddy_typing,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="BuddyTyping")

bus.add_signal_receiver(buddy_typing_stopped,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="BuddyTypingStopped")

bus.add_signal_receiver(received_message,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="ReceivedImMsg")

# start main loop
loop = gobject.MainLoop()
loop.run()
