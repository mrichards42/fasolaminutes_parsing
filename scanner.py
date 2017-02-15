import regex # This is so much faster than the regular re module

class Token(object):
    def __init__(self, name, match, group_names=None):
        self.name = name
        self.text = match.group()
        if group_names:
            captures = match.captures(*group_names)
            self.captures = dict(zip(group_names, captures))
        else:
            self.captures = {}

    def __getattr__(self, k):
        try:
            return self.captures[k]
        except KeyError:
            raise AttributeError()

    def first(self, k):
        for item in self.captures[k]:
            return item

    def all(self, k):
        return self.captures[k]

    def count(self, k):
        return len(self.all(k))

    def __repr__(self):
        return "%s(%r)" % (self.name, self.text)

    def to_html(self):
        text = self.text
        for key, values in self.captures.iteritems():
            if not values:
                continue
            pat = regex.compile('(' + '|'.join(regex.escape(v) for v in values) + r')')
            text = pat.sub(r'<span class="%s">\1</span>' % key, text)
        return '<span class="%s">%s</span>' % (self.name, text)


class Scanner(object):
    def __init__(self, token=Token):
        self._token_class = token

    @classmethod
    def grammar(cls):
        """Override to return an iterable with matching regex patterns."""
        raise NotImplementedError("You must define a grammar function")

    def tokenize(self, text):
        """Tokenize text using the class grammar."""
        self.tokens = list(self.iter_tokens(text))
        return self.tokens

    def iter_tokens(self, text):
        """Iterate over tokens using the class grammar."""
        for m in self._scanner.finditer(text):
            token_name = m.lastgroup
            # Yield the token
            yield self._token_class(token_name, m, self._groups[token_name])

    def finditer(self, pattern):
        """Find tokens using a modified regex (similar to NLTK chunking)

        Tokens are stringified like so:
            <n:token_name:text>

        The pattern is transformed like so:
            {{token_name}}           <\d+:token_name:[^>]*>
            {{token_name:pattern}}   <\d+:token_name:pattern>
            <other> <text>           <\d+:word:other><\d+:word:text>

        Note: the stringified delimiter is actually ascii 31 (record separator)
        but '<>' is used here for simplicity.

        """
        pattern = self._transform_pattern(pattern)
        # TODO: actually do the match
        print pattern

    def _build_token_string(self):
        # TODO: get rid of numbers and build a dict mapping m.start() to token
        return ''.join("\x1f%d:%s:%s\x1f" % (i, t.name, t.text.replace('\x1f', '')) for i, t in enumerate(self.tokens) if t.name != 'space')
        

    def _transform_pattern(self, pattern):
        def do_replace(m):
            name, pat, word = m.groups()
            if word:
                name = '.+'
                pat = word
            pat = pat or '.*'
            pat = pat.replace('.', '[^\x1f]')
            name = name.replace('.', '[^:\x1f]')
            return '(?:\x1f(\\d+):(?:%s):(?:%s)\x1f)' % (name, pat)

        # TODO: can probably get rid of capture numbers and use m.start()
        pattern = regex.sub(r'{{([^:}]+):?([^}]*)}}|<([^>]+)>', do_replace, pattern)
        return regex.compile(pattern, regex.X)

    def __new__(cls):
        # Get patterns and do {{ }} replacements
        cls._build_scanner()
        return super(Scanner, cls).__new__(cls)

    @classmethod
    def _build_scanner(cls):
        """Build the regex scanner from the class grammar."""
        if hasattr(cls, '_scanner'):
            return
        # Replace double brackets
        cls._replace_brackets()
        # Build the scanner from the provided grammar
        token_name = {v:k for k,v in cls.__dict__.iteritems() if isinstance(v, str)}
        # Build the matching regex
        grammar = cls.grammar()   # Each pattern to match in order
        big_re = []               # The final matching regex
        cls._groups = {}          # Groups internal to each pattern
        for pattern in grammar:
            group = token_name[pattern] # Internal name for each pattern
            big_re.append(r'(?P<%s>%s)' % (group, pattern))
            cls._groups[group] = list(set(regex.findall(r'\(\?P?<([^!=][^>]*)>', pattern)))
        # Compile each pattern
        for pattern, name in token_name.iteritems():
            try:
                setattr(cls, name, regex.compile(pattern, regex.X))
            except regex.error as e:
                print e
                print name
                raise
        # Compile the full scanner
        try:
            big_re = '|'.join(big_re)
            cls._scanner = regex.compile(big_re, regex.X)
        except regex.error as e:
            print e
            print(big_re)
            raise

    @classmethod
    def _replace_brackets(cls):
        """Replace {{ }} style format strings in patterns."""
        pattern_names = set(k for k,v in cls.__dict__.iteritems() if isinstance(v, str))
        # Check to see that all replacements exist
        replace_names = set(n for p in pattern_names for n in regex.findall(r'\{\{([^}]+)\}\}', getattr(cls, p)))
        for name in replace_names:
            if name not in pattern_names:
                raise KeyError('Unknown pattern: %r' % name)
        # Replace
        while True:
            # Find patterns with {{ }} replacements
            to_replace = set(p for p in pattern_names if getattr(cls, p).find('{{') > -1)
            if not to_replace:
                return
            # Regex to replace patterns that are not in to_replace
            replace_pattern = '|'.join(p for p in pattern_names if p not in to_replace)
            replace_pattern = regex.compile(r'\{\{(' + replace_pattern + r')\}\}')
            # Replace
            did_replace = False
            for p in to_replace:
                # Replace, wrapping sub-patterns in a non-matching group
                (pat, n) = replace_pattern.subn(lambda m: '(?:' + getattr(cls, m.group(1)) + ')', getattr(cls, p))
                setattr(cls, p, pat)
                did_replace = did_replace or n > 0
            if not did_replace:
                # If nothing was replaced, we have an error
                raise regex.error("Recursive patterns detected: %r" % to_replace)
