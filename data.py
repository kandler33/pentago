import dataclasses
import json
import os.path

from assets import assets
from themes import themes
from settings import settings


class Data:
    def __init__(self):
        self.settings = settings
        self.assets = assets
        self.themes = themes
        self.score = Score.from_json()

    def save(self):
        self.settings.save()
        self.score.save()


@dataclasses.dataclass
class Score:
    cross: int = 0
    zero: int = 0
    draw: int = 0

    @staticmethod
    def json_path():
        return os.path.join(settings.data_path, "score.json")

    @classmethod
    def from_json(cls):
        try:
            with open(cls.json_path()) as score_file:
                data = json.load(score_file)
            return cls(**data)

        except FileNotFoundError:
            return cls()

    def save(self):
        with open(self.json_path(), "w") as score_file:
            json.dump(
                {"cross": self.cross, "zero": self.zero, "draw": self.draw},
                score_file,
            )

    def reset(self):
        self.cross = 0
        self.zero = 0
        self.draw = 0

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value


data = Data()
