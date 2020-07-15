import copy
from collections import Counter

def translate(vaddr_str):
    vaddr = int(vaddr_str, base=16)
    if 0x80000000 <= vaddr <= 0x9FFFFFFF:
        addr = vaddr - 0x80000000
    elif 0xA0000000 <= vaddr <= 0xBFFFFFFF:
        addr = vaddr - 0xA0000000
    else:
        raise ValueError(vaddr_str)
    return '{:08x}'.format(addr)

# 读取每一行一开始的 PC 值，返回一个列表
def read_instructions(fp):
    return [
        translate(line.split(':')[0])
        for line in fp
        if ':' in line
    ]

# 指定测试点
target_name = 'stream_copy'
target = f'{target_name}/{target_name}'

lw_file_fp = open(f'{target}.lw', 'r')
sw_file_fp = open(f'{target}.sw', 'r')
trace_fp = open(f'{target}.txt', 'r')

traces = list(map(lambda x: x.split(','), trace_fp.read().split('\n')))

# 使用 .sw 和 .lw 文件来辅助判断某条指令是不是 lw/sw
# 因为 trace 中只会记录指令的 PC，而不会记录指令的编码，
# 所以我们只能利用反汇编文件，用 PC 找到对应的指令是谁，
# 从而确定是不是 lw/sw。
sw_list = read_instructions(sw_file_fp)
lw_list = read_instructions(lw_file_fp)
sw_set = set(sw_list)
lw_set = set(lw_list)

x1faf_read_count = 0
x1faf_write_count = 0
x1fc_read_count = 0
x1fc_write_count = 0
instr_count = 0
sw_count = 0
lw_count = 0

last_vaddr = None
for rec in traces:
    if len(rec) == 1:
        continue
    elif len(rec) == 2:
        addr, channel = rec
        if addr.startswith('1faf'):
            if channel == 'aw':
                x1faf_write_count += 1
            else:
                x1faf_read_count += 1
        elif addr.startswith('1fc'):
            if channel == 'aw':
                x1fc_write_count += 1
            else:
                x1fc_read_count += 1
        else:
            raise RuntimeError(f'AXI: {addr}')
    else:
        vaddr, write_en, reg_num, data = rec
        if vaddr == last_vaddr:
            continue
        last_vaddr = vaddr
        instr_count += 1

        paddr = translate(vaddr)
        if paddr in sw_set:
            sw_count += 1
        elif paddr in lw_set:
            lw_count += 1

# 打印所有 *_count 变量
local_map = copy.copy(locals())
for key, value in local_map.items():
    if key.endswith('count'):
        print(f'{key}: {value}')
del local_map

axi_count = x1faf_read_count + x1faf_write_count + x1fc_read_count + x1fc_write_count
print(f'axi_count = {axi_count}')

cpu_count = instr_count + sw_count + lw_count
print(f'cpu_count = {cpu_count}')

diff = axi_count - cpu_count
print(f'diff = {diff}')