

OpCodes = [
    'NOP',
    'ADD',
    'SUB',
    'MUL',
    'DIV',
    'MOD',
    'AND',
    'OR',
    'NOT',
    'LIST',
    'SUM',
    'LOAD',
]

class OpCode:
    nextId = 0
    
    def __init__(self, name, fn, nargs=0):
        self.bin = OpCode.nextId
        OpCode.nextId += 1
        self.name = name
        self.nargs = nargs
        self.fn = fn

    def exec(self, stack, heap, *args):
        if args:
            return self.fn(stack, heap, *args)
        else:
            return self.fn(stack, heap)

opcodes = [OpCode('NOP'), OpCode('ADD',add),OpCode('SUB',sub),OpCode('MUL',mul),
           OpCode('DIV',div),OpCode('AND',b_and),OpCode('OR',b_or),
           OpCode('XOR',b_xor),OpCode('NOT',b_not),OpCode('PUSHVAR',pushvar,1),
           OpCode('POPVAR',popvar,1),OpCode('PUSHNUM',pushnum,1),
           OpCode('PUSHSTR',pushstr,1),OpCode('DUP',dup,1),OpCode('POP',pop,1),
           OpCode('MAKELST',makelist),OpCode('SEED',seed),OpCode('RAND',rand),
           OpCode('LEN',length),OpCode('LT',lt),OpCode('LTE',lte),
           OpCode('GT',gt),OpCode('GTE',gte),OpCode('EQ',eq),OpCode('NE',ne),
           OpCode('GOTO',goto,1),OpCode('GOTOIF',gotoif,1),OpCode('PRINT',prnt),
           OpCode('GETV',getv),OpCode('SETV',setv),OpCode('SAVEVAR',savevar,1),
           OpCode('INPUT',getinp),OpCode('INC',increment),
           OpCode('FLOOR',do_floor),OpCode('CEIL',do_ceil),
           OpCode('DEC',decrement),OpCode('TIME',gettime),OpCode('POW',power)]

def getInstruction(mnemonic):
    for o in opcodes:
        if o.name == mnemonic:
            return o.bin

def assemble(instructions):
    instructions = instructions.split("\n")
    pgm = []
    
    for instr in instructions:
        instr = instr.strip()
        if len(instr) == 0: continue
        
        if " " in instr:
            instr, args = instr.split(" ")
            instr = instr.strip()
            args = args.strip()
            if args.isnumeric() or (args.startswith('-') and args[1:].isnumeric()):
                args = int(args)
            pgm.append(getInstruction(instr))
            pgm.append(args)
        else:
            pgm.append(getInstruction(instr))
    return pgm

def execute(pgm):
    address = 0
    stack = Stack()
    heap = Heap()
    while address < len(pgm):
        op = opcodes[pgm[address]]
        args = [pgm[address+1+n] for n in range(0,op.nargs)]
        res = op.exec(stack, heap, *args)
        if res:
            address += res.toNumber()
        else:
            address += 1 + len(args)
