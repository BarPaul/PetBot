
from dataclasses import dataclass, field
from typing import Literal
# from math import e
from sqlite3 import connect
from datetime import datetime
from time import sleep
from threading import Thread


@dataclass
class User:
    id: int = field(repr=False)
    pet_type: str
    level: int
    xp: int
    energy: int = field(repr=False)
    money: int

    def as_tuple(self) -> tuple:
        return (self.id, self.pet_type, self.level, self.xp, self.energy, self.money,)


class Database:
    def __init__(self):
        self.__conn = connect('database.db', check_same_thread=False)
        self.__cur = self.__conn.cursor()
        self.__execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER UNIQUE,
                            pet_type TEXT,
                            level INTEGER,
                            xp INTEGER,
                            energy INTEGER,
                            money INTEGER
                        )''')
        self.__execute('''CREATE TABLE IF NOT EXISTS timer (
                            id INTEGER UNIQUE,
                            seconds INTEGER,
                            action TEXT
                        )''')
        self.__execute('''CREATE TABLE IF NOT EXISTS levels (
                            level INTEGER UNIQUE,
                            xp INTEGER
                        )''')
        # for i in range(1, 1000):
        #     self.__execute("INSERT or IGNORE INTO levels VALUES (?, ?)", (i, int(i ** e)))
        
    def __execute(self, query, args=None, fetchone=False):
        if args is None:
            self.__cur.execute(query) 
        else:
            self.__cur.execute(query, args)
        self.__conn.commit()
        if fetchone:
            return self.__cur.fetchone()
        return self.__cur.fetchall()

    def __get_unix_time(self) -> int:
        return int(datetime.now().timestamp())

    def insert_user(self, user: User):
        self.__execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", user.as_tuple())

    def is_user(self, uid: int) -> bool:
        result = self.__execute("SELECT * FROM users WHERE id = ?", (uid,), True)
        return result is not None

    def delete_user(self, uid: int):
        self.__execute("DELETE FROM users WHERE id = ?", (uid,))
        self.__execute("DELETE FROM timer WHERE id = ?", (uid,))


    def get_user(self, uid: int) -> User:
        result = self.__execute("SELECT * FROM users WHERE id = ?", (str(uid),), fetchone=True)
        return User(*result) if result else None

    def update_user(self, user: User):
        self.__execute("UPDATE users SET id = ?, pet_type = ?, level = ?, xp = ?, energy = ?, money = ? WHERE id = ?", 
                        user.as_tuple() + (user.id,))

    def add_timer(self, uid: int, seconds: int, action: str):
        self.__execute("INSERT INTO timer VALUES (?, ?, ?)", (uid, self.__get_unix_time() + seconds, action,))

    def is_calldown(self, uid: int, action: str) -> bool:
        result = self.__execute("SELECT * FROM timer WHERE id = ? AND action = ?", (uid, action,), fetchone=True)
        return result is not None

    def get_timer(self, uid: int, action: str) -> int:
        result = self.__execute("SELECT seconds FROM timer WHERE id = ? AND action = ?", (uid, action,), fetchone=True)
        return result[0] if result else 0

    def check_timer(self):
        while True:
            res = self.__execute("SELECT * FROM timer")
            if not res:
                continue
            for uid, seconds, action in res:
                if seconds <= int(datetime.now().timestamp()):
                    self.__execute("DELETE FROM timer WHERE id = ? AND action = ?", (uid, action,))
                    continue
                sleep(1)
    
    def get_xp(self, user: User, level: int = None) -> int:
        if level is None:
            level = user.level + 1
        return self.__execute("SELECT xp FROM levels WHERE level = ?", (level,), True)[0]

    def level_up(self, user: User):
        prev_level = user.level
        while user.xp >= self.get_xp(user):
            user.level += 1
        user.xp -= self.get_xp(user, user.level) if user.level != prev_level else 0
        self.update_user(user)
    
    def get_leaderboard(self, by: Literal["money", "level"]) -> list[User]:
        return [User(*user) for user in self.__execute("SELECT * FROM users ORDER BY ? LIMIT 10", (by,))]

db = Database()
# timer = Thread(target=db.check_timer, daemon=True)
# timer.start()
# timer.join()