#!/usr/bin/env python3

import re
import operator
import itertools
import collections

Instruction = collections.namedtuple('Instruction', ['addr', 'op', 'target'])

def translate(vaddr_str):
    vaddr = int(vaddr_str, base=16)
    if 0x80000000 <= vaddr <= 0x9FFFFFFF:
        addr = vaddr - 0x80000000
    elif 0xA0000000 <= vaddr <= 0xBFFFFFFF:
        addr = vaddr - 0xA0000000
    else:
        raise ValueError(vaddr_str)
    return addr

def unique(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    # unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
    # unique_justseen('ABBCcAD', str.lower) --> A B C A D
    return map(next, map(operator.itemgetter(1), itertools.groupby(iterable, key)))

def run(strategy, target):
    with open(f'{target}/{target}.si') as fp:
        content = fp.read()

    def convert(raw):
        addr, op, target = raw
        addr = translate(addr)
        target = translate(target)
        return addr, Instruction(addr=addr, op=op, target=target)

    pattern = '([0-9a-f]{8}):\s[0-9a-f]{8}\s+([bj][a-z]*).+([0-9a-f]{8})'
    branch = dict(map(convert, re.findall(pattern, content)))

    with open(f'{target}/{target}.txt') as fp:
        content = fp.read()

    pattern = '([0-9a-f]{8}),[0-9a-f],[0-9a-f]{2},[0-9a-f]{8}'
    pc = list(unique(map(translate, re.findall(pattern, content))))

    p = strategy()
    branch_count = [0, 0]
    correct_count = 0
    for i, addr in enumerate(pc):
        if addr not in branch:
            continue
        if i + 2 >= len(pc):
            # print(i)
            continue

        instr = branch[addr]
        taken = instr.target == pc[i + 2]
        branch_count[int(taken)] += 1
        if taken == p.predict(instr):
            correct_count += 1
        p.update(instr, taken)

    return branch_count, correct_count

def evaluate(strategy):
    tests = [
        'bitcount', 'bubble_sort', 'coremark', 'crc32', 'dhrystone',
        'quick_sort', 'select_sort', 'sha', 'stream_copy', 'stringsearch'
    ]

    sum_correct_count = 0
    sum_branch_count = 0
    for test in tests:
        branch_count, correct_count = run(strategy, test)
        accuracy = correct_count / sum(branch_count)
        print(f'{format(test, "15s")}{format(100 * accuracy, "-5.2f")}%, {branch_count}')
        sum_correct_count += correct_count
        sum_branch_count += sum(branch_count)

    accuracy = sum_correct_count / sum_branch_count
    print(f'{format("(avg.)", "15s")}{format(100 * accuracy, "-5.2f")}%')

class AlwaysTaken:
    def __init__(self):
        pass

    def predict(self, instr: Instruction) -> bool:
        return True

    def update(self, instr: Instruction, taken: bool):
        pass

class AlwaysNotTaken:
    def __init__(self):
        pass

    def predict(self, instr: Instruction) -> bool:
        return False

    def update(self, instr: Instruction, taken: bool):
        pass

class BackwardsTakenForwardsNotTaken:
    def __init__(self):
        pass

    def predict(self, instr: Instruction) -> bool:
        return instr.target <= instr.addr

    def update(self, instr: Instruction, taken: bool):
        pass

class XuYipei652e5766:
    '''@master 652e57666ec4ec09a5505541120e3627cca6eabb'''

    def __init__(self, n = 64):
        self.mask = 0x3f
        self.shamt = 8
        self.bpb = [0] * n
        self.tag = [None] * n

    def predict(self, instr: Instruction) -> bool:
        index = (instr.addr >> 2) & self.mask
        tag = instr.addr >> self.shamt

        if self.tag[index] != tag:
            self.tag[index] = tag
            self.bpb[index] = 0b01
        return self.bpb[index] > 1

    def update(self, instr: Instruction, taken: bool):
        index = (instr.addr >> 2) & self.mask
        tag = instr.addr >> self.shamt
        assert self.tag[index] == tag

        v = self.bpb[index]
        if taken:
            v += 1
        else:
            v -= 1
        if v > 3:
            v = 3
        if v < 0:
            v = 0
        self.bpb[index] = v

strategies = [
    XuYipei652e5766,
    AlwaysTaken,
    AlwaysNotTaken,
    BackwardsTakenForwardsNotTaken
]

for strategy in strategies:
    print(f'# {strategy.__name__}')
    evaluate(strategy)
    print("")