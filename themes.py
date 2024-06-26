import dataclasses
import functools

from database import database


@dataclasses.dataclass
class Theme:
    id: int
    name: str
    background_color: tuple
    non_clickable_color: tuple
    clickable_color: tuple
    text_color: tuple
    hovered_color: tuple
    interface_color: tuple

    def get_colors(self):
        return (
            self.background_color,
            self.non_clickable_color,
            self.clickable_color,
            self.text_color,
            self.hovered_color,
            self.interface_color,
        )

    def __getitem__(self, item):
        try:
            return getattr(self, item)

        except AttributeError:
            raise KeyError


class Themes:
    def __init__(self) -> None:
        self.db = database
        self.themes = {}
        for data in self.db.select_from("theme"):
            print(self.db.select_from("theme"))
            theme = self._create_theme_from_dict(data)
            self.themes[theme.name] = theme

    def _create_theme_from_dict(self, data: dict):
        for key in data:
            if key.endswith("color"):
                color = self._get_color(data[key])
                data[key] = color

        return Theme(**data)

    @functools.cache
    def _get_color(self, pk):
        data = self.db.get_from("color", id=pk)
        data.pop("id")
        return tuple(data.values())

    def get_color(self, theme, name):
        return self.themes[theme].__dict__[name]

    def __getattr__(self, item):
        if item in self.themes:
            return self.themes[item]

        raise AttributeError

    def __getitem__(self, item):
        if item in self.themes:
            return self.themes[item]

        raise KeyError


themes = Themes()
