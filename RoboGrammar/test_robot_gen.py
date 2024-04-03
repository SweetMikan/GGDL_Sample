import os
import sys
import matplotlib.pyplot as plt
import networkx as nx
import math
sys.path.insert(0, os.path.abspath('../utility'))
from graph_compiler import GraphCompiler 
from decorated_print import DecoratedPrint as dc

color = dc.yellow

def rot(theta, v):
    ct = math.cos(theta)
    st = math.sin(theta)
    nv1 = ct*v[0] - st*v[1]
    nv2 = st*v[0] + ct*v[1]
    return (nv1, nv2)

def mypos(graph, length):
    node_pos = {}
    node_list = list(graph.nodes())
    while len(node_list) != 0:
        node = node_list[0]
        node_list = node_list[1:]
        if node not in node_pos:
            x, y, th = (0, 0, 0)
            node_pos[node] = (x, y, th)
        else:
            x, y, th = node_pos[node]
        from_nodes = [edge[0] for edge in graph.in_edges(node)]
        to_nodes = [edge[1] for edge in graph.out_edges(node)]
        num = len(from_nodes)
        unit = math.pi / (num + 1)
        lc_th = 0
        #if num % 2 != 0:
        #   lc_th = 0
        #else:
        #   lc_th = unit / 2
        for lc_node in from_nodes:
            if lc_node not in node_pos:
                print(rot(lc_th, (length,0)))
                lc_x, lc_y = rot(lc_th, (length,0))
                new_x, new_y = rot(th, (lc_x, lc_y))
                new_x += x
                new_y += y
                new_th = th + lc_th
                node_pos[lc_node] = (new_x, new_y, new_th)
            lc_th += unit
            #if lc_th > 0:
            #   lc_th = -lc_th
            #else:
            #   lc_th = -lc_th + unit
        num = len(to_nodes)
        unit = math.pi / (num + 1)
        lc_th = 0
        #if num % 2 != 0:
        #    lc_th = 0
        #else:
        #    lc_th = unit / 2
        for lc_node in to_nodes:
            if lc_node not in node_pos:
                print(rot(lc_th, (length,0)))
                lc_x, lc_y = rot(lc_th + math.pi, (length,0))
                new_x, new_y = rot(th, (lc_x, lc_y))
                new_th = th + lc_th + math.pi
                node_pos[lc_node] = (new_x, new_y, new_th)
            lc_th += unit
            #if lc_th > 0:
            #    lc_th = -lc_th
            #else:
            #    lc_th = -lc_th + unit
    return {k: (v[0], v[1]) for k, v in node_pos.items()}

def load_gml(filepath):
    g = nx.read_gml(filepath)
    old_nodes = list(g.nodes())
    g.add_nodes_from([(int(node_id), attribute) 
        for node_id, attribute in g.nodes(True)])

    g.add_edges_from([(int(edge[0]), int(edge[1]), edge[2])
        for edge in g.edges(data=True)])
    g.remove_nodes_from(old_nodes)
    return g
        

def input_and_parse(choices):
    str_list = input('>> ').split()
    errorp = False
    if str_list[0] == 'end' or str_list[0] == 'exit':
        cmd = 'end'
        arg = None
    elif str_list[0] == 'show':
        cmd = 'show'
        arg = None
    elif str_list[0] == 'pool':
        cmd = 'pool'
        arg = None
    elif str_list[0] == 'node':
        cmd = 'node'
        arg = None
    elif str_list[0] == 'edge':
        cmd = 'edge'
        if len(str_list) > 1:
            arg = True
        else:
            arg = False
    elif str_list[0] == 'choice':
        cmd = 'choice'
        arg = None
    elif str_list[0] == 'save':
        if len(str_list) > 1:
            cmd = 'save'
            arg = str_list[1]
        else:
            errorp = True
            dc.deco_print("<Error: No file path>", color)
    elif str_list[0] in choices:
        if len(str_list) > 1:
            if str_list[1].isdigit():
                cmd = 'apply'
                arg = (str_list[0], int(str_list[1]))
            else:
                errorp = True
                dc.deco_print("<Error: Invalid Argument>", color)
        else:
            errorp = True
            dc.deco_print("<Error: Wrong number of Argument>", color)
    else:
        errorp = True
        dc.deco_print("<Error: Unknown Command>", color)
    if errorp:
        return None, None
    else:
        return cmd, arg

