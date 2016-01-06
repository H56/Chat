import Queue
import threading
import access
from singleton import *

__author__ = 'hupeng'


@singleton
class Rooms:
    class Room:
        def __init__(self, rid, name, owner):
            self.rid = rid
            self.name = name
            self.members = set()
            self.owner = owner
            # self.members.add(owner)
            self.mutex = threading.Lock()
            self.messages = Queue.Queue()

        def remove(self, member):
            try:
                with self.mutex:
                    self.members.remove(member)
            except KeyError:
                pass

        def is_member(self, member):
            return member in self.members

        def add_member(self, member):
            with self.mutex:
                self.members.add(member)

        def add_message(self, msg):
            self.messages.put(msg)

        def get_message(self):
            return self.messages.get_nowait()

        def get_all_messages(self):
            all_messages = []
            while not self.messages.empty():
                all_messages.append(self.messages.get_nowait())
            return all_messages

        def __iter__(self):
            self.members_next = self.members.__iter__()
            return self

        def next(self):
            return self.members_next.next()

        def __contains__(self, item):
            return item in self.members

    def __init__(self):
        self.rooms = {}
        dao = access.AccessDao()
        rooms = dao.get_rooms()
        for room in rooms:
            self.rooms[room[0]] = self.Room(room[0], room[1], room[2])

        self.index = 0

    def add(self, room_id, room_name, owner):
        self.rooms[room_id] = self.Room(room_id, room_name, owner)

    def get_message(self, room):
        try:
            return self.rooms[room].get_message()
        except Exception as e:
            raise e

    def get_all_message(self, room):
        try:
            return self.rooms[room].get_all_messages()
        except Exception as e:
            raise e

    def __iter__(self):
        self.rooms_next = self.rooms.__iter__()
        return self

    def next(self):
        return self.rooms_next.next()

    def __getitem__(self, item):
        return self.rooms[item]

    def __contains__(self, item):
        return item in self.rooms








