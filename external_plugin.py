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


    This external munin plugin will load any external
    program that can respond to commands to give data,
    give munin configuration information and give it's name.
'''
__author__="Chris Holcombe"
__date__ ="$Mar 4, 2010 12:28:01 PM$"

from subprocess import Popen,PIPE

#whether or not this command should be run from a shell.
shell=True
#command to run to call the script
command=None

def get_name():
    #get the name and strip off newline chars
    name = Popen(command + " name", stdout=PIPE, shell=shell).stdout.read().strip('\r\n')
    return name

def get_config():
    #get the data and strip off newline chars ( they mess up formatting of output )
    data = []
    config = Popen(command + " config", stdout=PIPE, shell=shell).stdout.read()
    lines = config.split("\n")
    for line in lines:
        data.append(line)
    return data

def get_data():
    tmp = []
    data = Popen(command, stdout=PIPE, shell=shell).stdout.read()
    lines = data.split("\n")
    for line in lines:
        tmp.append(line)
    return tmp

def main():
    pass

if __name__ == "__main__":
    main()
