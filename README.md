munin-node-python
=================

A munin node written in pure python

This piece of code is here to support munin on Windows.

https://github.com/munin-monitoring/munin-node-win32 fails miserably after a few
days on Windows 2008R2 server

It was sort of impossible to get the new munin-node-c working on windows with
inetd-ish servers.

TODOs:
- big code cleanup
- multi connect works, but multi command execution does not
