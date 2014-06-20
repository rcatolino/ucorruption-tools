#!/usr/bin/python3

import argparse

oneop_flag = 0xfc
oneop_kind = 0x10

jmp_kind = 0x20
jmp_flag = 0xe0
jmp_cond = 0x1c
jmp_pc = 0x3
jmp = ['jnz', 'jz', 'jnc', 'jc', 'jn', 'jge', 'jl', 'jmp']

def jump(opc):
  cond = (opc[0] & jmp_cond) >> 2
  pc = 2 * ((opc[0] & jmp_pc << 8) + opc[1]) + 2
  return "{} pc{:+#x}".format(jmp[cond], pc)

def dis_line(leftovers, code, offset):
  opcodes = [[int(code[i+2:i+4], 16), int(code[i:i+2], 16)] for i in range(0, len(code)-1, 4)]
  i = 0
  while i != len(opcodes):
    next = opcodes[i]
    if next[0] & jmp_flag == jmp_kind:
      print("{:#x}:\t{}".format(offset + 2*i, jump(next)))
#    if next[0] == oneop_kind:
#      return oneop(next, opcodes[i+1])
    i += 1

  return (leftovers, '')

def get_args():
  parser = argparse.ArgumentParser('Disassemble an msp430 binary')
  parser.add_argument('input', type=argparse.FileType('r'), help='binary to disassemble')
  parser.add_argument('-o', '--offset', default = 0x00, type=int, help='offset at which to start disassembly')
  args = parser.parse_args()
  return (args.input, args.offset)

def main():
  (inp, offset) = get_args()
  if offset % 0x2 != 0:
    print("Offset must be aligned on a 2 byte boundary")
    return

  leftovers = []
  for line in inp:
    [loffset, code] = line.split(':', 1)
    loffset = int(loffset, 16)
    if code[0] == '*':
      if len(leftovers) != 0:
        # Use 0 as arguments.
        print(leftovers)
      continue

    if offset - loffset > 0x10:
      continue
    elif loffset <= offset:
      (leftovers, disassembly) = dis_line(leftovers, code[offset - loffset:], offset)
    else:
      (leftovers, disassembly) = dis_line(leftovers, code, loffset)

main()
