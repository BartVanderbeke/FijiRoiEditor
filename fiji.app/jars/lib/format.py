"""

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.

"""

def format_number(val):
    if abs(val) >= 1e5:
        temp = "%.0f" % val
    else:
        temp = "%.4g" % val
    temp = temp.replace(".", ",")
    return temp