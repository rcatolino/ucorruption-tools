#!/usr/bin/python3

import argparse

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('input', type=argparse.FileType('r'))
  parser.add_argument('output', type=argparse.FileType('wb'))
  args = parser.parse_args()
  input = args.input
  output = args.output

  for line in input.readlines():
    index = 0
    splited = [line[i:i+2] for i in range(0, len(line)-1, 2)]
    output.write(bytearray(map(lambda x: int(x, 16), splited)))

main()
