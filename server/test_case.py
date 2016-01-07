from calculator import *

__author__ = 'hupeng'

test_dict = {'1': 1,
             '12345': 12345,
             '1+2': 3,
             '     4   /    2': 2,
             '  3 +  2 -  5   * 0  ': 5,
             ' (   1   + 3  ) *   (2  + 5) ': 28,
             ' ( 3)': 3,
             '((((3) + ((2)) - 5 * (0)  ) ) )': 5,
             '(( 4 + 1 ) + 3': 'error',
             ' (3 + 11) + )': 'error',
             ' (3 + 1))': 'error'
             }


l = []
r = calculator('(1 + 2) * 3 + 2', nums_list=l)
print(r)


for test in test_dict:
    try:
        ret = calculator(test)
    except Exception as e:
        ret = 'error'
    if ret == test_dict[test]:
        print(test + ': OK\r\n')
    else:
        print(test + ': WRONG\r\n')
