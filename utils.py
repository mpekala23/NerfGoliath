def print_error(msg):
    """
    Print an error string in red color
    """
    print("\033[91m{}\033[00m".format(msg))


def print_success(msg):
    """
    Print a success string in green color
    """
    print("\033[92m{}\033[00m".format(msg))


def print_info(msg):
    """
    Print an info string in a blue color
    """
    print("\033[94m{}\033[00m".format(msg))
