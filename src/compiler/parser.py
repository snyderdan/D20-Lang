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

nextLabel = 0
def genLabel():
    global nextLabel
    label = ':L%d' % nextLabel
    nextLabel += 1
    return label

class exprlist:
    def __init__(self, tokens, terminators=[]):
        self.expressions = []
        self.toplevel = not terminators
        while len(tokens) > 0:
            if peek(tokens).label in terminators: break
            self.expressions.append(expr(tokens))

    def gen(self, pgm):
        for expr in self.expressions:
            expr.gen(pgm)
            if self.toplevel:
                pgm.append('POP')

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
    def gen(self, pgm):
        self.expr.gen(pgm)

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
    
    def gen(self, pgm):
        endLabel = genLabel()
        for condition, expression in self.conditions:
            condition.gen(pgm)
            jumpLabel = genLabel()
            pgm.append('GOTONIF ' + jumpLabel)
            pgm.append('POP')
            expression.gen(pgm)
            pgm.append('GOTO ' + endLabel)
            pgm.append(jumpLabel)
            pgm.append('POP')
        if self.elseclause:
            self.elseclause.gen(pgm)
        else:
            # Add a dummy else clause loading 0 onto the stack
            # necessary so the ifexpr will always yield a value
            pgm.append('LOAD 0')
        pgm.append(endLabel)

class storeexpr:
    def __init__(self, tokens):
        tok = peek(tokens)
        if tok.label in ['file_open_r', 'file_open_w', 'file_read', 'prompt']:
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

    def gen(self, pgm):
        if self.type == 'prompt':
            pgm.append('READ')
        elif self.type == 'file_read':
            self.value.gen(pgm)
            pgm.append('FREAD')
        elif self.type == 'file_open_r':
            self.value.gen(pgm)
            pgm.append('OPENR')
        elif self.type == 'file_open_w':
            self.value.gen(pgm)
            pgm.append('OPENW')
        else:
            self.value.gen(pgm)

        if self.store:
            self.store.gen(pgm)

class closeexpr:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'file_close':
            raise CompileException(tok, 'Close expression expected.')
        self.file = readref(tokens)

    def gen(self, pgm):
        self.file.gen(pgm)
        pgm.append('CLOSE')

class printexpr:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label not in ['print', 'file_write']:
            raise CompileException(tok, 'Expected print or file write.')
        
        if tok.label == 'file_write':
            self.file = readref(tokens)
        else:
            self.file = None
        self.value = expr(tokens)

    def gen(self, pgm):
        if self.file:
            self.value.gen(pgm)
            self.file.gen(pgm)
            pgm.append('FPRINT')
        else:
            self.value.gen(pgm)
            pgm.append('PRINT')

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

    def gen(self, pgm):
        if not self.op:
            self.left.gen(pgm)
        else:
            mapping = {'local_and': 'AND', 'logical_or': 'OR'}
            self.right.gen(pgm)
            self.left.gen(pgm)
            pgm.append(mapping[self.op])

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

    def gen(self, pgm):
        if not self.op:
            self.left.gen(pgm)
        else:
            mapping = {'add': 'ADD', 'subtract': 'SUB'}
            self.right.gen(pgm)
            self.left.gen(pgm)
            pgm.append(mapping[self.op])

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

    def gen(self, pgm):
        if not self.op:
            self.left.gen(pgm)
        else:
            mapping = {'multiply': 'MUL', 'divide': 'DIV', 'modulo': 'MOD'}
            self.right.gen(pgm)
            self.left.gen(pgm)
            pgm.append(mapping[self.op])

class prefix:
    def __init__(self, tokens):
        if peek(tokens).label in ('invert', 'add'):
            self.op = pop(tokens).label
        else:
            self.op = None
        self.value = value(tokens)

    def gen(self, pgm):
        self.value.gen(pgm)
        if self.op == 'invert':
            pgm.append('INV')
        elif self.op == 'add':
            pgm.append('SUM')

