import threading
import access
from singleton import *

__author__ = 'hupeng'


@singleton
class Rooms:

    class Room:
        def __init__(self, name, members=[]):
            self.name = name
            self.members = set()
            self.members.add(self.owner)
            for m in members:
                self.members.add(m)
            self.mutex = threading.Lock()

        def remove(self, member):
            with self.mutex:
                self.members.remove(member)

        def is_member(self, member):
            return member in self.members

        def add(self, member):
            with self.mutex:
                self.members.add(member)

    def __init__(self):
        self.rooms = set()
        self.access = access.AccessDao()
        rooms = self.access.get_rooms()
        for room in rooms:
            self.rooms.add(self.Room(room, rooms[room]))





