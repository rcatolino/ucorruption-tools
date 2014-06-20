#!/usr/bin/python3

import argparse

def get_args():
  parser = argparse.ArgumentParser('Disassemble an msp430 binary')
  parser.add_argument('input', type=argparse.FileType('r'), help='binary to disassemble')
  parser.add_argument('-o', '--offset', default = 0x10, type=int, help='offset at which to start disassembly')
  args = parser.parse_args()
  return (args.input, args.offset)

def main():
  (input, offset) = get_args()

main()
