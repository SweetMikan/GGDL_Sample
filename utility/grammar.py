import xml.etree.ElementTree as ET
import copy
import itertools
from functools import reduce

class ColoredException(Exception):
    def __init__(self, arg="", color="\033[31m"):
        self.arg = arg
        self.color = color
        super().__init__(self.__color_str(self.arg))

    def __color_str(self, string):
        return self.color + string + "\033[0m"

class ElementAbsenceError(ColoredException):
    """ This error is called when a XML element needed is absent. """
    def __init__(self, element_tag, color="\033[31m"):
        super().__init__(arg="The element '" + element_tag + "' does not exist.")

class ElementAttributeAbsenceError(ColoredException):
    """ This error is called when the XML element to be parsed does not have
        the specified attribute.
    """
    def __init__(self, element, attribute, color="\033[31m"):
        if not isinstance(element, ET.Element):
            raise ColoredException('Non- Element class object was passed to ElementAttributeAbsenceError')

        attrib = element.attrib
        string = "The element: " + str(element) + " "
        if len(attrib) != 0:
            for a in attrib:
                string += '\n' + ' '*4 + str(a) + ': ' + attrib[a]
            string += '\n'
        string += "does not have the '" + attribute + "' attribute."
        super().__init__(arg=string)

class DuplicatedIdError(ColoredException):
    """ This error is called when the value of the id attribute of the node element of a GGDL file
        already used by anothor node.
    """
    def __init__(self, idvalue, optional_description=""):
        string = 'The id "' + str(idvalue) +'" is already used.'
        string += optional_description
        super().__init__(arg=string)

class InvalidTypeError(ColoredException):
    """ This error is called when the given object is not an instance of the specified class. """
    def __init__(self, examined_object, class_type):
        string = "The object: " + str(examined_object) + \
                "(type: " + examined_object.__class__.__name__ + ") "\
                "is not a " + str(class_type.__name__) +" object."
        super().__init__(arg=string)

class GraphNodeAbsenceError(ColoredException):
    """ This error is called when the graph does not have a node with the given ID. """
    def __init__(self, arg):
        string = "No nodes have '" + str(arg) + "' as the ID."
        super().__init__(arg=string)


class InvalidExoticGraphError(ColoredException):
    """ This error is called when a checking process of exotic graphs finds an error."""

class InvalidRuleError(ColoredException):
    """ This error is called when a checking process of rules finds an error. """

class InvalidFileError(ColoredException):
    """ This error is called when a checking process of files finds an error. """

class VocaburaryError(ColoredException):
    """ This error is called when a checking process of GGDL file finds a symbol not in the vocaburary."""

class SymbolDefinitionOverriedError(ColoredException):
    """ This error is called when a symbol to be defined is already defined as a different type. """
    def __init__(self, symbol, symbol_type):
        super().__init__(arg="The given symbol '" + symbol +"' is already defined as " + symbol_type)


class SimpleNode():
    """ A class for nodes of SimpleGraph class 
    
    Each instance of this class represents a node of labelled directed graphs.
    To imitate nodes of networkx, this class support multiple labels per node.

    """
    def __init__(self, node_id, label_dict={}):
        """

        Args:
            node_id: An identifier for a node.
                Nodes are distinguished by node_id.
            label_dict: Each key is a label name.
                        The value is the label value.

        """
        self.node_id = node_id
        self.label_dict = label_dict

    def __str__(self):
        if isinstance(self.node_id, str):
            idstr = "'" + str(self.node_id) +"'"
        else:
            idstr = str(self.node_id)
        return "<" + self.__class__.__name__ + " id = " + idstr +">"

    def add_label(self, label_name, label_value):
        """ Adds a new label to a node.

        Args:
            label_name: A key to access the label.
            label_value: The label to be added.
        
        """
        self.label_dict[label_name] = label_value

    def data(self, data=False):
        """ Returns member data. 
        
        Args:
            data(bool): If true, the returned value is a tuple
                        containing node_id and label_dict.
        
        """
        if data:
            return (self.node_id, self.label_dict)
        else:
            return self.node_id

    def gen_element(self, indent_num=0, indent_width=2, tag='node'):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.
            tag(str): The tag for the element.

        """
        ret = '<' + tag+ ' id="' + str(self.node_id) + '"'
        # To easily check elements, the name element is written right next of the id attribute.
        try:
            ret += ' name="' + str(self['name']) + '"'
        except KeyError:
            # In the case of exotic nodes.
            pass
        for label_name, label_value in self.label_dict.items():
            if label_name not in ['id', 'name']:
                ret += ' ' + label_name + '="' + str(label_value) + '"'
        ret += '/>'
        return ' '*indent_width*indent_num + ret

    def __getitem__(self, item):
        return self.label_dict[item]

    #@classmethod
    #def define_symbol_node(cls, node_id, symbol_name, label_dict={}):
    #    """ Wraps the constructor. 
    #
    #    In the GGDL file parsing, the symbol of the node is stored at label_dict
    #    with key 'symbol'. This method does that.
    #
    #    Args:
    #        node_id: The identifier for the newly defined node.
    #        symbol_name(str): The symbol of the node.
    #        label_dict(dict, optionary): The additional labels.
    #
    #   """
    #    if type(symbol_name) is not str:
    #        raise ValueError("The symbol_name ( " + str(symbol_name) + " ) is not a string.")
    #    node = SimpleNode(node_id, label_dict=label_dict)
    #    node.add_label('symbol', symbol_name)
    #    return node
    @classmethod
    def is_same_node(cls, node1, node2):
        """ Check if node1 and node2 is same. """
        return node1.data(data=True) == node2.data(data=True)

    @classmethod
    def parse_node_element(cls, node_element):
        """ Checks if the node_element has the 'id' and the 'name' attributes. 

        When the node_element do not have the 'name' attribute, 
        automatically set it "" (the empty string).

        Args:
            node_element(Element): An element corresponding to the node element of GGDL file.

        """
        node_id = node_element.get('id')
        node_symbol = node_element.get('name')
        label_dict = node_element.attrib
        if node_id is None:
            raise ElementAttributeAbsenceError(node_element, 'id')
        if node_symbol is None:
            label_dict['name'] = ""

        return cls(node_id, label_dict=label_dict)



class SimpleEdge():
    """ A class for edges of SimpleGraph class

    #ach instance of this class represents an edge of labelled directed graphs.
    To imitate edges of networkx, this class support multiple labels per edge.

    """
    def __init__(self, start_node_id, end_node_id, label_dict={}, edge_id=""):
        """

        Creates an directed edge from a node with start_node_id to a node with end_node_id.

        Args:
            start_node_id: An ID of SimpleNode class object.
                           The existence of the node is not considered.
            end_node_id: An ID of SimpleNode class object.
                         The existence of the node is not considered.
            label_dict: Each key is a label name.
                        The value is the label value.
            edge_id(optional): An ID for the edge itself.

        """
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.label_dict = label_dict
        self.edge_id = edge_id

    def add_label(self, label_name, label_value):
        """ Adds a new label to a node.

        Args:
            label_name: A key to access the label.
            label_value: The label to be added.
        
        """
        self.label_dict[label_name] = label_value

    def get_label(self, label_name):
        """ Returns the label in the label_dict. 

        Args:
            label_name: A key to access the label.
        
        """
        return self.label_dict[label_name]

    def get_label_dict(self):
        return self.label_dict

    def data(self, data=False):
        """ Returns member data. 
        
        Args:
            data(bool): If true, the returned value is a tuple
                        containing ids and label_dict.
        
        """
        if data:
            return (self.start_node_id, self.end_node_id, self.label_dict)
        else:
            return (self.start_node_id, self.end_node_id)

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.

        """
        ret = '<edge id="' + str(self.edge_id) + '"'
        # To easily check elements, the from and to attributes are written right next the id attribute.
        ret += ' from="' + str(self.start_node_id) + '"' 
        ret += ' to="' + str(self.end_node_id) + '"' 
        for label_name, label_value in self.label_dict.items():
            if label_name not in ['id', 'from', 'to']:
                ret += ' ' + label_name + '="' + str(label_value) + '"'
        ret += '/>'
        return ' '*indent_width*indent_num + ret

    def __call__(self, index):
        if index == 0:
            return self.start_node_id
        elif index == 1:
            return self.end_node_id
        else:
            raise IndexError("Out of index")

    def __getitem__(self, item):
        return self.label_dict[item]

    def __str__(self):
        return "<" + self.__class__.__name__ + \
                " (" + str(self.start_node_id) + ", " + str(self.end_node_id) + ")>"

    @classmethod
    def parse_edge_element(cls, edge_element):
        """ Parses an edge element of a GGDL file and generates a SimpleEdge class object.

        When the edge_element do not have the 'name' attribute, 
        automatically set it "" (the empty string).

        Args:
            edge_element(Element): An element corresponding to the edge element of GGDL file.

        Returns:
            
            SimpleEdge: The generated object.

        """
        edge_id = edge_element.get('id')
        edge_type = edge_element.get('type')
        start_node_id = edge_element.get('from')
        end_node_id = edge_element.get('to')
        label_dict = edge_element.attrib

        if edge_id is None:
            raise ElementAttributeAbsenceError(edge_element, 'id')
        #if edge_type is None:
        #    raise ValueError(self.__error_msg(
        #        "The element does not have the 'type' attribute."))
        if start_node_id is None:
            raise ElementAttributeAbsenceError(edge_element, 'from')
        if end_node_id is None:
            raise ElementAttributeAbsenceError(edge_element, 'to')

        if edge_element.get('name') is None:
            label_dict['name'] = ""

        return cls(start_node_id, end_node_id, label_dict=label_dict, edge_id=edge_id)




class SimpleNodeBundle():
    """ A class to bundle SimpleNode class objects. """
    def __init__(self):
        self.node_dict = {}

    def add_node(self, node):
        """ Adds a SimpleNode class object to the node_dict. """
        self.node_dict[node.node_id] = node

    def existp(self, node_id):
        """ Check if a node with the given node_id exists. """
        return node_id in self.node_dict

    def get_node(self, node_id):
        return self.node_dict[node_id]

    def remove_node(self, node_id):
        return self.node_dict.pop(node_id)

    def get_nodes(self):
        return self.node_dict.values()

    def keys(self):
        """ Returns a set of keys of the node_dict."""
        return set(self.node_dict.keys())

    def gen_element(self, indent_num=0, indent_width=2, tag='node', exception_id_list=[]):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.
            tag(str): The tag for node elements.
            exception_id_list(list): The list of IDs not contained in the resulting string.

        """
        str_list = []
        for node_id in self:
            if node_id not in exception_id_list:
                str_list.append(
                        self.get_node(node_id).gen_element(
                            indent_num=indent_num, 
                            indent_width=indent_width,
                            tag=tag))
        return '\n'.join(str_list)

    def __getitem__(self, node_id):
        return self.get_node(node_id).label_dict

    def __call__(self, data=False):
        """ Returns a list of data of nodes. """
        return [node.data(data=data) for node in self.node_dict.values()]

    def __iter__(self):
        """ Works like nodes of networkx. """
        yield from self.node_dict

    @classmethod
    def is_same_bundle(cls, bundle1, bundle2):
        """ Check if bundle1 and bundle2 contain same nodes. """
        if bundle1.keys() != bundle2.keys():
            return False
        for node_id in bundle1.keys():
            if not SimpleNode.is_same_node(bundle1.get_node(node_id), bundle2.get_node(node_id)):
                return False
        return True

