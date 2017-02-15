import sqlite3
import os
import re
from collections import defaultdict
from itertools import izip

dbname = 'minutes.db'

_db = None

def get_db():
    global _db
    if not _db:
        print dbname
        _db = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES)
        _db.row_factory = sqlite3.Row
    return _db

def close_db():
    global _db
    if _db:
        _db.close()
        _db = None

def execute(*args, **kwargs):
    return get_db().execute(*args, **kwargs)

newline_re = re.compile(r"\s*\\n+\s*")
def parse_text(text):
    """Parse as either UTF-8 or Mac Roman"""
    try:
        text = text.decode('utf-8')
    except UnicodeDecodeError:
        text = text.decode('mac-roman')

    # Some text contains literal newlines (that should just be spaces)
    if '\\n' in text:
        text = newline_re.sub(' ', text)
    # Minutes text is separated on vertical newlines
    text = text.replace('\v', '\n')
    return text

sqlite3.register_converter("TEXT", parse_text)

def get_minutes(id):
    """Return a dict of minutes data"""
    cursor = execute("""
        SELECT id, name, location, date, minutes
        FROM minutes
        WHERE id=?
    """, (id,))
    (id, name, location, date, minutes) = next(cursor)
    return {
        'id': id,
        'name': name,
        'location': location,
        'date': date,
        'minutes': minutes,
    }

def get_leaders(id):
    """Return a list of leader data"""
    cursor = execute("""
        SELECT lead_id, leaders.name, songs.PageNum
        FROM song_leader_joins
        LEFT JOIN leaders ON leader_id=leaders.id
        LEFT JOIN songs ON song_id=songs.id
        WHERE minutes_id=?
		ORDER BY lead_id, leaders.name
    """, (id,))

    lead = defaultdict(lambda: defaultdict(list))
    for (lead_id, name, page) in cursor:
        leads[lead_id][lead_id] = lead_id
        leads[lead_id][page] = page
        leads[lead_id][leaders].append(name)

    leads = lead.values()
    leads.sort(key='lead_id')
    return leads

def get_songs():
    """Return a set of song page numbers"""
    cursor = execute("""SELECT PageNum FROM songs""")
    return set(page for (page,) in cursor)

def get_index():
    columns = ('id', 'name', 'location', 'date', 'year')
    cursor = execute("SELECT " + ', '.join(columns) + " FROM minutes")

    return [dict(izip(columns, row)) for row in cursor]
    
