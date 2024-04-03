import os
import sys
import random
import datetime
import argparse
sys.path.insert(0, os.path.abspath('../utility'))
from graph_compiler import GraphCompiler 
from urdf_compiler import UrdfCompiler 
from test_robot_gen import *

def get_random_rule(rulelist, choice):
    applicable_rule = {}
    #print("choice = " + str(choice))
    for key in choice:
        if key not in rulelist:
            continue
        if len(choice[key]) != 0:
            applicable_rule[key] = choice[key]
    if len(applicable_rule) != 0:
        rulename = random.choice(list(applicable_rule.keys()))
        target = random.choice(applicable_rule[rulename])
    else:
        rulename = None
        target = None
    return rulename, target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Randomly generates a robot urdf file')
    parser.add_argument('-rn', '--robot_name', help='A robot_name with extension')
    parser.add_argument('--seed', help='An integer for random seed')
    parser.add_argument('--strnum', help='An integer for the number for the structure rule application')
    parser.add_argument('-o', '--outputdir', help='An output directory')

    args = parser.parse_args()
    if args.robot_name:
        robot_name = args.robot_name
    else:
        t_delta = datetime.timedelta(hours=9)
        jst = datetime.timezone(t_delta, 'JST')
        now = datetime.datetime.now(jst)
        robot_name = "robot_" + now.strftime('%Y%m%d%H%M%S')
    if args.seed:
        random.seed(int(args.seed))
        print("seed = " + args.seed)
    if args.outputdir:
        outputdir = args.outputdir
        if not outputdir.endswith('/'):
            outputdir += '/'
    else:
        outputdir = './'
    filename = outputdir + robot_name + '.urdf'
    if args.strnum:
        structure_rule_num = int(args.strnum)
    else:
        structure_rule_num = 10 



    print("\n[ STRUCTURE ]")
    g_robogrammar = GraphCompiler('./RoboGrammar.grammar')
    structure_rulelist = ['r' + str(i) for i in range(1, 8)]

    for i in range(structure_rule_num):
        choices = g_robogrammar.get_applicable_rule()
        rulename, target = get_random_rule(structure_rulelist, choices)
        if rulename is None:
            break
        print("[ RULE ] " + rulename + " [ TARGET ] " + str(target))
        g_robogrammar.apply_rule(rulename, target)

    print("\n[ COMPONENT-BASED ]")
    component_rulelist = ['r' + str(i) for i in range(8, 30)]

    try:
        while not g_robogrammar.is_sentence():
            #print("is sentence ? = " + str(g_robogrammar.is_sentence()))
            choices = g_robogrammar.get_applicable_rule()
            rulename, target = get_random_rule(component_rulelist, choices)
            if rulename is None:
                if not g_robogrammar.is_sentence():
                    print('Re-STRUCTURE RULE')
                    rulename, target = get_random_rule(structure_rulelist, choices)
                else:
                    break
            print("[ RULE ] " + rulename + " [ TARGET ] " + str(target))
            g_robogrammar.apply_rule(rulename, target)
    except TypeError as e:
        print(e)
        prompt(g_robogrammar)

    try:
        g_compiler = UrdfCompiler(
                    './Compiler.grammar',
                    './urdf', 
                    initial_graph=g_robogrammar.get_graph()
                    )
    except ValueError as e:
        print(e)
        print('EXIST NON-TERMINAL SYMBOL ERROR')
        print('REQUIRE MANUAL COMPILE')
        prompt(g_robogrammar)
        g_compiler = UrdfCompiler(
                    './Compiler.grammar',
                    './urdf', 
                    initial_graph=g_robogrammar.get_graph()
                    )

    try:
        g_compiler.generate_urdf(robot_name=robot_name, filename=filename)
        nx.write_gml(g_compiler.get_graph(), outputdir + 'result.gml')
    except ValueError as e:
        print(e)
        prompt(g_compiler)
    except KeyError as e:
        print(e)
        prompt(g_compiler)

