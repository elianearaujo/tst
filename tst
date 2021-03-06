#!/usr/bin/env python
# coding: utf-8
# (c) 2011-2014 Dalton Serey, UFCG
#
# TST Commander. Invokes TST commands. It supports both internal
# and external commands. Internal commands are functions within
# this script named 'tst_*' and external commands are scripts
# named 'tst_*.py' contained within the base directory of this
# script during runtime.
#
# To invoke a command, use the general syntax:
#
#       $ tst <command-name> [<arg> [<arg> ...]]
#
# If no recognized <command-name> is supplied, the
# DEFAULT_COMMAND will be invoked.

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import glob
import shlex
import subprocess

from subprocess import Popen, PIPE


# TST INTERNAL COMMANDS
DEFAULT_COMMAND = 'test'


def tst_help(args):
    """short description of commands"""
    print("External commands:")
    for cmd in externals():
        print(" %-12s%s" % (cmd, get_one_line_help(cmd)))

    print("\nInternal commands:")
    for cmd in internals():
        print(" %-12s%s" % (cmd, globals()['tst_' + cmd].__doc__))


def tst_newver(args):
    """print version of currently installed TST CLI"""
    TST_CLI_URL = "https://dl.dropboxusercontent.com/u/9427789/tst"
    CHANGELOG = os.path.dirname(__file__) + "/CHANGELOG.md"
    try:
        changelog = open(CHANGELOG, "r").readlines()
        version_line = [line for line in changelog if line.startswith("## ")]
        version = version_line[1].split()[1]
    except:
        print("tst: couldn't read CHANGELOG.md")
        sys.exit(1)

    print(version)
    print("checking for new version...")

    # perform request
    # TODO: remove requests; use json description of version
    import requests
    session = requests.session()
    response = session.get(TST_CLI_URL + "/CHANGELOG.md",
        allow_redirects=False
    )

    if response.status_code != 200:
        print("tst: couldn't check for updates (status code = %d)" % response.status_code)
        sys.exit()

    # process response
    changelog = response.text.splitlines()
    version_line = [line for line in changelog if line.startswith("## ")]
    last_version = version_line[1].split()[1]

    if last_version == version:
        print("tst: TST is up to date")
    else:
        print("tst: TST version %s is available" % last_version)


def run_external_command(command, args):
    cmd_args = " ".join(args)
    command_line = "tst_%s.py --one_line_help" % (command, cmd_args)
    cmd = shlex.split(command_line.encode('utf-8'))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        pass
    except OSError:
        print("tst: unknown command '%s'" % command, file=sys.stderr)
        print(cmd)


def get_one_line_help(command):

    script = "/Users/dalton/Dropbox/tst/2/cli/tst_%s.py" % command
    process = Popen([script, "--one-line-help"], stdout=PIPE, stderr=PIPE) 

    try:
        stdout, stderr = process.communicate()
    except: # something went wrong
        return "<couldn't find one line help for %s>" % command

    # collect report from stderr or stdout
    return stdout.strip()


def run_external_command(command, args):
    cmd_args = " ".join(args)
    command_line = "tst_%s.py %s" % (command, cmd_args)
    cmd = shlex.split(command_line.encode('utf-8'))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        pass
    except OSError:
        print("tst: unknown command '%s'" % command, file=sys.stderr)
        print(cmd)


def internals():
    return [f[4:] for f in globals().keys() if f.startswith('tst_')]


def externals():
    return ["login", "checkout", "test", "commit", "version"]


def identify_and_run_command(args):

    if args and args[0] in internals():
        command_name = args.pop(0) # discard command name
        run_internal_command = globals()["tst_" + command_name]
        run_internal_command(args)

    elif args and args[0] in externals():
        command_name = args.pop(0)
        run_external_command(command_name, args)

    else: # neither internal, nor external command!?
        args.insert(0, DEFAULT_COMMAND)
        identify_and_run_command(args)


if __name__ == "__main__":
    # make a safe and mutable copy of the arguments list
    args = sys.argv[:]
    args.pop(0) # discard commander name
    identify_and_run_command(args)
