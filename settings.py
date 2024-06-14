import dataclasses
import json
import os


@dataclasses.dataclass
class Settings:
    base_width: int
    base_height: int
    base_cell_width: int
    base_grid_width: int
    scale: int
    theme: str
    sound_state: int
    data_folder: str
    base_img_folder: str
    img_folder: str
    db_filename: str

    @property
    def width(self):
        return self.base_width * self.scale

    @property
    def height(self):
        return self.base_height * self.scale

    @property
    def cell_width(self):
        return self.base_cell_width * self.scale

    @property
    def grid_width(self):
        return self.base_grid_width * self.scale

    @property
    def data_path(self):
        return os.path.join(os.path.dirname(__name__), self.data_folder)

    @property
    def base_img_path(self):
        return os.path.join(self.data_path, self.base_img_folder)

    @property
    def img_path(self):
        return os.path.join(self.data_path, self.img_folder)

    @property
    def field_center(self) -> (int, int):
        return self.width // 2, self.width // 2 + 80 * self.scale

    @property
    def subfield_center_distance(self) -> int:
        return int(self.grid_width * 2.5 + self.cell_width * 1.5)

    @classmethod
    def from_jsons(cls):
        with open("config.json") as config_file:
            data = json.load(config_file)

        with open("settings.json") as settings_file:
            data.update(json.load(settings_file))

        return cls(**data)

    def back_to_default(self):
        with open("config.json") as config_file:
            data = json.load(config_file)
        self.__dict__.update(data)

    def save(self):
        with open("settings.json", "w") as settings_file:
            json.dump(
                {
                    "scale": self.scale,
                    "theme": self.theme,
                    "sound_state": self.sound_state,
                },
                settings_file
            )


settings = Settings.from_jsons()