def exec_cmd(cmd, arg, gc, choices):
    if cmd == 'end':
        return True
    elif cmd == 'show':
        graph = gc.get_graph()
        symbol_label = nx.get_node_attributes(graph, 'name')
        symbol_pos = {}
        id_label = {}
        id_pos = {}

        pos = nx.planar_layout(graph)
        #pos = mypos(graph, 0.1)
        nx.draw_networkx(graph, pos, with_labels=False)
        for node in graph.nodes():
            id_label[node] = str(node)
            c = pos[node]
            symbol_pos[node] = (c[0], c[1]-0.0002)
            id_pos[node] = (c[0], c[1]-0.15)
        nx.draw_networkx_labels(graph, symbol_pos, symbol_label, font_size=16)
        nx.draw_networkx_labels(graph, id_pos, id_label, font_size=16)
        plt.show()
    elif cmd =='pool':
        print("pool = " + str(gc.get_id_pool()))
    elif cmd == 'node':
        show_nodes(gc.get_graph())
    elif cmd == 'edge':
        show_edges(gc.get_graph(), data=arg)
    elif cmd == 'choice':
        show_choices(choices)
    elif cmd == 'apply':
        try:
            gc.apply_rule(arg[0], choices[arg[0]][arg[1]])
        except IndexError:
            dc.deco_print("<Error: Wrong Index>", color)
    elif cmd == 'save':
        nx.write_gml(gc.get_graph(), arg)

def show_nodes(graph, indent_num=4):
    print("[ NODES ]")
    for node_id, attribute in graph.nodes(True):
        print(' '*indent_num + '[ ' + str(node_id) + ' ] ' + attribute['name'])
    print("")

def show_edges(graph, indent_num=4, data=False):
    print("[ EDGES ]")
    for edge in graph.edges(data=data):
        print(' '*indent_num, end="")
        print('[' + str(edge[0]) + '] ' + graph.nodes[edge[0]]['name'], end=' -> ')
        if data:
            print('[' + str(edge[1]) + '] ' + graph.nodes[edge[1]]['name'], end="")
            print(' ATTR = ' + str(edge[2]))
        else:
            print('[' + str(edge[1]) + '] ' + graph.nodes[edge[1]]['name'])
    print("")

def show_choices(choices, indent_num=4):
    print("[ CHOICES ]")
    for rule_name, targets in choices.items():
        print(' '*indent_num +"[ " + rule_name + " ] ", end="")
        for target, i in zip(targets, range(len(targets))):
            print("[" + str(i) + "] ", end="")
            print(str(target),end=", ")
        print("")
        #temp =' '*indent_num +"[ " + rule_name + " ] "
        #pos = len(temp)
        #print(temp, end="")
        #for target in targets:
        #    print(' '*pos + str(target))

def prompt(gc, indent_num=4):
    finishp = False
    while not finishp:
        graph = gc.get_graph()
        choices = gc.get_applicable_rule()
        cmd, arg = input_and_parse(choices)
        finishp = exec_cmd(cmd, arg, gc, choices)

if __name__ == "__main__":
    args = sys.argv
    first_grammar_path = None
    second_grammar_path = None
    if len(args) == 2:
        first_grammar_path = args[1]
    elif len(args) > 2:
        first_grammar_path = args[1]
        second_grammar_path = args[2]

    if first_grammar_path is not None:
        y_n = input("\n\nLOAD [y/n]? :")
        if (y_n == 'y') or (y_n == 'Y'):
            filepath = input('FILEPATH: ')
            g = load_gml(filepath)
            g_robogrammar = GraphCompiler(first_grammar_path, graph=g)
        else:
            g_robogrammar = GraphCompiler(first_grammar_path)
        prompt(g_robogrammar)

    if second_grammar_path is not None:
        g_compiler = GraphCompiler(second_grammar_path, graph=g_robogrammar.get_graph())
        prompt(g_compiler)


