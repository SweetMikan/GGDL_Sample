import os
import xml.etree.ElementTree as ET
from decorated_print import DecoratedPrint

class UrdfHandler():
    """ Class for reading / generating urdf files.

    This class merges several urdf files (representing modules) 
    into one (represeinting a robot).
    Each module urdf must have the following comment rows;

    <!-- PYTHON_READ_START -->

    <!-- PYTHON_READ_END -->

    The links and the joints of the module are required to be written between the comments
    (Call the section sandwitched by the comments 'python section')
    (The conventional "base_link" link and the joint connecting base_link and a link
    need to be outside of the python section)

    To generate unique names for links and joints in the robot urdf file, 
    write '(id)' in the end of the names in a module urdf file.
    e.g.

    <link name="body_link(id)">

    <joint name="roll_joint(id)">

    In the robot urdf file, 'id' is replaced by an unique number.
    The number is shared by all links and joints in a module.

    Attributes:
        __start_symbol(string): '<!-- PYTHON_READ_START -->' without any blanks.
        __end_symbol(string): '<!-- PYTHON_READ_END -->' without any blanks.

    """
    __start_symbol = '<!--PYTHON_READ_START-->'
    __end_symbol = '<!--PYTHON_READ_END-->'

    def __init__(self):
        """
        Each urdf file is handled as a file path to the file.
        The instance registers them into a dictionary 

        key: file name with the extension.

        value: list of strings corresponding to each line in the python section

        links and joints are also dictionaries as above. 

        value(links): list of strings corresponding to each link name

        value(joints): list of strings corresponding to each joint name

        """
        self.urdf_files = {}
        self.links = {}
        self.joints = {}

    def add_urdf(self, path):
        """ Adds an urdf file into the dictionary. 
        
        Returns:
            key(string): A key to access the content of the file.


        """
        chk, str_list, link_list, joint_list = UrdfHandler.is_valid_urdf(path)
        if not chk:
            raise ValueError(DecoratedPrint.decorated_string(
                "[Warning] The given file path(" \
                        + str(path) \
                        + ") was invalid. No urdf file is added.", 
                        DecoratedPrint.red))
        key = UrdfHandler.gen_key(path)
        self.urdf_files[key] = str_list
        self.links[key] = link_list
        self.joints[key] = joint_list
        return key

    def remove_urdf(self, key):
        """ Removes an item with the given key from urdf_files.

        Args:
            key(string): A key for the dictionaries.

        """
        if (key in self.urdf_files) and (key in self.links) and (key in self.joints):
            self.urdf_files.pop(key)
            self.links.pop(key)
            self.joints.pop(key)
        else:
            raise ValueError(DecoratedPrint.decorated_string(
                "[Warning] The given key(" \
                        + str(key) \
                        + ") didn't exist. No urdf file is removed",
                        DecoratedPrint.red))

    def replace_id(self, key, unique_id):
        """ Replaces 'id' for a number in urdf_file[key], and generates a concatenated string. 
        
        Args:
            key(string): A key for the dictionaries
            unique_id(Integer): A number for the unique module ID
        
        """
        str_list = self.urdf_files[key]
        new_list = []
        for s in str_list:
            new_list.append(s.replace('(id)', '(' + str(unique_id) + ')'))

        return UrdfHandler.concatenate_string_list(new_list)

    @classmethod
    def gen_key(cls, path):
        """ Generates a key for the dictionary from path."""
        return os.path.basename(path)

    @classmethod
    def remove_blank(cls, string):
        """ Removes whitespace, tab, newline """
        return ''.join(string.split())

    @classmethod
    def is_valid_urdf(cls, path):
        """ Check if the given path leads to a valid urdf file.

        This method check 
            1. the existence of the file with the given path, 
            2. the existence of the python section in the file.

        Args:
            path(string): A path to be examined

        Returns:
            result(bool): the validity of the file
            str_list(list of string): lines in the python section
            link_list(list of string): list of values of the attribute 'name' of <link>
            joint_list(list of string): list of values of the attribute 'name' of <joint>

        """
        if not os.path.isfile(path):
            return False, None, None, None
        
        with open(path) as f:
            str_list = f.readlines()

        str_list = [s.rstrip() for s in str_list]

        start_index = None
        end_index = None
        for i, e in enumerate(str_list):
            e_ = UrdfHandler.remove_blank(e)
            if e_ == cls.__start_symbol:
                start_index = i
            elif e_ == cls.__end_symbol:
                end_index = i

        if (start_index is None) or (end_index is None) or (start_index > end_index):
            return False, None, None, None

        # Lines in the python section.
        str_list = str_list[start_index+1:end_index]

        # To get link name and joint name, parse the python section.
        # xml parser requires a single root tree, so generate urdf file of form:
        # <robot> python section </robot>
        root_list = ['<robot>', '</robot>']
        root_list[1:1] = str_list
        root = ET.fromstring(UrdfHandler.concatenate_string_list(root_list))

        link_list = []
        joint_list = []

        for link in root.findall('link'):
            link_list.append(link.get('name'))

        for joint in root.findall('joint'):
            joint_list.append(joint.get('name'))

        return True, str_list, link_list, joint_list
    
    @classmethod
    def concatenate_string_list(cls, string_list):
        """ Concatenates the given list of strings.

        This method regards each string in string_list as a line.

        """
        return '\n'.join(string_list)
 
    @classmethod
    def create_fix_joint(cls, id1, link_name1, id2, link_name2, xyz="0 0 0", rpy="0 0 0", indent_num=2):
        """ Generates a string to create a fixed joint. 

        The generated string is a <joint> section.
        This method does not care the existence of link_name1 and link_name2.

        The parent of the joint is link_name1.
        The child of the joint is link_name2.

        The name of the generated joint is link_name1'+'To'+link_name2', 
        where 
        
        link_name1' = link_name1.replace('(id)', '(' + str(id1) + ')'), 

        link_name2' = link_name2.replace('(id)', '(' + str(id2) + ')').

        Args:
            id1(Integer): An id for link_name1
            link_name1(string): the name of link with '(id)'.
            id2(Integer): An id for link_name2
            link_name2(string): the name of link with '(id)'.
            xyz(string): the xyz attribute of the origin tag of urdf
            rpy(string): the rpy attribute of the origin tag of urdf
            indent_num(Integer): Number of whitespace to be inserted.

        """
        link_name1 = link_name1.replace('(id)', '(' + str(id1) + ')')
        link_name2 = link_name2.replace('(id)', '(' + str(id2) + ')')
        joint_name = link_name1 + 'To' + link_name2
        s_tag = ' '*indent_num + '<joint name ="' + joint_name + '" type="fixed">'
        parent = ' '*2*indent_num + '<parent link="' + link_name1 + '"/>'
        child = ' '*2*indent_num + '<child link="' + link_name2 + '"/>'
        origin = ' '*2*indent_num + '<origin xyz="' + xyz +'" rpy="' + rpy + '"/>'
        e_tag = ' '*indent_num + '</joint>'
        return UrdfHandler.concatenate_string_list([s_tag, parent, child, origin, e_tag])

    @classmethod
    def write_header(cls, robot_name, first_link, first_id, indent_num=2):
        """ Returns a header for urdf file. 
        
         
        """
        s = '<robot name="' + robot_name + '">'
        base_link = ' '*indent_num + '<link name="base_link"/>'
        joint = UrdfHandler.create_fix_joint(0, 'base_link', 
                    first_id, first_link, indent_num=indent_num)
        return UrdfHandler.concatenate_string_list([s, base_link,joint])

    @classmethod
    def write_footer(cls):
        """ Returns a footer for urdf file. """
        return '</robot>'


    @classmethod
    def write_robot_urdf(cls, filename, robot_name, str_list, first_link, first_id, indent_num=2):
        """ Generates an urdf file for a robot.

        Args:
            filename(string): A file name for the generated urdf file.
            robot_name(string): the name for the robot.
            str_list(list of string): strings to be written in robot tag.

        """
        root_list = [UrdfHandler.write_header(robot_name, first_link, first_id, indent_num=indent_num), 
                UrdfHandler.write_footer()]
        root_list[1:1] = str_list

        with open(filename, mode='w') as f:
            f.write(UrdfHandler.concatenate_string_list(root_list))
 
