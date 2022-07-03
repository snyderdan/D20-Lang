from tokenizer import tokenize
from parser import exprlist

def compile(code):
    tokens = tokenize(code)
    tree = exprlist(tokens)
    asm = []
    tree.gen(asm)
    asm = optimize(asm)
    return assemble(trimmed)

def optimize(instructions):
    optimized = [instructions[0]]
    for i in range(1, len(instructions)):
        ''' 
        Since the dice roll doesn't have knowledge of what the left and right
        hand operands are, it always attempts to sum them to ensure it's using 
        a single number for the dice roll. 
        For any standard dice roll XdY, the code generated will be:
            LOAD Y
            SUM
            LOAD X
            SUM
            ROLL
        We can remove the SUM instructions proceeding a LOAD in this case.
        '''
        if instructions[i-1].startswith('LOAD') and instructions[i] == 'SUM':
            continue
        optimized.append(instructions[i])
    return optimized

def assemble(instructions):
    pass