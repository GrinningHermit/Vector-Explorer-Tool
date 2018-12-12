import enum

def print_format_table():
    """
    prints table of formatted text format options
    """
    for style in range(8):
        for fg in range(30,38):
            s1 = ''
            for bg in range(40,48):
                format = ';'.join([str(style), str(fg), str(bg)])
                s1 += '\x1b[%sm %s \x1b[0m' % (format, format)
            print(s1)
        print('\n')

# print_format_table()

class Pcolors (enum.Enum):
    BLACK = '7;30;47'
    WHITE = '7;30;47'
    YELLOW = '7;30;43'
    BLUE = '7;30;44'
    RED = '7;30;41'
    PURPLE = '7;30;45'
    GREEN = '7;30;42'
    BG_BLACK = '7;30;47'
    BG_WHITE = '7;37;40'
    BG_YELLOW = '7;33;40'
    BG_BLUE = '7;34;40'
    BG_RED = '7;31;40'
    BG_PURPLE = '7;35;40'
    BG_GREEN = '7;32;40'

def printf(string,enum_color=Pcolors.WHITE):
    print('\x1b[' + enum_color.value + 'm' + string + '\x1b[0m')