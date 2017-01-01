"""Minutes text parser."""
from minutes_scanner import MinutesScanner
import minutes_db
import regex as re

scanner = MinutesScanner()

def parse(text, song_title=False, breaks=False):
    """Parse minutes text.
    
    Returns a list of leaders and songs
    
    """
    leads = []
    last_leader = None
    ignore_leader = False
    ignore_song = False
    officers = {}
    for token in scanner.tokenize(text):
        if token.name == 'leader_list':
            if '_next' in officers:
                name = officers.pop('_next')
                officers[name] = token.all('leader')
            if ignore_leader:
                print "IGNORED (LEADER): ",token
            else:
                last_leader = token
        elif token.name == 'song':
            if ignore_song:
                print "IGNORED (SONG): ",token
            elif last_leader:
                book = get_book_abbr(token.first('book'))
                song = token.first('number')
                if song and not book:
                    song = get_song(song).lower()
                if not song and song_title:
                    song = token.first('title')
                    if song.endswith('Singing'):
                        song = None
                if song:
                    if book:
                        song = book + ' ' + song
                    for leader in last_leader.all('leader'):
                        leads.append({'leader':leader, 'song': song})
                else:
                    print "MISSING_SONG", token.captures
            else:
                print 'MISSING_LEADER', token.captures
        elif token.name == 'session' and breaks:
                leads.append({'leader': token.text, 'song': 'BREAK'})
        elif token.name in ('paragraph', 'sentence'):
            last_leader = None
        elif token.name == 'role':
            officers['_next'] = token.text
        # Check ignore flag
        if token.name == 'ignore_leader':
            ignore_leader = True
            print "IGNORE LEADER"
        if token.name == 'ignore_song':
            ignore_song = True
            print "IGNORE SONG"
        elif token.name in ('sentence', 'paragraph', 'session'):
            ignore_leader = False
            ignore_song = False
    return leads


SONGS = None
def get_song(number, strict=False):
    global SONGS
    if not SONGS:
        SONGS = minutes_db.get_songs()
    if not number or number in SONGS:
        return number
    # Look for extra t/b
    if re.match(r'\d+[tb]', number):
        if number[:-1] in SONGS:
            return number[:-1]
    if not strict:
        return number

books = {
    'Christmas Harp': 'ACH',
    'Christian Harmony': 'CH',
    'Cooper Book': 'CB',
}
def get_book_abbr(title):
    return books.get(title, title)

if __name__ == '__main__':
    from pprint import pprint
    from time import time
    start = time()
    count = 0
    for id in xrange(1, 10):
        count += 1
        print "id=",id
        text = minutes_db.get_minutes(id)['minutes']
        leads = parse(text, breaks=True)
        #pprint(leads)
        #leads = []
        #for paragraph in tokens.paragraphs:
        #    for sentence in paragraph.sentences:
        #        leads.extend(SentenceParser([]).get_leads(sentence))
        #pprint(leads)
    end = time()
    total_time = end - start
    print "Parsed %d minutes in %f seconds (avg: %f)" % (count, total_time, float(total_time) / count)




# Old utility functions

invalid_song_re = re.compile(r'''
    ^(singer|people|lead|led|attend|state|song|tune|lesson)
''', re.I | re.X)

def score_song(song):
    """How likely is it that this is a real song?
    
    Args:
        song: a song token

    Returns:
        probability (int; 0-1) that this is a song
    
    """
    if song.next() and invalid_song_re.search(song.next().text or ''):
        return 0 # Song is followed by an invalid word -- this is not a song
    score = 1.0
    if not song.sentence.get('leader_list'):
        if not song.sentence.get('other_leader'):
            # No leaders; this not likely to be a song
            return 0.25
        # Only an alternative leader . . . less likely
        score *= 0.9
    if song.findnode('song_title'):
        # Song titles (instead of page numbers) are less likely
        score *= 0.9
    return score
