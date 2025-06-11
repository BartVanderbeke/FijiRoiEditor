def format_number(val):
    if abs(val) >= 1e5:
        temp = "%.0f" % val
    else:
        temp = "%.4g" % val
    temp = temp.replace(".", ",")
    return temp