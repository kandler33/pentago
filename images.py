import itertools

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
        yield from itertools.batched(obj, num)

    @staticmethod
    def scaled_data_gen(data, scale):
        for row in data:
            new_row = []
            for pixel in row:
                for _ in range(scale):
                    new_row.append(pixel)
            for _ in range(scale):
                yield from new_row

    @staticmethod
    def apply_palet(data, palet):
        yield from (palet.get(color, (255, 255, 255, 0)) for color in data)

    def create_non_themeable_img(self, input_path, output_path):
        with Image.open(input_path).convert(
                "RGBA"
        ) as base_img:
            new_img = Image.new(
                "RGBA", (base_img.width * settings.scale * 5, base_img.height * settings.scale * 5)
            )
            data = self.split_by_len(base_img.getdata(), base_img.width)
            data = tuple(self.scaled_data_gen(data, settings.scale * 5))
            new_img.putdata(data)
            new_img.save(output_path)

    def create_themeable_img(self, input_path, output_path, hovered=False):
        palet = self.hovered_palet if hovered else self.palet
        with Image.open(input_path).convert(
                "RGBA"
        ) as base_img:
            new_img = Image.new(
                "RGBA",
                (base_img.width * settings.scale * 5, base_img.height * settings.scale * 5),
            )
            data = self.apply_palet(base_img.getdata(), palet)
            data = self.split_by_len(data, base_img.width)
            data = tuple(self.scaled_data_gen(data, settings.scale * 5))
            new_img.putdata(data)
            new_img.save(output_path)

    def create_hovered_img(self, input_path, output_path):
        self.create_themeable_img(input_path, output_path, True)
