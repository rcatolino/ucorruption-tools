#!/usr/bin/python3

import argparse

# cf http://mspgcc.sourceforge.net/manual/x223.html
registers = ['pc', 'sp', 'sr', 'cg', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'r11',
             'r12', 'r13', 'r14', 'r15']

oneop_flag = 0xfc
oneop_kind = 0x10
oneop_oph = 0x3
oneop_opl = 0x80
oneop_byte = 0x40
oneop_reg = 0xf
oneop_addressing = 0x30
oneop_opc = ['rrc', 'swp', 'rra', 'sxt', 'push', 'call', 'ret', 'invalid']

jmp_kind = 0x20
jmp_flag = 0xe0
jmp_cond = 0x1c
jmp_pc = 0x3
jmp = ['jnz', 'jz', 'jnc', 'jc', 'jn', 'jge', 'jl', 'jmp']

def jump(instruction):
  cond = (instruction[0] & jmp_cond) >> 2
  pc = 2 * (1 + instruction[1] + ((instruction[0] & jmp_pc) << 8))
  return "{} pc{:+#x}".format(jmp[cond], pc)

def oneop(instruction, operand):
  opcode = (instruction[0] & oneop_oph) << 1
  opcode += (instruction[1] & oneop_opl) >> 7
  if instruction[1] & oneop_byte == oneop_byte:
    op_byte = '.b'
  else:
    op_byte = ''
  addressing = (instruction[1] & oneop_addressing) >> 4
  reg = instruction[1] & oneop_reg
  print(addressing)
  if addressing == 0x3:
    return (1, "{}{} #{:#02x}{:02x}".format(oneop_opc[opcode], op_byte, operand[0], operand[1]))
  elif addressing == 0x0:
    return (0, "{}{} {}".format(oneop_opc[opcode], op_byte, registers[reg]))


def dis_line(leftovers, code, offset):
  opcodes = [[int(code[i+2:i+4], 16), int(code[i:i+2], 16)] for i in range(0, len(code)-1, 4)]
  i = 0
  listing = []
  while i != len(opcodes):
    next = opcodes[i]
    if next[0] & jmp_flag == jmp_kind:
      listing.append("{:#x}:\t{:02x}{:02x}\t\t{}".format(offset + 2*i, next[1],
                                                         next[0], jump(next)))
    elif i == len(opcodes) - 1:
      leftovers = [next]
    elif next[0] & oneop_flag == oneop_kind:
      (c, res) = oneop(next, opcodes[i+1])
      listing.append("{:#x}:\t{} {}\t{}".format(offset + 2*i, code[i*4:(i+1)*4],
                                                code[i*4+4:i*4+8], res))
      i += c

    i += 1

  return (leftovers, listing)

def get_args():
  parser = argparse.ArgumentParser('Disassemble an msp430 binary')
  parser.add_argument('input', type=argparse.FileType('r'), help='binary to disassemble')
  parser.add_argument('-o', '--offset', default = 0x00, type=int,
                      help='offset at which to start disassembly')
  args = parser.parse_args()
  return (args.input, args.offset)

def main():
  (inp, offset) = get_args()
  if offset % 0x2 != 0:
    print("Offset must be aligned on a 2 byte boundary")
    return

  leftovers = []
  disassembly = []
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

    print('\n'.join(disassembly))

main()
