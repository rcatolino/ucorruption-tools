#!/usr/bin/python3

import argparse

def dis_line(leftovers, code):
  opcodes = [code[i:i+4] for i in range(0, len(code)-1, 4)]
  for opc in opcodes:
    print(opcodes, leftovers)
  return (opcodes, '')

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
      (leftovers, disassembly) = dis_line(leftovers, code[offset - loffset:])
    else:
      (leftovers, disassembly) = dis_line(leftovers, code)

main()
