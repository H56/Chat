__author__ = 'hupeng'


def skip_space(s, start):
    end = start
    length = len(s)
    while end < length and s[end].isspace():
        end += 1
    return end


def calculate(num1, num2, operator):
    if operator == '+':
        return num1 + num2
    elif operator == '-':
        return num1 - num2
    elif operator == '*':
        return num1 * num2
    elif operator == '/':
        return num1 / num2
    else:
        raise Exception("Wrong operator!")


def calculate_all(nums, operators):
    # nums.reverse()
    # operators.reverse()
    iter_nums = iter(nums)
    ret = iter_nums.next()
    try:
        for o in operators:
            ret = calculate(ret, iter_nums.next(), o)
    except StopIteration:
        raise Exception("Too many operators!")
    try:
        iter_nums.next()
    except StopIteration:
        return ret
    else:
        raise Exception('Too many numbers!')


def calculator(s, start=0, brackets_count=0, nums_list=[]):
    nums = []
    operators = []
    length = len(s)
    end = skip_space(s, start)
    while end < length:
        start = end
        if s[start].isdigit() or s[start] is '(':
            end = start + 1
            if s[start].isdigit():
                while end < length and s[end].isdigit():
                    end += 1
                num = int(s[start: end])
                nums_list.append(num)
            else:
                try:
                    num, end = calculator(s, end, 1, nums_list)
                except TypeError:
                    raise Exception("Too many '('!")
                if end >= length or s[end] != ')':
                    raise Exception("missing ')' at " + str(end))
                end += 1
            if operators and operators[len(operators) - 1] in ['*', '/']:
                if nums:
                    nums[len(nums) - 1] = calculate(nums[len(nums) - 1], num, operators.pop())
                else:
                    raise Exception('Wrong format!')
            else:
                nums.append(num)
        elif s[start] in ['+', '-', '*', '/']:
            operators.append(s[start])
            end = start + 1
        elif s[start] is ')':
            if brackets_count <= 0:
                raise Exception("Too much ')'")
            return calculate_all(nums, operators), start
        else:
            raise Exception("Wrong format!")
        end = skip_space(s, end)
    return calculate_all(nums, operators)