class SimpleEdgeBundle():
    """ A class to bundle SimpleEdge class objects. """
    def __init__(self):
        self.__edge_dict = {}
        self.__rev_edge_dict = {}

    def add_edge(self, edge):
        """ Adds a SimpleEdge class object to the __edge_dict. """
        start, end = edge.data()
        if start not in self.__edge_dict:
            self.__edge_dict[start] = {end: edge}
        else:
            self.__edge_dict[start][end] = edge

        if end not in self.__rev_edge_dict:
            self.__rev_edge_dict[end] = {start}
        else:
            self.__rev_edge_dict[end].add(start)

    def remove_edge(self, edge):
        """ Removes the given edge from the bundle. 
        
        Args:
            edge(SimpleEdge): The edge to be removed.
        
        """
        start, end = edge.data()
        self.__edge_dict[start].pop(end)
        if len(self.__edge_dict[start]) == 0:
            self.__edge_dict.pop(start)

        self.__rev_dict[end].remove(start)
        if len(self.__rev_edge_dict[end]) == 0:
            self.__edge_dict.pop(end)

    def get_connecting_edges(self, node_id):
        """ Returns edges connect with the given node. 
        
        Args:
            node_id: The value for the node_id member of SimpleNode class object.
        
        """
        outward_edges = []
        inward_edges = []
        if node_id in self.__edge_dict:
            outward_edges = self.__edge_dict[node_id].values()
        if node_id in self.__rev_edge_dict:
            inward_edges = [self.__edge_dict[from_id][node_id] 
                            for from_id in self.__rev_edge_dict[node_id]]
        return outward_edges, inward_edges

    def get_edges(self):
        """ Returns a list of SimpleEdge class objects contained in the bundle. """
        ret = []
        for end_dict in self.__edge_dict.values():
            for edge in end_dict.values():
                ret.append(edge)
        return ret

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates edge elements of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.

        """
        str_list = []
        for edge in self.get_edges():
            str_list.append(edge.gen_element(indent_num=indent_num, indent_width=indent_width))
        return '\n'.join(str_list)


    def __getitem__(self, item):
        start, end = item
        return self.__edge_dict[start][end].get_label_dict()

    def __call__(self, data=False):
        """ Returns a list of data of edges. """
        ret = []
        for end_dict in self.__edge_dict.values():
            for edge in end_dict.values():
                ret.append(edge.data(data=data))
        return ret

    def __iter__(self):
        """ Works like edges of networkx. """
        yield from self.__call__()


class SimpleGraph():
    """ A class for labelled directed graphs.

    The purpose of this class is to enhance the portability of the grammar.py module.

    In the Grammar class, some fundamental graph handling are required.
    The famous networkx library DO works well for such tasks, 
    however, the installation of the networkx requires internet access and pip,
    and the most of the methods are unnecessary for the tasks.

    To let the grammar.py module be self-contained, 
    this class implements a simplifed version of the DiGraph class of the networkx.

    """
    def __init__(self):
        self.nodes = SimpleNodeBundle()
        self.edges = SimpleEdgeBundle()

    def __getitem__(self, item):
        if isinstance(item, tuple):
            start_node_id = item[0]
            end_node_id = item[1]
            self.node_dict[start_node_id]

    def existp(self, node_id):
        """ Checks if a node with the given id exists. """
        return self.nodes.existp(node_id)

    def is_valid_edges(self):
        """ Checks if the start node and the end node of each edge belong to the vertices set. """
        for edge in self.edges():
            if not self.existp(edge[0]):
                return False
            if not self.existp(edge[1]):
                return False
        return True
        

    def add_node_by_simple_node(self, node):
        """

        Args:
            node(SimpleNode): A node to be added

        """
        if self.existp(node.node_id):
            self.remove_node(node.node_id)
        self.nodes.add_node(node)

    def add_node(self, node_id, **attr):
        """ Creates a SimpleNode class object with the given id and labels, and
            add it into the node_dict.

        Args:
            node_id: An identifier for a node.
                     This value becomes a key for the node_dict of the nodes..
            attr: Label names and thieir labels.

        """
        self.add_node_by_simple_node(SimpleNode(node_id, label_dict=attr))

    def add_nodes_from(self, node_list):
        """ Creates multiple nodes and add them into the node_dict.

        Args:
            node_list(list): Each element of the list is a pair
                             of a node_id and its label_dict
                             or a node_id.

        """
        for data in node_list:
            if isinstance(data, tuple):
                self.add_node(data[0], **data[1])
            else:
                self.add_node(data[0])
                
    def remove_node(self, node_id):
        """ Removes a node and edges connecting with it. 

        Args:
            node_id: The node_id member value of a SimpleNode class object.
        
        
        """
        outward_edges, inward_edges = self.edges.get_connecting_edges(node_id)
        self.nodes.remove_node(node_id)
        self.remove_edges_from(outward_edges)
        self.remove_edges_from(inward_edges)

    def remove_nodes_from(self, node_list):
        for node_id in node_list:
            self.remove_node(node_id)

    def add_edge_by_simple_edge(self, edge, ignore_existence_of_node=False):
        """ Adds a SimpleEdge object to the edges. """
        start_node_id, end_node_id = edge.data()
        if not ignore_existence_of_node:
            if not self.nodes.existp(start_node_id):
                raise GraphNodeAbsenceError(start_node_id)
                #raise KeyError("The node " + str(start_node_id) + " does not exist.")
            if not self.nodes.existp(end_node_id):
                raise GraphNodeAbsenceError(end_node_id)
                #raise KeyError("The node " + str(end_node_id) + " does not exist.")
        self.edges.add_edge(edge)

    def add_edge(self, start_node_id, end_node_id, **attr):
        """ Creates a SimpleEdge class object with the given id and labels, and
            add it into the node_dict.

        Args:
            start_node_id: An identifier for a node.
                           This value becomes a key for the edge_dict of the edges.
            end_node_id: An identifier for a node.
                         This value becomes a key for the edge_dict of the edges.
            attr: Label names and thieir labels.

        """
        if not self.nodes.existp(start_node_id):
            self.add_node(start_node_id)
        if not self.nodes.existp(end_node_id):
            self.add_node(end_node_id)
        self.add_edge_by_simple_edge(SimpleEdge(start_node_id, end_node_id, label_dict=attr))

    def add_edges_from(self, edge_list):
        """ Creates multiple edges form the list.

        Args:
            edge_list(list): Each element of the list is 
                             a pair of the start_node_id and the end_node_id
                             or a tuple of them and the label dictionary.

        """
        for data in edge_list:
            if len(data) == 3:
                self.add_edge(data[0], data[1], **data[2])
            else:
                self.add_edge(data[0], data[1])

    def remove_edge(self, start_node_id, end_node_id):
        self.edges.remove_edge(self.edges[start_node_id, end_node_id])

    def remove_edges_from(self, edge_list):
        for edge in edge_list:
            if isinstance(edge, SimpleEdge):
                start, end = edge.data()
                self.remove_edge(start, end)
            else:
                self.remove_edge(edge[0], edge[1])

    def in_edges(self, node_id, data=False):
        """ Returns inward edges connecting with the node. 
        
        Args:
            data(bool, optional): If True, each element of the returned list
                                  is a tuple (start_node_id, end_node_id, label_dict).
        
        """
        outward_edges, inward_edges = self.edges.get_connecting_edges(node_id)
        return [edge.data(data=data) for edge in inward_edges]

    def out_edges(self, node_id, data=False):
        """ Returns outward edges connecting with the node. 
        
        Args:
            data(bool, optional): If True, each element of the returned list
                                  is a tuple (start_node_id, end_node_id, label_dict).
        
        """
        outward_edges, inward_edges = self.edges.get_connecting_edges(node_id)
        return [edge.data(data=data) for edge in outward_edges]

    def convert_into_networkx(self, id_converter={}):
        """ Generates a networkx DiGraph object from the instance. 

        By giving id_converter, the IDs of the nodes can be converted.
        
        Args:
            id_converter(dict): The keys are the IDs of nodes.
                                The values are the newly allocated value.
        
        """
        import networkx
        g = networkx.DiGraph()
        if len(id_converter) == 0:
            g.add_nodes_from(self.nodes(data=True))
            g.add_edges_from(self.edges(data=True))
        else:
            nodes = [(id_converter[p[0]], p[1]) for p in self.nodes(data=True)]
            edges = [(id_converter[p[0]], id_converter[p[1]], p[2]) for p in self.edges(data=True)]
            g.add_nodes_from(nodes)
            g.add_edges_from(edges)
        return g

    def _networkx_dimatcher_generator(self, target_graph, node_match=None, edge_match=None):
        """ Returns a networkx DiGraphMatcher class object. 
        
        The node_match is a function from attribute dictionaries of two nodes to bool.
        i.e. the node_match is called in the form of ::

            node_match(G1.nodes[n1], G2.nodes[n2])

        The node_match returns True if and only if the nodes[n1] and nodes[n2] are considered
        equal nodes durieng isomorphism check.
        When node_match is None, the attributes of the nodes are not considererd during the isomorphism
        check.

        In the case of the edge_match, the function is called like::
            
            edge_match(G1.edges[u1][u2], G2.edges[u1][u2])

        This function also returns True if and only if the two edges are considered as same during 
        the checking process.
        As the node_match, setting edge_match None makes the attributes of the edges unconsidered
        during the process.

        See the document of the networkx for further description 
        (https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.isomorphism.GraphMatcher.__init__.html#networkx.algorithms.isomorphism.GraphMatcher.__init__)

        Args:
            target_graph(networkx.DiGraph): The target graph searched for subgraphs
                                            which are isomorphc with the self graph.
            node_match(function): The node_match for DiGraphMatcher.
            edge_match(function): The edge_match for DiGraphMatcher.
        
        """
        import networkx
        from networkx.algorithms.isomorphism.vf2userfunc import DiGraphMatcher
        g = self.convert_into_networkx()
        return DiGraphMatcher(target_graph, g, node_match=node_match, edge_match=edge_match)

    def find_subgraph_labelless_morphism(self, target_graph):
        """ Returns a list of dictionaries which represent subgraph morphisms.

        Note:
            Each matching can be seen as a labelless morphism from the graph of the self to the target_graph.
            The keys of the dictionaries in the returned list are the node ids of the self graph.
            The values are the node ids of the target_graph.        
        
        Examples:
            
            * an_instance_graph_node_id: An identifier for a node in the self graph.
            * an_instance: A SimpleGraph class object.
            * i: An index.

            >>> matchings = an_instance.find_matching(target_graph)
            >>> matching = matchings[i]
            >>> matching[an_instance_graph_node_id] in target_graph.nodes 
                True

        Note:
            The structure of the returned dictionary is reverse of the result of 
            subgraph_isomorphisms_iter of the networkx library.

        Args:
            target_graph(networkx.DiGraph): The target graph searched for subgraphs
                                            which are isomorphic with the instance graph.


        """
        morphisms = self._networkx_dimatcher_generator(
                target_graph, 
                node_match=None, 
                edge_match=None)
        return [dict(zip(morphism.values(), morphism.keys())) for morphism 
                in morphism.subgraph_isomorphisms_iter()]


    def find_subgraph_labelled_morphism(self, target_graph):
        """ Returns a list of dictionaries which represent subgraph morphisms.

        Note:
            Each matching can be seen as a labelled morphism from the graph of the self to the target_graph.
            The keys of the dictionaries in the returned list are the node ids of the self graph.
            The values are the node ids of the target_graph.        
        
        Examples:
        
            * an_instance_graph_node_id: An identifier for a node in the self graph.
            * an_instance: A SimpleGraph class object.
            * i: An index.

            >>> matchings = an_instance.find_matching(target_graph)
            >>> matching = matchings[i]
            >>> matching[an_instance_graph_node_id] in target_graph.nodes 
                True

        Note:
            The structure of the returned dictionary is reverse of the result of 
            subgraph_isomorphisms_iter of the networkx library.

        Args:
            target_graph(networkx.DiGraph): The target graph searched for subgraphs
                                            which are isomorphic with the instance graph.

        """
        morphisms = self._networkx_dimatcher_generator(
                target_graph, 
                node_match=self.node_match, 
                edge_match=self.edge_match)
        return [dict(zip(morphism.values(), morphism.keys())) for morphism 
                in morphisms.subgraph_isomorphisms_iter()]


    def find_matching(self, target_graph):
        """ Returns a list of dictionaries which represent matchings.

        Each matching can be seen as a morphism fromthe graph of the self to the target_graph.
        The keys of the dictionaries in the returned list are the node ids of the self graph.
        The values are the node ids of the target_graph.

        Examples:
            * an_instance: A SimpleGraph class object.
            * an_instance_graph_node_id: An identifier for a node in the an_instance.
            * i: An index.

            >>> matchings = an_instance.find_matching(target_graph)
            >>> matching = matchings[i]
            >>> matching[an_instance_graph_node_id] in target_graph.nodes 
                True

        Note:
            The structure of the returned dictionary is reverse of the result of 
            subgraph_isomorphisms_iter of the networkx library.

        Note:
            To customize the searching process of matchings, override the find_matching method.
            However, overriding the following methods also can change the matching criteria.

                * node_match: Compares the attributes of nodes.
                * edge_match: Compares the attributes of edges.
                * candidate_node_checker: Postprocess for matching candidates.

            See each method for further description.

        Args:
            target_graph(networkx.DiGraph): The target graph searched for subgraphs
                                            which are isomorphic with the instance graph.

        """
        candidates = self.find_subgraph_labelled_morphism(target_graph)
        match_list = []

        for candidate in candidates:
            is_not_candidate = False
            for target_node_id in candidate:
                if not self.candidate_node_checker(target_node_id, candidate, target_graph):
                    is_not_candidate = True
                    break
            if is_not_candidate:
                continue
            else:
                match_list.append(candidate)
        return match_list

    @classmethod
    def node_match(cls, node1_attr, node2_attr):
        """ 

        The node_match is a function from attribute dictionaries of two nodes to bool.
        i.e. the node_match is called in the form of ::

            node_match(G1.nodes[n1], G2.nodes[n2])

        The node_match returns True if and only if the nodes[n1] and nodes[n2] are considered
        equal nodes durieng isomorphism check.
        When node_match is None, the attributes of the nodes are not considererd during the isomorphism
        check.

        Overriding this class method customizes the attributes to be checked.

        This method itself checks the 'name' attribution of the nodes.
        When node1_attr or node2_attr does not have the 'name' label,
        return False.

        Args:
            node1_attr(dictionary): An attribute dictionary for a node.
            node2_attr(dictionary): An attribute dictionary for a node.

        """
        try:
            name1 = node1_attr['name']
            name2 = node2_attr['name']
        except KeyError:
            return False
        #print("name1 = " + name1 + ", name2 = " + name2)
        return name1 == name2

    @classmethod
    def edge_match(cls, edge1_attr, edge2_attr):
        """ 

        The edge_match is a function from attribute dictionaries of two edges to bool.
        i.e. the edge_match is called in the form of ::

            edge_match(G1.edges[u1][u2], G2.edges[u1][u2])

        The edge_match returns True if and only if the edges[u1][u2] and edges[u1][u2] are considered
        equal edges durieng isomorphism check.
        When edge_match is None, the attributes of the edges are not considererd during the isomorphism
        check.

        Overriding this class method customizes the attributes to be checked.

        This method itself checks the 'name' attribution of the edges.
        When edge1_attr or edge2_attr does not have the 'name' label,
        return False.

        When edge1_attr or edge2_attr does not have the 'name' label,
        return False.

        Args:
            edge1_attr(dictionary): An attribute dictionary for a edge.
            edge2_attr(dictionary): An attribute dictionary for a edge.

        """
        try:
            name1 = edge1_attr['name']
            name2 = edge2_attr['name']
        except KeyError:
            return False
        #print("name1 = " + name1 + ", name2 = " + name2)
        return name1 == name2

    def candidate_node_checker(self, target_node_id, candidate, target_graph):
        """ Checks the node in the matching candidate meets additional criteria.
        
        The find_matching call the subgraph_isomorphisms_iter method of the networkx library.
        The method can check the attributes (labels) of the nodes during the searching.
        However, the method does not check other properties of the nodes 
        such as the indegree or the outdegree.

        The candidate_node_checker method works as a checker for the other properties.
        Overriding this method customizes the properties to be checked.

        This method itself checks the indegree and the outdegree of the node.

        Args:
            target_node_id: The identifier of a node of the target_graph.
            candidate(dict): The keys are the node ids of the target_graph.
                             The values are the node ids of the graph of the instance.
                             This works as same as the mating of the find_matching method.
                             See the description of the method for further information.
            target_graph(DiGraph): The target graph for which the candidate can be a matching.

        
        """
        instance_node_id = candidate[target_node_id]
        if len(target_graph.in_edges(target_graph_node_id)) != len(self.in_edges(instance_node_id)):
            return False
        if len(target_graph.out_edges(target_graph_node_id)) != len(self.out_edges(instance_node_id)):
            return False
        return True

    @classmethod
    def parse_graph_element(cls, 
            graph_element, 
            ignore_absence_of_base=False, 
            ignore_existence_of_node=False,
            initial_graph=None):
        """ Parses a graph element of a GGDL file and generate an object.

        Args:
            graph_element(Element): The element to be parsed.
            ignore_absence_of_base(bool): If true, this method will not call an error for the absence
                                          of the base node.
            ignore_existence_of_node(bool): If true, this method will not call an error even when
                                            the start node or the end node of an edge does not belong
                                            to the vertices set.
            initial_graph(None or cls): The initial graph. This graph needs to belong the same class
                                        of the returned graph.

        Note:
            This method is destructive.
            The initial_graph will be modified in the process.

        """
        if initial_graph is None:
            graph = cls()
        elif type(initial_graph) is cls:
            graph = initial_graph
        else:
            raise InvalidTypeError(initial_graph, cls)
        edge_id_set = set()

        base_symbol = graph_element.get('base')
        if base_symbol is None:
            if not ignore_absence_of_base:
                raise ElementAttributeAbsenceError(graph_element, 'base')
                #raise ValueError("The graph element does not have the base attribute.")
        else:
            label_dict = {key:value for key, value in graph_element.attrib.items() if key not in ['base']}
            label_dict['name'] = base_symbol
            base_node = SimpleNode('base', label_dict=label_dict)
            graph.add_node_by_simple_node(base_node)

        for node_element in graph_element.findall('node'):
            node = SimpleNode.parse_node_element(node_element)
            if graph.existp(node.node_id):
                raise DuplicatedIdError(node.node_id, optional_description='(In checking node elements)')
                #raise ColoredException('A duplicated node ID is detected (id = ' + str(node.node_id) + ')')
            graph.add_node_by_simple_node(node)

        for edge_element in graph_element.findall('edge'):
            edge = SimpleEdge.parse_edge_element(edge_element)
            if edge.edge_id in edge_id_set:
                raise DuplicatedIdError(edge.edge_id, optional_description='(In checking edge elements)')
                #raise ColoredException('A duplicated edge ID is detected (id = ' + str(edge.edge_id) + ')')
            graph.add_edge_by_simple_edge(edge, ignore_existence_of_node=ignore_existence_of_node)
            edge_id_set.add(edge.edge_id)
            # The edge_type property currently is not supported.
            #if edge_type == 'bi':
            #    rhs_graph.add_edge_by_simple_edge(
            #            SimpleEdge(edge(1), edge(0), label_dict=edge.get_label_dict()))
        return graph



    #def gen_labelled_strong_morphism_finder(self):
    #    """ Returns a function which returns a networkx DiGraphMatcher classs object.
    #
    #    The returned function takes a DiGraph object as its argument.
    #    The DiGraphMatcher object finds labelled morphisms.
    #
    #    """
    #    pass

    def gen_element_graph(self, indent_num=0, indent_width=2):
        """ Generates a graph element of GGDL files. 

        Inheritance classes may want to call the gen_element of the SimpleGraph class.
        To make that possible virtually, define the gen_element_graph and 
        make the gen_element of the SimpleGraph be just a wrapper of the gen_element_graph.

        Args:   
            indent_num(int): The number of indents.
            indent_width(int): The width of a single indent.

        
        """
        str_list = []
        exception_id_list = ['base']
        try:
            base_node = self.nodes.get_node('base')
            base_name = base_node['name']
            temp = ' '*indent_width*indent_num + '<graph base="' + base_name + '"'
            for label_name, label_value in base_node.data(data=True)[1].items():
                if label_name not in ['id', 'name']:
                    temp += ' ' + label_name + '="' + str(label_value) + '"'
            temp += '>'
        except KeyError:
            temp = ' '*indent_width*indent_num + '<graph>'
            pass
        str_list.append(temp)
        str_list.append(self.nodes.gen_element(
            indent_num=indent_num+1, 
            indent_width=indent_width,
            exception_id_list=exception_id_list))
        str_list.append(self.edges.gen_element(indent_num=indent_num+1, indent_width=indent_width))
        temp = ' '*indent_width*indent_num + '</graph>'
        str_list.append(temp)
        return '\n'.join(str_list)

    def gen_element(self, indent_num=0, indent_width=2):
        """ Wraps gen_element_graph.

        Args:   
            base_node(SimpleNode): A node correspoinding to the base attribute.
            indent_width(int): The width of a single indent.
        
        """       
        return self.gen_element_graph(indent_num=indent_num, indent_width=indent_width)



class SimpleExoticGraph(SimpleGraph):
    """ A class for graphs containing exotic nodes. 
    
    GGDL handles graphs with special nodes distingushed from ordinary nodes.
    This class handles such exotic nodes and stores them in exotic_nodes.
    Also, this class provides some override methods for safely handling exotic nodes.
    
    """
    exotic_class = 'exotic'
    def __init__(self):
        super().__init__()
        self.exotic_nodes = SimpleNodeBundle()

    def add_exotic_node(self, node_id, label_dict={}):
        """ Adds an exotic node to the exotic_nodes.

        The object is stored differently from ordinary nodes.
        However, the case such that an exotic node and an ordinary node
        have a same node_id may cause confusion.

        Thus, when node_id is used by an ordinary node, 
        this method removes the ordinary node, then continues the procedure.

        Args:
            node_id: An identifier for the exotic node.
            label_dict(dict, optional): Labels for the exotic node.

        """
        if self.nodes.existp(node_id):
            #raise ColoredException("The node id is already used by a non-" + \
            #        self.exotic_class +" node.")
            self.remove_node(node_id)
        self.exotic_nodes.add_node(SimpleNode(node_id, label_dict=label_dict))

    def existp(self, node_id):
        """ Method Override. """
        return self.nodes.existp(node_id) or self.exotic_nodes.existp(node_id)

#    def add_node_by_simple_node(self, node):
#        """ Overrides the add_node_by_simple_node method.
#
#        When node_id is used by an exotic node, this method removes the exotic node and 
#        continues the procedure.
#
#        Args:
#            node: A SimpleNode class object.
#
#        """
#        if self.exotic_nodes.existp(node.data()):
#            self.remove_node(node.node_id)
#            #raise ColoredException("The node id is already used by a " + \
#            #        self.exotic_class +" node.")
#        super().add_node_by_simple_node(node)

    def remove_node(self, node_id):
        """ Method override. """
        if self.is_exotic_node(node_id):
            outward_edges, inward_edges = self.edges.get_connecting_edges(node_id)
            self.exotic_nodes.remove_node(node_id)
            self.remove_edges_from(outward_edges)
            self.remove_edges_from(inward_edges)
        else:
            super().remove_node(node_id)


    def add_edge_by_simple_edge(self, edge, ignore_existence_of_node=False):
        """ Overrides the add_node_by_simple_node method."""
        start_node_id, end_node_id = edge.data()
        if not ignore_existence_of_node:
            if not self.nodes.existp(start_node_id):
                if not self.exotic_nodes.existp(start_node_id):
                    raise GraphNodeAbsenceError(start_node_id)
                    #raise KeyError("The node " + str(start_node_id) + " does not exist.")
            if not self.nodes.existp(end_node_id):
                if not self.exotic_nodes.existp(end_node_id):
                    raise GraphNodeAbsenceError(end_node_id)
                    #raise KeyError("The node " + str(end_node_id) + " does not exist.")
        self.edges.add_edge(edge)

    def sort_out_edges(self):
        """ Returns a tuple of edges. 

        This method sorts out edges into:
            * edges between ordinary nodes.
            * edges from an exotic node  to an ordinary node.
            * edges from an ordinary node to an exotic node. 
            * edges between exotic nodes.

        """
        edges_between_nodes = [] 
        edges_from_exotic_to_node = []
        edges_from_node_to_exotic = []
        edges_between_exotics = []
        for edge in self.edges.get_edges():
            if self.nodes.existp(edge(0)):
                if self.nodes.existp(edge(1)):
                    edges_between_nodes.append(edge)
                else:
                    edges_from_node_to_exotic.append(edge)
            else:
                if self.nodes.existp(edge(1)):
                    edges_from_exotic_to_node.append(edge)
                else:
                    edges_between_exotics.append(edge)
        return edges_between_nodes, edges_from_exotic_to_node, \
                edges_from_node_to_exotic, edges_between_exotics

    def get_exotic_nodes(self):
        """ Returns exotic_nodes. """
        return self.exotic_nodes

    def de_exotic(self):
        """ Generates a SimpleGraph object by removing all the exotic node. """
        g = SimpleGraph()
        g.add_nodes_from(self.nodes(data=True))
        edge_sort = self.sort_out_edges()
        g.add_edges_from([edge.data(data=True) for edge in edge_sort[0]])
        return g

    def is_exotic_node(self, node_id):
        """ Checks if the node with the given node_id is a exotic node. """
        return node_id in self.exotic_nodes

    def gen_element(self, exotic_graph_tag, exotic_node_tag, indent_num=0, indent_width=2):
        """ Generates a graph element of GGDL files. 

        Args:   
            exotic_graph_tag(str): The tag for the element representing the exotic graph.
                                   e.g. 'agraph', 'wgraph'.
            exotic_node_tag(str): The tag for the element representing the exotic node.
                                   e.g. 'anode', 'wnode'.
            indent_num(int): The number of indents.
            indent_width(int): The width of a single indent.
        
        """
        str_list = []
        temp = ' '*indent_width*indent_num + '<' + exotic_graph_tag + '>'
        str_list.append(temp)
        str_list.append(self.nodes.gen_element(indent_num=indent_num+1, indent_width=indent_width))
        str_list.append(self.exotic_nodes.gen_element(
            indent_num=indent_num+1, 
            indent_width=indent_width,
            tag=exotic_node_tag))
        str_list.append(self.edges.gen_element(indent_num=indent_num+1, indent_width=indent_width))
        temp = ' '*indent_width*indent_num + '</' + exotic_graph_tag + '>'
        str_list.append(temp)
        return '\n'.join(str_list)
 
    def convert_into_networkx(self):
        """ Overrides the convert_into_networkx of the SimpleGraph class.

        The exotic nodes is converted into a node with the attribute '__exotic'.
        The value of the attribute is the one of the exotic_class.
        
        """
        import networkx
        g = super().convert_into_networkx()
        # Add exotic nodes with label '__exotic'
        g.add_nodes_from([(p[0], dict(**p[1], **{'__exotic':self.exotic_class}))
            for p in self.exotic_nodes(data=True)])
        #print("nodes = " + str(g.nodes(True)))
        return g

    @classmethod
    def parse_graph_element(cls, graph_element, exotic_node_tag, optional_exotic_nodes=None):
        """ Parses an exotic graph element of a GGDL file and generate an object.

        Args:
            graph_element(Element): The element to be parsed.
            exotic_node_tag(str): The tag for exotic node.
            optional_exotic_nodes(SimpleNodeBundle or None): A bundle of exotic nodes to be added externaly.

        """
        graph = cls()
        #print("CLS = " + graph.__class__.__name__)

        for exotic_node_element in graph_element.findall(exotic_node_tag):
            node_id = exotic_node_element.get('id')
            if node_id is None:
                raise ElementAttributeAbsenceError(exotic_node_element, 'id')
                #raise ValueError('The ' + exotic_node_tag + ' dose not have the "id" attribute.')
            if graph.existp(node_id):
                raise DuplicatedIdError(node_id, optional_description='(In checking exotic node elements)')
            graph.add_exotic_node(node_id, label_dict=exotic_node_element.attrib)

        if optional_exotic_nodes is not None:
            for node_id in optional_exotic_nodes:
                graph.add_exotic_node(node_id, label_dict=optional_exotic_nodes[node_id])
        if not graph.is_valid_edges():
            for edge in graph.edges():
                if not graph.existp(edge[0]):
                    raise GraphNodeAbsenceError(edge[0])
                if not graph.existp(edge[1]):
                    raise GraphNodeAbsenceError(edge[1])

        graph = super().parse_graph_element(
                graph_element, 
                ignore_absence_of_base=True, 
                ignore_existence_of_node=False,
                initial_graph=graph)

        return graph
    

class SimpleAnchorGraph(SimpleExoticGraph):
    """ A class for graphs with anchor nodes.

    The concept of 'anchor node' is introduced by Guo et al. in 
    "Data-efficient graph grammar learning for molecular generation" (2022), 
    in the context of graph grammar theory.

    The anchor node is handled as a node which matches any node in the process of subgraph matching.
    For theoretical description, see GGDLParser.

    """
    exotic_class = 'anchor'

    def add_edge_by_simple_edge(self, edge, ignore_existence_of_node=False):
        """ Method override.

        Anchor graphs does not allows edges between anchor nodes.
        Therefore, if the given edge is such the one, call an error.

        """
        start_node_id, end_node_id = edge.data()
        if self.is_anchor_node(start_node_id) and self.is_anchor_node(end_node_id):
            raise InvalidExoticGraphError("Edges between anchor nodes are not allowed.")
        super().add_edge_by_simple_edge(edge, ignore_existence_of_node=ignore_existence_of_node)

    def add_anchor_node(self, node_id):
        """ Wraps add_exotic_node

        Args:
            node_id: An identifier for the anchor node.

        """
        self.add_exotic_node(node_id)

    def get_anchor_nodes(self):
        """ Wraps get_exotic_nodes. """
        return self.get_exotic_nodes()

    def de_anchor(self):
        """ Wraps de_exotic. """
        return self.de_exotic()

    def is_anchor_node(self, node_id):
        """ Wraps is_exotic_node. """
        return self.is_exotic_node(node_id)


    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a graph element of GGDL files. 

        Args:   
            indent_num(int): The number of indents.
            indent_width(int): The width of a single indent.
        
        """
        return super().gen_element('agraph', 'anode', indent_num=indent_num, indent_width=indent_width)
    
    @classmethod
    def __node_match(cls, node1_attr, node2_attr):
        """ Overrides the node_match of the SimpleGraph class.

        When node1_attr or node2_attr has the '__exotic' label, return True.
        Otherwise, this method calls the super class method.

        Args:
            node1_attr(dictionary): An attribute dictionary for a node.
            node2_attr(dictionary): An attribute dictionary for a node.

        """
        try:
            exotic_class1 = node1_attr['__exotic']
            if exotic_class1 == cls.exotic_class:
                return True
        except KeyError:
            pass
        try:
            exotic_class2 = node2_attr['__exotic']
            if exotic_class2 == cls.exotic_class:
                return True
        except KeyError:
            pass           
        return super().node_match(node1_attr, node2_attr)

    def __candidate_node_checker(self, target_node_id, candidate, target_graph):
        """ Overrides the candidate_node_checker method of the SimpleGraph class.

        Basically, as the method of the super class, this method checks 
        the indegree and the outdegree of the node.
        When the target_node_id corresponds to an anchor node, 
        this method immediately return True.
        
        """
        instance_node_id = candidate[target_node_id]
        if self.is_anchor_node(instance_node_id):
            return True
        
        if len(target_graph.in_edges(target_node_id)) != len(self.in_edges(instance_node_id)):
            return False
        if len(target_graph.out_edges(target_node_id)) != len(self.out_edges(instance_node_id)):
            return False
        return True

    def find_matching(self, target_graph):
        """ Fully overrides the find_matching method of the SimpleGraph class. """
        pattern = self.de_anchor()
        #print("pattern node = " + str(pattern.nodes(data=True)))
        #print("pattern edge = " + str(pattern.edges()))
        # The partial_matches below cares only the labels of nodes and edges.
        partial_matches = pattern.find_subgraph_labelled_morphism(target_graph)
        #print("partial_matches = " + str(partial_matches))
        matches = []

        # Discard matches which contain a node which has exceeding degree.
        for i in range(len(partial_matches)):
            pm = partial_matches[i]
            anchor_patterns_of_each_node = {}
            is_invalid_pm = False
            # print("pm = " + str(pm))
            for instance_node_id in pm:
                pattern_in_edges = self.in_edges(instance_node_id)
                pattern_out_edges = self.out_edges(instance_node_id)

                target_node_id = pm[instance_node_id]
                target_in_edges = target_graph.in_edges(target_node_id)
                target_out_edges = target_graph.out_edges(target_node_id)
                #print("target_in_edges = " + str(target_in_edges))
                #print("target_out_edges = " + str(target_out_edges))

                if len(target_in_edges) != len(pattern_in_edges):
                    is_invalid_pm = True
                    break
                if len(target_out_edges) != len(pattern_out_edges):
                    is_invalid_pm = True
                    break

                # check out possible anchor patterns
                # Get nodes which can match with anchors.
                # Those nodes must be chosen from nodes not in the partial match.
                anchor_candidate_in = [edge[0] for edge in target_in_edges if edge[0] not in pm.values()]
                anchor_candidate_out = [edge[1] for edge in target_out_edges if edge[1] not in pm.values()]
                #print("anchor_candidate_in = " + str(anchor_candidate_in))
                #print("anchor_candidate_out = " + str(anchor_candidate_out))

                anchor_in = [edge[0] for edge in pattern_in_edges if self.is_anchor_node(edge[0])]
                anchor_out = [edge[1] for edge in pattern_out_edges if self.is_anchor_node(edge[1])]
                #print("anchor_in = " + str(anchor_in))
                #print("anchor_out = " + str(anchor_out))

                anchor_num_in = len(anchor_in)
                anchor_num_out = len(anchor_out)

                # Check out all the permutation patterns of the anchors.
                patterns_in = set(itertools.permutations(anchor_candidate_in, anchor_num_in))
                patterns_out = set(itertools.permutations(anchor_candidate_out, anchor_num_out))

                # Save the patterns in the same format with pm.
                # i.e. a dictionary which takes node_ids of the exotic_nodes (anchors) of self
                #      and returns the corresponding node ids of the target_graph.
                anchor_pattern = []
                for pattern_in in patterns_in:
                    for pattern_out in patterns_out:
                        added_pattern = dict(zip(anchor_in + anchor_out, pattern_in + pattern_out))
                        non_none_anchors = {k:v for k, v in added_pattern.items() if v is not None}
                        # Note: In the added_pattern, more than two anchors can matches with a single node.
                        # e.g. {'-1':1, '-2':1, ... } ('-1', and '-2' are the ids for the anchors.)
                        # Such the cases are not acceptable, therefore reject such the patterns.
                        if len(set(non_none_anchors.keys())) == len(set(non_none_anchors.values())):
                                anchor_pattern.append(added_pattern)

                anchor_patterns_of_each_node[instance_node_id] = anchor_pattern

            if is_invalid_pm:
                continue
            # The validity of all the nodes is confirmed, and all the anchor patterns are collected.

            # Concatenate the partial match with a anchor pattern
            # and add it into the matches.
            for anchor_pattern_of_nodes in itertools.product(*anchor_patterns_of_each_node.values()):
                # anchor_pattern_of_all_nodes is a tuple of dictionaries.
                copied_pm = copy.deepcopy(pm)
                matches.append(reduce(lambda d1, d2: {**d1, **d2}, anchor_pattern_of_nodes, pm))

        return matches



    @classmethod
    def parse_graph_element(cls, graph_element, optional_anchor_nodes=None):
        """ Parses an exotic graph element of a GGDL file and generate an object.

        Args:
            graph_element(Element): The element to be parsed.

        """
        return super().parse_graph_element(graph_element, 'anode', optional_anchor_nodes)


class SimpleWildcardGraph(SimpleExoticGraph):
    """ A class for graphs with wildcard nodes.

    The concept of 'wildcard node' is minor change of 'anchor node'. 

    The wildcard node is handled as a node which matches any node like anchor node.
    Even when no nodes corresponds to a wildcard node in a pattern graph, 
    the pattern is regarded as matched.

    """
    exotic_class = 'wildcard'

    def add_edge_by_simple_edge(self, edge, ignore_existence_of_node=False):
        """ Method override.

        Wildcard graphs does not allows edges between wildcard nodes.
        Therefore, if the given edge is such the one, call an error.

        """
        start_node_id, end_node_id = edge.data()
        if self.is_wildcard_node(start_node_id) and self.is_wildcard_node(end_node_id):
            raise InvalidExoticGraphError("Edges between wildcard nodes are not allowed.")
        super().add_edge_by_simple_edge(edge, ignore_existence_of_node=ignore_existence_of_node)

    def add_wildcard_node(self, node_id):
        """ Wraps add_exotic_node

        Args:
            node_id: An identifier for the wildcard node.

        """
        self.add_exotic_node(node_id)

    def get_wildcard_nodes(self):
        """ Wraps get_exotic_nodes. """
        return self.get_exotic_nodes()

    def de_wildcard(self):
        """ Wraps de_exotic """
        return self.de_exotic()

    def is_wildcard_node(self, node_id):
        """ Wraps is_exotic_node. """
        return self.is_exotic_node(node_id)

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a graph element of GGDL files. 

        Args:   
            indent_num(int): The number of indents.
            indent_width(int): The width of a single indent.
        
        """
        return super().gen_element('wgraph', 'wnode', indent_num=indent_num, indent_width=indent_width)

    def candidate_node_checker(self, target_node_id, candidate, target_graph):
        """ Checks the node in the matching candidate meets additional criteria."""
        return True
    
    def find_matching(self, target_graph):
        """ Fully overrides the find_matching method of the SimpleGraph class. """
        pattern = self.de_wildcard()
        #print("pattern node = " + str(pattern.nodes(data=True)))
        #print("pattern edge = " + str(pattern.edges()))
        # The partial_matches below cares only the labels of nodes and edges.
        partial_matches = pattern.find_subgraph_labelled_morphism(target_graph)
        #print("partial_matches = " + str(partial_matches))
        matches = []

        # Discard matches which contain a node which has exceeding degree.
        for i in range(len(partial_matches)):
            pm = partial_matches[i]
            wildcard_patterns_of_each_node = {}
            is_invalid_pm = False
            # print("pm = " + str(pm))
            for instance_node_id in pm:
                pattern_in_edges = self.in_edges(instance_node_id)
                pattern_out_edges = self.out_edges(instance_node_id)

                target_node_id = pm[instance_node_id]
                target_in_edges = target_graph.in_edges(target_node_id)
                target_out_edges = target_graph.out_edges(target_node_id)
                #print("target_in_edges = " + str(target_in_edges))
                #print("target_out_edges = " + str(target_out_edges))

                if len(target_in_edges) > len(pattern_in_edges):
                    is_invalid_pm = True
                    break
                if len(target_out_edges) > len(pattern_out_edges):
                    is_invalid_pm = True
                    break

                # check out possible wildcard patterns
                # Get nodes which can match with wildcards.
                # Those nodes must be chosen from nodes not in the partial match.
                wildcard_candidate_in = [edge[0] for edge in target_in_edges if edge[0] not in pm.values()]
                wildcard_candidate_out = [edge[1] for edge in target_out_edges if edge[1] not in pm.values()]
                #print("wildcard_candidate_in = " + str(wildcard_candidate_in))
                #print("wildcard_candidate_out = " + str(wildcard_candidate_out))

                wildcard_in = [edge[0] for edge in pattern_in_edges if self.is_wildcard_node(edge[0])]
                wildcard_out = [edge[1] for edge in pattern_out_edges if self.is_wildcard_node(edge[1])]
                #print("wildcard_in = " + str(wildcard_in))
                #print("wildcard_out = " + str(wildcard_out))

                wildcard_num_in = len(wildcard_in)
                wildcard_num_out = len(wildcard_out)
                num_of_absent_nodes_in = wildcard_num_in - len(wildcard_candidate_in)
                num_of_absent_nodes_out = wildcard_num_out - len(wildcard_candidate_out)

                # Fullfill candidate lists with None
                wildcard_candidate_in = wildcard_candidate_in + [None] * num_of_absent_nodes_in
                wildcard_candidate_out = wildcard_candidate_out + [None] * num_of_absent_nodes_out
                #print("wildcard_candidate_in = " + str(wildcard_candidate_in))
                #print("wildcard_candidate_out = " + str(wildcard_candidate_out))

                # Check out all the permutation patterns of the wildcards.
                patterns_in = set(itertools.permutations(wildcard_candidate_in, wildcard_num_in))
                patterns_out = set(itertools.permutations(wildcard_candidate_out, wildcard_num_out))

                # Save the patterns in the same format with pm.
                # i.e. a dictionary which takes node_ids of the exotic_nodes (wildcards) of self
                #      and returns the corresponding node ids of the target_graph.
                wildcard_pattern = []
                for pattern_in in patterns_in:
                    for pattern_out in patterns_out:
                        added_pattern = dict(zip(wildcard_in + wildcard_out, pattern_in + pattern_out))
                        non_none_wildcards = {k:v for k, v in added_pattern.items() if v is not None}
                        # Note: In the added_pattern, more than two wildcards can matches with a single node.
                        # e.g. {'-1':1, '-2':1, ... } ('-1', and '-2' are the ids for the wildcards.)
                        # Such the cases are not acceptable, therefore reject such the patterns.
                        if len(set(non_none_wildcards.keys())) == len(set(non_none_wildcards.values())):
                                wildcard_pattern.append(added_pattern)

                wildcard_patterns_of_each_node[instance_node_id] = wildcard_pattern

            if is_invalid_pm:
                continue
            # The validity of all the nodes is confirmed, and all the wildcard patterns are collected.

            # Concatenate the partial match with a wildcard pattern
            # and add it into the matches.
            for wildcard_pattern_of_nodes in itertools.product(*wildcard_patterns_of_each_node.values()):
                # wildcard_pattern_of_all_nodes is a tuple of dictionaries.
                copied_pm = copy.deepcopy(pm)
                matches.append(reduce(lambda d1, d2: {**d1, **d2}, wildcard_pattern_of_nodes, pm))

        return matches

    @classmethod
    def parse_graph_element(cls, graph_element, optional_wildcard_nodes=None):
        """ Parses an exotic graph element of a GGDL file and generate an object.

        Args:
            graph_element(Element): The element to be parsed.

        """
        return super().parse_graph_element(graph_element, 'wnode', optional_wildcard_nodes)




class BaseRule():
    """ A base class for rules of graph grammar. 
    
    See GGDLParser for the theoretical description.

    Instances of this class can be handled as a dictionary-like object.
    As a dictionary, an instance 'rule' accepts following keys:

        * rule['name']: returns the name of the rule.
        * rule['LHS']: returns the object registered as the LHS.
        * rule['RHS']: returns the object registered as the RHS.
        * rule['class']: A string specifying the kind of the rule.
    
    Attributes:
        rule_class(str): Specifying the kind of rule.   
                         Each rule and inheritance class is distinguished
                         by this attribute.
        lhs_element_name(str): The tag of the child element of a rule element passed to parser methods.
                               By checking if the rule element has the child element with this tag, 
                               this class determines the rule element can be parsed.
        rhs_element_name(str): The tag of the child element of a rule element passed to parser methods.
                               By checking if the rule element has the child element with this tag, 
                               this class determines the rule element can be parsed.   

    """
    rule_class = 'base_rule'
    lhs_element_name = 'base_rule_lhs'
    rhs_element_name = 'graph'

    def __init__(self, name, lhs, rhs):
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
        self._check_lhs_format()
        self._check_rhs_format()

    def __getitem__(self, item):
        if item == 'name':
            return self.name
        if item == 'LHS':
            return self.lhs
        if item == 'RHS':
            return self.rhs
        if item == 'class':
            return self.rule_class

    def _check_lhs_format(self):
        if not isinstance(self.lhs, SimpleGraph):
            raise InvalidTypeError(self.lhs, SimpleGraph)
            #raise ValueError("The given LHS is not SimpleGraph object")
        return True

    def _check_rhs_format(self):
        if not isinstance(self.rhs, SimpleGraph):
            raise InvalidTypeError(self.rhs, SimpleGraph)
            #raise ValueError("The given RHS is not SimpleGraph object")
        return True

    def get_lhs_nodes(self):
        return self.lhs.nodes.get_nodes()

    def get_rhs_nodes(self):
        return self.rhs.nodes.get_nodes()

    def gen_element_list(self, indent_num=0, indent_width=2):
        """ Generates a list of strings for element generation. """
        temp1 = ' '*indent_width*indent_num + '<rule name="' + self.name + '">'
        temp2 = ' '*indent_width*indent_num + '</rule>'
        return [temp1, temp2]

    def get_target_subgraph(self, target_graph):
        """ Returns a list of morphisms to subgraphs to which the rule is applicable.

        Note:
            This method needs to be overrided from inheritance classes.

        Args:
            target_graph(DiGraph): A graph searched for subgraphs.

        """
        raise ColoredException("This method should not be called.")

    def apply_rule(self, morphism, target_graph):
        """ Applys the rule to the subgraph of the target_graph specified with the codomain of the morphism.

        Note:
            This method needs to be overrided from inheritance classes.

        Args:
            target_graph(DiGraph): A graph searched for subgraphs.

        """
        raise ColoredException("This method should not be called.")


    @classmethod
    def parse_rule_element(self, rule_element):
        """ Parses a xml element corresponding to a rule and generates an object. 

        Note:
            This method needs to be overrided from inheritance classes.

        Args:
            rule_element(Element): A xml.etree.ElementTree.Element class object to be parsed.
        
        """
        raise ColoredException("This method should not be called.")

    @classmethod
    def is_parsable_rule(cls, rule_element):
        """ Checks if the given rule element has the child elements with the same tags
            lhs_element_name and rhs_element_name."""
        lhs = rule_element.find(cls.lhs_element_name)
        rhs = rule_element.find(cls.rhs_element_name)
        return (lhs is not None) and (rhs is not None)

    @classmethod
    def get_elements(cls, rule_element):
        """ Parses a xml element corresponding to a rule and returns the name, the LHS and the RHS.

        Args:
            rule_element(Element): A xml.etree.ElementTree.Element class object to be parsed.

        Returns:
            name(str): The name of the rule.
            lhs(Element): The element corresponding to the LHS.
            rhs(Element): The element corresponding to the RHS.

        """
        name = rule_element.get('name')
        lhs = rule_element.find(cls.lhs_element_name)
        rhs = rule_element.find(cls.rhs_element_name)

        if name is None:
            raise ElementAttributeAbsenceError(rule_element, 'name')
            #raise ValueError("The given element does not have the name attribute")

        if lhs is None:
            raise ElementAbsenceError(lhs_element_name)
            #raise ColoredException("The element( " + name + " ) does not have the " \
            #        + lhs_element_name + " element.")
        if rhs is None:
            raise ElementAbsenceError(rhs_element_name)
            #raise ColoredException("The element( " + name + " ) does not have the " \
            #        + rhs_element_name + " element.")

        return name, lhs, rhs


class ContextFreeRule(BaseRule):
    """ This class handles context-free rules. 
    
    The LHS is a SimpleNode class object, 
    and the RHS is a SimpleGraph class object which contains a node having 'base' as node_id.
    The rule_class is 'context_free_rule'.
    
    """
    rule_class = 'context_free_rule'
    lhs_element_name = 'nt'
    rhs_element_name = 'graph'

    def _check_lhs_format(self):
        if type(self.lhs) is not SimpleNode:
            raise InvalidTypeError(self.lhs, SimpleNode)
            #raise ValueError("The given LHS is not a SimpleNode class object: " + str(type(self.lhs)))
        return True

    def _check_rhs_format(self):
        #if type(self.rhs) is not tuple:
        #    raise ValueError(self.__error_msg(
        #        "The given RHS is not a tuple: " + str(type(self.rhs))))
        #if len(self.rhs) != 2:
        #    raise ValueError(self.__error_msg("The passed tuple is not a pair."))
        try:
            node = self.rhs.nodes.get_node('base')
        except KeyError:
            raise InvalidRuleError("The RHS does not contains a node with the ID 'base'. ")

        #if type(node) is not SimpleNode:
        #    raise ValueError(self.__error_msg(
        #        "The first element of the RHS is not a SimpleNode class object: " + str(type(node))))
 
        if type(self.rhs) is not SimpleGraph:
            raise Invalid(self.rhs, SimpleGraph)
            #raise ValueError(
                    #"The second element of the RHS is not a SimpleGraph class object: " + str(type(graph)))

        return True

    def get_lhs_nodes(self):
        return [self.lhs]

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.

        """
        str_list = self.gen_element_list(indent_num=indent_num, indent_width=indent_width)
        temp = '<nt name="' + self.lhs['name'] + '"'
        for key in self.lhs.data(data=True)[1]:
            if key not in ['name']:
                temp += ' ' + key +'="' + str(self.lhs[key]) + '"'
        temp += '/>'
        str_list.insert(1, ' '*indent_width*(indent_num + 1) + temp)

        str_list.insert(2, self.rhs.gen_element_graph(
                indent_num=indent_num + 1,
                indent_width=indent_width))
        return '\n'.join(str_list)

 
    def get_target_subgraph(self, target_graph):
        """ Returns a list of morphisms to subgraphs to which the rule is applicable.

        Args:
            target_graph(DiGraph): A graph searched for subgraphs.

        Returns:
            list: Each element is a node id of the target graph.
                  The node specified with the id have the 'name' attribute of which
                  the value is same as the one of the LHS.

        """
        ret = []
        for node_id in target_graph.nodes:
            try:
                if target_graph.nodes[node_id]['name'] == self['LHS']['name']:
                    ret.append(node_id)
            except KeyError:
                pass
        return ret


    def apply_rule(self, target_node_id, target_graph, id_generator):
        """ Applys the rule to the subgraph of the target_graph specified with the codomain of the morphism.

        Note:
            This method modifies the target_graph.

        Args:
            target_node_id: The id for a node to be replaced.
            target_graph(DiGraph): A graph searched for subgraphs.
            id_generator(function): A function generating an unique id from the ID of the nodes of the RHS.
                                    'Unique' means that the target graph does not have a node with the id,
                                    and the id_generator returns different ids for all the passed ids.

        """
        # Remember the nodes connecting with the target node.
        in_edges =  target_graph.in_edges(target_node_id, data=True)
        out_edges = target_graph.out_edges(target_node_id, data=True)
        
        # Generates a label changer.
        # That corresponds to choosing a graph to be inserted into the target_graph.
        morphism = {node_id:id_generator(node_id) for node_id in self['RHS'].nodes}
        target_graph.add_nodes_from(
                [(morphism[p[0]], p[1]) for p in self['RHS'].nodes(data=True)])
        target_graph.add_edges_from(
                [(morphism[p[0]], morphism[p[1]], p[2]) for p in self['RHS'].edges(data=True)])

        for edge in in_edges:
            target_graph.add_edge(edge[0], morphism['base'], **edge[2])

        for edge in out_edges:
            target_graph.add_edge(morphism['base'], edge[1], **edge[2])
        
        target_graph.remove_node(target_node_id)
       
        
    @classmethod
    def parse_rule_element(cls, rule_element):
        """ Parses a xml element corresponding to a rule and generates an object. 

        Note:
            Context-free grammar version.

        Args:
            rule_element(Element): A xml.etree.ElementTree.Element class object to be parsed.

        """
        name, lhs, rhs = ContextFreeRule.get_elements(rule_element)
        
        # parse lhs.
        lhs_symbol_name = lhs.get('name')
        # define a node with all the attribute.
        lhs_node = SimpleNode("base", label_dict=lhs.attrib) 

        # parse rhs.
        rhs_graph = SimpleGraph.parse_graph_element(rhs)
        return cls(name, lhs_node, rhs_graph)


class AnchorRule(BaseRule):
    """ This class handles rules with anchor graphs. 
    
    The LHS and the RHS passed to the constructor need to be SimpleAnchorGraph class objects.
    The rule_class is 'anchor_rule'.
    
    """
    rule_class = 'anchor_rule'
    lhs_element_name = 'agraph'
    rhs_element_name = 'graph'

    def _check_lhs_format(self):
        super()._check_lhs_format()
        if not isinstance(self.lhs, SimpleAnchorGraph):
            raise InvalidTypeError(self.lhs, SimpleAnchorGraph)
            #raise ValueError("The given LHS is not a SimpleAnchorGraph object.")
        return True 

    def _check_rhs_format(self):
        super()._check_rhs_format()
        if not isinstance(self.rhs, SimpleAnchorGraph):
            raise InvalidTypeError(self.rhs, SimpleAnchorGraph)
            #raise ValueError("The given LHS is not a SimpleAnchorGraph object.")
        if not SimpleNodeBundle.is_same_bundle(
                self.rhs.get_anchor_nodes(), 
                self.lhs.get_anchor_nodes()):
            raise InvalidRuleError("The set of anchors of the LHS is different from the RHS.")
        return True

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.

        """
        str_list = self.gen_element_list(indent_num=indent_num, indent_width=indent_width)
        str_list.insert(1, self.lhs.gen_element(indent_num=indent_num+1, indent_width=indent_width))
        str_list.insert(2, self.rhs.gen_element_graph(
                indent_num=indent_num+1, 
                indent_width=indent_width))
        return '\n'.join(str_list)
        
    def get_target_subgraph(self, target_graph):
        """ Returns a list of morphisms to subgraphs to which the rule is applicable.

        Args:
            target_graph(DiGraph): A graph searched for subgraphs.

        Returns:
            list: Each element is a morphism from the LHS to a subgraph.

        """
        return self['LHS'].find_matching(target_graph)


    def apply_rule(self, morphism, target_graph, id_generator):
        """ Applys the rule to the subgraph of the target_graph specified with the codomain of the morphism.

        Note:
            This method modifies the target_graph.

        Args:
            morphism(dict): A morphism from the LHS to a subgraph.
                            Use one of the morphisms returned from get_target_subgraph.
            target_graph(DiGraph): A graph searched for subgraphs.
            id_generator(function): A function generating an unique id from the ID of the nodes of the RHS.
                                    'Unique' means that the target graph does not have a node with the id,
                                    and the id_generator returns different ids for all the passed ids.

        """
        
        # Generates a label changer.
        # That corresponds to choosing a graph to be inserted into the target_graph.
        morphism_to_new = {node_id:id_generator(node_id) for node_id in self['RHS'].nodes}
        for anchor_node_id in self['LHS'].get_anchor_nodes():
            morphism_to_new[anchor_node_id] = morphism[anchor_node_id]

        target_graph.add_nodes_from(
                [(morphism_to_new[p[0]], p[1]) for p in self['RHS'].nodes(data=True)])
        target_graph.add_edges_from(
                [(morphism_to_new[p[0]], morphism_to_new[p[1]], p[2]) for p in self['RHS'].edges(data=True)])

        # Remove the nodes corresponding the ones of the LHS except for the ones corresponding the anchor nodes.
        target_graph.remove_nodes_from([morphism[node_id] for node_id in self['LHS'].nodes])
        
    @classmethod
    def parse_rule_element(cls, rule_element):
        """ Parses a xml element corresponding to a rule and generates an object. 

        Note:
            Anchor grammar version.

        Args:
            rule_element(Element): A xml.etree.ElementTree.Element class object to be parsed.

        """
        name, lhs, rhs = cls.get_elements(rule_element)
        
        lhs_graph = SimpleAnchorGraph.parse_graph_element(lhs)
        rhs_graph = SimpleAnchorGraph.parse_graph_element(
                rhs, 
                optional_anchor_nodes=lhs_graph.get_anchor_nodes())
       
        return cls(name, lhs_graph, rhs_graph)


class WildcardRule(BaseRule):
    """ This class handles rules with anchor graphs. 
    
    The LHS and the RHS passed to the constructor need to be SimpleWildcardGraph class objects.
    The rule_class is 'wildcard_rule'.
    
    """

    rule_class = 'wildcard_rule'
    lhs_element_name = 'wgraph'
    rhs_element_name = 'graph'

    def _check_lhs_format(self):
        super()._check_lhs_format()
        if not isinstance(self.lhs, SimpleWildcardGraph):
            raise InvalidTypeError(self.lhs, SimpleWildcardGraph)
            #raise ValueError("The given LHS is not a SimpleWildcardGraph object.")

        #edges_between_nodes, edges_from_wildcard_to_node, \
        #        edges_from_node_to_wildcard, edges_between_wildcards = self.lhs.sort_out_edges()
        #if len(edges_between_wildcards) != 0:
        #    raise InvalidRuleError("There exists an edge between wildcards.")

        return True 

    def _check_rhs_format(self):
        super()._check_rhs_format()
        if not isinstance(self.rhs, SimpleWildcardGraph):
            raise InvalidTypeError(self.rhs, SimpleWildcardGraph)
            #raise ValueError("The given LHS is not a SimpleWildcardGraph object.")
        if not SimpleNodeBundle.is_same_bundle(
                self.rhs.get_wildcard_nodes(), 
                self.lhs.get_wildcard_nodes()):
            raise InvalidRuleError("The set of wildcards of the LHS is different from the RHS.")
        return True

    def gen_element(self, indent_num=0, indent_width=2):
        """ Generates a node element of GGDL file.

        Args:
            indent_num(int): The number of indents to be inserted in front of the tag
            indent_width(int): The width of a single indent.

        """
        str_list = self.gen_element_list(indent_num=indent_num, indent_width=indent_width)
        str_list.insert(1, self.lhs.gen_element(indent_num=indent_num+1, indent_width=indent_width))
        str_list.insert(2, self.rhs.gen_element_graph(
                indent_num=indent_num+1, 
                indent_width=indent_width))
        return '\n'.join(str_list)

    def get_target_subgraph(self, target_graph):
        """ Returns a list of morphisms to subgraphs to which the rule is applicable.

        Args:
            target_graph(DiGraph): A graph searched for subgraphs.

        Returns:
            list: Each element is a morphism from the LHS to a subgraph.

        """
        #print("NAME : " + self['name'])
        return self['LHS'].find_matching(target_graph)


    def apply_rule(self, morphism, target_graph, id_generator):
        """ Applys the rule to the subgraph of the target_graph specified with the codomain of the morphism.

        Note:
            This method modifies the target_graph.

        Args:
            morphism(dict): A morphism from the LHS to a subgraph.
                            Use one of the morphisms returned from get_target_subgraph.
            target_graph(DiGraph): A graph searched for subgraphs.
            id_generator(function): A function generating an unique id from the ID of the nodes of the RHS.
                                    'Unique' means that the target graph does not have a node with the id,
                                    and the id_generator returns different ids for all the passed ids.

        """
        
        # Generates a label changer.
        # That corresponds to choosing a graph to be inserted into the target_graph.
        morphism_to_new = {node_id:id_generator(node_id) for node_id in self['RHS'].nodes}
        for wildcard_node_id in self['LHS'].get_wildcard_nodes():
            if morphism[wildcard_node_id] is not None:
                morphism_to_new[wildcard_node_id] = morphism[wildcard_node_id]

        target_graph.add_nodes_from(
                [(morphism_to_new[p[0]], p[1]) for p in self['RHS'].nodes(data=True)])
        target_graph.add_edges_from(
                [(morphism_to_new[p[0]], morphism_to_new[p[1]], p[2]) 
                    for p in self['RHS'].edges(data=True)
                    if (p[0] in morphism_to_new) and (p[1] in morphism_to_new)])

        # Remove the nodes corresponding the ones of the LHS 
        # except for the ones corresponding the wildcard nodes.
        target_graph.remove_nodes_from([morphism[node_id] for node_id in self['LHS'].nodes])
        
    @classmethod
    def parse_rule_element(cls, rule_element):
        """ Parses a xml element corresponding to a rule and generates an object. 

        Note:
            Wildcard grammar version 

        Args:
            rule_element(Element): A xml.etree.ElementTree.Element class object to be parsed.

        """
        name, lhs, rhs = cls.get_elements(rule_element)
        
        lhs_graph = SimpleWildcardGraph.parse_graph_element(lhs)
        rhs_graph = SimpleWildcardGraph.parse_graph_element(
                rhs, 
                optional_wildcard_nodes=lhs_graph.get_wildcard_nodes())
       
        return cls(name, lhs_graph, rhs_graph)
    
class RuleBundle():
    """ A class to bundle BaseRule class objects. 
    
    This class accepts BaseRule class and its inheritance class objects.
    Each rule can be accessed like a dictionary.
    The key is a name of the rule contained.

    """
    def __init__(self):
        self.rule_dict = {}
        self.rule_class_dict = {}

    def add_rule(self, rule):
        """ Adds a BaseRule class object into the bundle. """
        if rule['class'] not in self.rule_class_dict:
            self.rule_class_dict[rule['class']] = {rule['name']}
        else:
            self.rule_class_dict[rule['class']].add(rule['name'])
        self.rule_dict[rule['name']] = rule

    def remove_rule(self, rule_name):
        """ Removes the rule with the given name from rule_dict."""
        rule = self.rule_dict.pop(rule_name)
        self.rule_class_dict[rule['class']].pop(rule['name'])


    def extract_rules_by_class(self, rule_class):
        """ Extracts rules with the given rule_class. 
        
        Args:
            rule_class(str): the BaseRule class attribute.
                             If no rules with it exists in the bundle, 
                             returns the empty set.
        
        """
        if rule_class in self.rule_class_dict:
            return self.rule_class_dict[rule_class]
        else:
            return set()

    def __getitem__(self, item):
        return self.rule_dict[item]

    def __iter__(self):
        yield from self.rule_dict

        
class GGDLParser():        
    """ A class to parse a GGDL file.
    
    As formal grammar theory, a graph grammar is modeled as a 4-tuple (T, N, S, P).
    
        * The T is a set containing terminal symbols.
        * The N is a set as terminal_symbol_set.
          No symbol can belong to T and N at the same time.
        * The S is a labelled directed graph over T and N, which means 
          each node and each edge have a label which belongs to T or N.
        * The P is a set of production rules.
          Basically, each rule is modeled as a pair (L, R).
          The L (often called as the Left hand side, LHS) represents the pattern of the subgraph
          for which the rule can apply. 
          The R (the Right hand side, RHS) is the new subgraph which replaces the subgraph.

    However, not as formal grammar theory, the definition of 'rule' varies from research to research.
    Therefore, the strict definition of (L, R) also varies.
    This class supports several manners that may work well in the current project.
    
    This class supports the following manners (the name of each manner is named by myself).
        * [ Context-free rule ] Introduced in [1]. The LHS is a non-terminal symbol which
          represents a single node graph. The RHS is modeled as a pair of a graph and a node (base node) 
          in the graph. Once the rule is applied to a node with a symbol same as the LHS, 
          the node is removed and the graph in the RHS is added to the existing graph.
          All the edges connected with the removed node connect with the base node in the RHS.
          In this program, the RHS is a SimpleGraph class object which contains a node
          having 'base' as its ID. The node represents the base node.
        * [ Anchor rule ] Introduced in [2]. The LHS is a labelled directed graph
          which contains special nodes called 'anchor' 
          (call a labelled directed graph with anchors 'anchor graph' (or 'anode' short for it). 
          The 'anchor' is considered as some kind of wildcard and matches any node of 
          the target graph in the process of the pattern matching.
          The RHS is also an anchor graph. The set of the anchors of the RHS needs to be same as
          the one of the LHS. By restricting so, we can connect the newly added nodes in the RHS
          with the existing nodes represented by the anchors.
        * [ Wildcard rule ] This is a minor change of Anchor rule. The structure of the LHS 
          and the RHS is almost same as the ones of Anchor rule.
          The LHS of an anchor rule matches a subgraph of the target graph when all the anchors
          corresponds nodes in the target. The wildcard rule removes the requirement.
          That is, the LHS of a wildcard rule matches a subgraph even when some of the anchors
          do not have corresponding nodes. By introducing wildcard rule, the amount of rules
          is greatly reduced. To avoid confusion, call anchor nodes of Wildcard rule 
          'wildcard nodes' (or 'wnode' short for it).

    [References]
        * [1] Zhao et al. (2020) "RoboGrammar: Graph Grammar for Terrain-Optimized Robot Design",
          ACM Transactions on Graphics (TOG), 39(6), 1-16.
        * [2] Guo et al. (2022) "Data-efficient graph grammar learning for molecular generation",
          arXiv preprint arXiv:2203.08031.

    """
    def __init__(self, 
            path=None, 
            acceptable_rule_classes=[ContextFreeRule, AnchorRule, WildcardRule],
            show_content=False):
        self.start_graph = None
        self.terminal_symbol_set = {""} # The empty string is always regarded as the terminal symbol.
        self.non_terminal_symbol_set = set()
        self.rules = RuleBundle()
        self.acceptable_rule_classes = acceptable_rule_classes

        if path is not None:
            self.load_grammar(path, show_content)

    def load_grammar(self, path, show_content=True):
        """ Loads a grammar file and sets members. 
        
        Args:
            path(str): A relative path to a grammar file to be loaded.
        
        """
        self.__print("LOAD GRAMMAR @ " + path, show_content)
        tree = ET.parse(path)
        root = tree.getroot()

        self.__print("\nTERMINAL-SYMBOLS : ", show_content)
        terminal_symbol_element = root.find('terminal-symbol')
        for symbol in terminal_symbol_element.findall('symbol'):
            self.define_terminal_symbol(symbol.get('name'))
            self.__print(' ' * 4 + "SYMBOLS : " + symbol.get('name'), show_content)

        self.__print("\nNON-TERMINAL-SYMBOLS : ", show_content)
        non_terminal_symbol_element = root.find('non-terminal-symbol')
        for symbol in non_terminal_symbol_element.findall('symbol'):
            self.define_non_terminal_symbol(symbol.get('name'))
            self.__print(' ' * 4 + "SYMBOLS : " + symbol.get('name'), show_content)

        start_symbol_element = root.find('start-symbol')
        start_graph_element = root.find('start-graph')
        if (start_symbol_element is not None) and (start_graph_element is not None):
            raise ColoredException('Both "start-symbol" and "start-graph" are contained.')
        if start_symbol_element is not None:
            self.define_start_symbol(start_symbol_element)
            self.__print("START-SYMBOL : " + str(start_symbol_element.get('name')), show_content)
        else:
            self.define_start_graph(start_graph_element)
            self.__print("START-GRAPH LOADED", show_content)

        self.__print("\nPRODUCTION-RULES : ", show_content)
        production_rule_element = root.find('production-rule')
        for rule_element in production_rule_element.findall('rule'):
            temp_checker = False
            for rule_class in self.acceptable_rule_classes:
                if rule_class.is_parsable_rule(rule_element):
                    rule = rule_class.parse_rule_element(rule_element)
                    self.__print(' ' * 4 + 'RULE-CLASS: ' + rule_class.rule_class + ' NAME: ' + rule['name'],
                            show_content)

                    lhs_nodes = rule.get_lhs_nodes()
                    rhs_nodes = rule.get_rhs_nodes()
                    for node in lhs_nodes:
                        if not self.is_vocabulary(node['name']):
                            raise ColoredException('The symbol ( ' + node['name'] + \
                                    ' ) is not in the vocabulary.')
                    for node in rhs_nodes:
                        if not self.is_vocabulary(node['name']):
                            raise ColoredException('The symbol ( ' + node['name'] + \
                                    ' ) is not in the vocabulary.')
                    self.rules.add_rule(rule)
                    temp_checker = True
                    break
            if not temp_checker:
                raise ColoredException("Unsupported rule is detected.")
        self.__print("LOAD GRAMMAR DONE", show_content)

    def save_grammar(self, filename, indent_width=2):
        """ Create a grammar file from an instance.

        Args:   
            filename(str): A relative path to a file to be saved.
            indent_width(int): The width of an indent.

        """
        str_list = ['<grammar>']
        str_list.append(' '*indent_width + '<start-graph>')
        str_list.append(self.start_graph.gen_element(indent_num=2, indent_width=indent_width))
        str_list.append(' '*indent_width + '</start-graph>')

        # terminal-symbol
        str_list.append(' '*indent_width + '<terminal-symbol>')
        for symbol in self.terminal_symbol_set:
            if symbol != "": # The empty string does not need to be saved.
                str_list.append(' '*2*indent_width + '<symbol name="' + symbol +'"/>')
        str_list.append(' '*indent_width + '</terminal-symbol>')

        # non-terminal-symbol
        str_list.append(' '*indent_width + '<non-terminal-symbol>')
        for symbol in self.non_terminal_symbol_set:
            str_list.append(' '*2*indent_width + '<symbol name="' + symbol +'"/>')
        str_list.append(' '*indent_width + '</non-terminal-symbol>')

        # productio-rule
        str_list.append(' '*indent_width + '<production-rule>')
        for rule_name in self.rules:
            str_list.append(self.rules[rule_name].gen_element(indent_num=1, indent_width=indent_width))
        str_list.append(' '*indent_width + '</production-rule>')
        str_list.append('</grammar>')
        with open(filename, mode='w') as f:
            f.write('\n'.join(str_list))
            
    def define_start_symbol(self, start_symbol_element):
        """ Generates a single node graph from the symbol and register the graph as 
            start_graph.

        Note:
            When the start_symbol_element does not have the attribute 'name', 
            the start_graph is set as None.
        
        Args:
            start_symbol_element(Element): The start-symbol element.
        
        """
        symbol = start_symbol_element.get('name')
        if symbol is None:
            self.start_graph = None
        else:
            self.define_non_terminal_symbol(symbol)
            self.start_graph = SimpleGraph()
            self.start_graph.add_node('base', **start_symbol_element.attrib)

    def define_start_graph(self, start_graph_element):
        """ Parse the start-graph element and register the generated graph as 
            start_graph.

        Args:
            start_graph_element(Element): A start-graph element.

        """
        graph_elements = start_graph_element.findall('graph')
        num_elements = len(graph_elements)
        if num_elements > 1:
            raise InvalidFileError("The start-graph element contains multiple graph elements")
        if num_elements == 0:
            self.start_graph = None
            return
        graph = SimpleGraph.parse_graph_element(graph_elements[0], ignore_absence_of_base=True)
        if not self.is_symbol_graph(graph, ignore_node_label=False, ignore_edge_label=False):
            raise VocaburaryError("The name attributes contains non-symbol string.") 
        self.start_graph = graph

    def define_terminal_symbol(self, symbol):
        """ Adds a new terminal symbol into terminal_symbol_set 

        This method is called when parsing a graph file.
        Therefore, the validity of symbol is checked before symbol is added.

        Args:
            symbol(string): a string to be examined and to be added.

        """
        if type(symbol) is not str:
            raise InvalidTypeError(symbol, str)
            #raise ColoredException("Invalid type for symbol")

        if self.is_non_terminal_symbol(symbol):
            raise SymbolDefinitionOverriedError(symbol, 'a non-terminal symbol')
            #raise ColoredException("The given symbol: " + \
            #            symbol + " is already defined as a non-terminal symbol")

        self.terminal_symbol_set.add(symbol)

    def define_non_terminal_symbol(self, symbol):
        """ Adds a new non-terminal symbol into non_terminal_symbol_set 

        This method is called when parsing a graph file.
        Therefore, the validity of symbol is checked before symbol is added.

        Args:
            symbol(string): a string to be examined and to be added.

        """
        if type(symbol) is not str:
            raise InvalidTypeError(symbol, str)
            #raise ColoredException("Invalid type for symbol")

        if self.is_terminal_symbol(symbol):
            raise SymbolDefinitionOverriedError(symbol, 'a terminal symbol')
            #raise VocaburaryError("The given symbol: " + \
            #           symbol + " is already defined as a terminal symbol")

        self.non_terminal_symbol_set.add(symbol)

    def undefine_start_graph(self):
        """ Sets start_graph to None. """
        self.start_graph = None

    def undefine_terminal_symbol(self, symbol):
        """ Removes the given symbol from terminal_symbol_set 
        
        Args:
            symbol(string): a string of a symbol
        
        """
        self.terminal_symbol_set.discard(symbol)

    def undefine_non_terminal_symbol(self, symbol):
        """ Removes the given symbol from non_terminal_symbol_set
        
        Args:
            symbol(string): a string of a symbol
        
        """
        if self.start_graph is not None:
            if GGDLParser.is_contained_label(self.start_graph, symbol):
                self.undefine_start_graph()     
        self.non_terminal_symbol_set.discard(symbol)

    def undefine_rule(self, rule_name):
        """ Removes the rule with the given name. """
        self.rules.remove_rule(rule_name)

    def is_terminal_symbol(self, sym):
        """ Checks if sym is a terminal symbol """
        return sym in self.terminal_symbol_set

    def is_non_terminal_symbol(self, sym):
        """ Checks if sym is a non-terminal symbol """
        return sym in self.non_terminal_symbol_set

    def is_vocabulary(self, sym):
        """ Checks if sym is one of the terminal symbols or the non terminal symbols."""
        # start_symbol is contained in non_terminal_symbol_set
        return self.is_terminal_symbol(sym) or \
                self.is_non_terminal_symbol(sym)

    def __label_checker(self, graph, check_fcn, ignore_node_label=False, ignore_edge_label=True):
        """ Checks if all the labels of the nodes and the edges pass the check_fcn

        Args:
            graph(DiGraph): The graph to be examined.
            check_fcn(function): A function which takes a label and returns bool.
            ignore_node_label(bool): If True, this method will not check the labels of the nodes.
            ignore_edge_label(bool): If True, this method will not check the labels of the edges.

        """
        if not ignore_node_label:
            for node_id in graph.nodes:
                try:
                    symbol = graph.nodes[node_id]['name']
                except KeyError:
                    return False
                if not check_fcn(symbol):
                    return False
        if not ignore_edge_label:
            for edge in graph.edges:
                try:
                    symbol = graph.edges[edge[0], edge[1]]['name']
                except KeyError:
                    return False
                if not check_fcn(symbol):
                    return False
        return True



    def is_symbol_graph(self, graph, ignore_node_label=False, ignore_edge_label=True):
        """ Checks if the given graph is a symbol graph.

        A symbol graph over an alphabet is a labelled directed graph of which
        all the label belong to the alphabet.

        In this method (and the class), the values of the 'name' attribute of nodes and edges
        regarded as the label of them.
        The alphabet is regarded as an union of the terminal symbol set and the non-terminal symbol set.

        This method checks all the labels of the nodes and the edges of the given graph object.

        Args:
            graph(DiGraph): The graph to be examined.
            ignore_node_label(bool): If True, this method will not check the labels of the nodes.
            ignore_edge_label(bool): If True, this method will not check the labels of the edges.

        """
        return self.__label_checker(
                graph, 
                self.is_vocabulary, 
                ignore_node_label=ignore_node_label,
                ignore_edge_label=ignore_edge_label)
                    
    def is_sentence(self, graph, ignore_node_label=False, ignore_edge_label=True):
        """ Checks if the given graph is a sentence. 

        A sentence graph is a symbol graph such that all the nodes have terminal symbols.

        Args:
            graph(DiGraph): The graph to be examined.
            ignore_node_label(bool): If True, this method will not check the labels of the nodes.
            ignore_edge_label(bool): If True, this method will not check the labels of the edges.

        """
        return self.__label_checker(
                graph, 
                self.is_vocabulary, 
                ignore_node_label=ignore_node_label,
                ignore_edge_label=ignore_edge_label)

    @classmethod
    def __print(cls, string, show_content=True):
        if show_content:
            print(string)

    @classmethod
    def is_contained_label(cls, graph, symbol):
        """ Checks if there exists a node or an edge of which the label is the given symbol.
       
        Args:
            graph(SimpleGraph or DiGraph): The graph to be searched for the symbol.
            symbol: The symbol.
        
        """
        try:
            for node_id in graph.nodes():
                if symbol == graph.nodes[node_id]['name']:
                    return True
            for edge in graph.edges():
                if symbol == graph.edges[edge[0], edge[1]]['name']:
                    return True
        except KeyError:
            pass
        return False


class Grammar():
    """ A class for define grammers

    Note:
        This class is outdated.
    
    As generative grammar of formal grammar theory, a grammar has 4 main members: 
    (start_symbol, terminal_symbol_set, non_terminal_symbol_set, rule_dict).
    
    * start_symbol is a string representing the start symbol of the grammer.

    * terminal_symbol_set is a set containing terminal symbols, 
      where symbol means a string as start_symbol.

    * non_terminal_symbol_set is a set as terminal_symbol_set.
      No symbol can belong to terminal_symbol_set and non_terminal_symbol_set at same time.
      non_terminal_symbol_set should contains start_symbol.

    * rule_dict is a dictionary which stores context-free rules.
      Each key of it represents a name of a rule and should not be a key of the cs_rule_dict below.
      Each rule (value of the dictionary) is a 3-tuple (nt, node_dict, edge_dict)

        * nt is a non-terminal symbol to be replaced by a graph.
        * node_dict is a dictionary, where a key is a number string such as "1", "10".
          The number string represents the id of the node.
          A value of a key is a symbol representing a node.
        * node_dict have a special key 'base' that returns a symbol representing a node
          that replaces nt. 
        * edge_dict is a dictionary of newly connected edges,
          where a key is a number string such as "1", "10".

      Each edge in edge_dict is represented by a tuple '(type from_id to_id)': 

        * type is 'di' or 'bi'.
          They mean directed edge and reversed directed edge and bidirectional edge, respectively.
        * from_id is a number string representing an id of a node from which the edge starts.
        * to_id is a number string representing an id of a node to which the edge goes.
        * 'base' can be passed to from_id and to_id.
    
    e.g.

    |   rule = ('A', 
    |           {'B':'base', 'C':'1', 'D':'2', 'E':'3'}, 
    |           [('di', 'base', '1'), ('di', '2', 'base'), ('bi', 'base', '3')] ):
    | A is replaced by a subgraph C <- B <-  D 
    |                                    <-> E
    | and all edges that connected with A in a graph now connect with B.

    This class supports context-sensitive grammars.
    To store context-sensitive rules, instances has the cs_rule_dict member.

    The cs_rule dict is a dictionary: as rule_dict, each key of it represents a name of a rule.
    The key should be one not used in rule_dict.
    Each rule is a 3-tuple (wgraph, node_dict, edge_dict).

        * The node_dict and the edge_dict work as same as context-free rules above.
        * The wgraph represents a subgraph pattern to be replaced 
           by a graph specified with the node_dict and the edge_dict.
        * The wgraph itself is a 3-tuple (wnode_list, node_dict, edge_dict).
            * The node_dict and the edge_dict in a wgraph store nodes and edges which appear in the pattern.
            * The wnode_list is a list of numbers. 
              Each number of the list represents the id for a wildcard node.

    Note that a single node in the wgraph is allowed to have one edge from a wildcard and 
    one edge toward a wildcard. Having multiple edges from / toward wildcards is not allowed.

    
    """
    def __init__(self, path=None):
        self.start_symbol = None
        self.terminal_symbol_set = set()
        self.non_terminal_symbol_set = set()
        self.rule_dict = {}
        self.cs_rule_dict = {}

        if path is not None:
            self.load_grammar(path)

    ############################################################
    #
    #   General methods for handling grammar
    #
    ############################################################
    def get_rule_list(self):
        """ Returns a full list of keys of rules in the grammar. """
        return self.get_context_free_rule_list() + \
                self.get_context_sensitive_rule_list()

    def get_rule(self, rule_name):
        """ Returns value of rule_dict / cs_rule_dict. """
        if self.is_context_free_rule(rule_name):
            return self.rule_dict[rule_name]
        if self.is_context_sensitive_rule(rule_name):
            return self.cs_rule_dict[rule_name]

    def get_newly_added_nodes(self, rule_name):
        """ Returns the dictionary of the nodes to be added by the rule. """
        if self.is_context_free_rule(rule_name):
            return self.get_newly_added_nodes_of_context_free_rule(rule_name)
        if self.is_context_sensitive_rule(rule_name):
            return self.get_newly_added_nodes_of_context_sensitive_rule(rule_name)

    def get_newly_added_edges(self, rule_name):
        """ Returns the dictionary of the edges to be added by the rule. """
        if self.is_context_free_rule(rule_name):
            return self.get_newly_added_edges_of_context_free_rule(rule_name)
        if self.is_context_sensitive_rule(rule_name):
            return self.get_newly_added_edges_of_context_sensitive_rule(rule_name)

    def define_start_symbol(self, symbol):
        """ Registers symbol as start_symbol 
        
        This method is called when parsing a graph file.
        Therefore, the validity of symbol is checked before symbol is registered.

        Args:
            symbol(string): a string to be examined and to be registered.
        
        """
        if symbol is None:
            self.start_symbol = symbol
        else:
            if type(symbol) is not str:
                raise ValueError("Invalid type for symbol")

            # automatically added into non_terminal_symbol_set
            self.define_non_terminal_symbol(symbol)
            self.start_symbol = symbol

    def define_terminal_symbol(self, symbol):
        """ Adds a new terminal symbol into terminal_symbol_set 

        This method is called when parsing a graph file.
        Therefore, the validity of symbol is checked before symbol is added.

        Args:
            symbol(string): a string to be examined and to be added.

        """
        if type(symbol) is not str:
            raise ValueError("Invalid type for symbol")

        if self.is_non_terminal_symbol(symbol):
            raise ValueError("The given symbol: " + \
                        symbol + " is already defined as a non-terminal symbol")

        self.terminal_symbol_set.add(symbol)

    def define_non_terminal_symbol(self, symbol):
        """ Adds a new non-terminal symbol into non_terminal_symbol_set 

        This method is called when parsing a graph file.
        Therefore, the validity of symbol is checked before symbol is added.

        Args:
            symbol(string): a string to be examined and to be added.

        """
        if type(symbol) is not str:
            raise ValueError("Invalid type for symbol")

        if self.is_terminal_symbol(symbol):
            raise ValueError("The given symbol: " + \
                        symbol + " is already defined as a terminal symbol")

        self.non_terminal_symbol_set.add(symbol)

    def undefine_start_symbol(self):
        """ Sets start_symbol to None. """
        self.start_symbol = None

    def undefine_terminal_symbol(self, symbol):
        """ Removes the given symbol from terminal_symbol_set 
        
        Args:
            symbol(string): a string of a symbol
        
        """
        self.terminal_symbol_set.discard(symbol)

    def undefine_non_terminal_symbol(self, symbol):
        """ Removes the given symbol from non_terminal_symbol_set
        
        Args:
            symbol(string): a string of a symbol
        
        """
        if self.is_start_symbol(symbol):
            self.undefine_start_symbol()
        self.non_terminal_symbol_set.discard(symbol)

    def is_start_symbol(self, sym):
        """ Checks if a string sym is the start symbol 

        Args:
            sym(String): A string to be examined

        """
        return self.start_symbol == sym

    def is_terminal_symbol(self, sym):
        """ Checks if sym is a terminal symbol """
        return sym in self.terminal_symbol_set

    def is_non_terminal_symbol(self, sym):
        """ Checks if sym is a non-terminal symbol """
        return sym in self.non_terminal_symbol_set

    def is_vocabulary(self, sym):
        """ Check if sym is one of the terminal symbols or the non terminal symbols."""
        # start_symbol is contained in non_terminal_symbol_set
        return self.is_terminal_symbol(sym) or \
                self.is_non_terminal_symbol(sym)

    def is_edge(self, edge, node_dict):
        """ Checks if edge is a valid edge.
        
        This method checks
            * type of edge is 'di' or 'bi',
            * Ids exist in node_dict.
        
        """
        ret = True
        if edge[0] not in {'di', 'bi'}:
            ret = False
        if edge[1] not in node_dict:
            ret = False
        if edge[2] not in node_dict:
            ret = False
        return ret

    def load_grammar(self, path):
        """ Loads a grammar file and sets members """
        tree = ET.parse(path)
        root = tree.getroot()

        start_symbol_section = root.find('start-symbol')
        self.define_start_symbol(start_symbol_section.attrib.get('name'))

        terminal_symbol_section = root.find('terminal-symbol')
        for symbol in terminal_symbol_section.findall('symbol'):
            self.define_terminal_symbol(symbol.attrib.get('name'))

        non_terminal_symbol_section = root.find('non-terminal-symbol')
        for symbol in non_terminal_symbol_section.findall('symbol'):
            self.define_non_terminal_symbol(symbol.attrib.get('name'))

        production_rule_section = root.find('production-rule')
        for rule in production_rule_section.findall('rule'):
            nt_section = rule.find('nt')
            if nt_section is None:
                wgraph_section = rule.find('wgraph')
                wnode_list = []
                node_dict_in_wgraph = {}
                edge_dict_in_wgraph = {}
                for wnode in wgraph_section.findall('wnode'):
                    wnode_list.append(wnode.attrib.get('id'))
                for node in wgraph_section.findall('node'):
                    node_dict_in_wgraph[node.attrib.get('id')] = node.attrib.get('name')
                for edge in wgraph_section.findall('edge'):
                    edge_dict_in_wgraph[edge.attrib.get('id')] = (edge.attrib.get('type'),
                            edge.attrib.get('from'),
                            edge.attrib.get('to'))
                pattern = (wnode_list, node_dict_in_wgraph, edge_dict_in_wgraph)
            else:
                pattern = nt_section.attrib.get('name')

            graph_section = rule.find('graph')
            base = graph_section.attrib.get('base')
            node_dict = {'base':base}
            edge_dict = {}
            for node in graph_section.findall('node'):
                node_dict[node.attrib.get('id')] = node.attrib.get('name')

            for edge in graph_section.findall('edge'):
                edge_dict[edge.attrib.get('id')] = (edge.attrib.get('type'),
                                                    edge.attrib.get('from'),
                                                    edge.attrib.get('to'))
            if type(pattern) is str:      
                self.define_context_free_rule(rule.attrib['name'], 
                        pattern,
                        node_dict,
                        edge_dict)
            else:
                self.define_context_sensitive_rule(rule.attrib['name'], 
                        pattern,
                        node_dict,
                        edge_dict)


    def save_grammar(self, filename, indent_num=2):
        """ Create a grammar file from an instance """
        str_list = ['<grammar>']

        # start-symbol
        str_list.append(' '*indent_num + '<start-symbol name="' + self.start_symbol + '"/>')

        # terminal-symbol
        str_list.append(' '*indent_num + '<terminal-symbol>')
        for symbol in self.terminal_symbol_set:
            str_list.append(' '*2*indent_num + '<symbol name="' + symbol +'"/>')
        str_list.append(' '*indent_num + '</terminal-symbol>')

        # non-terminal-symbol
        str_list.append(' '*indent_num + '<non-terminal-symbol>')
        for symbol in self.non_terminal_symbol_set:
            str_list.append(' '*2*indent_num + '<symbol name="' + symbol +'"/>')
        str_list.append(' '*indent_num + '</non-terminal-symbol>')

        # productio-rule
        str_list.append(' '*indent_num + '<production-rule>')
        for rule in self.rule_dict:
            str_list.append(' '*2*indent_num + '<rule name="' + rule + '">')
            nt = self.rule_dict[rule][0]
            node_dict = self.rule_dict[rule][1]
            edge_dict = self.rule_dict[rule][2]

            str_list.append(' '*3*indent_num + '<nt name="' + nt + '"/>')
            str_list.append(' '*3*indent_num + '<graph base="' + node_dict['base'] + '">')

            for node_id in node_dict:
                if node_id != 'base':
                    str_list.append(' '*4*indent_num + \
                            '<node name="' + node_dict[node_id] + '" ' + \
                            'id="' + node_id +'"/>')

            for edge_id in edge_dict:
                edge = edge_dict[edge_id]
                str_list.append(' '*4*indent_num + \
                    '<edge id="' + edge_id + '" '\
                    'type="' + edge[0] + '" ' +\
                    'from="' + edge[1] + '" ' + \
                    'to="' + edge[2] +'"/>')
            str_list.append(' '*3*indent_num + '</graph>')
            str_list.append(' '*2*indent_num + '</rule>')

        for rule in self.cs_rule_dict:
            str_list.append(' '*2*indent_num + '<rule name="' + rule + '">')
            wgraph = self.cs_rule_dict[rule][0]
            node_dict = self.cs_rule_dict[rule][1]
            edge_dict = self.cs_rule_dict[rule][2]

            str_list.append(' '*3*indent_num + '<wgraph>')
            for wnode_id in wgraph[0]:
                str_list.append(' '*4*indent_num + \
                        '<wnode id="' + wnode_id +'"/>')

            for node_id in wgraph[1]:
                str_list.append(' '*4*indent_num + \
                        '<node name="' + wgraph[1][node_id] + '" ' + \
                        'id="' + node_id +'"/>')

            for edge_id in wgraph[2]:
                edge = wgraph[2][edge_id]
                str_list.append(' '*4*indent_num + \
                    '<edge id="' + edge_id + '" '\
                    'type="' + edge[0] + '" ' +\
                    'from="' + edge[1] + '" ' + \
                    'to="' + edge[2] +'"/>')
            str_list.append(' '*3*indent_num + '</wgraph>')

            str_list.append(' '*3*indent_num + '<graph base="' + node_dict['base'] + '">')
            for node_id in node_dict:
                if node_id != 'base':
                    str_list.append(' '*4*indent_num + \
                            '<node name="' + node_dict[node_id] + '" ' + \
                            'id="' + node_id +'"/>')

            for edge_id in edge_dict:
                edge = edge_dict[edge_id]
                str_list.append(' '*4*indent_num + \
                    '<edge id="' + edge_id + '" '\
                    'type="' + edge[0] + '" ' +\
                    'from="' + edge[1] + '" ' + \
                    'to="' + edge[2] +'"/>')
            str_list.append(' '*3*indent_num + '</graph>')
            str_list.append(' '*2*indent_num + '</rule>')


        str_list.append(' '*indent_num + '</production-rule>')
        str_list.append('</grammar>')

        with open(filename, mode='w') as f:
            f.write('\n'.join(str_list))

    def show_grammar(self, indent_num=4):
        """ Prints data of the grammar """
        if self.start_symbol is None:
            print("[start-symbol]\n" + ' '*indent_num + 'UNDEFINED' + "\n")
        else:
            print("[start-symbol]\n" + ' '*indent_num + self.start_symbol + "\n")
        print("[terminal-symbol]\n" + ' '*indent_num + str(self.terminal_symbol_set) + "\n")
        print("[non-terminal-symbol]\n" + ' '*indent_num + str(self.non_terminal_symbol_set) + "\n")
        print("[production-rule]")
        for rule in self.rule_dict:
            Grammar.show_rule(rule, self.rule_dict[rule], indent_num)

        for rule in self.cs_rule_dict:
            Grammar.show_rule(rule, self.cs_rule_dict[rule], indent_num)


    ############################################################
    #
    #   General methods for context-free rules
    #
    ############################################################
    def is_context_free_rule(self, rule_name):
        """ Checks if rule_name is a key for rule_dict."""
        return rule_name in self.rule_dict

    def is_context_free_rule_applicable(self, rule_name, symbol):
        """ Checks if the rule with the given name is applicable to the node(symbol). 
        
        This method only cares if the node to be replaced in the rule is same as symbol.
         
        """
        rule = self.rule_dict[rule_name]
        return symbol == rule[0]

    def get_context_free_rule_list(self):
        """ Returns a list of keys of rule_dict. """
        return [rule_name for rule_name in self.rule_dict]

    def get_applicable_context_free_rules(self, symbol):
        """ Returns a list of names of rules which are applicable to the node(symbol). """
        return [rule_name for rule_name in self.rule_dict 
                if self.is_context_free_rule_applicable(rule_name, symbol)]
        

    def get_replaced_symbol(self, rule_name):
        """ Returns a non-terminal symbol to be replaced by the rule. """
        return self.rule_dict[rule_name][0]

    def get_newly_added_nodes_of_context_free_rule(self, rule_name):
        """ Returns the dictionary of the nodes to be added by the rule. """
        return self.rule_dict[rule_name][1]

    def get_newly_added_edges_of_context_free_rule(self, rule_name):
        """ Returns the dictionary of the nodes to be added by the rule. """
        return self.rule_dict[rule_name][2]

    def define_context_free_rule(self, name, nt, node_dict, edge_dict):
        """ Adds a new context free rule into rule_dict 

        This method is called when parsing a graph file.
        Therefore, the validity of arguments is checked before rule is added.

        If a rule with the given name already exists, invoke error.

        Args:
            name(string): A name of a new rule.
            nt(string): A non-terminal symbol in non_terminal_symbol_set.
            node_dict(dictionary): Each key is either a number string or 'base'. 
                                   its value is a symbol.
            edge_dict(dictionary): Each element is a tuple of form (type from_id to_id).
                                   type is either 'di' or 'bi'.
                                   from_id and to_id are either a number string or 'base'.
                                   Each key is a number string.
                                   

        """
        if type(name) is not str:
            raise ValueError("name: " + str(name) + " is not a string")

        if (name in self.rule_dict) or (name in self.cs_rule_dict):
            raise ValueError("name: " + str(name) + " is already used for a rule")

        if not self.is_non_terminal_symbol(nt):
            raise ValueError("nt: " + str(nt) + " is not a non-terminal symbol")

        for node_id in node_dict:
            if not self.is_vocabulary(node_dict[node_id]):
                raise ValueError("node: " + str(node_dict[node_id]) + " is not a defined symbol")
            if not Grammar.is_valid_as_id(node_id):
                raise ValueError("ID: " + str(node_id) + " is not valid.")

        for edge_id in edge_dict:
            if not self.is_edge(edge_dict[edge_id], node_dict):
                raise ValueError("edge: " + str(edge_dict[edge_id]) + " is not valid")
            if not Grammar.is_valid_as_id(edge_id):
                raise ValueError("ID: " + str(edge_id) + " is not valid.")

        self.rule_dict[name] = (nt, node_dict, edge_dict)

    def undefine_context_free_rule(self, name):
        """ Removes a rule with the given name 
        
            Args:
                name(string): A name of the rule to be removed.

        """
        if name in self.rule_dict:
            self.rule_dict.pop(name)
 

    ############################################################
    #
    #   General methods for context-sensitive rules
    #
    ############################################################
    def is_context_sensitive_rule(self, rule_name):
        """ Checks if rule_name is a key for cd_rule_dict."""
        return rule_name in self.cs_rule_dict

    def get_context_sensitive_rule_list(self):
        """ Returns a list of keys of cs_rule_dict. """
        return [rule_name for rule_name in self.cs_rule_dict]


    def get_newly_added_nodes_of_context_sensitive_rule(self, rule_name):
        """ Returns the dictionary of the nodes to be added by the rule. """
        return self.cs_rule_dict[rule_name][1]

    def get_newly_added_edges_of_context_sensitive_rule(self, rule_name):
        """ Returns the dictionary of the nodes to be added by the rule. """
        return self.cs_rule_dict[rule_name][2]

    def get_wgraph(self, rule_name):
        """ Returns the tuple of the wgraph specified with rule_name.
        
        Args:
            rule_name(string): A key for cs_rule_dict.
        
        """
        return self.cs_rule_dict[rule_name][0]

    def get_wgraph_wnode_list(self, rule_name):
        """ Returns the wnode_list of the wgraph.
        
        Args:
            rule_name(string): A key for cs_rule_dict.
        
        """
        return self.get_wgraph(rule_name)[0]


    def get_wgraph_node_dict(self, rule_name):
        """ Returns the node_dict of the wgraph.
        
        Args:
            rule_name(string): A key for cs_rule_dict.
        
        """
        return self.get_wgraph(rule_name)[1]

    def get_wgraph_edge_dict(self, rule_name):
        """ Returns the edge_dict of the wgraph.
        
        Args:
            rule_name(string): A key for cs_rule_dict.
        
        """
        return self.get_wgraph(rule_name)[2]


    def define_context_sensitive_rule(self, name, wgraph, node_dict, edge_dict):
        """ Adds a new context-sensitive rule into cs_rule_dict 

        This method is called when parsing a graph file.
        Therefore, the validity of arguments is checked before rule is added.

        Note: 
            When a condition below meet, invoke error.
                * If name is not a string.
                * If a rule with the given name already exists.
                * If the ID of a wildcard is not a string represents an integer.
                * If there exists a edge from a wildcard to a wildcard.
                * If a node has edges with a same type connecting with different wildcard nodes.
                * If a node is not in the vocabulary.
                * If an edge is not valid.

        Args:
            name(string): A name of a new rule.
            wgraph(tuple): A tuple of wnode_list, node_dict, edge_dict representing a pattern.
            node_dict(dictionary): Each key is either a number string or 'base'. 
                                   its value is a symbol.
            edge_dict(dictionary): Each element is a tuple of form (type from_id to_id).
                                   type is either 'di' or 'bi'.
                                   from_id and to_id are either a number string or 'base'.
                                   Each key is a number string.
                                   

        """
        if type(name) is not str:
            raise ValueError("name: " + str(name) + " is not a string")

        if (name in self.rule_dict) or (name in self.cs_rule_dict):
            raise ValueError("name: " + str(name) + " is already used for a rule")

        error_rule_name = "RULENAME: " + name + '\n' 

        wnode_list = wgraph[0] 
        node_dict_in_wgraph = wgraph[1] 
        edge_dict_in_wgraph = wgraph[2]

        wgraph_wnode_in_counter = dict.fromkeys(node_dict_in_wgraph.keys(), 0)
        wgraph_wnode_out_counter = dict.fromkeys(node_dict_in_wgraph.keys(), 0)

        # Check if wildcard_id is a string represents an number.
        for wildcard_id in wnode_list:
            try:
                float(wildcard_id)
            except ValueError:
                raise ValueError(error_rule_name + "wildcard id: " + str(wildcard_id) + " is not valid")

        for node_id in node_dict_in_wgraph:
            if not self.is_vocabulary(node_dict_in_wgraph[node_id]):
                raise ValueError(error_rule_name + "node: " + str(node_dict[node_id]) + " is not a defined symbol")

        for edge in edge_dict_in_wgraph.values():
            # Validity check of edges in wgraph.
            temp_dict = node_dict_in_wgraph.copy()
            for wildcard_id in wnode_list:
                temp_dict[wildcard_id] = ""
            if not self.is_edge(edge, temp_dict):
                raise ValueError(error_rule_name + "edge: " + str(edge) + " is not valid")

            # Count the number of wildcards of each node,
            # and check the existence of edges between wildcards.
            if Grammar.get_edge_from(edge) in wnode_list:
                if Grammar.get_edge_to(edge) in wnode_list:
                    raise ValueError(error_rule_name + "edge: " + str(edge) + " connect a wildcard with a wildcard.")
                wgraph_wnode_in_counter[Grammar.get_edge_to(edge)] += 1
                if Grammar.get_edge_type(edge) == 'bi':
                    wgraph_wnode_out_counter[Grammar.get_edge_to(edge)] += 1
            if Grammar.get_edge_to(edge) in wnode_list:
                wgraph_wnode_out_counter[Grammar.get_edge_from(edge)] += 1
                if Grammar.get_edge_type(edge) == 'bi':
                    wgraph_wnode_in_counter[Grammar.get_edge_from(edge)] += 1

        excess_in = [(node_id, num) for node_id, num 
                     in wgraph_wnode_in_counter.items() if num > 1]

        excess_out = [(node_id, num) for node_id, num 
                      in wgraph_wnode_out_counter.items() if num > 1]

        if len(excess_in) != 0 or len(excess_out) != 0:
            print(error_rule_name)
            if len(excess_in) != 0:
                print("Following nodes have more than one edges from wildcard nodes.")
            for pair in excess_in:
                print("Node: " + str(pair[0]) + " (" + str(pair[1]) + ")")
            if len(excess_out) != 0:
                print("Following nodes have more than one edges toward wildcard nodes.")
            for pair in excess_out:
                print("Node: " + str(pair[0]) + " (" + str(pair[1]) + ")")
            raise ValueError(error_rule_name + "Invalid number of wildcard nodes")

        for node_id in node_dict:
            if not self.is_vocabulary(node_dict[node_id]):
                raise ValueError(error_rule_name + "node: " + str(node_dict[node_id]) + " is not a defined symbol")

        for edge_id in edge_dict:
            temp_dict = node_dict.copy()
            for wildcard_id in wnode_list:
                temp_dict[wildcard_id] = ""
            if not self.is_edge(edge_dict[edge_id], temp_dict):
                raise ValueError(error_rule_name + "edge: " + str(edge_dict[edge_id]) + " is not valid")

        self.cs_rule_dict[name] = (wgraph, node_dict, edge_dict)
 
    def undefine_context_sensitive_rule(self, name):
        """ Removes a rule with the given name 
        
            Args:
                name(string): A name of the rule to be removed.

        """
        if name in self.rule_dict:
            self.cs_rule_dict.pop(name)       

    ############################################################
    #
    #   Class methods
    #
    ############################################################
    @classmethod
    def is_valid_as_id(cls, id_key):
        """ Checks if a key is a string which represents
            an integer or is 'base'.

        """
        if id_key == 'base':
            return True
        if id_key[0] == '-' or id_key[0] == '+':   
            return Grammar.is_valid_as_id(id_key[1:])
        else:
            return id_key.isdigit()

    @classmethod
    def get_edge_type(cls, edge):
        """ Returns from_id of the edge """
        return edge[0]

    @classmethod
    def get_edge_from(cls, edge):
        """ Returns from_id of the edge """
        return edge[1]

    @classmethod
    def get_edge_to(cls, edge):
        """ Returns from_id of the edge """
        return edge[2]

    @classmethod
    def get_wnode_list(cls, wgraph):
        """ Returns a list of ids of wildcard nodes. """
        return wgraph[0]

    @classmethod
    def get_node_dict_of_wgraph(cls, wgraph):
        """ Returns the node dictionary of the wgraph. """
        return wgraph[1]

    @classmethod
    def get_edge_dict_of_wgraph(cls, wgraph):
        """ Returns the edge dictionary of the wgraph. """
        return wgraph[2]

    @classmethod
    def get_inoutdegree_of_wgraph_node(cls, wgraph, node_id):
        """ Returns the information about the indegree and the outdegree.
        
        Returns:
            indegree(Number): the indegree of the node.
            outdegree(Number): the outdegree of the node.
            wildcard_in(list): the wildcards towards the node.
            wildcard_out(list): the wildcards from the node.

        Note:
            Currently, a single node can hold at most one edge from a wildcard
            and one edge toward a wildcard.
            Therefore, wildcard_in and wildcard_out are always single-element list.
            However, for the future improvement, keep wildcard_in and wildcard_out as lists.
        
        """
        edge_dict = Grammar.get_edge_dict_of_wgraph(wgraph)
        wnode_list = Grammar.get_wnode_list(wgraph)
        indegree = 0
        outdegree = 0
        wildcard_in = []
        wildcard_out = []
        for edge in edge_dict.values():
            if Grammar.get_edge_from(edge) == node_id:
                outdegree += 1
                if Grammar.get_edge_to(edge) in wnode_list:
                    wildcard_out.append(Grammar.get_edge_to(edge))
            if Grammar.get_edge_to(edge) == node_id:
                indegree += 1
                if Grammar.get_edge_from(edge) in wnode_list:
                    wildcard_in.append(Grammar.get_edge_from(edge))
        return indegree, outdegree, wildcard_in, wildcard_out

    @classmethod
    def show_rule(cls, rule, rule_tuple, indent_num):
        pattern = rule_tuple[0]
        node_dict = rule_tuple[1].copy()
        edge_dict = rule_tuple[2]
        base = node_dict['base']
        
        temp = ' '*indent_num + '[ ' + rule + ' ] '
        rparen = '( ['
        for node_id in node_dict:
            if node_id != 'base':
                temp = temp + rparen + node_id + '] ' + node_dict[node_id] 
                rparen = ', ['
        if rparen == '( [':
            print(temp)
        else:
            print(temp + ' )')

        if type(pattern) is str:
            root = pattern
        else:
            root = 'pattern'
            print(' '*2*indent_num + '[pattern] ')
            temp = ' '*3*indent_num + '[wildcard] '
            for wildcard_id in pattern[0]:
                temp = temp + ' ' + wildcard_id
                node_dict[wildcard_id] = ":WC:"
            print(temp)
            temp = ' '*3*indent_num + '[ nodes ] '
            rparen = '( ['
            for node_id in pattern[1]:
                temp = temp + rparen + node_id + '] ' + pattern[1][node_id] 
                rparen = ', ['
            if rparen == '( [':
                print(temp)
            else:
                print(temp + ' )')
            print(' '*3*indent_num + '[ edges ]')
            for edge in pattern[2]:
                print(' '*4*indent_num + str(pattern[2][edge]))
            print(' '*2*indent_num + '[/pattern] ')
        Grammar.show_edge(root, base, node_dict, edge_dict, indent_num)

    @classmethod 
    def show_edge(cls, root, base, node_dict, edge_dict, indent_num):
        temp = ' '*2*indent_num + root + ' -> ' + base
        pos = len(temp)
        print(temp)
        for edge_id in edge_dict:
            edge = edge_dict[edge_id]
            if Grammar.get_edge_from(edge) == 'base':
                if edge[0] == 'di':
                    arrow = '| -> '
                elif edge[0] == 'bi':
                    arrow = '|<-> '
                node_id = Grammar.get_edge_to(edge)
            elif Grammar.get_edge_to(edge) == 'base':
                if edge[0] == 'di':
                    arrow = '|<- '
                elif edge[0] == 'bi':
                    arrow = '|<->'
                node_id = Grammar.get_edge_from(edge)
            else:
                continue
            print(' '*(pos - len(base)) + arrow + \
                    node_dict[node_id] + ' : ' + node_id + ' |edge_id: ' + edge_id)

        for edge_id in edge_dict:
            edge = edge_dict[edge_id]
            if Grammar.get_edge_from(edge) != 'base' and Grammar.get_edge_to(edge) != 'base':
                if edge[0] == 'di':
                    arrow = '  -> '
                elif edge[0] == 'bi':
                    arrow = ' <-> '
                print(' '*2*indent_num + Grammar.get_edge_from(edge) + arrow + \
                    node_dict[Grammar.get_edge_to(edge)] + ' : ' + Grammar.get_edge_to(edge) + \
                    ' |edge_id: ' + edge_id)



