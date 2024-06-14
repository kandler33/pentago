import os

from PIL import Image

from settings import settings
from themes import themes


class ImageCreator:
    base_colors = (
        (255, 255, 255, 255),
        (170, 220, 175, 255),
        (93, 143, 98, 255),
        (0, 0, 0, 255),
        (180, 180, 180, 255),
        (9, 56, 13, 255),
    )
    hovered_colors = (
        (255, 255, 255, 255),
        (170, 220, 175, 255),
        (-1, -1, -1, -1),
        (0, 0, 0, 255),
        (93, 143, 98, 255),
        (9, 56, 13, 255),
    )

    @property
    def palet(self):
        return dict(zip(self.base_colors, themes[settings.theme].get_colors()))

    @property
    def hovered_palet(self):
        return dict(zip(self.hovered_colors, themes[settings.theme].get_colors()))
    
    @staticmethod
    def split_by_len(obj, num):
        for i in range(num, len(obj) + 1, num):
            yield obj[i - num : i]

    @staticmethod
    def scaled_data_gen(data, scale):
        for row in data:
            new_row = []
            for pixel in row:
                for _ in range(scale):
                    new_row.append(pixel)
            for _ in range(scale):
                yield from new_row

    def create_non_themeable_img(self, input_path, output_path):
        with Image.open(input_path).convert(
                "RGBA"
        ) as base_img:
            new_img = Image.new(
                "RGBA", (base_img.width * settings.scale * 5, base_img.height * settings.scale * 5)
            )
            data = tuple(self.split_by_len(tuple(base_img.getdata()), base_img.width))
            new_data = tuple(self.scaled_data_gen(data, settings.scale * 5))
            new_img.putdata(new_data)
            new_img.save(output_path)

    def create_themeable_img(self, input_path, output_path):
        with Image.open(input_path).convert(
                "RGBA"
        ) as base_img:
            new_img = Image.new(
                "RGBA",
                (base_img.width * settings.scale * 5, base_img.height * settings.scale * 5),
            )
            data = tuple(self.split_by_len(tuple(base_img.getdata()), base_img.width))
            new_data = tuple(
                map(
                    lambda x: self.palet.get(x, (255, 255, 255, 0)),
                    self.scaled_data_gen(data, settings.scale * 5),
                )
            )
            new_img.putdata(new_data)
            new_img.save(output_path)

    def create_hovered_img(self, input_path, output_path):
        with Image.open(input_path).convert(
                "RGBA"
        ) as base_img:
            hovered_img = Image.new(
                "RGBA",
                (base_img.width * settings.scale * 5, base_img.height * settings.scale * 5),
            )
            data = tuple(self.split_by_len(tuple(base_img.getdata()), base_img.width))
            hovered_data = tuple(
                map(
                    lambda x: self.hovered_palet.get(x, (255, 255, 255, 0)),
                    self.scaled_data_gen(data, settings.scale * 5),
                )
            )
            hovered_img.putdata(hovered_data)
            hovered_img.save(output_path)
