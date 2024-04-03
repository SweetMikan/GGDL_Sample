""" GraphCompiler """

import copy
import networkx as nx
from networkx.algorithms.isomorphism.vf2userfunc import DiGraphMatcher
from grammar import GGDLParser

class GraphCompiler():
    """ 
    This class handles a graph object and modifies it 
    by following rules given by a grammar.
    The graph (__graph) is modeled as a attributed directed graph
    and is implemented by using networkx.

    To add nodes with a same symbol separately,
    each instance of the class has an unique id pool (__id_pool).
    Each node of __graph is distinguished / accessed by the ID.

    """
    def __init__(self, grammar_path, graph=None, chunk_size=100):
        self.__grammar = GGDLParser(grammar_path)

        self.chunk_size = chunk_size
        self.__id_pool = set([i for i in range(chunk_size)])
        self.__id_max = max(self.__id_pool)

        if graph is None:
            self.initialize_graph()
        else:
            self.load_graph(graph)

    ############################################################
    #
    #   General methods for handling graphs
    #
    ############################################################
    def load_graph(self, graph):
        """ Loads a nx.DiGraph class graph.

        To avoid side-effects on the given graph, 
        a deepcopied graph is passed to __graph.

        Args:
            graph(DiGraph): A graph to be loaded.

        """
        # Check all the symbols in the given graph belong to the vocabulary.
        illegal_symbols = []
        errorp = False
        for node_id in graph.nodes():
            if not isinstance(node_id, int):
                raise ValueError("Node_id < " + str(node_id) + " > is not an instance of the int class.")
            if 'name' not in graph.nodes[node_id]:
                raise ValueError("Node < " + str(node_id) + " > does not have the attribution 'name'")
            symbol = graph.nodes[node_id]['name']
            if not self.__grammar.is_vocabulary(symbol):
                errorp = True
                illegal_symbols.append(symbol)
        if errorp:
            raise ValueError(
                    "The given graph contains symbols do not belong to the vocabulary:\n" + \
                            str(illegal_symbols))

        # Reset __id_pool
        self.__reset_pool()
        self.__remove_pool(set(graph.nodes()))

        self.__graph = copy.deepcopy(graph)
        self.__initial_graph = copy.deepcopy(graph)

    def initialize_graph(self):
        """ Initializes __graph with the start-symbol of the grammar. """
        if self.__grammar.start_graph is None:
            # Reset __id_pool
            self.__reset_pool()
            self.__graph = None
            self.__initial_graph = None
        else:
            self.__reset_pool()
            id_converter = {node_id:self.__pop_id() for node_id in self.__grammar.start_graph.nodes()}
            self.__graph = self.__grammar.start_graph.convert_into_networkx(id_converter=id_converter)
            self.__initial_graph = copy.deepcopy(self.__graph)
    
    def reset_graph(self):
        """ Resets __graph. """
        self.__reset_pool()
        self.__remove_pool(set(self.__initial_graph.nodes()))
        self.__graph = copy.deepcopy(self.__initial_graph)

    def get_graph(self):
        """ Returns a copy of __graph.
        
        To avoid manually modification of __graph, 
        a deepcopied graph object is returned.
        
        """
        return copy.deepcopy(self.__graph)

    def get_id_pool(self):
        """ Returns a copy of __id_pool. """
        return copy.deepcopy(self.__id_pool)

    def get_label(self, node_id, label_type='name'):
        """ Gets a symbol from a node with the node_id.

        Networkx suports multiple labels on a node.
        Therefore, to give flexibility for future applications, 
        A label type can be specified.

        Args:
            node_id(Number): The id of the node.
            label_type(str, optional): The label type to be read.

        """
        return self.__graph.nodes[node_id][label_type]

    def get_symbol(self, node_id):
        """ Wraps get_label method. """
        return self.get_label(node_id)

    def add_node(self, symbol, label_dict={}):
        """ Manually adds a node to the graph.

        Args:
            symbol(str): The symbol of the node to be added into the __graph.
            label_dict(dict): The attribute for the node.

        Returns:
            node_id(int): The id of the newly added node.

        """
        node_id = self.__pop_id()
        attribute = copy.deepcopy(label_dict)
        attribute['name'] = symbol
        self.__graph.add_nodes_from([(node_id, attribute)])
        return node_id

    def remove_node(self, node_id):
        """ Removes the node with node_id from __graph. 

        Args:
            node_id(int): The id of the node to be removed from the __graph.
        
        Note:
            The networkx removes the all edges connecting with a removed node.
         
        """
        self.__graph.remove_node(node_id)
        self.__push_id(node_id)

    def add_edge(self, start_id, end_id, label_dict={}):
        """ Adds an edge between start_id and end_id. 
        
        Args:
            start_id(int): The ID of the node where the edge starts.
            end_id(int): The ID of the node where the edge ends.
            label_dict(dict): The attribute for the edge.
        
        """
        self.__graph.add_edge(from_id, to_id, **label_dict)

    def remove_edge(self, start_id, end_id):
        """ Removes the edge (start_id, end_id).

        Args:
            start_id(int): The ID of the node where the edge starts.
            end_id(int): The ID of the node where the edge ends.
        
        """
        self.__graph.remove_edge(from_id, to_id)


    def get_node_list(self, data=False):
        """ Returns the list of IDs of nodes.

            data(bool): If True, this method returns a list of pairs 
                        which contain a node id and an attribute dictionary, respectively.
        
        """
        return list(self.__graph.nodes(data=data))

    def get_edge_list(self, data=False):
        """ Returns the list of pairs of which [0] is a start node and [1] is a end node.

            data(bool): If True, this method returns a list of pairs 
                        which contain the edge pairs above and an attribute dictionary, respectively.
        
        """
        return list(self.__graph.edges(data=data))


    def get_terminal_symbol_node(self):
        """ Returns a list of IDs of nodes which have non-terminal-symbol. """
        return [node_id for node_id in self.get_node_list()
                if self.is_terminal_symbol_node(node_id)]
 
    def get_non_terminal_symbol_node(self):
        """ Returns a list of IDs of nodes which have non-terminal-symbol. """
        return [node_id for node_id in self.get_node_list()
                if self.is_non_terminal_symbol_node(node_id)]

    def is_terminal_symbol_node(self, node_id):
        """ Checks if the given symbol is a terminal symbol of the grammar.

        Args:
            symbol(string): A symbol

        """
        return self.__grammar.is_terminal_symbol(self.get_label(node_id))
 
    def is_non_terminal_symbol_node(self, node_id):
        """ Checks if the given symbol is a non-terminal symbol of the grammar.

        Args:
            symbol(string): A symbol

        """
        return self.__grammar.is_non_terminal_symbol(self.get_label(node_id))

    def is_sentence(self):
        """ Checks if the __graph consists of only terminal symbols. """
        return 0 == len(self.get_non_terminal_symbol_node())
 
    def get_applicable_rule(self):
        """ Finds the target subgraphs to which each rule can apply.

        Returns:
            dict: Each key is the name of a rule.
                  The value is a list returned by the get_target_subgraph method of the rule.

        """
        ret = {}
        for rule_name in self.__grammar.rules:
            ret[rule_name] = self.__grammar.rules[rule_name].get_target_subgraph(self.__graph)

        return ret

    def is_there_no_applicable_rules(self, applicable_rule_dict):
        """ Check if all the values of get_applicable_rule is []. 
        
        Args:
            applicable_rule_dict(dict): The returnd list by the get_applicable_rule.
        
        """
        for v in applicable_rule_dict.values():
            if len(v) != 0:
                return False
        return True

    def apply_rule(self, rule_name, target):
        """ Applys the given rule to the target.

        Args:
            rule_name(str): A name of the rule.
            target: Choose from a list in the result of the get_applicable_rule. 

        """
        self.__grammar.rules[rule_name].apply_rule(target, self.__graph, lambda x:self.__pop_id())

    def __pop_id(self):
        """ Pops an unique number for an ID for a node. """
        ret = self.__id_pool.pop()
        if len(self.__id_pool) == 0:
            self.__refill_id_pool()
        return ret

    def __push_id(self, node_id):
        """ Returns a number to the pool. 
        
        Args:
            node_id(number): A number pop from the pool.
        
        """
        self.__id_pool.add(node_id)

    def __refill_id_pool(self):
        """ Refills the id pool. """
        self.__id_pool.update([i for i in 
            range(self.__id_max + 1, self.__id_max + self.chunk_size)])
        self.__id_max = max(self.__id_pool)

    def __remove_pool(self, id_set):
        """ Removes numbers in id_set. """
        self.__id_pool = self.__id_pool - id_set

    def __reset_pool(self):
        """ Resets __id_pool to the initial state. """
        self.__id_pool = set([i for i in range(self.chunk_size)])
 

