#!/usr/bin/env python
# coding: utf-8
# TST-Online Command Line Login
# (C) 2012-2014 Dalton Serey / UFCG
#
# Login no tst-online via OAuth-Like Login.

from __future__ import print_function
from __future__ import unicode_literals

import getpass
import json
import sys
import os
import webbrowser

import tstlib

# optionally import yaml
try:
    import requests
except ImportError:
    print("tst: login: Sorry, you don't have requests module installed")
    sys.exit()
    

def main(token):

    if not token:
        webbrowser.open(config['url'] + "/token/get")
        print("Copie e cole seu token aqui:")
        token = raw_input().strip()

    email = raw_input("Seu email: ")

    # request login authentication at google
    headers = {'Authorization': 'Bearer ' + token}
    url = config['url'] + '/token/validate/%s' % email

    print("Validando o token no TST Online.")
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print("tst: sorry, no internet connection?", file=sys.stderr)
        exit()

    validation_msg = response.text.splitlines()[0]
    if validation_msg != "Valid token.":
        print("ERRO: '%s'" % response.text)
        sys.exit()

    config['access_token'] = token
    config['email'] = email
    with open(os.path.expanduser("~/.curlrc"), "a") as curlrc:
        curlrc.write('-H "Authorization: Bearer %s"' % token)
        
    tstlib.save_config(config)
    print("Token validado.")
    print("Você está logado no tst-online como '%s'." % email)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--one-line-help':
        print("log into TST Server")
        sys.exit()

    config = tstlib.read_config(exit=True)
    token = sys.argv[1] if len(sys.argv) > 1 else None
    main(token)
