# -*- coding: utf-8 -*-
# MIT License
#
# Copyright (c) 2017 Matthias Adamczyk
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Download all uploads from https://w1r3.net and other file hosters

Commands:
    /w1r3catcher list
        List all file hosters the script is currently aware of
    /w1r3catcher add <domain>
        Add a new file hoster
    /w1r3catcher del {<domain> | <position>}
        Delete a file hoster by name or by position in /w1r3catcher list
    /w1r3catcher logging {on | off}
        Enable/disable logging of matched urls to core buffer

Configuration:
    plugins.var.python.w1r3catcher.domains: List of filehoster domains to download from (default: "w1r3.net")
    plugins.var.python.w1r3catcher.logging: Log matched urls to core buffer (default: "on")

History:
2017-03-09: Matthias Adamczyk <mail@notmatti.me>
    version 0.1: Initial release

https://github.com/notmatti/w1r3catcher
"""
import sys
import os
import re
from datetime import datetime
try:
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, HTTPError, URLError

import_ok = True
try:
    import weechat
    from weechat import WEECHAT_RC_OK, prnt
except ImportError:
    print("Script must be run under weechat. https://weechat.org")
    import_ok = False


SCRIPT_NAME = "w1r3catcher"
SCRIPT_AUTHOR = "Matthias Adamczyk <mail@notmatti.me>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Download all uploads from https://w1r3.net and other file hosters"
SCRIPT_COMMAND = SCRIPT_NAME

SAVEPATH_NAME = SCRIPT_NAME
DELIMITER = "|@|"

savepath = ""
config_option = {}


def w1r3catcher_config_init():
    """Init configuration"""
    global savepath

    # Create a directory for our downloads
    weechat_home = weechat.info_get("weechat_dir", "")
    savepath = os.path.join(weechat_home, SAVEPATH_NAME)
    if not os.path.isdir(savepath):
        os.mkdir(savepath)

    settings = {
        "domains": ("w1r3.net", "List of filehoster domains to download from. Seperated by {}".format(DELIMITER)),
        "logging": ("on", "Log matched urls to core buffer")
    }

    for option, default_value in settings.items():
        if weechat.config_get_plugin(option) == "":
            weechat.config_set_plugin(option, default_value[0])
        weechat.config_set_desc_plugin(
            option, '{} (default: "{}")'.format(default_value[1], default_value[0]))


def parse_url(server, channel, nick, message):
    """Parse an IRC message for matching domains"""
    data = weechat.config_get_plugin("domains")
    patterns = data.split(DELIMITER)
    for pattern in patterns:
        if pattern == "":
            continue
        pattern = "((?:https?://)?" + pattern + "/[^ ]+)"
        result = re.findall(pattern, message)
        for url in result:
            # TODO Add verbose flag
            if logging_enabled():
                prnt("", "[{}] Downloading {} from {} on {} {}".format(
                    SCRIPT_COMMAND, url, nick, server, channel))
            download(server, channel, url)


def download(server, channel, url):
    """Download a file from given URL"""
    try:
        filename = "irc." + server + "." + channel + "." \
            + "{:%Y%m%d-%H:%M:%S}".format(datetime.now())
        filename = filename.replace("/", "_")
        if os.path.isfile(os.path.join(savepath, filename + "." + url.split(".")[-1])):
            count = 1
            while True:
                newfilename = filename + "-" + \
                    str(count) + "." + url.split(".")[-1]
                if not os.path.isfile(os.path.join(savepath, newfilename)):
                    filename = newfilename
                    break
                count += 1
        else:
            filename = filename + "." + url.split(".")[-1]

        r = urlopen(url)
        with open(os.path.join(savepath, filename), "w") as f:
            f.write(r.read())
        if logging_enabled():
            prnt("", "[{}] filename: {}".format(SCRIPT_COMMAND, filename))

    except HTTPError as err:
        prnt("", "[{}] Downloading {} failed with Error {}".format(
            SCRIPT_COMMAND, url, err.code))
    except URLError as err:
        prnt("", "[{}] Error opening {} - {}".format(SCRIPT_COMMAND, url, err.reason))
    except ValueError:
        download(server, channel, "http://{}".format(url))


def add_domain(url):
    """Add url to plugin section"""
    # Strip leading slash and http(s):// from url
    url = re.sub("https?://", "", url).split("/")[0]

    # Add url
    data = weechat.config_get_plugin("domains")
    domains = []
    found = False
    for entry in data.split(DELIMITER):
        if not entry:
            continue
        if entry == url:
            found = True
        domains.append(entry)

    if not found:
        domains.append(url)

    weechat.config_set_plugin("domains", DELIMITER.join(domains))
    weechat.prnt(
        "", "[{}] url {} successfully added".format(
            SCRIPT_COMMAND, url))


def del_domain(value):
    """Delete given url by list value or name"""
    data = weechat.config_get_plugin("domains").split(DELIMITER)
    try:
        # As a digit from list command
        value = int(value)
        domains = []
        url = ""
        try:
            if value - 1 < 0:
                raise IndexError
            url = data.pop(value - 1)
            for entry in data:
                if not entry:
                    continue
                domains.append(entry)
            weechat.config_set_plugin("domains", DELIMITER.join(domains))
            prnt("", "[{}] Successfully deleted {}".format(
                SCRIPT_COMMAND, url))
        except IndexError:
            prnt("", "[{}] Wrong index number".format(SCRIPT_COMMAND))
    except ValueError:
        try:
            # as a string
            data.remove(value)
            weechat.config_set_plugin("domains", DELIMITER.join(data))
            prnt("", "[{}] Successfully deleted {}".format(
                SCRIPT_COMMAND, value))
        except ValueError:
            prnt("", "[{}] Couldn't find {}".format(SCRIPT_COMMAND, value))


def list_domains(buffer):
    """List all domains the script is currently aware of"""
    data = weechat.config_get_plugin("domains").split(DELIMITER)
    count = 1
    if data[0] != "":
        for entry in data:
            prnt(buffer, "{}: {}".format(count, entry))
            count += 1
    else:
        prnt("", "[{}] No domains added so far".format(SCRIPT_COMMAND))


def logging_enabled():
    """Return True if logging is enabled"""
    return weechat.config_get_plugin("logging") == "on"


def print_message_cb(data, signal, signal_data):
    """Parse raw IRC messages and extract the network, channel and message text from the message"""
    server = signal.split(",")[0]
    message = weechat.info_get_hashtable(
        "irc_message_parse",
        {"message": signal_data})
    message_text = message["arguments"][message["arguments"].find(':') + 1:]
    parse_url(server, channel=message["channel"], nick=message[
              "nick"], message=message_text)
    return WEECHAT_RC_OK


def w1r3catcher_command_cb(data, buffer, args):
    """Parse and execute the given command"""
    list_args = args.split(" ")

    if list_args[0] not in ["add", "del", "list", "logging"]:
        prnt(buffer, "[{}] bad option while using /{} command, try '/help {}' for more info".format(
            SCRIPT_COMMAND, SCRIPT_COMMAND, SCRIPT_COMMAND))
        return WEECHAT_RC_OK

    elif list_args[0] == "add":
        if len(list_args) == 2:
            add_domain(list_args[1])
            return WEECHAT_RC_OK

    elif list_args[0] == "del":
        if len(list_args) == 2:
            del_domain(list_args[1])
            return WEECHAT_RC_OK

    elif list_args[0] == "list":
        list_domains(buffer)
        return WEECHAT_RC_OK

    elif list_args[0] == "logging":
        if list_args[1] == "on":
            weechat.config_set_option("logging", "on")
            return WEECHAT_RC_OK
        elif list_args[1] == "off":
            weechat.config_set_option("logging", "off")
            return WEECHAT_RC_OK

    weechat.command(buffer, "/help " + SCRIPT_COMMAND)
    return WEECHAT_RC_OK


if __name__ == '__main__' and import_ok and \
        weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                         SCRIPT_DESC, '', ''):
    w1r3catcher_config_init()

    weechat.hook_signal("*,irc_in2_privmsg", "print_message_cb", "")
    weechat.hook_command(
        SCRIPT_NAME,
        SCRIPT_DESC,
        "{ add $url | del { $url | $list_number } | list | logging {on | off}}",
        "  add    : add a URL $url\n"
        "  del    : delete $url\n"
        " list    : Return a nubered list of all domains\n"
        " logging : Enable/disable logging of matched urls to core buffer",
        "add|del|list|logging",
        "w1r3catcher_command_cb",
        ""
    )
