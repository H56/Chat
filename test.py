import sys
import select
import threading
from time import sleep
import termios
import tty
import thread


class iter_test:
    def __init__(self):
        self.data = [1, 2, 3, 4]
        self.index = 0
        pass

    def __iter__(self):
        self.data_next = self.data.__iter__()
        return self

    def next(self):
        return self.data_next.next()

    def __contains__(self, item):
        return item in self.data

it = iter_test()
for i in it:
    print(i)
for i in it:
    print(i)
print(1 in it)

def timer(ID):
    print(str(ID) + ':  ' + str(thread.get_ident()))

for i in range(0, 2):
    timer0 = threading.Timer(0.1, timer, (0, ))
    timer0.start()
    timer1 = threading.Timer(0.1, timer, (1, ))
    timer1.start()
    timer2 = threading.Timer(0.1, timer, (2, ))
    timer2.start()
    thread.start_new_thread(timer, ('thread0', ))
    thread.start_new_thread(timer, ('thread1', ))
    thread.start_new_thread(timer, ('thread2', ))
    sleep(1)

old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())
while True:
    sleep(.001)
    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        c = sys.stdin.read(1)
        if c == '\x1b': break
        sys.stdout.write(c)
        sys.stdout.flush()
termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
print raw_input('123:')