class modifiers:
    def __init__(self, tokens):
        # I am so sorry for what you're about to witness.
        keys = ['repeat_once', 'repeat', 'keep_high', 'keep_low', 
                'discard_high', 'discard_low', 'sort', 'sort_descend',
                'greater_than', 'less_than', 'equals']
        self.kh = None
        self.kl = None
        self.dh = None
        self.dl = None
        self.sort = False
        self.sortd = False
        self.ro = None
        self.r = None
        self.critcheck = None
        token = peek(tokens, False)
        while token and token.label in keys:
            mod = pop(tokens).label
            if mod == 'keep_high':
                if self.kh:
                    raise CompileException(token, 'Only 1 "kh" allowed per expression')
                if self.dh or self.dl:
                    raise CompileException(token, 'Cannot have keeps mixed with discards')
                self.kh = paren(tokens)
            elif mod == 'keep_low':
                if self.kl:
                    raise CompileException(token, 'Only 1 "kl" allowed per expression')
                if self.dh or self.dl:
                    raise CompileException(token, 'Cannot have keeps mixed with discards')
                self.kl = paren(tokens)
            elif mod == 'discard_high':
                if self.dh:
                    raise CompileException(token, 'Only 1 "dh" allowed per expression')
                if self.kl or self.kh:
                    raise CompileException(token, 'Cannot have keeps mixed with discards')
                self.dh = paren(tokens)
            elif mod == 'discard_low':
                if self.dl:
                    raise CompileException(token, 'Only 1 "dl" allowed per expression')
                if self.kl or self.kh:
                    raise CompileException(token, 'Cannot have keeps mixed with discards')
                self.dl = paren(tokens)
            elif mod == 'sort':
                if self.sort or self.sortd:
                    raise CompileException(token, 'Only 1 sort allowed per expression')
                self.sort = True
            elif mod == 'sort_descend':
                if self.sort or self.sortd:
                    raise CompileException(token, 'Only 1 sort allowed per expression')
                self.sortd = True
            elif mod == 'repeat':
                if self.r or self.ro:
                    raise CompileException(token, 'Only 1 repeat allowed per expression')
                if peek(tokens).value in '><=':
                    self.r = critcheck(tokens)
                else:
                    self.r = paren(tokens)
            elif mod == 'repeat_once':
                if self.r or self.ro:
                    raise CompileException(token, 'Only 1 repeat allowed per expression')
                self.ro = critcheck(tokens)
            else:
                # critcheck
                if self.critcheck:
                    raise CompileException(token, 'Only 1 crit check allowed per expression')
                self.critcheck = critcheck(tokens, token=token)
            token = peek(tokens, False)

    def gen(self, pgm, repeatLabel):
        '''
        Order of operations:
            repeat
            keep/discard
            sort
            critcheck
        '''

class critcheck:
    def __init__(self, tokens, token=None):
        if not token: token = pop(tokens)
        self.op = token.label
        if self.op not in ['greater_than', 'less_than', 'equals']:
            raise CompileException(token, 'Expected crit check, got "{}"'.format(token.value))
        self.value = paren(tokens)
    def gen(self, pgm):
        pass

class value:
    def __init__(self, tokens):
        if peek(tokens).label == 'load':
            self.value = readref(tokens)
        elif peek(tokens).label == 'o_square':
            self.value = listgen(tokens)
        else:
            self.value = paren(tokens)
            tok = peek(tokens, False)
            if tok and tok.label == 'roll':
                self.value = diceroll(tokens, count=self.value)

        self.modifiers = modifiers(tokens)

    def gen(self, pgm):
        repeatLabel = genLabel()
        self.value.gen(pgm)
        self.modifiers.gen(pgm, repeatLabel)

class listgen:
    def __init__(self, tokens):
        if peek(tokens).label != 'o_square':
            raise CompileException(peek(tokens), 'Expected list generator')
        pop(tokens)
        self.value = exprlist(tokens, terminators=['c_square'])
        if pop(tokens).label != 'c_square':
            raise CompileException(peek(tokens), 'Expected closing square bracket')

    def gen(self, pgm):
        self.value.gen(pgm)
        pgm.append('MLIST {}'.format(len(self.value.expressions)))

class storeref:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'store':
            raise CompileException(tok, 'Expected write storage reference')
        self.ref = diceroll(tokens)

    def gen(self, pgm):
        self.ref.genSides(pgm)
        self.ref.genCount(pgm)
        pgm.append('POPV')

class readref:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label != 'load':
            raise CompileException(tok, 'Expected read storage reference')
        self.ref = diceroll(tokens)

    def gen(self, pgm):
        self.ref.genSides(pgm)
        self.ref.genCount(pgm)
        pgm.append('PUSHV')

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

    def genSides(self, pgm):
        self.sides.gen(pgm)
        pgm.append('SUM')

    def genCount(self, pgm):
        self.count.gen(pgm)
        pgm.append('SUM')

    def gen(self, pgm):
        self.genSides(pgm)
        self.genCount(pgm)
        pgm.append('ROLL')

class paren:
    def __init__(self, tokens):
        tok = pop(tokens)
        if tok.label == 'number':
            self.type = 'numeric'
            self.inner = tok.value
            return 

        if tok.label != 'o_paren':
            raise CompileException(tok, "Expected a number or open parenthesis")
        self.type = 'expression'
        self.inner = expr(tokens)
        tok = pop(tokens)
        if tok.label != 'c_paren':
            raise CompileException(tok, "Expected a closing parenthesis")

    def gen(self, pgm):
        if self.type == 'numeric':
            pgm.append('PUSH {}'.format(self.inner))
        else:
            self.inner.gen(pgm)
