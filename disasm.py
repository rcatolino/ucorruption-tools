#!/usr/bin/python3

import argparse

# cf http://mspgcc.sourceforge.net/manual/x223.html
registers = ['pc', 'sp', 'sr', 'cg', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'r11',
             'r12', 'r13', 'r14', 'r15']
reg_mask = 0xf
byte_mask = 0x40
laddressing_mask = 0x30
haddressing_mask = 0x80

twoop_opc = ['mov', 'add', 'addc', 'subc', 'sub', 'cmp', 'dadd', 'bit', 'bic', 'bis',
             'xor', 'and']

oneop_flag = 0xfc
oneop_kind = 0x10
oneop_oph = 0x3
oneop_opl = 0x80
oneop_opc = ['rrc', 'swp', 'rra', 'sxt', 'push', 'call', 'ret', 'invalid']

jmp_kind = 0x20
jmp_flag = 0xe0
jmp_cond = 0x1c
jmp_pc = 0x3
jmp = ['jnz', 'jz', 'jnc', 'jc', 'jn', 'jge', 'jl', 'jmp']

class InvalidOpcodeError(Exception):
  def __init__(self, opcode):
    self.value = opcode

def jump(instruction, offset):
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  cond = (high & jmp_cond) >> 2
  pc = 2 * (1 + low + ((high & jmp_pc) << 8))
  return "{:#x}:\t{}\t\t{} pc{:+#x}".format(offset, instruction, jmp[cond], pc)

def swap(word):
  return word[2:] + word[:2]

def get_byte_mode(byte):
  if byte & byte_mask == byte_mask:
    return '.b'
  else:
    return ''

def oneop(instruction, operand, offset):
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  opcode = (high & oneop_oph) << 1
  opcode += (low & oneop_opl) >> 7
  byte_mode = get_byte_mode(low)
  addressing = (low & laddressing_mask) >> 4
  reg = low & reg_mask
  if addressing == 0x3:
    return (1, "{:#x}:\t{} {}\t{}{} #0x{}".format(offset, instruction, operand,
      oneop_opc[opcode], byte_mode, swap(operand)))
  elif addressing == 0x2:
    return (0, "{:#x}:\t{}\t\t{}{} @{}".format(offset, instruction, oneop_opc[opcode],
      byte_mode, registers[reg]))
  elif addressing == 0x1:
    return (1, "{:#x}:\t{} {}\t{}{} 0x{}({})".format(offset, instruction, operand,
      oneop_opc[opcode], byte_mode, swap(operand), registers[reg]))
  elif addressing == 0x0:
    return (0, "{:#x}:\t{}\t\t{}{} {}".format(offset, instruction, oneop_opc[opcode],
      byte_mode, registers[reg]))

def twoop(instruction, operands, offset):
  code = [instruction]
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  opcode = (high & 0xf0) >> 4
  if opcode-4 < 0:
    raise InvalidOpcodeError(opcode)

  src_reg = (high & reg_mask)
  dest_reg = (low & reg_mask)
  byte_mode = get_byte_mode(low)
  saddressing = (low & laddressing_mask) >> 4
  daddressing = (low & haddressing_mask) >> 7
  if saddressing == 0x0:
    code.append('\t')
    src = registers[src_reg]
  elif saddressing == 0x1:
    code.append(operands.pop())
    src = "0x{}({})".format(swap(code[1]), registers[src_reg])
  elif saddressing == 0x2:
    code.append('\t')
    src = "@{}".format(registers[src_reg])
  else:
    code.append(operands.pop())
    src = "#0x{}".format(swap(code[-1]))

  if daddressing == 0x0:
    code.append('\t')
    dest = registers[dest_reg]
  else:
    code.append(operands.pop())
    dest = "0x{}({})".format(swap(code[-1]), registers[dest_reg])
  return (2-len(operands), "{:#x}:\t{}\t{}{} {} {}".format(offset, " ".join(code),
    twoop_opc[opcode-4], byte_mode, src, dest))

def dis_line(leftovers, code, offset):
  opcodes = [code[i:i+4] for i in range(0, len(code)-1, 4)]
  i = 0
  listing = []
  while i != len(opcodes):
    next = opcodes[i]
    high = int(next[2:], 16)
    if  high & jmp_flag == jmp_kind:
      listing.append(jump(next, offset + i*4))
    elif i == len(opcodes) - 1:
      leftovers = [next]
    elif high & oneop_flag == oneop_kind:
      (c, res) = oneop(next, opcodes[i+1], offset + i*4)
      listing.append(res)
      i += c
    elif i == len(opcodes) - 2:
      leftovers = [next, opcodes[i+1]]
      i += 1
    else:
      try:
        (c, res) = twoop(next, [opcodes[i+1], opcodes[i+2]], offset + i*4)
        listing.append(res)
        i += c
      except InvalidOpcodeError as e:
        listing.append("{:#x}:\t{}\t\t invalid".format(offset + i*4, next))

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
