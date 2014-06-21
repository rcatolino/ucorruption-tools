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
oneop_opc = ['rrc', 'swp', 'rra', 'sxt', 'push', 'call', 'reti', 'invalid']

jmp_kind = 0x20
jmp_flag = 0xe0
jmp_cond = 0x1c
jmp_pc = 0x3
jmp = ['jnz', 'jz', 'jnc', 'jc', 'jn', 'jge', 'jl', 'jmp']

class InstructionStream:
  offset = 0
  def __init__(self, inp):
    self.inp = inp
    self.lines = iter(inp)
    self.next_line()

  def next_line(self):
    while True:
      [loffset, code] = self.lines.__next__().split(':', 1)
      self.offset = int(loffset, 16) - 2
      if code[0] == '*':
        continue
      break

    self.words = [code[i:i+4] for i in range(0, len(code)-1, 4)].__iter__()

  def get_word_and_offset(self):
    return (self.get_word(), self.offset)

  def get_word(self):
    try:
      word = self.words.__next__()
    except StopIteration:
      self.next_line()
      word = self.words.__next__()

    self.offset += 2
    return word

class InvalidOpcodeError(Exception):
  def __init__(self, opcode):
    self.value = opcode

def jump(instruction, offset):
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  cond = (high & jmp_cond) >> 2
  pc = 2 * (1 + low + ((high & jmp_pc) << 8))
  return "{:#x}:\t{}\t\t{} ${:+#x}".format(offset, instruction, jmp[cond], pc)

def swap(word):
  return word[2:] + word[:2]

def get_byte_mode(byte):
  if byte & byte_mask == byte_mask:
    return '.b'
  else:
    return ''

def addressing_fmt(kind, reg, word):
  if reg == 2 and kind == 0x1:
    return "&0x{}".format(swap(word))
  elif reg == 2 and kind == 0x2:
    return "#0x04"
  elif reg == 2 and kind == 0x3:
    return "#0x08"
  elif reg == 3 and kind == 0x0:
    return "#0x00"
  elif reg == 3 and kind == 0x1:
    return "#0x01"
  elif reg == 3 and kind == 0x2:
    return "#0x02"
  elif reg == 3 and kind == 0x3:
    return "#-0x01"
  elif kind == 0x0:
    return registers[reg]
  elif kind == 0x1:
    return "0x{}({})".format(swap(word), registers[reg])
  elif kind == 0x2:
    return "@{}".format(registers[reg])
  elif reg == 0:
    return "#0x{}".format(swap(word))
  else:
    return "@{}+".format(registers[reg])

def oneop(instruction, stream, offset):
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  opcode = (high & oneop_oph) << 1
  opcode += (low & oneop_opl) >> 7
  byte_mode = get_byte_mode(low)
  addressing = (low & laddressing_mask) >> 4
  reg = low & reg_mask
  operand = "    "
  if addressing == 0x1 or (addressing == 0x3 and reg == 0):
    operand = stream.get_word()

  dst = addressing_fmt(addressing, reg, operand)
  return "{:#x}:\t{} {}\t{}{} {}".format(offset, instruction, operand,
    oneop_opc[opcode], byte_mode, dst)

def twoop(instruction, stream, offset):
  code = [instruction]
  high = int(instruction[2:], 16)
  low = int(instruction[:2], 16)
  opcode = (high & 0xf0) >> 4
  if opcode-4 < 0:
    raise InvalidOpcodeError(opcode)
  elif instruction == '3041':
    return "{:#x}:\t3041            ret".format(offset)

  src_reg = (high & reg_mask)
  dest_reg = (low & reg_mask)
  byte_mode = get_byte_mode(low)
  saddressing = (low & laddressing_mask) >> 4
  daddressing = (low & haddressing_mask) >> 7
  code = [instruction]
  if saddressing == 0x1 or (saddressing == 0x3 and src_reg == 0):
    code.append(stream.get_word())

  src = addressing_fmt(saddressing, src_reg, code[-1])
  if daddressing == 0x1:
    code.append(stream.get_word())

  dest = addressing_fmt(daddressing, dest_reg, code[-1])
  while len(code) != 3:
    code.append("    ")

  return "{:#x}:\t{}\t{}{} {}, {}".format(offset, " ".join(code),
    twoop_opc[opcode-4], byte_mode, src, dest)

def process(word, offset, stream):
  high = int(word[2:], 16)
  if  high & jmp_flag == jmp_kind:
    print(jump(word, offset))
  elif high & oneop_flag == oneop_kind:
    print(oneop(word, stream, offset))
  else:
    try:
      print(twoop(word, stream, offset))
    except InvalidOpcodeError as e:
      print("{:#x}:\t{}\t\tinvalid".format(offset, word))

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

  istream = InstructionStream(inp)
  while True:
    try:
      (next, offset) = istream.get_word_and_offset()
      process(next, offset, istream)
    except StopIteration:
      break

main()
