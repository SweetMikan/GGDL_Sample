class DecoratedPrint():
    """ Extensions for print function

    This class provides methods such as printing string with color.
    Almost same class and methods are provided by 'colorama' package.
    However, the package is required to be installed via pip.
    To avoid unnecessary pip operation, imprement them by myself.

    Attributes: 
        black(string): Escape sequence for black
        red(string): Escape sequence for red
        green(string): Escape sequence for green
        yellow(string): Escape sequence for yellow
        blue(string): Escape sequence for blue
        magenta(string): Escape sequence for magenta
        cyan(string): Escape sequence for cyan
        white(string): Escape sequence for white
        bold(string): Escape sequence for bold
        underline(string): Escape sequence for underline
        bg_black(string): Escape sequence for bg_black
        bg_red(string): Escape sequence for bg_red
        bg_green(string): Escape sequence for bg_green
        bg_blue(string): Escape sequence for bg_blue
        bg_magenta(string): Escape sequence for bg_magenta
        bg_cyan(string): Escape sequence for bg_cyan
    
    """
    ## Public attributes
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"
    bold = "\033[1m"
    underline = "\033[4m"
    bg_black = "\033[40m"
    bg_red = "\033[41m"
    bg_green = "\033[42m"
    bg_yellow = "\033[43m"
    bg_blue = "\033[44m"
    bg_magenta = "\033[45m"
    bg_cyan = "\033[46m"
    bg_white = "\033[47m"
    reset = "\033[0m"

    ## Public class methods
    @classmethod
    def decorated_string(cls, string, *args):
        """ Generates a string with decoration specifiers.

        The returned string have 'reset' option at the end

        Args:
            string(string): A string to be decorated
            args(strings): Decoration specifiers. Use the class attributions.


        """
        s = str(string)
        for arg in args:
            s = arg + s
        return s + DecoratedPrint.reset

    @classmethod
    def deco_print(cls, string, *args):
        """ Print a string with decoration 
        
        Args: 
            string(string): A string to be decorated
            args(strings): Decoration specifiers. Use the class attributions.
            
        """
        return print(DecoratedPrint.decorated_string(string, *args))


