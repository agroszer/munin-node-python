#! /usr/bin/python
# $Id$

'''
The MIT License

Copyright (c) 2010 Chris Holcombe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

    Munin node will assumes that all files in a
    plugin directory are plugins and will try to
    gain configuration information from each one.

    The usual munin plugin command apply when creating
    the plugin.  If a special command needs to be run
    for the plugin to work ie Windows not understanding
    shell scripts you can specify that in the config file.

    Config file format:

    # = comment line
    [<plugin name>]
    user <user> (not used)
    group <group> (not used)
    command <command>
    native <yes|no>
    env.<variable> <value> (not used)
    host_name <host-name> (not used)
    timeout <seconds> (not used)

    See http://munin.projects.linpro.no/wiki/plugin-conf.d for more details

'''

__author__="Chris Holcombe"
__date__ ="$Feb 24, 2010 11:35:31 AM$"
VERSION = "0.1"

import sys
import os.path
import imp
import logging
import logging.handlers
import time

import SocketServer
import hashlib
import optparse
import socket

LOGGER = logging.Logger('munin-node')

if sys.platform == "win32":
    import os
    import msvcrt
    LOGGER.info("Setting windows binary write mode")
    try:
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except:
        pass

hostname = socket.gethostname()
full_hostname = socket.getfqdn(hostname)

modules = {}


def load_module(name, config, plugin_dir):
    plugin = plugin_dir + "/" + name
    if not os.path.isfile(plugin):
        LOGGER.error("Could not locate plugin: %s - ignoring ...", plugin)
        return None

    try:
        if config["native"] == "yes":
            fin = open(plugin, "rb")
            m = hashlib.md5()
            m.update(plugin)
            return imp.load_source(m.hexdigest(), plugin, fin)

        # must be an external plugin
        # need to know which command to run
        if config.has_key("command"):
            fin = open("external_plugin.py", "rb")
            m = hashlib.md5()
            m.update(plugin)
            mod = imp.load_source(m.hexdigest(), plugin, fin)
            mod.command = config["command"]
            return mod

        LOGGER.error("Could not find command parameter for external " \
                     "plugin. Please fix config file")
        LOGGER.error("Ignoring plugin: %s", plugin)
        return None
    finally:
        try:
            fin.close()
        except:
            pass


def get_module_data(name):
    try:
        return modules[name].get_data()
    except KeyError:
        LOGGER.error("No such module: %s", name)

    return None


def get_module_config(name):
    try:
        return modules[name].get_config()
    except KeyError:
        LOGGER.error("No such module: %s", name)

    return None


def parse_config_file(cfile):
    # store config information in dict
    config = {}

    for line in cfile:
        line = line.strip()

        # skip comment lines and blank lines
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.startswith("["):
            if not line.endswith("]"):
                LOGGER.error("The config files contains an invalid " \
                             "section header (no closing bracket)")
            else:
                name = line[1:-1]
                config[name] = {}
        else:
            try:
                k, v = line.split(" ", 1)
            except ValueError:
                LOGGER.error("The config file contains an invalid " \
                             "parameter without value")
                k = line
                v = ""

            try:
                config[name][k] = v
            except TypeError:
                LOGGER.error("The config file contains invalid chars" \
                             "Line: " + name + " " + k + " " + v)
    return config


class MuninHandler(SocketServer.StreamRequestHandler):
    """
    Munin server implementation

    Possible commands:
    list, nodes, config, fetch, version or quit
    """

    allow_reuse_address = True
    timeout = 60

    def write(self, data):
        try:
            self.wfile.write(data)
            self.wfile.flush()
        except Exception:
            LOGGER.exception("socket write failed %s")
            LOGGER.debug(data)

    def handle(self):
        self.write("# munin node at %s\n" % full_hostname)

        try:
            while True:
                line = self.rfile.readline().strip()
                try:
                    cmd, args = line.split(" ", 1)
                except ValueError:
                    cmd = line
                    args = ""

                LOGGER.info("Command %s", line)

                if not cmd or cmd == "quit":
                    break

                if cmd == "list":
                    # List all plugins that are available
                    self.write(" ".join(modules.keys()) + "\n")
                elif cmd == "nodes":
                    # We just support this host
                    self.write("%s\n.\n" % full_hostname)
                elif cmd == "config":
                    # display the config information of the plugin
                    if not args:
                        self.write("# Unknown service\n.\n")
                    else:
                        config = get_module_config(args)
                        if config is None:
                            self.write("# Unknown service\n.\n")
                        else:
                            self.write("\n".join(config) + "\n.\n")
                elif cmd == "fetch":
                    # display the data information as returned by the plugin
                    if not args:
                        self.write("# Unknown service\n.\n")
                    else:
                        data = get_module_data(args)
                        if data is None:
                            self.write("# Unknown service\n.\n")
                        else:
                            self.write("\n".join(data) + "\n.\n")
                elif cmd == "version":
                    # display the server version
                    self.write("munin node on %s version: %s\n" %
                               (full_hostname, VERSION))
                else:
                    self.write("# Unknown command. Try list, nodes, " \
                               "config, fetch, version or quit\n")
        except Exception:
            self.write("ERROR")
            LOGGER.exception("exception")
        LOGGER.info("End of connection")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)

    # Set up logger handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

    handler = logging.handlers.RotatingFileHandler(
        os.path.join(here, 'munin-node.log'),
        maxBytes=10*1024*1024, backupCount=10)
    #handler = logging.FileHandler(os.path.join(here, 'munin-node.log'))
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

    LOGGER.setLevel(logging.INFO)

    parser = optparse.OptionParser(usage="usage: %prog [options] arg",
                                   version="%prog "+VERSION)
    parser.add_option("-c", dest="config", help="config file",
                      default='munin_node.conf')
    parser.add_option("-p", dest="pdir", help="plugin directory")

    opts, args = parser.parse_args()

    plugin_dir = opts.pdir
    config_file = opts.config

    if not config_file:
        LOGGER.error("Please specify the config file with the -c option")
        parser.print_help()
        sys.exit(1)

    if not plugin_dir:
        plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')

    if not os.path.isdir(plugin_dir):
        LOGGER.error("Can not find plugin directory: %s ", plugin_dir)
        sys.exit(1)

    config = parse_config_file(file(config_file, "r"))

    LOGGER.info("Loading modules ...")
    for k, v in config.items():
        mod = load_module(k, v, plugin_dir)
        if not mod:
            LOGGER.error("Failed to load plugin: %s", k)
        else:
            nname = mod.get_name()
            modules[nname] = mod
            LOGGER.info("Plugin %s (%s) loaded" % (nname, k))

    for fname in os.listdir(plugin_dir):
        name, ext = os.path.splitext(fname)
        if ext == '.exe':
            fullfname = os.path.abspath(os.path.join(plugin_dir, fname))
            conf = {}
            conf['native'] = False
            conf['command'] = fullfname
            mod = load_module(fname, conf, plugin_dir)
            if not mod:
                LOGGER.error("Failed to load plugin: %s", fname)
            else:
                nname = mod.get_name()
                modules[nname] = mod
                LOGGER.info("Plugin %s (%s) loaded" % (nname, fname))

    try:
        # Munin default port is 4949
        host, port = "0.0.0.0", 4949

        socket.setdefaulttimeout(60)
        server = SocketServer.ThreadingTCPServer((host, port), MuninHandler)

        LOGGER.info("serving munin ...")
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("KeyboardInterrupt received, terminating ...")

if __name__ == "__main__":
    main()
