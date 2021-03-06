#!/usr/bin/env python
# coding: utf-8
# TST-Online Command Line Login
# (C) 2012-2014 Dalton Serey / UFCG
#
# TST Checkout -- Permite baixar a última versão do programa.
# Sobreescreve a versão local.
#
# CHANGELOG:
#
# - tst_logout.py dá mensagem adequada, quando o usuário não
#   está logado (ou quando o cookie venceu);

# TODO:
#
# - se existir um tst.json no diretório corrente, deveria
#   dispensar o uso de key; se o usuário usar um key, havendo
#   um tst.json no diretório, deve-se indicar erro; isso evitará
#   que o usuário venha a sobrepor o tst.json de outro problema;
# - deveria criar o diretório com base no name da activity (?)
# - deveria usar o name da activity como chave de download (?)

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import codecs
import json

import tstlib


def get_key():

    # try from command line
    if len(sys.argv) > 1:
        try:
            integer_id = int(sys.argv[1], 16)
        except:
            print("tst: invalid key", file=sys.stderr)
        return str(integer_id)

    # otherwise, try reading from the tstjson file
    key = tstjson.get('key')
    if key:
        return str(int(key, 16))

    print("tst: what key should be used?", file=sys.stderr)
    sys.exit(1)


def checkout_url(key):
    return config['url'] + "/api/assignment/" + key 


def main():
    assignment_key = get_key()
    token = config['access_token']
    tstonline = tstlib.TSTOnline(token)
    url = checkout_url(assignment_key) + '?checkout=true'
    
    # perform request
    print("Downloading files.")
    response = tstonline.get(url)

    if 400 <= response.status_code < 500:
        msg = response.json()['messages'][0]
        print("tst: %s" % msg, file=sys.stderr)
        print("tst: response status code: %d" % response.status_code)
        sys.exit()

    if response.status_code != 200:
        print("tst: it seems you're not logged in", file=sys.stderr)
        print("tst: response status code: %d" % response.status_code)
        sys.exit()

    # process response
    data = response.json()
    activity_revision = data.get('activity_revision')
    files = data.get('files', [])
    if '__code' in data:
        files.append({
            "name":data['__code']['__filename'],
            "data":data['__code']['__code']
        })

    print("Revision %s of the activity has been checked out." % activity_revision)
    print("Saving downloaded files.")

    # save/overwrite files
    filename = None
    for file in files:
        filename = file["name"]
        filedata = file["data"]
        if os.path.exists(filename):
            while True:
                confirm = raw_input("tst: overwrite '%s'? (Y/n) " % filename)
                if confirm.lower() in "ny": break

            if confirm == "n":
                continue

        program_file = open(filename, "w")
        filedata = filedata.encode('utf-8')
        program_file.write(filedata)
        print("- %s (%d bytes)" % (filename, len(filedata)))

    # save/update tst.json
    tstjson['key'] = "%X" % int(assignment_key)
    tstjson['activity_revision'] = activity_revision
    tstjson['tests'] = data['tests']
    if data.get('files'):
        tstjson['tst_files'] = [file['name'] for file in data.get('files')]
    if filename:
        tstjson['filename'] = filename
        tstjson['tst_files'].remove(filename)
    tstlib.save_tstjson(tstjson)
    print("- tst.json")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--one-line-help':
        print("download assignment files")
        sys.exit()

    config = tstlib.read_config(exit=True)
    tstjson = tstlib.read_tstjson(exit=True)
    logfile = os.path.expanduser("~/.tst/logs")
    log = codecs.open(logfile, mode="a", encoding='utf-8')
    headers = {'Authorization': 'Bearer ' + config['access_token']}
    main()
