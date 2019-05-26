#!/usr/bin/env python3

# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
Utilities for working with and converting between the various data structures
used to represent programs.
"""


def is_chain(program_list):
  visited = [False for fn in program_list]
  cur_idx = len(program_list) - 1
  while True:
    visited[cur_idx] = True
    dependencies = program_list[cur_idx]['dependencies']
    if len(dependencies) == 0:
      break
    elif len(dependencies) == 1:
      cur_idx = dependencies[0]
    elif len(dependencies) > 1:
      return False
  return all(visited)


def list_to_tree(program_list):
  def build_subtree(cur):
    return {
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
      'dependencies': [build_subtree(program_list[i]) for i in cur['dependencies']],
    }
  return build_subtree(program_list[-1])


def tree_to_prefix(program_tree):
  output = []
  def helper(cur):
    output.append({
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
    })
    for node in cur['dependencies']:
      helper(node)
  helper(program_tree)
  return output


def list_to_prefix(program_list):
  return tree_to_prefix(list_to_tree(program_list))


def tree_to_postfix(program_tree):
  output = []
  def helper(cur):
    for node in cur['dependencies']:
      helper(node)
    output.append({
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
    })
  helper(program_tree)
  return output


def tree_to_list(program_tree):
  # First count nodes
  def count_nodes(cur):
    return 1 + sum(count_nodes(x) for x in cur['dependencies'])
  num_nodes = count_nodes(program_tree)
  output = [None] * num_nodes
  def helper(cur, idx):
    output[idx] = {
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
      'dependencies': [],
    }
    next_idx = idx - 1
    for node in reversed(cur['dependencies']):
      output[idx]['dependencies'].insert(0, next_idx)
      next_idx = helper(node, next_idx)
    return next_idx
  helper(program_tree, num_nodes - 1)
  return output


def prefix_to_tree(program_prefix):
  program_prefix = [x for x in program_prefix]
  def helper():
    cur = program_prefix.pop(0)
    return {
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
      'dependencies': [helper() for _ in range(get_num_dependencies(cur))],
    }
  return helper()


def prefix_to_list(program_prefix):
  return tree_to_list(prefix_to_tree(program_prefix))


def list_to_postfix(program_list):
  return tree_to_postfix(list_to_tree(program_list))


def postfix_to_tree(program_postfix):
  program_postfix = [x for x in program_postfix]
  def helper():
    cur = program_postfix.pop()
    return {
      'operation': cur['operation'],
      'argument': [x for x in cur['argument']],
      'dependencies': [helper() for _ in range(get_num_dependencies(cur))][::-1],
    }
  return helper()


def postfix_to_list(program_postfix):
  return tree_to_list(postfix_to_tree(program_postfix))


def operation_to_str(f):
  value_str = ''
  if f['argument']:
    value_str = '[%s]' % ','.join(f['argument'])
  return '%s%s' % (f['operation'], value_str)


def str_to_operation(s):
  if '[' not in s:
    return {
      'operation': s,
      'argument': [],
    }
  name, value_str = s.replace(']', '').split('[')
  return {
    'operation': name,
    'argument': value_str.split(','),
  }


def list_to_str(program_list):
  return ' '.join(operation_to_str(f) for f in program_list)


def get_num_dependencies(f):
  # This is a litle hacky; it would be better to look up from metadata.json
  if type(f) is str:
    f = str_to_operation(f)
  name = f['operation']
  if name == 'scene':
    return 0
  if 'equal' in name or name in ['union', 'intersect', 'less_than', 'greater_than']:
    return 2
  return 1
