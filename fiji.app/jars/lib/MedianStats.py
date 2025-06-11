from java.util import Arrays
from jarray import array

def median_stats_from_jarray(jarr, range_stop):
    if jarr is None or range_stop <= 0 or range_stop > len(jarr):
        return None, None, None, None

    # copy  the required range
    subset = Arrays.copyOf(jarr, range_stop)
    Arrays.sort(subset)

    n = range_stop

    # Helper: median of subarray
    def median_jarray(arr, start, end):
        count = end - start
        mid = start + count // 2
        if count % 2 == 1:
            return arr[mid]
        else:
            return 0.5 * (arr[mid - 1] + arr[mid])

    # Median en quartiles
    med = median_jarray(subset, 0, n)
    q1 = median_jarray(subset, 0, n // 2)
    q3 = median_jarray(subset, (n + 1) // 2, n)

    # MAD (median absolute deviation)
    # https://en.wikipedia.org/wiki/Median_absolute_deviation
    abs_dev = array([abs(jarr[i] - med) for i in range(range_stop)], 'd')
    Arrays.sort(abs_dev)
    mad = median_jarray(abs_dev, 0, n)
    
    # lower limit for filtering: Q1 - 1.5 * IQR
    # upper limit for filtering: Q3 + 1.5 * IQR

    return med, q1, q3, mad
