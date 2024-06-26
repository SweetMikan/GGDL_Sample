import os
from graph_compiler import GraphCompiler
from urdf_handler import UrdfHandler

class UrdfCompiler(GraphCompiler):
    """ A class for generating URDF files from graphs. 
    
    UrdfCompiler serves as the postprocessor for robot structure determination.
    The constructor of UrdfCompiler receives a sentence graph (a graph contains no non-terminal symbols)
    generated by a GraphCompiler object, and compiles it into an actual urdf file.
    
    Basically, the non-terminal symbols of the grammar passed to UrdfCompiler 
    are the terminal symbols of the grammar used in the preprocess (GraphCompiler).
    The UrdfCompiler grammar has the full responsibility for execution of the urdf file generation.
    
    This class, at first, compiles the given graph into a tree with a specific structure.
    Therefore, the terminal symbols and the rules of the UrdfCompiler graph need to follow
    the assumputions below. 

        * A terminal symbol is either a file name of a module urdf file, e.g. "some-module.urdf" , 
          or a name of a link in a urdf file which an UrdfHandler class object accepts.
        * In the case of a link name, the link is considered as a connector port to link modules.
        * A urdf node connect only with connector nodes.
        * A urdf node connect with only one root connector node. 
          The link of the label of the root connector node is considered as the root link of the module.
        * A connector node have multiple outward edges 
          if and only if the connector node is a root of the entire robot.
        * The rules need to generate graphs which meet the above assumptions.

    Note:
        [ Terminology ] 
            * A node which has a file name as a label is called a urdf node.
            * A node which has a link name as a label is called a connector node.
            * A connector node which connects with a urdf node via a directed edge
              starting from the urdf node and ending with the connector node
              is called a leaf connector node.
            * A connector node which connects with a urdf node via a directed edge
              starting from the connector node and ending with the urdf node
              is called a root connector node.

    
    """
    def __init__(self, grammar_file_path, urdf_dir_path, initial_graph, chunk_size=100):
        """
        Args:
            grammar_file_path(str): A full path to the grammar file.
            urdf_dir_path(str): A full path to the directory where module urdf files are stored.
            initial_graph(str): A networkx graph object to be compiled into a urdf file.
            chunk_size(integer, optional): See the description of the GraphCompiler class.

        """
        super().__init__(grammar_file_path, initial_graph, chunk_size)
        if urdf_dir_path.endswith('/'):
            self.urdf_dir_path = urdf_dir_path
        else:
            self.urdf_dir_path = urdf_dir_path + '/'
        self.urdf_handler = UrdfHandler()
        for filename in self.__get_urdf_filenames():
            self.urdf_handler.add_urdf(self.__filename_to_fullpath(filename))

    def is_compilable(self):
        """ Check if the graph consists only of terminal symbols. """
        return self.is_sentence()

    def auto_compile(self):
        """ Applies all the applicable rules to the graph. 
        
        Note:
            If there are no applicable rules and the graph still has a non-terminal symbol,
            this method calls an error.
            The grammar itself is responsible for causing / avoiding such a case.
        
        """
        print("[ AUTOCOMPILE START ]")
        applicable_rule_dict = self.get_applicable_rule()
        while not self.is_there_no_applicable_rules(applicable_rule_dict):
            for rule_name in applicable_rule_dict:
                if len(applicable_rule_dict[rule_name]) == 0:
                    continue
                print(' '*4 + "CHOSEN RULE: " + str(rule_name) + \
                        " TARGET: " + str(applicable_rule_dict[rule_name][0]))
                self.apply_rule(rule_name, applicable_rule_dict[rule_name][0])
                break;
            applicable_rule_dict = self.get_applicable_rule()
        if not self.is_compilable():
            error_text = "\033[31m"
            error_text = "[ FATAL ERROR ]\n"
            error_text += "The graph is not compilable into a urdf " + \
                    "even though there are no applicable rules.\n"
            error_text += "The following nodes is not terminal symbols of the compiler grammar:\n"
            for node_id in self.get_non_terminal_symbol_node():
                error_text += ' '*4 + "NODE ID: " + str(node_id) + " ( " + \
                        str(self.get_symbol(node_id)) + " )\n"
            error_text += "\033[0m"
            raise ValueError(error_text) 
        print("[ AUTOCOMPILE DONE ]")

    def generate_urdf(self, robot_name="generated_robot", filename=None, rpy="0 0 3.14159265359"):
        """ Generates a urdf file from the graph (the __graph member). 

        When the graph contains a non-terminal symbol, the auto_compile method is called.
        
        Args:
            robot_name(str): the name of the generated robot.
            filename(str, optional): a full path to a saved file.
                                     When not given, the urdf file is saved at the current directory
                                     as "robot_name".urdf
            rpy(str): specifies rotational orientation between connectors.
                      the format is same as the rpy of the joint of URDF.
            
        
        """
        if filename is None:
            filename = robot_name + ".urdf"

        if not self.is_compilable():
            self.auto_compile()

        graph = self.get_graph()
        urdf_node_in_graph = self.__get_urdf_file_nodes()
        module_connecting_edges = []
        urdf_ids = {}
        robot_root = None

        for urdf_node_id in urdf_node_in_graph:
            urdf_ids[urdf_node_id] = urdf_node_id
            # For any urdf node, all the node connecting with it
            # are regarded as connectors to other modules.
            # To add joint sections into the resulting urdf file, 
            # list up all the edges between connectors of other modules.
            in_edges = list(graph.in_edges(urdf_node_id))
            out_edges = list(graph.out_edges(urdf_node_id))
            
            leaf_connector_node_id = []
            for edge in out_edges:
                leaf_connector_node_id.append(edge[1])
                urdf_ids[edge[1]] = urdf_node_id

            # Checking the edges between connector nodes.
            # Any connector nodes have only one outward edge and only one inward edge.
            # In the case of the leaf connector, 
            # the outward edge is nothing more than the rigid connection with another module.
            for connector_node in leaf_connector_node_id:
                #print("module = " + self.get_symbol(urdf_node_id) + " [" + str(urdf_node_id) + " ]" +\
                #        " leaf = " + self.get_symbol(connector_node)+ " [" + str(connector_node) + " ]")
                outward_edges = list(graph.out_edges(connector_node))
                #print("  out_edges = " + str([(edge[1], self.get_symbol(edge[1])) for edge in outward_edges]))
                if len(outward_edges) != 0:
                    module_connecting_edges.append(outward_edges[0])

            # In the case of the root connector,
            # the inward edge is the connection betweeen anther module.
            # Note that, all the connection are added to module_connecting_edges
            # via above outward_edges check
            # Therefore, no edges are added by checking the inward edges for the root connector. 
            # However, in a compilable graph, there exists a connector node
            # which is the root of the graph.
            # Here, search for the root node.

            if len(in_edges) == 0:
                # In this case, the urdf node itself is a root.
                robot_root = urdf_node_id 
                #print("urdf root = " + str(robot_root) + " " + self.get_symbol(robot_root))
            else:
                root_connector_node_id = in_edges[0][0]
                urdf_ids[root_connector_node_id] = urdf_node_id

                inward_edges = list(graph.in_edges(root_connector_node_id))
                if len(inward_edges) == 0:
                    robot_root = root_connector_node_id
                    #print("connector root = " + str(robot_root) + " " + self.get_symbol(robot_root))
                    # A root connector registered as robot_root can have multiple outward edges.
                    # (not recommended though)
                    # For such cases, check the outward edges of robot_root 
                    # and register them in module_connecting_edges.
                    outward_edges_of_robot_root = graph.out_edges(robot_root)
                    for edge in outward_edges_of_robot_root:
                        if edge[1] != urdf_node_id:
                            module_connecting_edges.append(edge)


        # Generating strings which describe the existing modules.
        urdf_string_list = []

        #print("urdf_node_in_graph = " + str([self.get_symbol(id) for id in urdf_node_in_graph]))
        for urdf_node_id in urdf_node_in_graph:
            #print("urdf_node_id = " + str(urdf_node_id))
            urdf_filename = self.get_symbol(urdf_node_id)
            urdf_string_list.append(self.urdf_handler.replace_id(urdf_filename, urdf_node_id))

        for edge in module_connecting_edges:
            #print("edge = ", end="")
            #print(self.get_symbol(edge[0]) + "[ " + str(edge[0]) + " ] ",end="")
            #print(self.get_symbol(edge[1]) + "[ " + str(edge[1]) + " ] ")
            urdf_string_list.append(
                    self.urdf_handler.create_fix_joint(
                        urdf_ids[edge[0]],
                        self.get_symbol(edge[0]),
                        urdf_ids[edge[1]],
                        self.get_symbol(edge[1]),
                        rpy=rpy
                        )
                    )
        #print("robot_root = " + str(robot_root) + " [ " + self.get_label(robot_root) + " ] ")
        #print("urdf_ids = " + str(urdf_ids[robot_root]))
        UrdfHandler.write_robot_urdf(
                filename, 
                robot_name,
                urdf_string_list,
                self.get_label(robot_root),
                urdf_ids[robot_root]
                )
        print("[ COMPILE DONE ] output = " + filename)

    def __is_urdf_node(self, node_id):
        """ Checks if the symbol of the given node ends with ".urdf". """
        return self.get_symbol(node_id).endswith('.urdf')

    def __is_connector_node(self, node_id):
        """ Checks if the given node represents a connector. """
        return not self.__is_urdf_node(node_id)

    def __get_urdf_in_graph(self):
        """ Returns urdf_filenames contained in a file at grammar_file_path. """
        return [self.get_symbol(node_id) for node_id in self.get_terminal_symbol_node() 
                if self.get_symbol(node_id).endswith('.urdf')]

    def __get_urdf_filenames(self, include_subdir=False):
        """ Get all the urdf files in the given directory at the initialization."""
        ret = []
        for current_dir, sub_dirs, files_list in os.walk(self.urdf_dir_path):
            ret += files_list 
            if not include_subdir:
                break;
        return ret 

    def __filename_to_fullpath(self, filename):
        """ Concatenates the given filename with the path to the urdf directory. """
        return self.urdf_dir_path + filename

    def __get_urdf_file_nodes(self):
        """ Returns IDs of nodes of which symbols are urdf filenames. """
        return [node_id for node_id in self.get_terminal_symbol_node()
                if self.__is_urdf_node(node_id)]

        





