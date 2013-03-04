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

import SocketServer
import hashlib
import optparse
import socket
import traceback

debug = 1

if debug:
    def DBG(*args):
        for w in args[:-1]:
            print w,
        print args[-1]
else:
    def DBG(*args):
        pass

if sys.platform == "win32":
    import os
    import msvcrt
    DBG("Setting windows binary write mode")
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

hostname = socket.gethostname()
full_hostname = socket.getfqdn(hostname)

modules = {}

def load_module(name, config, plugin_dir):
    plugin = plugin_dir + "/" + name
    if not os.path.isfile(plugin):
        print >>sys.stderr, "Could not locate plugin: %s - ignoring ..." % plugin
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
            fin = open(plugin_dir + "/external_plugin.py", "rb")
            m = hashlib.md5()
            m.update(plugin)
            mod = imp.load_source(m.hexdigest(), plugin, fin)
            mod.command = config["command"]
            return ex_mod

        print >>sys.stderr, "Could not find command parameter for external " \
                            "plugin. Please fix config file"
        print >>sys.stderr, "Ignoring plugin: %s" % plugin
        return None
    finally:
        try:
            fin.close()
        except:
            pass
#    except:
#        traceback.print_exc(file = sys.stderr)
#        raise

def get_module_data(name):
    try:
        return modules[name].get_data()
    except KeyError:
        print >>sys.stderr, "No such module:", name

    return None

def get_module_config(name):
    try:
        return modules[name].get_config()
    except KeyError:
        print >>sys.stderr, "No such module:", name

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
                print >>sys.stderr, "The config files contains an invalid " \
                                    "section header (no closing bracket)"
            else:
                name = line[1:-1]
                config[name] = {}
        else:
            try:
                k, v = line.split(" ", 1)
            except ValueError:
                print >>sys.stderr, "The config file contains an invalid " \
                                    "parameter without value"
                k = line
                v = ""

            try:
                config[name][k] = v
            except TypeError:
                print >>sys.stderr, "The config file contains invalid chars"
                print >>sys.stderr, "Line: " + name + " " + k + " " + v

    return config

class MuninHandler(SocketServer.StreamRequestHandler):
    """
    Munin server implementation

    Possible commands:
    list, nodes, config, fetch, version or quit
    """

    allow_reuse_address = True

    def handle(self):
        self.wfile.write("# munin node at %s\n" % full_hostname)

        while True:
            line = self.rfile.readline().strip()
            try:
                cmd, args = line.split(" ", 1)
            except ValueError:
                cmd = line
                args = ""

            DBG("Command %s" % line)

            if not cmd or cmd == "quit":
                break

            if cmd == "list":
                # List all plugins that are available
                self.wfile.write(" ".join(modules.keys()) + "\n")
            elif cmd == "nodes":
                # We just support this host
                self.wfile.write("%s\n.\n" % full_hostname)
            elif cmd == "config":
                # display the config information of the plugin
                if not args:
                    self.wfile.write("# Unknown service\n.\n" )
                else:
                    config = get_module_config(args)
                    if config is None:
                        self.wfile.write("# Unknown service\n.\n")
                    else:
                        self.wfile.write("\n".join(config) + "\n.\n")
            elif cmd == "fetch":
                # display the data information as returned by the plugin
                if not args:
                    self.wfile.write("# Unknown service\n.\n")
                else:
                    data = get_module_data(args)
                    if data is None:
                        self.wfile.write("# Unknown service\n.\n")
                    else:
                        self.wfile.write("\n".join(data) + "\n.\n")
            elif cmd == "version":
                # display the server version
                self.wfile.write("munin node on %s version: %s\n" %
                                 (full_hostname, VERSION))
            else:
                self.wfile.write("# Unknown command. Try list, nodes, " \
                                 "config, fetch, version or quit\n")


def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] arg",
                                   version="%prog "+VERSION)
    parser.add_option("-c", dest="config", help="config file")
    parser.add_option("-p", dest="pdir", help="plugin directory")

    opts, args = parser.parse_args()

    plugin_dir = opts.pdir
    config_file = opts.config

    if not config_file:
        print >>sys.stderr, "Please specify the config file with the -c option"
        parser.print_help()
        sys.exit(1)

    if not plugin_dir:
        print >>sys.stderr, "Please specify the plugin directory with the -p option"
        parser.print_help()
        sys.exit(1)

    if not os.path.isdir(plugin_dir):
        print >>sys.stderr, "Can not find plugin directory: %s " % plugin_dir
        sys.exit(1)

    config = parse_config_file(file(config_file, "r"))

    DBG("Loading modules ...")
    for k, v in config.items():
        mod = load_module(k, v, plugin_dir)
        if not mod:
            print >>sys.stderr, "Failed to load plugin: %s" % k
        else:
            modules[mod.get_name()] = mod
            DBG("Plugin %s loaded" % k)

    try:
        # Munin default port is 4949
        host, port = "0.0.0.0", 4949

        server = SocketServer.TCPServer((host, port), MuninHandler)

        DBG("serving munin ...")
        server.serve_forever()
    except KeyboardInterrupt:
        print " received, terminating ..."

if __name__ == "__main__":
    main()
