#!/usr/bin/env python
# encoding: utf-8

import sqlite3

def open_db():
    conn = sqlite3.connect("minutes.db")
    conn.text_factory = lambda x: unicode(x, 'utf-8')
    return conn
