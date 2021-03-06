#!/usr/bin/env python
# coding: utf-8
# TST-Online Command Line Login
# (C) 2012-2014 Dalton Serey / UFCG
#
# TST Commit -- Permite salvar uma nova versão do programa.

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import md5
import time
import json

import requests

import tstlib

def get_results(program_md5):

    # poll server for results
    program_data = tstjson.get(program_md5)
    if not program_data:
        tstjson[program_md5] = {}
    timestamp = tstjson[program_md5].get('timestamp')
    sleep_time = 2
    retries = 0

    time.sleep(1)
    token = config['access_token']
    tstonline = tstlib.TSTOnline(token)
    while True:

        print("Checking server for results...")
        response = tstonline.get(results_url(assignment_key))

        if response.status_code == 200:
            results = json.loads(response.text)
            if timestamp in results and results[timestamp]:

                # determine summary and feedback
                if type(results[timestamp]) == type(""):
                    summary = results[timestamp]
                    feedback = ""
                elif type(results[timestamp]) == type({}):
                    summary = results[timestamp]['summary']
                    feedback = results[timestamp].get('feedback', "")

                # store summary and feedback in tstjson
                tstjson[program_md5]['summary'] = summary
                tstjson[program_md5]['feedback'] = feedback
                tstlib.save_tstjson(tstjson)

                # return report
                return summary, feedback
            
        retries += 1
        if retries > 8:
            print("The test worker seems to be down, please try again later.")
            sys.exit()

        print("Will check again in %d seconds." % sleep_time)
        time.sleep(sleep_time)

        sleep_time = 2 * sleep_time if sleep_time < 32 else 60


def get_filename():

    # was filename provided in command line?
    if len(sys.argv) > 1:
        return sys.argv[-1]

    # get filename from 'tst.json'
    filename = tstjson.get('filename')
    
    if not filename:
        print("syntax: tst commit [filename]", file=sys.stderr)
        sys.exit(1)

    return filename


def get_key():

    # try reading key from 'tst.json'
    key = tstjson.get('key')

    if not key:
        print("tst: couldn't read key from tst.json", file=sys.stderr)
        sys.exit(1)

    # return hexadecimal key converted to decimal
    key = str(int(key, 16))

    return key


def assignment_url(key):
    return config['url'] + "/api/assignment/" + key 


def results_url(key):
    return config['url'] + "/api/results/" + key 


def main():

    # read submission code
    filename = get_filename()
    if not os.path.exists(filename):
        print("tst: no file name identified", file=sys.stderr)
        sys.exit(0)
    code = tstlib.to_unicode(open(filename, "r").read())
    program_md5 = md5.md5(code.encode('utf-8')).hexdigest()

    # is the code the same submitted in the last commit?
    if tstjson.get('last_commit') == program_md5:
        print("WARNING: no changes in '%s' since last commit!" % filename)
        print("WARNING: No commit performed.")
        program_data = tstjson.get(program_md5)
        if program_data:
            summary = program_data.get('summary')
            feedback = program_data.get('feedback')
            if summary:
                print("Previous results: [%s] %s" % (filename, summary))
                if feedback:
                    print(feedback)
                sys.exit()

        print("No previous results.")

    else:
        # the code has not been sent to the server yet
        local_revision = tstjson.get('activity_revision', "1.0.0")
        payload = [{
            "op": "add",
            "path": "/answers",
            "value": {
                "__code": code,
                "__filename": filename,
                "__activity_revision": local_revision
            }
        }]

        # send program to the server
        print("Uploading file '%s' (key: %s)... " % (filename, key))
        token = config['access_token']
        tstonline = tstlib.TSTOnline(token)
        response = tstonline.patch(assignment_url(assignment_key), payload)

        # was there an error 412?
        if response.status_code == 412:
            msg = response.json()['messages'][0]
            print("tst: %s" % msg, file=sys.stderr)
            print("tst: status code: %d" % response.status_code)
            sys.exit()

        # was there a different error?
        if response.status_code != 200:
            print(response.stdout)
            print("tst: are you logged in?", file=sys.stderr)
            print("tst: status code: %d" % response.status_code)
            sys.exit()

        # get some data from the server response
        assignment = json.loads(response.text)
        timestamp = assignment['answers'][-1]['__timestamp']
        activity_revision = assignment.get('activity_revision')

        # was the activity updated?
        if activity_revision and activity_revision != local_revision:
            if activity_revision.split(".")[0] != local_revision.split(".")[0]:
                # major is different
                print("WARNING: A MAJOR revision of this activity has been issued.")
            else:
                # either minor or patch is different
                print("WARNING: A MINOR revision of this activity has been issued.")
            print("WARNING: You SHOULD renew your copy and update your files.")
            print("WARNING: - local revision: %s" % local_revision)
            print("WARNING: - online revision: %s" % activity_revision)

        # report everything is ok
        print("Upload completed at '%s' (UTC)" % timestamp)

        # update tst.json with commit data
        tstjson['last_commit'] = program_md5
        tstjson[program_md5] = {
            'timestamp': timestamp
        }
        tstjson['key'] = key
        tstlib.save_tstjson(tstjson)

    # poll server for results
    summary, feedback = get_results(program_md5)
    print("[%s] %s" % (filename, summary))
    if feedback:
        print(feedback)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--one-line-help':
        print("send solution to server")
        sys.exit()

    config = tstlib.read_config(exit=True)
    headers = {'Authorization': 'Bearer ' + config['access_token']}
    tstjson = tstlib.read_tstjson(exit=True)
    assignment_key = get_key()
    key = "%X" % int(assignment_key)
    main()
