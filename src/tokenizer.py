import re

class Token:
    nextIndex = 0
    def __init__(self, match, toktype, toklabel, line, column):
        self.index = Token.nextIndex
        Token.nextIndex += 1
        self.value = match.group(0)
        self.length = len(self.value)
        self.type = toktype
        self.label = toklabel
        self.match = match
        self.line = line
        self.column = column

    def __repr__(self):
        return "<Token[%s] = %s>" % (self.label, self.value)
    

class DummyMatch:
    def __init__(self, data, end):
        self._data = data
        self._end = end

    def group(self, num):
        if num == 0:
            return self._data
        else:
            return None

    def end(self):
        return self._end
    

class TokenFactory:
    nextId = 0
    def __init__(self, name):
        self.ID = TokenFactory.nextId
        TokenFactory.nextId += 1
        self.name = name

    def getMatch(self, inp):
        raise NotImplemented()

    def getToken(self, match, line, col):
        return Token(match, self.ID, self.name, line, col)

    def __repr__(self):
        return "<TokenFactory[%s] ID %d>" % (self.name, self.ID)
    

class SingleTokenFactory(TokenFactory):
    def __init__(self, name, chars):
        super().__init__(name)
        self.chars = chars

    def getMatch(self, inp):
        if inp.startswith(self.chars):
            return DummyMatch(self.chars, len(self.chars))
        return None
    

class ReTokenFactory(TokenFactory):
    def __init__(self, name, regexp):
        super().__init__(name)
        self.pattern = re.compile(regexp)

    def getMatch(self, inp):
        return self.pattern.match(inp)


tokens = [SingleTokenFactory('file_open_r', '^'),
          SingleTokenFactory('file_open_w', 'v'),
          SingleTokenFactory('file_read', '?|'),
          SingleTokenFactory('file_write', '!|'),
          SingleTokenFactory('file_close', '|'),
          SingleTokenFactory('prompt', '?'),
          SingleTokenFactory('print', '!'),
          SingleTokenFactory('logical_and', '&&'),
          SingleTokenFactory('logical_or', '||'),
          SingleTokenFactory('store', '@'),
          SingleTokenFactory('load', '&'),
          SingleTokenFactory('invert', '~'),
          SingleTokenFactory('o_bracket', '{'),
          SingleTokenFactory('c_bracket', '}'),
          SingleTokenFactory('o_square', '['),
          SingleTokenFactory('c_square', ']'),
          SingleTokenFactory('o_paren', '('),
          SingleTokenFactory('c_paren', ')'),
          SingleTokenFactory('multiply', '*'),
          SingleTokenFactory('divide', '/'),
          SingleTokenFactory('percent', '%'),
          SingleTokenFactory('add', '+'),
          SingleTokenFactory('subtract', '-'),
          SingleTokenFactory('greater_than', '>'),
          SingleTokenFactory('less_than', '<'),
          SingleTokenFactory('equals', '='),
          SingleTokenFactory('repeat_once', 'ro'),
          SingleTokenFactory('repeat', 'r'),
          SingleTokenFactory('keep_high', 'kh'),
          SingleTokenFactory('keep_low', 'kl'),
          SingleTokenFactory('discard_high', 'dh'),
          SingleTokenFactory('discard_low', 'dl'),
          SingleTokenFactory('sort_descend', 'sd'),
          SingleTokenFactory('sort', 's'),
          SingleTokenFactory('roll', 'd'),
          ReTokenFactory('number',r'\d+'),
          ReTokenFactory('comment',r'//.*')]

tokendict = dict(((tok.name, tok.ID) for tok in tokens))

def addToken(name):
    tokendict[name] = TokenFactory.nextId
    TokenFactory.nextId += 1

addToken('unknown')

def getfactory(string):
    for factory in tokens:
        match = factory.getMatch(string)
        if match:
            return factory
    return None

def tokenize(string):
    output = []
    unknownId = tokendict['unknown']

    line, column = 1, 0
    lastLength = 1
    
    while len(string) > 0:
        char = string[0]
        column += lastLength
        if char == '\n':
            line += 1
            column = 0
            
        if char in '\t \n\r':
            lastLength = 1
            string = string[1:]
            continue
        
        factory = getfactory(string)
        if factory:
            match = factory.getMatch(string)
            string = string[match.end():]
            token = factory.getToken(match, line, column)
            if token.label != 'comment':
                output.append(token)
            lastLength = match.end() 
        else:
            # no match, it's an unknown
            idx = 1
            while idx < len(string) and not getfactory(string[idx:]) and string[idx] not in '\n\t \r':
                idx += 1

            match = DummyMatch(string[:idx], idx)
            output.append(Token(match, unknownId, 'unknown', line, column))
            string = string[idx:]
            lastLength = idx
            
    return output