from grammar import Grammar

class __GraphCompiler():
    """ 
    Note:
        This class is outdated.

    This class handles a graph object and modifies it 
    by following rules given by a grammar.
    The graph (__graph) is modeled as a attributed directed graph
    and is implemented by using networkx.

    To add nodes with a same symbol separately,
    each instance of the class has an unique id pool (__id_pool).
    Each node of __graph is distinguished / accessed by the ID.

    """
    def __init__(self, grammar_path, graph=None, chunk_size=100):
        self.__grammar = Grammar(grammar_path)
        self.__wgraph_dict = {}

        for rule_name in self.__grammar.get_context_sensitive_rule_list():
            lhs_graph, lhs_key_to_int, rhs_graph, rhs_key_to_int = \
                    self.make_graphs_from_rule(rule_name)
            self.__wgraph_dict[rule_name] = (lhs_graph, lhs_key_to_int)

        self.chunk_size = chunk_size
        self.__id_pool = set([i for i in range(chunk_size)])
        self.__id_max = max(self.__id_pool)

        if graph is None:
            self.initialize_graph()
        else:
            self.load_graph(graph)

    ############################################################
    #
    #   General methods for handling graphs
    #
    ############################################################
    def load_graph(self, graph):
        """ Loads a nx.DiGraph class graph.

        To avoid side-effects on the given graph, 
        a deepcopied graph is passed to __graph.

        Args:
            graph(DiGraph): A graph to be loaded.

        """
        # Check all the symbols in the given graph belong to the vocabulary.
        illegal_symbols = []
        errorp = False
        for node_id in graph.nodes():
            if not isinstance(node_id, int):
                raise ValueError("Node_id < " + str(node_id) + " > is not an instance of the int class.")
            if 'symbol' not in graph.nodes[node_id]:
                raise ValueError("Node < " + str(node_id) + " > does not have the attribution 'symbol'")
            symbol = graph.nodes[node_id]['symbol']
            if not self.__grammar.is_vocabulary(symbol):
                errorp = True
                illegal_symbols.append(symbol)
        if errorp:
            raise ValueError(
                    "The given graph contains symbols do not belong to the vocabulary:\n" + \
                            str(illegal_symbols))

        # Reset __id_pool
        self.__reset_pool()
        self.__remove_pool(set(graph.nodes()))

        self.__graph = copy.deepcopy(graph)
        self.__initial_graph = copy.deepcopy(graph)

    def initialize_graph(self):
        """ Initializes __graph with the start-symbol of the grammar. """
        if self.__grammar.start_symbol is None:
            # Reset __id_pool
            self.__reset_pool()
            self.__graph = None
            self.__initial_graph = None
        else:
            self.__reset_pool()
            self.__graph = nx.DiGraph()
            self.__add_node(self.__grammar.start_symbol)
            self.__initial_graph = copy.deepcopy(self.__graph)
    
    def reset_graph(self):
        """ Resets __graph. """
        self.__reset_pool()
        self.__remove_pool(set(self.__initial_graph.nodes()))
        self.__graph = copy.deepcopy(self.__initial_graph)

    def get_graph(self):
        """ Returns a copy of __graph.
        
        To avoid manually modification of __graph, 
        a deepcopied graph object is returned.

        
        """
        return copy.deepcopy(self.__graph)

    def get_id_pool(self):
        """ Returns a copy of __id_pool. """
        return copy.deepcopy(self.__id_pool)

    def get_label(self, node_id, label_type='symbol'):
        """ Gets a symbol from a node with the node_id.

        Networkx suports multiple labels on a node.
        Therefore, to give flexibility for future applications, 
        A label type can be specified.

        Args:
            node_id(Number): The id of the node.
            label_type(str, optional): The label type to be read.

        """
        return self.__graph.nodes[node_id][label_type]

    def get_symbol(self, node_id):
        """ Wraps get_label method. """
        return self.get_label(node_id)

    def get_node_list(self, data=False):
        """ Returns the list of IDs of nodes.

            data(bool): If True, this method returns a list of pairs 
                        which contain a node id and an attribute dictionary, respectively.
        
        """
        return list(self.__graph.nodes(data=data))

    def get_terminal_symbol_node(self):
        """ Returns a list of IDs of nodes which have non-terminal-symbol. """
        return [node_id for node_id in self.get_node_list()
                if self.is_terminal_symbol_node(node_id)]
 
    def get_non_terminal_symbol_node(self):
        """ Returns a list of IDs of nodes which have non-terminal-symbol. """
        return [node_id for node_id in self.get_node_list()
                if self.is_non_terminal_symbol_node(node_id)]

    def get_edge_list(self, data=False):
        """ Returns the list of pairs of which [0] is a start node and [1] is a end node.

            data(bool): If True, this method returns a list of pairs 
                        which contain the edge pairs above and an attribute dictionary, respectively.
        
        """
        return list(self.__graph.edges(data=data))

    def is_terminal_symbol_node(self, node_id):
        """ Checks if the given symbol is a terminal symbol of the grammar.

        Args:
            symbol(string): A symbol

        """
        return self.__grammar.is_terminal_symbol(self.get_label(node_id))
 
    def is_non_terminal_symbol_node(self, node_id):
        """ Checks if the given symbol is a non-terminal symbol of the grammar.

        Args:
            symbol(string): A symbol

        """
        return self.__grammar.is_non_terminal_symbol(self.get_label(node_id))

    def is_sentence(self):
        """ Checks if the __graph consists of only terminal symbols. """
        return 0 == len(self.get_non_terminal_symbol_node())
 
    def make_graphs_from_rule(self, rule_name):
        """ Creates graphs from a rule.
        
        In the context of the graph grammar theory, 
        a subgraph pattern to which a rule can be applied is called a left hand side graph (or just lhs),
        and a graph to be inserted is called a right hand side graph (rhs).
        lhs_graph and rhs_graph correspond lhs and rhs, respectively.

        In graph file, wgraph or nt element corresponds the lhs,
        and graph element corresponds the rhs.
        
        Note:
            The wnode in wgraph is ignored.
            Thus wildcard nodes and edges with them are absent in the lhs_graph.

        Args:
            rule_name(string): A name of a rule in the grammar.

        Returns:
            lhs_graph(DiGraph): A graph representing a pattern to be replaced
                                Each node id is a number which 
                                the rule specifies in the grammar file.
                                In the case of a context-free rule, 
                                the node id is set at 0.

            lhs_key_to_int(Dictionary): This stores the correspondence between
                                        node ids in lhs_graph and keys of node_dict of wgraph.
                                        In the case of context-free rules, returns 0.

            rhs_graph(DiGraph): A directed graph which replaces the lhs.
                                Each node id is a number which 
                                the rule specifies in the grammar file.
                                The node id for the base node is chosen 
                                from numbers which did not appear in the rule.

            rhs_key_to_int(Dictionary): This stores the correspondence between
                                        node ids in rhs_graph and keys of node_dict of the rule.

        """
        # LHS
        lhs_graph = nx.DiGraph()
        lhs_key_to_int = {}
        
        if self.__grammar.is_context_free_rule(rule_name):
            symbol = self.__grammar.get_replaced_symbol(rule_name)
            lhs_graph.add_nodes_from([(0, {'symbol': symbol})])
            lhs_key_to_int = 0
        else:
            wnode_list = self.__grammar.get_wgraph_wnode_list(rule_name)
            node_dict = self.__grammar.get_wgraph_node_dict(rule_name)
            edge_dict = self.__grammar.get_wgraph_edge_dict(rule_name)

            # Extract edges not containing any wildcard nodes.
            edge_list = [edge for edge in edge_dict.values() 
                         if (Grammar.get_edge_from(edge) in node_dict) 
                         and (Grammar.get_edge_to(edge) in node_dict)]

            for node_key in node_dict:
                lhs_graph.add_nodes_from([(int(node_key), {'symbol': node_dict[node_key]})])
                lhs_key_to_int[node_key] = int(node_key) 

            for edge in edge_list:
                lhs_graph.add_edge(
                        lhs_key_to_int[Grammar.get_edge_from(edge)],
                        lhs_key_to_int[Grammar.get_edge_to(edge)]
                        )
                if Grammar.get_edge_type == 'bi':
                    lhs_graph.add_edge(
                            lhs_key_to_int[Grammar.get_edge_to(edge)],
                            lhs_key_to_int[Grammar.get_edge_from(edge)]
                            )
        
        # RHS
        rhs_graph = nx.DiGraph()
        node_dict = self.__grammar.get_newly_added_nodes(rule_name)
        edge_dict = self.__grammar.get_newly_added_edges(rule_name)
        rhs_key_to_int = {}

        for node_key in node_dict:
            if node_key == 'base':
                continue
            rhs_graph.add_nodes_from([(int(node_key), {'symbol': node_dict[node_key]})])
            rhs_key_to_int[node_key] = int(node_key) 

        base_id = min(rhs_key_to_int.values()) - 1
        rhs_graph.add_nodes_from([(base_id, {'symbol': node_dict['base']})])
        rhs_key_to_int['base'] = base_id

        for edge in edge_dict.values():
            try:
                rhs_graph.add_edge(
                        rhs_key_to_int[Grammar.get_edge_from(edge)],
                        rhs_key_to_int[Grammar.get_edge_to(edge)]
                        )
                if Grammar.get_edge_type == 'bi':
                    rhs_graph.add_edge(
                            rhs_key_to_int[Grammar.get_edge_to(edge)],
                            rhs_key_to_int[Grammar.get_edge_from(edge)]
                            )
            except KeyError:
                continue

        return lhs_graph, lhs_key_to_int, rhs_graph, rhs_key_to_int

    def get_applicable_rule(self):
        """ Returns a dictionary of which keys are rule names and
            values are lists of targets.

        """
        return dict(**self.get_applicable_context_free_rule(), 
                **self.get_applicable_context_sensitive_rule())

    def is_there_no_applicable_rules(self, applicable_rule_dict):
        """ Check if all the values of get_applicable_rule is []. """
        for v in applicable_rule_dict.values():
            if len(v) != 0:
                return False
        return True

    def apply_rule(self, rule_name, target):
        """ Applys the given rule to the target.

        Args:
            rule_name(string): A name of the rule.
            target: 

        """
        if self.__grammar.is_context_free_rule(rule_name):
            self.apply_context_free_rule(rule_name, target)
        else:
            self.apply_context_sensitive_rule(rule_name, target)

              
    ##
    ####### private methods #######
    ##
    def __pop_id(self):
        """ Pops an unique number for an ID for a node. """
        ret = self.__id_pool.pop()
        if len(self.__id_pool) == 0:
            self.__refill_id_pool()
        return ret

    def __push_id(self, node_id):
        """ Returns a number to the pool. 
        
        Args:
            node_id(number): A number pop from the pool.
        
        """
        self.__id_pool.add(node_id)

    def __refill_id_pool(self):
        """ Refills the id pool. """
        self.__id_pool.update([i for i in 
            range(self.__id_max + 1, self.__id_max + self.chunk_size)])
        self.__id_max = max(self.__id_pool)

    def __remove_pool(self, id_set):
        """ Removes numbers in id_set. """
        self.__id_pool = self.__id_pool - id_set

    def __reset_pool(self):
        """ Resets __id_pool to the initial state. """
        self.__id_pool = set([i for i in range(self.chunk_size)])
        
    def __add_node(self, symbol):
        """ Adds a symbol as a node of graph.

        Assume this method is only called by other method.
        So, this does not check the type arguments.

        Args:
            symbol(string): A symbol to be added into __graph.

        Returns:
            node_id(Integer): The id of the newly added node.

        """
        node_id = self.__pop_id()
        self.__graph.add_nodes_from([(node_id, {'symbol':symbol})])
        return node_id

    def __remove_node(self, node_id):
        """ Removes the node with node_id from __graph. 
        
        Note that the networkx removes the all edges connecting with a removed node.
         
        """
        self.__graph.remove_node(node_id)
        self.__push_id(node_id)

    def __add_edge(self, from_id, to_id):
        """ Adds an edge between from_id and to_id. """
        self.__graph.add_edge(from_id, to_id)

    def __remove_edge(self, from_id, to_id):
        """ Removes the edge from from_id to to_id. """
        self.__graph.remove_edge(from_id, to_id)

    ############################################################
    #
    #   Methods for handling context-free grammers
    #
    ############################################################
    def get_target_of_context_free_rule(self, rule_name):
        """ Returns the IDs of nodes to which the rule is applicable to.

            Args:
                rule_name(String): A key of rule_dict of the grammar.

        """
        return [node_id for node_id in self.__graph.nodes() 
                if self.__grammar.is_context_free_rule_applicable(
                    rule_name, self.get_label(node_id))]

    def get_applicable_context_free_rule(self):
        """ Returns a dictionary of which keys are rule names and
            values are lists of targets.

        """
        return {rule_name: self.get_target_of_context_free_rule(rule_name) 
                for rule_name in self.__grammar.get_context_free_rule_list()}


    def apply_context_free_rule(self, rule_name, node_id):
        """ Applys a rule with the given rulename to a node with node_id.

        Args:
            rule_name(String): A key of rule_dict of the grammar.
            node_id(Number): An id of a node in __graph.

        """
        if not self.__grammar.is_context_free_rule_applicable(rule_name, self.get_label(node_id)):
            raise ValueError("The rule (" + rule_name + \
                    ") is not applicable to the node " + self.get_label(node_id) +\
                    " (id = " + str(node_id) + ").")

        id_dict = {}
        new_nodes = self.__grammar.get_newly_added_nodes(rule_name)
        for grammar_node_id in new_nodes:
            symbol = new_nodes[grammar_node_id]
            graph_id = self.__add_node(symbol)
            # Associate the id in the newly added subgraph with a popped id.
            id_dict[grammar_node_id] = graph_id

        new_edges = self.__grammar.get_newly_added_edges(rule_name)
        for edge in new_edges.values():
            from_id = id_dict[Grammar.get_edge_from(edge)]
            to_id = id_dict[Grammar.get_edge_to(edge)]
            if Grammar.get_edge_type(edge) == 'di':
                self.__add_edge(from_id, to_id)
            elif Grammar.get_edge_type(edge) == 'bi':
                self.__add_edge(from_id, to_id)
                self.__add_edge(to_id, from_id)

        # Reconnect edges connecting with node_id to the base node of the rule.
        base_id = id_dict['base']
        for suc_id in self.__graph.successors(node_id):
            self.__add_edge(base_id, suc_id)
        for dec_id in self.__graph.predecessors(node_id):
            self.__add_edge(dec_id, base_id)
        self.__remove_node(node_id)


    ############################################################
    #
    #   Methods for handling context-sensitive grammers
    #
    ############################################################
    @classmethod
    def __same_symbol(cls, node1_attr, node2_attr):
        """ Checks if 'symbol' is same.

        Args:
            node1_attr(dictionary): An attribute dictionary for a node.
            node2_attr(dictionary): An attribute dictionary for a node.

        """
        return node1_attr['symbol'] == node2_attr['symbol']

    def __generate_matcher(self, lhs_graph):
        """ Returns a DiGraphMatcher object to compair __graph and lhs_graph. """
        return DiGraphMatcher(self.__graph, lhs_graph, node_match=GraphCompiler.__same_symbol)

    def get_target_of_context_sensitive_rule(self, rule_name):
        """ Finds all subgraphs match with the pattern of the rule.

        Args:
            rule_name(string): A key of cs_rule_dict.

        Returns:
            match_list(list): A list of matches.

        Note:
            Each match in match_list is a dictionary:
                * Each key is either a key in node_dict in the wgraph.
                * Each value is a node id of __graph or None.
                * 'None' represents the absence of a node at the wildcard node.

        """
        lhs_graph, lhs_key_to_int = self.__wgraph_dict[rule_name]
        wgraph = self.__grammar.get_wgraph(rule_name)
        #wnode_list = self.__grammar.get_wgraph_wnode_list(rule_name)
        node_dict = self.__grammar.get_wgraph_node_dict(rule_name)
        #edge_dict = self.__grammar.get_wgraph_edge_dict(rule_name)

        # indegree_dict and outdegree_dict remember the indegree and the outdegree
        # which each node can have at most.
        indegree_dict = dict.fromkeys(node_dict.keys(), 0)
        outdegree_dict = dict.fromkeys(node_dict.keys(), 0)
        w_indegree_dict = dict.fromkeys(node_dict.keys(), 0)
        w_outdegree_dict = dict.fromkeys(node_dict.keys(), 0)

        for node_id in node_dict:
            indegree, outdegree, wildcard_in, wildcard_out = \
                    Grammar.get_inoutdegree_of_wgraph_node(wgraph, node_id)
            indegree_dict[node_id] = indegree
            outdegree_dict[node_id] = outdegree
            w_indegree_dict[node_id] = wildcard_in
            w_outdegree_dict[node_id] = wildcard_out

        #for edge in edge_dict.values():
            #if Grammar.get_edge_to(edge) not in wnode_list:
                #indegree_dict[Grammar.get_edge_to(edge)] += 1
                #if Grammar.get_edge_from(edge) in wnode_list:
                #    w_indegree_dict[Grammar.get_edge_to(edge)] += 1

            #if Grammar.get_edge_from(edge) not in wnode_list:
                #outdegree_dict[Grammar.get_edge_from(edge)] += 1
                #if Grammar.get_edge_to(edge) in wnode_list:
                #    w_outdegree_dict[Grammar.get_edge_from(edge)] += 1

        matcher = self.__generate_matcher(lhs_graph)
        match_list = []

        for nx_match in matcher.subgraph_isomorphisms_iter():
            # Each match in subgraph_isomorphisms_iter() is a dictionary
            # from node_ids of __graph to node_ids of lhs_graph.
            # Thus, reverse nx_match and concatenate it with lhs_key_to_int
            # to create a match.
            reverse_match = {v: k for k, v in nx_match.items()}
            match = {node_key: reverse_match[lhs_key_to_int[node_key]]
                    for node_key in lhs_key_to_int}            
            call_continue = False

            # nx_match does not consider the indegree and the outdegree of the nodes.
            # Reject match with unmatched indegree or outdegree.
            # If a node connects with a wildcard node, add the information to match.
            for node_key in node_dict:
                in_edges = self.__graph.in_edges(match[node_key])
                indegree = len(in_edges)
                if indegree > indegree_dict[node_key]:
                    call_continue = True
                    break;
                if indegree == indegree_dict[node_key]:
                    if len(w_indegree_dict[node_key]) != 0:
                        # The node connects with a wildcard node.
                        from_nodes = [edge[0] for edge in in_edges
                                      if edge[0] not in match.values()]
                        # Currently, the wgraph allows a node have only one single edge from a wildcard.
                        # Therefore, specify the index as 0.
                        wildcard_id = w_indegree_dict[node_key][0]

                        # The wildcard_id represents an unique id of a wildcard in wgraph.
                        # Therefore, when wildcard_id is already registed,
                        # the registered value and from_nodes[0] should match.
                        # Otherwise, the match represents a different topology from wgraph.
                        if wildcard_id not in match:
                            match[wildcard_id] = from_nodes[0]
                        elif match[wildcard_id] != from_nodes[0]:
                            call_continue = True
                            break
                if indegree < indegree_dict[node_key]:
                    # This condition means the absence of the wildcard.
                    # Therefore, len(w_indegree_dict[node_key]) != 0
                    wildcard_id = w_indegree_dict[node_key][0]
                    if wildcard_id not in match:
                        match[wildcard_id] = None
                    elif match[wildcard_id] != None:
                        # If the registered value is not None, that means a different topology.
                        call_continue = True
                        break

                out_edges = self.__graph.out_edges(match[node_key])
                outdegree = len(out_edges)
                #outdegree = len(self.__graph.out_edges(match[node_key]))
                if outdegree > outdegree_dict[node_key]:
                    call_continue = True
                    break;
                if outdegree == outdegree_dict[node_key]:
                    if len(w_outdegree_dict[node_key]) != 0:
                        # The node connects with a wildcard node.
                        to_nodes = [edge[1] for edge in out_edges
                                    if edge[1] not in match.values()]
                        # Currently, the wgraph allows a node have only one single edge toward a wildcard.
                        # Therefore, specify the index as 0.
                        wildcard_id = w_outdegree_dict[node_key][0]

                        # The wildcard_id represents an unique id of a wildcard in wgraph.
                        # Therefore, when wildcard_id is already registed,
                        # the registered value and to_nodes[0] should match.
                        # Otherwise, the match represents a different topology from wgraph.
                        if wildcard_id not in match:
                            match[wildcard_id] = to_nodes[0]
                        elif match[wildcard_id] != to_nodes[0]:
                            call_continue = True
                            break
                if outdegree < outdegree_dict[node_key]:
                    # This condition means the absence of the wildcard.
                    # Therefore, len(w_outdegree_dict[node_key]) != 0
                    wildcard_id = w_outdegree_dict[node_key][0]
                    if wildcard_id not in match:
                        match[wildcard_id] = None
                    elif match[wildcard_id] is not None:
                        # If the registered value is not None, that means a different topology.
                        call_continue = True
                        break

            if call_continue:
                call_continue = False
                continue
            match_list.append(match)
        return match_list

    def get_applicable_context_sensitive_rule(self):
        """ Returns a dictionary of which keys are rule names and
            values are lists of targets.

        """
        return {rule_name: self.get_target_of_context_sensitive_rule(rule_name)
                for rule_name in self.__grammar.get_context_sensitive_rule_list()}

    def apply_context_sensitive_rule(self, rule_name, match):
        """ Apply the rule to a subgraph specified with match.

        Args:
            rule_name(string): A key of cs_rule_dict.
            match(dictionary): Each key is either a key in node_dict in the wgraph.

        """
        # A mapping from wgraph node id to the updated graph id.
        id_dict = {}

        new_nodes = self.__grammar.get_newly_added_nodes(rule_name)
        for grammar_node_id in new_nodes:
            symbol = new_nodes[grammar_node_id]
            graph_id = self.__add_node(symbol)
            # Associate the id in the newly added subgraph with a popped id.
            id_dict[grammar_node_id] = graph_id

        # Add the information about wildcards to id_dict
        # The id of the node corresponding a wildcard does not change in __graph.
        wnode_list = self.__grammar.get_wgraph_wnode_list(rule_name)
        for wildcard_id in wnode_list:
            id_dict[wildcard_id] = match[wildcard_id]

        # Add edges
        new_edges = self.__grammar.get_newly_added_edges(rule_name)
        edge_from_wildcard_list = []
        edge_toward_wildcard_list = []
        for edge in new_edges.values():
            #print("[edge] type = " + Grammar.get_edge_type(edge), end=" ")
            #print("from = " + Grammar.get_edge_from(edge), end=" ")
            #print("to = " + Grammar.get_edge_to(edge))
            from_id = id_dict[Grammar.get_edge_from(edge)]
            to_id = id_dict[Grammar.get_edge_to(edge)]
            if (from_id is not None) and (to_id is not None):
                self.__add_edge(from_id, to_id)
                if Grammar.get_edge_type(edge) == 'bi':
                    self.__add_edge(to_id, from_id)

        # Remove all nodes matched with lhs_graph except for wildcards.
        for old_node_id in match:
            #print("old_node = " + str(old_node_id) + "match = " + str(match[old_node_id]))
            if old_node_id not in wnode_list:
                #print("old_node = " + str(old_node_id) + "match = " + str(match[old_node_id]))
                self.__remove_node(match[old_node_id])





