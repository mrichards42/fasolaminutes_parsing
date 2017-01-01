# Minutes grammar
import regex as re
import scanner
from itertools import repeat

def get_leaders(m, group_names):
    # Get a list of capture tokens in order
    tokens = []
    for group in group_names:
        tokens.extend(zip(m.starts(group), repeat(group), m.captures(group)))
    # Iterate in reverse order so we see last names first
    tokens.sort()
    tokens.reverse()
    # Build a list of names
    names = []
    last_name = None
    current_name = ''
    for start, token, text in tokens:
        if token == 'last':
            last_name = text
            current_name = last_name
        elif token == 'middle':
            current_name = text + ' ' + current_name
        elif token == 'first':
            current_name = text + ' ' + current_name
            names.append(current_name)
            current_name = last_name
    names.reverse() # iterated in reverse order, so reverse again
    return names

class MinutesToken(scanner.Token):
    def __init__(self, name, match, group_names=None):
        super(MinutesToken, self).__init__(name, match, group_names)
        if name == 'leader_list':
            self.captures['leader'] = get_leaders(match, group_names)

class MinutesScanner(scanner.Scanner):
    def __init__(self, token=MinutesToken):
        super(MinutesScanner, self).__init__(token)

    @classmethod
    def grammar(cls):
        return (
            cls.paragraph,
            cls.space,
            cls.session,
            cls.song,
            cls.role,
            cls.leader_list,
            cls.date,
            cls.ignore_leader,
            cls.word,
            cls.sentence,
            cls.anything,
        )

    #=========================================================================#
    # Leader                                                                  #
    #=========================================================================#

    leader_list = r'''
        {{leader}} (?: {{list_sep}} \s+ {{leader}} )*
    '''

    leader = r'''
        (?: {{name_prefix}} \s+)?        # Throw away name prefix
        (?P<first>{{first_name}})        # first name
        (?:
            {{list_sep}} \s+
            (?: {{name_prefix}} \s+)?
            (?P<first>{{first_name}})    # more first names
        )*
        \s+
        (?:
            (?P<middle>{{middle_name}})  # middle name
            \s+
        )?
        (?P<last>{{last_name}})          # last name
    '''

    first_name = r'''
        (?:
            {{name}} (?: \s* {{initial}} )*   # Name and multiple initials
        |
            {{initial}} \s+ {{name}}          # Single initial and a name
        |
            (?: {{initial}} \s*){2,}          # At least 2 initials
        )
        (?=\s|,|$)                            # space or list sep must follow
    '''

    middle_name = r'''
        (?: {{name}} | {{initial}} )          # Any number of names or initials
        (?: \s+ {{name}} | \s* {{initial}} )*
        (?=\s|$)                              # space must follow (not list sep)
    '''

    last_name = r'''
        {{name}} (?: , \s* {{name_suffix}} )?
    '''

    name = r'''
        \w*             # can start with any letter
        [A-Z]           # but must have an uppercase somewhere
        (?:
           [-'\u2019]?  # single hyphen or apostrophe (\u2019 is curly apostrophe)
           \w+
        )+
    '''

    initial = r'''
        [A-Z]           # uppercase
        (?:\.|(?!\w))   # followed by a period or non-letter
    '''

    name_suffix = r'[JjSs]r\.?'

    name_prefix = r'''
        Dr\.?    |
        Mrs?\.?  |
        Ms\.?    |
        Rev\.?   |
        [eE]lder
    '''


    role = r'''
        # Prefixes
        (?:(?:Co|Vice|Assistant|Honorary)[-\ ]?)*
        (?:
            # Regular officers
            (?:(?:Chair|Arrang|Secret|Treasur|Chaplain|President)\w*(?:\s+(?:[Cc]ommittee|[Oo]fficer)\w*)?)
        |
            # Committees
            (?:(?:Memorial|Resolution|Locat|Finance)\w*\s+(?:[Cc]ommittee|[Oo]fficer)\w*)
        )
    '''

    ignore_leader = r'''
            (?:
                in\ memory\ of
            |
                in\ remembrance\ of
            |
                in\ honor\ of
            |
                on\ behalf\ of
            |
                for\ the\ following
            ):?\s+
        |
            for\s+(?={{name}})
    '''

    #=========================================================================#
    # Song                                                                    #
    #=========================================================================#

    song = r'''
        (?: {{song_title}} | {{song_number}} )
        (?: \s* \( {{book_title}} \) )?
    '''

    song_title = r'''
        [\u201c"]                      # open quote -- \u201c is a curly quote
        (?P<title>
            (?:[^\u201d"\s]+\s+){,10}  # up to 10 words
            [A-Z]\w*                   # plus an uppercase word
        )
        [\u201d"]                      # close quote -- \u201d is a curly quote
        (?![\w:-])
    '''

    song_number = r'''
        [\{\[\<]?                      # Open bracket
        (?P<number>
            [0-9]{1,3}[tbTB]?            # Page number
        )
        (?://[0-9]{2,3}[tbTB]?)?         # Fixed page number
        [\}\]\>]?                      # Close bracket
        (?![\w:-])
    '''

    book_title = r'''
        (?P<book>
            (?: [A-Z]\w+ \s* )+
        )
    '''

    #=========================================================================#
    # Dates                                                                   #
    #=========================================================================#
    date = r'''
        # Sunday, March 20
        {{weekday}} ,? \s+ {{month}} ,? \s+ \d+ {{day_suffix}}?
    |
        {{month}} ,? \s+ {{weekday}} ,? \s+ \d+ {{day_suffix}}?
    |
        # Saturday before the third Sunday in March
        # Third Sunday in March
        # Third Sunday in March and the Saturday before
        # Third Sunday in March and the Saturday before
        # Third Sunday and the Saturday before in March
        (?: {{weekday}} \s+ before \s+ the \s+ )?
        {{ordinal}} \s+ {{weekday}}
        {{relative_date}}?+ \s+ in \s+ {{month}} {{relative_date}}?
    |
        {{month}} \s+ \d+ ,? \s+ {{year}}
    '''

    ordinal = r'''[Ff]irst|[Ss]econd|[Tt]hird|[Ff]ourth|[Ff]ifth|1st|2nd|3rd|4th|5th'''

    weekday = r'''(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*'''
    
    month = r'''(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*'''

    year = r'''\d{4}'''

    day_suffix = r'''st|nd|rd|th'''

    relative_date = r'''
        \s+ and \s+ (?:the \s+ )?
        {{weekday}} \s+
        (?:before|after)
    '''

    #=========================================================================#
    # Misc and building blocks                                                #
    #=========================================================================#

    paragraph = r'\n+'

    session = r'''
        [A-Z \t]{4,}     # All upper-case, at least 4 characters
        (?=$|\n)         # Must end w/ a paragraph break
    |
        RECESS\s+
    '''

    word = r'''
        # Times (which would otherwise be split up by punctuation)
        [AaPp]\.?[Mm]\.?
    |
        # Words with a single embedded non-word character
        \w+([^\w\s\n]\w+)*
    '''

    list_sep = r'''
        \s*, (?: \s* and )? (?=\s) # comma with or without and
    |
        \s* and (?=\s)                 # plain and
    '''

    sentence = r'[.;!?]+'

    space = r'[^\S\n]+'

    anything = r'[^\s.;!?]+'

