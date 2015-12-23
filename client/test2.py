#!/usr/bin/python
# -*- coding: utf-8 -*-
from threading import Timer
import sys
from getch import getch

timer1 = None
time2 = None
s = ''


def generate(a, b):
    global timer1
    global s
    s += str((a, b)) + '\r\n'
    timer1 = Timer(1, generate, (a + 1, b + 1))
    timer1.start()


def output():
    global time2
    global s
    if len(s) > 0:
        print(s)
    s = ''
    time2 = Timer(0.1, output, ())
    time2.start()


generate(1, 2)
output()
command = ""
while True:
    ch = getch()
    if ch == '\3':
        print('Exist')
        break
    time2.cancel()
    s1 = raw_input('Message:')
    print('input: ' + s1)
    output()

timer1.cancel()
time2.cancel()
