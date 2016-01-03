import sys
import select
from time import sleep
import termios
import tty
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