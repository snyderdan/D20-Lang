import tokenizer

class CompileException(Exception):
    def __init__(self, token, message):
        msg = "Error line {} column {}: {}".format(token.line, token.column, message)
        super().__init__(msg)

lastToken = None
def peek(tokens, throws=True):
    if len(tokens):
        return tokens[0]
    elif throws:
        raise CompileException(lastToken, 'Unexpected EOF')
    else:
        return None

def pop(tokens, throws=True):
    global lastToken
    if len(tokens):
        lastToken = tokens[0]
        return tokens.pop(0)
    elif throws:
        raise CompileException(lastToken, 'Unexpected EOF')
    else:
        return None

class exprlist:
    def __init__(self, tokens, terminators=[]):
        self.expressions = []
        while len(tokens) > 0:
            if peek(tokens).label in terminators: break
            self.expressions.append(expr(tokens))

diceEncountered = False

class expr:
    def __init__(self, tokens):
        global diceEncountered
        diceEncountered = False

        tok = peek(tokens)
        if tok.label in ('file_write', 'print'):
            self.expr = printexpr(tokens)
        elif tok.label == 'file_close':
            self.expr = closeexpr(tokens)
        elif tok.label == 'o_bracket':
            self.expr = ifexpr(tokens)
        else:
            self.expr = storeexpr(tokens)

        #if not diceEncountered:
        #    raise CompileException(tok, 'Expression does not contain a dice roll.')

class ifexpr:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'o_bracket':
            raise CompileException(tok, 'Conditional block must start with \'{\'')

        self.conditions = []
        self.elseclause = None
        while True:
            # parse expression (either conditional field or else clause)
            ifcond = expr(tokens)
            thendo = None
            tok = pop(tokens)
            if tok.label == 'comma':
                # normal conditional clause - parse the "do" portion of the condition
                thendo = expr(tokens)
                self.conditions.append((ifcond, thendo))
            elif tok.label == 'c_bracket':
                # ending else clause
                self.elseclause = ifcond
                break
            else:
                # error
                raise CompileException(tok, 'Unexpected symbol in condition block "{}"'.format(tok.value))
            # handle separator
            tok = pop(tokens)
            if tok.label == 'v_bar':
                # another condition/else clause
                continue
            elif tok.label == 'c_bracket':
                # no else clause
                break
            else:
                # error
                raise CompileException(tok, 'Unexpected symbol in condition block "{}"'.format(tok.value))

class storeexpr:
    def __init__(self, tokens):
        tok = peek(tokens)
        if tok.label in ['file_open', 'file_read', 'prompt']:
            self.type = pop(tokens).label
        else:
            self.type = 'basic'

        if self.type == 'prompt':
            self.value = None
        elif self.type == 'file_read':
            self.value = readref(tokens)
        else:
            self.value = mathexpr(tokens)

        tok = peek(tokens, False)
        if tok and tok.label == 'store':
            self.store = storeref(tokens)
        else:
            self.store = None

class closeexpr:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'file_close':
            raise CompileException(tok, 'Close expression expected.')
        self.file = readref(tokens)

class printexpr:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label not in ['print', 'file_write']:
            raise CompileException(tok, 'Expected print or file write.')
        
        if tok.label == 'file_write':
            self.file = readref(tokens)
        self.value = expr(tokens)


class mathexpr:
    def __init__(self, tokens):
        self.left = addsub(tokens)
        tok = peek(tokens, False)
        if tok and tok.label in ('logical_and', 'logical_or'):
            self.op = pop(tokens).label
            self.right = mathexpr(tokens)
        else:
            self.op = None
            self.right = None

class addsub:
    def __init__(self, tokens):
        self.left = muldiv(tokens)
        tok = peek(tokens, False)
        if tok and tok.label in ('add', 'subtract'):
            self.op = pop(tokens).label
            self.right = addsub(tokens)
        else:
            self.op = None
            self.right = None

class muldiv:
    def __init__(self, tokens):
        self.left = prefix(tokens)
        tok = peek(tokens, False)
        if tok and tok.label in ('multiply', 'divide', 'modulo'):
            self.op = pop(tokens).label
            self.right = muldiv(tokens)
        else:
            self.op = None
            self.right = None

class prefix:
    def __init__(self, tokens):
        if peek(tokens).label in ('invert', 'add'):
            self.op = pop(tokens).label
        else:
            self.op = None
        self.value = modifiable(tokens)

class modifiable:
    def __init__(self, tokens):
        if peek(tokens).label == 'o_square':
            pop(tokens)
            self.type = 'list'
            self.value = exprlist(tokens, terminators=['c_square'])
            if peek(tokens).label != 'c_square':
                raise CompileException(peek(tokens), 'Expected closing square bracket')
        else:
            self.type = 'value'
            self.value = value(tokens)

        self.modifiers = modifiers(tokens)

class modifiers:
    def __init__(self, tokens):
        pass

class value:
    def __init__(self, tokens):
        if peek(tokens).label == 'load':
            self.value = readref(tokens)
        else:
            self.value = paren(tokens)
            tok = peek(tokens, False)
            if tok and tok.label == 'roll':
                self.value = diceroll(tokens, count=self.value)

class storeref:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'store':
            raise CompileException(tok, 'Expected write storage reference')
        self.ref = diceroll(tokens)

class readref:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'load':
            raise CompileException(tok, 'Expected read storage reference')
        self.ref = diceroll(tokens)

class diceroll:
    def __init__(self, tokens, count=None):
        if count:
            self.count = count
        else:
            self.count = paren(tokens)
            
        tok = pop(tokens)
        if tok.label != 'roll':
            raise CompileException(tok, 'Expected dice roll')
        self.sides = paren(tokens)

class paren:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label == 'number':
            self.inner = tok.value
            return 

        if tok.label != 'o_paren':
            raise CompileException(tok, "Expected a number or open parenthesis")
        self.inner = expr(tokens)
        tok = pop(tokens)
        if tok.label != 'c_paren':
            raise CompileException(tok, "Expected a closing parenthesis")
