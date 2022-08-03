

def add(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().add(top))

def sub(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().sub(top))

def mul(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().mul(top))

def div(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().div(top))

def b_and(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().b_and(top))

def b_or(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().b_or(top))

def b_xor(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().b_xor(top))

def b_not(stack, heap):
    top = stack.pop()
    stack.push(stack.pop().b_not(top))

def pushvar(stack, heap, varname):
    stack.push(heap.lookup(varname))

def popvar(stack, heap, varname):
    heap.put(varname, stack.pop())

def pushnum(stack, heap, num):
    stack.push(Number(num))

def pushstr(stack, heap, string):
    stack.push(String(string))

def dup(stack, heap, num):
    value = stack.peek()
    for i in range(num):
        stack.push(value)

def pop(stack, heap, num):
    if not num:
        num = 1
    for i in range(num):
        stack.pop()

def makelist(stack, heap):
    lst = []
    num = stack.pop()
    for i in range(num):
        lst.push(stack.pop())
    stack.push(List(lst))

RNG = Random()

def seed(stack, heap):
    RNG.seed(stack.pop().toNumber())

def rand(stack, heap):
    stack.push(Number(RNG.random()))

def lt(stack, heap):
    top = stack.pop()
    if stack.pop().lt(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def lte(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.lt(top) or bot.eq(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def gt(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.gt(top) or bot.eq(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def gte(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.gt(top) or bot.eq(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def eq(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.eq(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def ne(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.eq(top):
        stack.push(Number(0))
    else:
        stack.push(Number(1))

def lte(stack, heap):
    top = stack.pop()
    bot = stack.pop()
    if bot.lt(top) or bot.eq(top):
        stack.push(Number(1))
    else:
        stack.push(Number(0))

def length(stack, heap):
    top = stack.pop()
    if isinstance(top, Number):
        stack.push(Number(4))
    else:
        stack.push(Number(len(top.value)))

def goto(stack, heap, addr):
    return addr

def gotoif(stack, heap, addr):
    top = stack.pop()
    if top.truthy():
        return addr

def prnt(stack, heap):
    top = stack.pop()
    print(top.print())

def getv(stack, heap):
    index = stack.pop()
    obj = stack.peek()
    stack.push(obj.getValue(index))

def setv(stack, heap):
    value = stack.pop()
    index = stack.pop()
    obj = stack.peek()
    obj.setValue(index, value)

def savevar(stack, heap, name):
    heap.put(name, stack.peek())

def getinp(stack, heap):
    stack.push(String(input()))

def increment(stack, heap):
    stack.push(stack.pop().add(Number(1)))

def decrement(stack, heap):
    stack.push(stack.pop().sub(Number(1)))

def gettime(stack, heap):
    stack.push(Number(int(time()*1000)))

def power(stack, heap):
    exp = stack.pop()
    base = stack.pop()
    stack.push(base.pow(exp))

def do_floor(stack, heap):
    stack.push(stack.pop().floor())

def do_ceil(stack, heap):
    stack.push(stack.pop().ceil())
    