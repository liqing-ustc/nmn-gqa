#!/usr/bin/env python3

# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
Utilities for modify the programs of GQA.
"""

import re
from copy import deepcopy
from pprint import pprint
import bisect

def eliminate_obj_id(program):
    for op in program:
        if type(op['argument']) is list:
            continue
        argument = re.sub("\((([0-9]+(,[0-9]+)*)|[-])\)", "",op['argument'])
        argument = argument.replace(',', '|').split('|')
        argument = [x.strip() for x in argument]
        op['argument'] = [x for x in argument if x != '']
    return program

if __name__ == '__main__':
    ### Test ###
    program = [{'argument': 'animal (757652,757650,3885555)', 'dependencies': [], 'operation': 'select'},
            {'argument': 'not(wood)', 'dependencies': [0], 'operation': 'filter material'},
            {'argument': '?', 'dependencies': [1], 'operation': 'exist'},
            {'argument': 'baseball bat (-) ', 'dependencies': [], 'operation': 'select'},
            {'argument': 'not(wood)', 'dependencies': [3], 'operation': 'filter material'},
            {'argument': '?', 'dependencies': [4], 'operation': 'exist'},
            {'argument': '', 'dependencies': [2, 5], 'operation': 'or'}]


    pprint(program)
    program = eliminate_obj_id(program)
    print()
    pprint(program)

def update_dependencies(dependencies, insert_nodes):
    if len(insert_nodes) == 0:
        return dependencies
    
    new_dependencies = []
    for dep in dependencies:
        #dep += sum([dep>=x for x in insert_nodes])
        dep += bisect.bisect_right(insert_nodes, dep)
        new_dependencies.append(dep)
    return new_dependencies

# Modify 'relate'
def modify_relate(program):
    new_program = []
    insert_nodes = [] # if we add more op into the program, we need to change the dependencies correspondingly.
    for idx, op in enumerate(program):
        op = deepcopy(op)
        op['dependencies'] = update_dependencies(op['dependencies'], insert_nodes)
        if op['operation'] != 'relate':
            new_program.append(op)          
        else:
            assert len(op['argument']) == 3
            
            new_op = deepcopy(op)
            new_op['operation'] = 'relocate'
            new_op['argument'] = op['argument'][1:]
            new_program.append(new_op)
            
            if op['argument'][0] != '_':
                new_op = {'operation': 'filter', 'argument': op['argument'][:1]}
                new_op['dependencies'] = [len(new_program)-1]
                insert_nodes.append(idx)
                new_program.append(new_op)
    
    return new_program

if __name__ == '__main__':
    ### Test ###
    dependencies = [1, 4, 6]
    insert_nodes = [2, 4, 7]
    print(update_dependencies(dependencies, insert_nodes))

    program = [
     {'argument': 'food (2386313)', 'dependencies': [], 'operation': 'select'},
     {'argument': 'not(small)', 'dependencies': [0], 'operation': 'filter size'},
     {'argument': '_,to the right of,s (3445544)', 'dependencies': [1], 'operation': 'relate'},
     {'argument': 'napkins,to the right of,s (3445544)', 'dependencies': [1], 'operation': 'relate'},
     {'argument': '?', 'dependencies': [1], 'operation': 'exist'},
     {'argument': '?', 'dependencies': [2], 'operation': 'exist'},
    {'argument': '?', 'dependencies': [4], 'operation': 'exist'}]


    program = eliminate_obj_id(program)
    new_program = modify_relate(program)

    pprint(program)
    print()
    pprint(new_program)

def modify_verify(program):
    new_program = []
    insert_nodes = [] # if we add more op into the program, we need to change the dependencies correspondingly.
    for idx, op in enumerate(program):
        op = deepcopy(op)
        op['dependencies'] = update_dependencies(op['dependencies'], insert_nodes)
        if 'verify' not in op['operation']:
            new_program.append(op)          
        else:
            if op['operation'] == 'verify rel':
                new_op = {'operation': 'relate'}
                new_op['argument'] = op['argument']
                new_op['dependencies'] = op['dependencies']
                new_program.append(new_op)
            else:
                new_op = {'operation': 'filter'}
                new_op['argument'] = op['argument']
                new_op['dependencies'] = op['dependencies']
                new_program.append(new_op)

            new_op = {'operation': 'exist'}
            new_op['argument'] = ['?']
            new_op['dependencies'] = [len(new_program) - 1]
            insert_nodes.append(idx)
            new_program.append(new_op)

    return new_program

if __name__ == '__main__':
    program = \
    [{'argument': 'knife (1337182)', 'dependencies': [], 'operation': 'select'},
 {'argument': 'pizza,on,o (-)', 'dependencies': [0], 'operation': 'verify rel'}]

    print()
    program = eliminate_obj_id(program)
    pprint(program)
    print()
    program = modify_verify(program)
    pprint(program)

# Modify 'choose'
def modify_choose(program):
    new_program = []
    insert_nodes = [] # if we add more op into the program, we need to change the dependencies correspondingly.
    for idx, op in enumerate(program):
        op = deepcopy(op)
        op['dependencies'] = update_dependencies(op['dependencies'], insert_nodes)    
        if 'choose' in op['operation']:
            if len(op['argument']) == 2:
                for arg in op['argument']:
                    new_op = {'operation': 'verify'}
                    new_op['argument'] = [arg]
                    new_op['dependencies'] = op['dependencies']
                    insert_nodes.append(idx)
                    new_program.append(new_op)
                    
            elif len(op['argument']) == 4:
                assert op['operation'] == 'choose rel'
                for arg in op['argument'][1:3]:
                    new_op = {'operation': 'verify rel'}
                    new_op['argument'] = [op['argument'][0], arg, op['argument'][3]]
                    new_op['dependencies'] = op['dependencies']
                    insert_nodes.append(idx)
                    new_program.append(new_op)
                op['argument'] = op['argument'][1:3]
            
            elif len(op['argument']) == 0: # 'choose healthier/less healthy/older/younger'
                op['argument'] = [new_program[dep]['argument'][0] for dep in op['dependencies']]
                tmp = {'choose healthier': 'healthy', 'choose less healthy': 'unhealthy',
                       'choose older': 'old', 'choose younger': 'young',
                       'choose taller': 'tall',
                       'choose higher': 'high', 'choose lower': 'low',
                       'choose larger': 'large', 'choose smaller': 'small',
                       'choose longer': 'long', 'choose shorter': 'short'
                       }
                arg = tmp[op['operation']]
                for dep in op['dependencies']:
                    new_op = {'operation': 'verify'}
                    new_op['argument'] = [arg]
                    new_op['dependencies'] = [dep]
                    insert_nodes.append(idx)
                    new_program.append(new_op)
                
            else:
                assert False
            
            new_op = deepcopy(op)
            new_op['operation'] = 'choose'
            new_op['dependencies'] = [len(new_program) - 2, len(new_program) - 1]
            new_program.append(new_op)
        
        else:
            new_program.append(op)
            
    return new_program

if __name__ == '__main__':
    program = [{'argument': 'coffee (1832036)', 'dependencies': [], 'operation': 'select'},
     {'argument': 'right', 'dependencies': [0], 'operation': 'filter hposition'},
     {'argument': 'napkin,to the left of|to the right of,s (1861257)',
      'dependencies': [1],
      'operation': 'choose rel'}]

    program = eliminate_obj_id(program)
    pprint(program)
    program = modify_choose(program)
    program = modify_verify(program)
    program = modify_relate(program)
    pprint(program)


# Modify 'different' / 'same' to 'compare
def modify_diff_same(program):
    new_program = []
    insert_nodes = [] # if we add more op into the program, we need to change the dependencies correspondingly.
    for idx, op in enumerate(program):
        op = deepcopy(op)
        op['dependencies'] = update_dependencies(op['dependencies'], insert_nodes)
        if 'different' not in op['operation'] and 'same' not in op['operation']:
            new_program.append(op)          
        else:
            if len(op['dependencies']) == 1:
                assert len(op['argument']) == 1
                new_op = {}
                new_op['operation'] = 'compare'
                new_op['argument'] = [op['operation']] + op['argument']
                new_op['dependencies'] = op['dependencies']
                new_program.append(new_op)

            elif len(op['dependencies']) == 2:
                assert len(op['argument']) == 0
                new_op = {}
                new_op['operation'] = 'attentionor'
                new_op['argument'] = []
                new_op['dependencies'] = op['dependencies']
                insert_nodes.append(idx)
                new_program.append(new_op)

                new_op = {}
                new_op['operation'] = 'compare'
                new_op['argument'] = op['operation'].split(' ')
                new_op['dependencies'] = [len(new_program) - 1]
                new_program.append(new_op)

            else:
                assert False, 'Unseen dependencies'
            
    
    return new_program

if __name__ == '__main__':
    program = \
    [{'argument': ['book'], 'dependencies': [], 'operation': 'select'},
     {'argument': ['cap'], 'dependencies': [], 'operation': 'select'},
     {'argument': [], 'dependencies': [0, 1], 'operation': 'same color'}]

    program = eliminate_obj_id(program)
    pprint(program)
    program = modify_choose(program)
    program = modify_diff_same(program)
    program = modify_relate(program)
    pprint(program)

def modify_filter(program):
    new_program = []
    insert_nodes = [] # if we add more op into the program, we need to change the dependencies correspondingly.
    for idx, op in enumerate(program):
        op = deepcopy(op)
        op['dependencies'] = update_dependencies(op['dependencies'], insert_nodes)
        if 'filter' not in op['operation']:
            new_program.append(op)          
        else:
            assert len(op['argument']) == 1 and len(op['dependencies']) == 1
            arg = op['argument'][0]
            has_not = False
            if arg.startswith('not(') and arg.endswith(')'):
                arg = arg[4:-1]
                has_not = True

            new_op = {'operation': 'select'}
            new_op['argument'] = [arg]
            new_op['dependencies'] = []
            insert_nodes.append(idx)
            new_program.append(new_op)

            if has_not:
                new_op = {'operation': 'attentionnot'}
                new_op['argument'] = []
                new_op['dependencies'] = [len(new_program)-1]
                insert_nodes.append(idx)
                new_program.append(new_op)

            new_op = {'operation': 'attentionand'}
            new_op['argument'] = []
            new_op['dependencies'] = [op['dependencies'][0], len(new_program) - 1]
            new_program.append(new_op)

    return new_program

if __name__ == '__main__':
    program = \
    [{'argument': 'bat (1261273)', 'dependencies': [], 'operation': 'select'},
    {'argument': 'not(wood)', 'dependencies': [0], 'operation': 'filter material'},
    {'argument': '?', 'dependencies': [1], 'operation': 'exist'},
    {'argument': 'baseball bat (-) ', 'dependencies': [], 'operation': 'select'},
    {'argument': 'not(wood)', 'dependencies': [3], 'operation': 'filter material'},
    {'argument': '?', 'dependencies': [4], 'operation': 'exist'},
    {'argument': '', 'dependencies': [2, 5], 'operation': 'or'}]

    print()
    program = eliminate_obj_id(program)
    pprint(program)
    print()
    program = modify_choose(program)
    program = modify_diff_same(program)
    program = modify_relate(program)
    program = modify_filter(program)
    pprint(program)

def update_program(questions):
    for q in questions:
        for k in ['equivalent', 'entailed', 'isBalanced', 'groups', 
                    'semanticStr', 'annotations', 'types', 'fullAnswer']:
            if k in q:
                del q[k]

        program = q['semantic']
        program = eliminate_obj_id(program)
        program = modify_choose(program)
        program = modify_diff_same(program)
        program = modify_verify(program)
        program = modify_relate(program)
        program = modify_filter(program)
        q['semantic'] = program