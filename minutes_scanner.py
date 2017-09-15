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
            cls.ignore_song,
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
        {{leader}} (?: {{list_sep}} [ \t]+ {{leader}} )*
    '''

    leader = r'''
        (?: {{name_prefix}} [ \t]+)?     # Throw away name prefix
        (?P<first>{{first_name}})        # first name
        (?:
            {{list_sep}} [ \t]+
            (?: {{name_prefix}} [ \t]+)?
            (?P<first>{{first_name}})    # more first names
        )*
        [ \t]+
        (?:
            (?P<middle>{{middle_name}})  # middle name
            [ \t]+
        )?
        (?P<last>{{last_name}})          # last name
    '''

    first_name = r'''
        (?:
            {{name}} (?: [ \t]* {{initial}} )*   # Name and multiple initials
        |
            {{initial}} [ \t]+ {{name}}          # Single initial and a name
        |
            (?: {{initial}} [ \t]*){2,}          # At least 2 initials
        )
        (?=[ \t]|,|$)                            # space or list sep must follow
    '''

    middle_name = r'''
        (?: {{name}} | {{initial}} )             # Any number of names or initials
        (?: [ \t]+ {{name}} | [ \t]* {{initial}} )*
        (?=[ \t]|$)                              # space must follow (not list sep)
    '''

    last_name = r'''
        {{name}} (?: , [ \t]* {{name_suffix}} )?
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
            (?:(?:Chair|Arrang|Secret|Treasur|Chaplain|President)\w*(?:[ \t]+(?:[Cc]ommittee|[Oo]fficer)\w*)?)
        |
            # Committees
            (?:(?:Memorial|Resolution|Locat|Finance)\w*[ \t]+(?:[Cc]ommittee|[Oo]fficer)\w*)
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
            ):?[ \t]+
        |
            for[ \t]+(?={{name}})
    '''

    #=========================================================================#
    # Song                                                                    #
    #=========================================================================#

    song = r'''
        (?: {{song_title}} | {{song_number}} )
        (?: [ \t]* \( {{book_title}} \) )?
    '''

    song_title = r'''
        [\u201c"]                      # open quote -- \u201c is a curly quote
        (?P<title>
            (?:[^\u201d" \t]+[ \t]+){,10}  # up to 10 words
            [A-Z]\w*                       # plus an uppercase word
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
            (?: [A-Z]\w+ [ \t]* )+
        )
    '''

    ignore_song = r'''
            (?:report\w*)[ \t]+
    '''

    #=========================================================================#
    # Dates                                                                   #
    #=========================================================================#
    date = r'''
        # Sunday, March 20
        {{weekday}} ,? [ \t]+ {{month}} ,? [ \t]+ \d+ {{day_suffix}}?
    |
        {{month}} ,? [ \t]+ {{weekday}} ,? [ \t]+ \d+ {{day_suffix}}?
    |
        # Saturday before the third Sunday in March
        # Third Sunday in March
        # Third Sunday in March and the Saturday before
        # Third Sunday in March and the Saturday before
        # Third Sunday and the Saturday before in March
        (?: {{weekday}} [ \t]+ before [ \t]+ the [ \t]+ )?
        {{ordinal}} [ \t]+ {{weekday}}
        {{relative_date}}?+ [ \t]+ in [ \t]+ {{month}} {{relative_date}}?
    |
        {{month}} [ \t]+ \d+ ,? [ \t]+ {{year}}
    '''

    ordinal = r'''[Ff]irst|[Ss]econd|[Tt]hird|[Ff]ourth|[Ff]ifth|1st|2nd|3rd|4th|5th'''

    weekday = r'''(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*'''
    
    month = r'''(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*'''

    year = r'''\d{4}'''

    day_suffix = r'''st|nd|rd|th'''

    relative_date = r'''
        [ \t]+ and [ \t]+ (?:the [ \t]+ )?
        {{weekday}} [ \t]+
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
        RECESS[ \t]+
    '''

    word = r'''
        # Times (which would otherwise be split up by punctuation)
        [AaPp]\.?[Mm]\.?
    |
        # Words with a single embedded non-word character
        \w+([^\w\s]\w+)*
    |
        # Separators that do not require a space
        --
    |
        # Money
        \$\d+(?:\.\d+)?
    '''

    list_sep = r'''
        [ \t]*, (?: [ \t]* and )? (?=[ \t]) # comma with or without and
    |
        [ \t]* and (?=[ \t])                # plain and
    '''

    sentence = r'[.;!?]+'

    space = r'[^\S\n]+'

    anything = r'[^ \t.;!?\w]+|\w'

