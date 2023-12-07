import pygame
import os
from PIL import Image
import pickle
import time
import asyncio


class SpriteObject(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self.img_path = img
        self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()

    def update_scale(self, old_scale, new_scale):
        self.image = pygame.image.load(self.img_path)

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)


class CordSpriteObject(SpriteObject):
    def __init__(self, img, cords):
        super().__init__(img)
        self.rect.center = cords

    def set_pos(self, cords):
        self.rect.center = cords

    def update_scale(self, old_scale, new_scale):
        self.image = pygame.image.load(self.img_path)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)


class Button(CordSpriteObject):
    def __init__(self, imgs, cords):
        super().__init__(imgs[0], cords)
        self.imgs_path = imgs
        self.basic_image = pygame.image.load(imgs[0])
        self.hovered_image = pygame.image.load(imgs[1])
        self.image = self.basic_image

    def update(self):
        if collide(pygame.mouse.get_pos(), self):
            self.image = self.hovered_image
        else:
            self.image = self.basic_image

    def update_scale(self, old_scale, new_scale):
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.image = self.basic_image
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self):
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.image = self.basic_image


class ChoiceButton(Button):
    def __init__(self, imgs, cords, clicked):
        super().__init__(imgs[:2], cords)
        self.imgs_path = imgs
        self.clicked_image = pygame.image.load(self.imgs_path[2])
        self.clicked = clicked
        if self.clicked:
            self.image = self.clicked_image

    def update(self):
        if self.clicked:
            self.image = self.clicked_image

        else:
            super().update()

    def update_scale(self, old_scale, new_scale):
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.clicked_image = pygame.image.load(self.imgs_path[2])
        if self.clicked:
            self.image = self.clicked_image
        else:
            self.image = self.basic_image

        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self):
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.clicked_image = pygame.image.load(self.imgs_path[2])
        if self.clicked:
            self.image = self.clicked_image
        else:
            self.image = self.basic_image


class SubField(pygame.sprite.Sprite):
    def __init__(self, num, img):
        super().__init__()
        self.img_path = img
        self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()
        self.rect.center = SUBFIELD_CORDS[num]
        self.field_list = [[Cell(self, i, j) for i in range(3)] for j in range(3)]
        for row in self.field_list:
            all_sprites.add(*row)

    def add_sign(self, x, y):
        global current_sign, current_step
        if type(self.field_list[y][x]) == Cell:
            self.field_list[y][x].kill()
            if current_sign == 1:
                self.field_list[y][x] = Cross(self, cross_img, x, y)
                current_sign = 0
            else:
                self.field_list[y][x] = Zero(self, zero_img, x, y)
                current_sign = 1
            all_sprites.add(self.field_list[y][x])
            if is_any_empty_subfields():
                current_step = -1
            else:
                current_step = 1

    def rotate_counterclockwise(self):
        new_field_list = [[None] * 3, [None] * 3, [None] * 3]
        for y in range(3):
            for x in range(3):
                new_field_list[y][x] = self.field_list[x][2 - y]
                new_field_list[y][x].change_pos(x, y)
        self.field_list = new_field_list

    def rotate_clockwise(self):
        new_field_list = [[None] * 3, [None] * 3, [None] * 3]
        for y in range(3):
            for x in range(3):
                new_field_list[y][x] = self.field_list[2 - x][y]
                new_field_list[y][x].change_pos(x, y)
        self.field_list = new_field_list

    def restart(self):
        for row in self.field_list:
            for cell in row:
                cell.kill()
        self.field_list = [[Cell(self, i, j) for i in range(3)] for j in range(3)]
        for row in self.field_list:
            all_sprites.add(row)

    def hovered(self):
        pass

    def is_empty(self):
        return all([all([type(i) == Cell for i in row]) for row in self])

    def update_scale(self, old_scale, new_scale):
        self.image = pygame.image.load(self.img_path)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)

    def __str__(self):
        return f'SubField {field.index(self)}'

    def __getitem__(self, key):
        return self.field_list[key]


class Arrow(Button):
    def __init__(self, cords, imgs, subfield, clockwise):
        super().__init__(imgs, cords)
        self.subfield = subfield
        self.clockwise = clockwise

    def click(self):
        global current_step
        if self.clockwise:
            self.subfield.rotate_clockwise()
        else:
            self.subfield.rotate_counterclockwise()

        current_step = 0

    def update(self):
        if game_active and not settings_opened and current_step in (-1, 1) and collide(pygame.mouse.get_pos(), self):
            self.image = self.hovered_image
        else:
            self.image = self.basic_image

    def __str__(self):
        return f'({"clockwise" if self.clockwise else "counterclockwise"} Arrow of {str(self.subfield)})'


class Cell(pygame.sprite.Sprite):
    def __init__(self, field, x, y):
        super().__init__()
        self.subfield = field
        self.cords = (x, y)
        self.basic_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.basic_image.fill(settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.hovered_image.fill(settings.get_color('hovered_color'))
        self.image = self.basic_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def get_cords(self):
        return self.cords

    def change_pos(self, x, y):
        self.cords = (x, y)
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update(self):
        if game_active and not settings_opened and current_step in (-1, 0) and collide(pygame.mouse.get_pos(), self):
            self.image = self.hovered_image
        else:
            self.image = self.basic_image

    def update_scale(self, *args):
        self.basic_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.basic_image.fill(settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.hovered_image.fill(settings.get_color('hovered_color'))
        self.image = self.basic_image

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update_theme(self):
        self.basic_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.basic_image.fill(settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((settings.cell_width, settings.cell_width))
        self.hovered_image.fill(settings.get_color('hovered_color'))
        self.image = self.basic_image

    def __str__(self):
        return f'(Cell[{self.cords[1]}][{self.cords[0]}] of {str(self.subfield)})'


class Sign(Cell):
    def __init__(self, field, image, x, y):
        super().__init__(field, x, y)
        self.img_path = image
        self.image = pygame.image.load(self.img_path)

    def update(self):
        pass

    def update_scale(self, *args):
        self.image = pygame.image.load(self.img_path)

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)


class Cross(Sign):
    def __init__(self, field, cross_img, x, y):
        super().__init__(field, cross_img, x, y)


class Zero(Sign):
    def __init__(self, field, zero_img, x, y):
        super().__init__(field, zero_img, x, y)


class Settings:
    def __init__(self, saved_settings=None):
        self.basic_settings = {'width': 600, 'height': 680, 'scale': 1, 'theme': 'basic',
                               'cell_width': 65, 'grid_width': 10}
        self.themes = {'basic': ((255, 255, 255, 255), (170, 220, 175, 255), (93, 143, 98, 255),
                                 (0, 0, 0, 255), (180, 180, 180, 255), (9, 56, 13, 255)),
                       'pale pink': ((254, 245, 239, 255), (220, 193, 196, 255), (157, 92, 99, 255),
                                     (88, 75, 83, 255), (202, 155, 114, 255), (75, 29, 34, 255))}
        if saved_settings is None:
            self.width = self.basic_settings['width']
            self.height = self.basic_settings['height']
            self.scale = self.basic_settings['scale']
            self.theme = self.basic_settings['theme']
            self.cell_width = self.basic_settings['cell_width']
            self.grid_width = self.basic_settings['grid_width']

        else:
            self.width = saved_settings['width']
            self.height = saved_settings['height']
            self.scale = saved_settings['scale']
            self.theme = saved_settings['theme']
            self.cell_width = saved_settings['cell_width']
            self.grid_width = saved_settings['grid_width']

    def get_color(self, color_name: str) -> tuple[int, int, int, int]:
        colors = ('background_color', 'non_clickable_color',
                  'clickable_color', 'text_color', 'hovered_color', 'interface_color')
        return self.themes[self.theme][colors.index(color_name)]

    def get_color_palet(self, palet_name: str = None):
        if palet_name is None:
            return self.themes[self.theme]
        return self.themes[palet_name]

    def update_scale(self, new_scale: int) -> None:
        if new_scale != self.scale:
            old_scale = self.scale
            self.scale = new_scale
            self.width = self.basic_settings['width'] * self.scale
            self.height = self.basic_settings['height'] * self.scale
            self.cell_width = self.basic_settings['cell_width'] * self.scale
            self.grid_width = self.basic_settings['grid_width'] * self.scale
            update_images(self.themes[self.theme], self.scale)
            update_screen_scale(old_scale, new_scale)

    def update_theme(self, new_theme: str) -> None:
        if new_theme != self.theme:
            self.theme = new_theme
            update_images(self.themes[self.theme], self.scale)
            update_screen_theme()

    def back_to_default(self):
        self.update_scale(1)
        self.update_theme('basic')


def split_by_len(obj, num):
    for i in range(num, len(obj) + 1, num):
        yield obj[i-num:i]


def scaled_data_gen(data, scale):
    for row in data:
        new_row = []
        for pixel in row:
            for _ in range(scale):
                new_row.append(pixel)
        for _ in range(scale):
            yield from new_row


def time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        res = func(*args, **kwargs)
        end_time = time.perf_counter() - start_time
        print(f'function {func.__name__} took {end_time}')
        return res
    return wrapper


def collide(cords, obj):
    x, y = cords
    if obj.rect.left <= x <= obj.rect.right and obj.rect.top <= y <= obj.rect.bottom:
        return True
    return False


def add_sign(subfield, cords):
    for row in subfield.field_list:
        for cell in row:
            if collide(cords, cell):
                subfield.add_sign(*cell.get_cords())


def unite_field():
    res = [None] * 6
    for i in range(3):
        res[i] = field[0][i] + field[1][i]
        res[3 + i] = field[2][i] + field[3][i]
    return res


def win_draw_check():
    global cross_win_condition, zero_win_condition, draw_condition
    field = list(map(lambda x: [type(i) for i in x], unite_field()))

    for i in range(6):
        # horizontal
        if [field[i][j] for j in range(5)].count(Cross) == 5 or [field[i][j] for j in range(1, 6)].count(Cross) == 5:
            cross_win_condition = True
        if [field[i][j] for j in range(5)].count(Zero) == 5 or [field[i][j] for j in range(1, 6)].count(Zero) == 5:
            zero_win_condition = True

        # vertical
        if [field[j][i] for j in range(5)].count(Cross) == 5 or [field[j][i] for j in range(1, 6)].count(Cross) == 5:
            cross_win_condition = True
        if [field[j][i] for j in range(5)].count(Zero) == 5 or [field[j][i] for j in range(1, 6)].count(Zero) == 5:
            zero_win_condition = True

    # main diagonals
    if any(([field[i][i + 1] for i in range(5)].count(Cross) == 5,
            [field[i][i] for i in range(5)].count(Cross) == 5,
            [field[i][i] for i in range(1, 6)].count(Cross) == 5,
            [field[i + 1][i] for i in range(5)].count(Cross) == 5)):
        cross_win_condition = True

    if any(([field[i][i + 1] for i in range(5)].count(Zero) == 5,
            [field[i][i] for i in range(5)].count(Zero) == 5,
            [field[i][i] for i in range(1, 6)].count(Zero) == 5,
            [field[i + 1][i] for i in range(5)].count(Zero) == 5)):
        zero_win_condition = True

    # side diagonals
    if any(([field[5 - i][i + 1] for i in range(5)].count(Cross) == 5,
            [field[5 - i][i] for i in range(5)].count(Cross) == 5,
            [field[5 - i][i] for i in range(1, 6)].count(Cross) == 5,
            [field[4 - i][i] for i in range(5)].count(Cross) == 5)):
        zero_win_condition = True

    if any(([field[5 - i][i + 1] for i in range(5)].count(Zero) == 5,
            [field[5 - i][i] for i in range(5)].count(Zero) == 5,
            [field[5 - i][i] for i in range(1, 6)].count(Zero) == 5,
            [field[4 - i][i] for i in range(5)].count(Zero) == 5)):
        zero_win_condition = True

    # draw check
    if all([all([i != Cell for i in row]) for row in field]):
        draw_condition = True

    if cross_win_condition and zero_win_condition:
        cross_win_condition, zero_win_condition = False, False
        draw_condition = True


def restart():
    global field, text_sprites
    global current_step, current_sign, game_active, info_panel_opened, settings_opened
    global cross_win_condition, zero_win_condition, draw_condition
    for sprite in text_sprites:
        sprite.kill()
    for subfield in field:
        subfield.restart()

    game_active = True
    info_panel_opened = False
    settings_opened = False
    cross_win_condition = False
    zero_win_condition = False
    draw_condition = False
    current_sign = 1
    current_step = 0


def is_any_empty_subfields():
    return any([subfield.is_empty() for subfield in field])


@time_decorator
def update_images(new_colors=None, scale=1) -> None:
    """Updates (or creates if not created) game images by given parameters
    new_colors = (background_color, non_clickable_color, clickable_color, text_color, hovered_color, interface_color)
    all colors are RGBA"""

    game_folder = os.path.dirname(__file__)
    img_folder = os.path.join(game_folder, 'pentago_img')
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
    base_img_folder = os.path.join(game_folder, 'base_img')
    themeable_folder = os.path.join(base_img_folder, 'themeable')
    hoverable_folder = os.path.join(themeable_folder, 'hoverable')

    base_colors = ((255, 255, 255, 255), (170, 220, 175, 255), (93, 143, 98, 255),
                   (0, 0, 0, 255), (180, 180, 180, 255), (9, 56, 13, 255))
    hovered_colors = ((255, 255, 255, 255), (170, 220, 175, 255), (-1, -1, -1, -1),
                      (0, 0, 0, 255), (93, 143, 98, 255), (9, 56, 13, 255))
    if new_colors is None:
        new_colors = base_colors
    palet = dict(zip(base_colors, new_colors))
    hovered_palet = dict(zip(hovered_colors, new_colors))
    scale *= 5

    for filename in os.listdir(base_img_folder):
        if os.path.isfile(os.path.join(base_img_folder, filename)):
            with Image.open(os.path.join(base_img_folder, filename)).convert('RGBA') as base_img:
                new_img = Image.new('RGBA', tuple(i * scale for i in base_img.size))
                data = tuple(split_by_len(tuple(base_img.getdata()), base_img.width))
                new_data = tuple(scaled_data_gen(data, scale))
                new_img.putdata(new_data)
                new_img.save(os.path.join(img_folder, filename))

    for filename in os.listdir(themeable_folder):
        coef = 1
        if filename in ('x_won_text.png', 'o_won_text.png'):
            coef = 2
        if os.path.isfile(os.path.join(themeable_folder, filename)):
            with Image.open(os.path.join(themeable_folder, filename)).convert('RGBA') as base_img:
                new_img = Image.new('RGBA', tuple(i * scale * coef for i in base_img.size))
                data = tuple(split_by_len(tuple(base_img.getdata()), base_img.width))
                new_data = tuple(map(lambda x: palet.get(x, (255, 255, 255, 0)), scaled_data_gen(data, scale * coef)))
                new_img.putdata(new_data)
                new_img.save(os.path.join(img_folder, filename))

    for filename in os.listdir(hoverable_folder):
        if os.path.isfile(os.path.join(hoverable_folder, filename)):
            with Image.open(os.path.join(hoverable_folder, filename)).convert('RGBA') as base_img:
                new_img = Image.new('RGBA', tuple(i * scale for i in base_img.size))
                hovered_img = Image.new('RGBA', tuple(i * scale for i in base_img.size))
                data = tuple(split_by_len(tuple(base_img.getdata()), base_img.width))
                new_data = tuple(map(lambda x: palet.get(x, (255, 255, 255, 0)), scaled_data_gen(data, scale)))
                hovered_data = tuple(map(lambda x: hovered_palet.get(x, (255, 255, 255, 0)),
                                         scaled_data_gen(data, scale)))
                new_img.putdata(new_data)
                hovered_img.putdata(hovered_data)
                hovered_filename = filename.split('.')[0] + '_hovered' + '.png'
                new_img.save(os.path.join(img_folder, filename))
                hovered_img.save(os.path.join(img_folder, hovered_filename))


def update_screen_scale(old_scale: int, new_scale: int) -> None:
    """Updates screen and all sprites with current scale setting"""

    global CENTER, SUBFIELD_CORDS, ARROW_CORDS_OPERATIONS, SIGN_CORDS, all_sprites_list
    CENTER = (settings.width // 2, settings.width // 2 + 80 * settings.scale)
    CENTER_SUBFIELD_CENTER_DIST = int(settings.grid_width * 2.5 + settings.cell_width * 1.5)
    SUBFIELD_CORDS = ((CENTER[0] - CENTER_SUBFIELD_CENTER_DIST, CENTER[1] - CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] + CENTER_SUBFIELD_CENTER_DIST, CENTER[1] - CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] - CENTER_SUBFIELD_CENTER_DIST, CENTER[1] + CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] + CENTER_SUBFIELD_CENTER_DIST, CENTER[1] + CENTER_SUBFIELD_CENTER_DIST)
                      )
    ARROW_CORDS_OPERATIONS = ((lambda cords: (cords[0] - (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1]),
                               lambda cords: (cords[0], cords[1] - (CENTER_SUBFIELD_CENTER_DIST + 25))),
                              (lambda cords: (cords[0], cords[1] - (CENTER_SUBFIELD_CENTER_DIST + 25)),
                               lambda cords: (cords[0] + (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1])),
                              (lambda cords: (cords[0], cords[1] + (CENTER_SUBFIELD_CENTER_DIST + 25)),
                               lambda cords: (cords[0] - (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1])),
                              (lambda cords: (cords[0] + (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1]),
                               lambda cords: (cords[0], cords[1] + (CENTER_SUBFIELD_CENTER_DIST + 25)))
                              )

    SIGN_CORDS = (settings.grid_width, 2 * settings.grid_width + settings.cell_width,
                  3 * settings.grid_width + 2 * settings.cell_width)

    pygame.display.set_mode((settings.width, settings.height))

    all_sprites_list.extend(filter(lambda sprite: sprite not in all_sprites_list, all_sprites))
    all_sprites_list.sort(key=lambda x: type(x) != SubField)

    for sprite in all_sprites_list:
        sprite.update_scale(old_scale, new_scale)


def update_screen_theme():
    """Updates all sprites with current theme setting"""

    all_sprites_list.extend(filter(lambda sprite: sprite not in all_sprites_list, all_sprites))
    all_sprites_list.sort(key=lambda x: type(x) != SubField)

    for sprite in all_sprites_list:
        sprite.update_theme()


def create_path(filename: str) -> str:
    return os.path.join(img_folder, filename)


def add_hovered(filename: str) -> tuple[str, str]:
    return filename, f'{filename.split(".")[0]}_hovered.png'


if __name__ == '__main__':
    # setting up parameters
    try:
        with open('settings.pkl', 'rb') as file:
            settings = pickle.load(file)
    except FileNotFoundError:
        settings = Settings()

    FPS = 30
    CENTER = (settings.width // 2, settings.width // 2 + 80 * settings.scale)
    CENTER_SUBFIELD_CENTER_DIST = int(settings.grid_width * 2.5 + settings.cell_width * 1.5)
    SUBFIELD_CORDS = ((CENTER[0] - CENTER_SUBFIELD_CENTER_DIST, CENTER[1] - CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] + CENTER_SUBFIELD_CENTER_DIST, CENTER[1] - CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] - CENTER_SUBFIELD_CENTER_DIST, CENTER[1] + CENTER_SUBFIELD_CENTER_DIST),
                      (CENTER[0] + CENTER_SUBFIELD_CENTER_DIST, CENTER[1] + CENTER_SUBFIELD_CENTER_DIST)
                      )
    ARROW_CORDS_OPERATIONS = ((lambda cords: (cords[0] - (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1]),
                               lambda cords: (cords[0], cords[1] - (CENTER_SUBFIELD_CENTER_DIST + 25))),
                              (lambda cords: (cords[0], cords[1] - (CENTER_SUBFIELD_CENTER_DIST + 25)),
                               lambda cords: (cords[0] + (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1])),
                              (lambda cords: (cords[0], cords[1] + (CENTER_SUBFIELD_CENTER_DIST + 25)),
                               lambda cords: (cords[0] - (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1])),
                              (lambda cords: (cords[0] + (CENTER_SUBFIELD_CENTER_DIST + 25), cords[1]),
                               lambda cords: (cords[0], cords[1] + (CENTER_SUBFIELD_CENTER_DIST + 25)))
                              )

    SIGN_CORDS = (settings.grid_width, 2 * settings.grid_width + settings.cell_width,
                  3 * settings.grid_width + 2 * settings.cell_width)

    COLORS = {'white': (255, 255, 255), 'black': (0, 0, 0)}

    update_images(settings.get_color_palet(), settings.scale)

    # creating game and window
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((settings.width, settings.height))
    pygame.display.set_caption("")
    clock = pygame.time.Clock()

    # loading images
    game_folder = os.path.dirname(__file__)
    img_folder = os.path.join(game_folder, 'pentago_img')

    arrow_filenames = (('arrow_left_up_lefter.png', 'arrow_left_up_upper.png'),
                       ('arrow_right_up_upper.png', 'arrow_right_up_righter.png'),
                       ('arrow_left_down_downer.png', 'arrow_left_down_lefter.png'),
                       ('arrow_right_down_righter.png', 'arrow_right_down_downer.png'))
    arrow_files = tuple(tuple(tuple(create_path(i)
                                    for i in add_hovered(filename))
                              for filename in filenames)
                        for filenames in arrow_filenames)

    subfield_img = create_path('subfield.png')
    cross_img = create_path('cross.png')
    zero_img = create_path('zero.png')
    x_won_text_img = create_path('x_won_text.png')
    o_won_text_img = create_path('o_won_text.png')
    draw_text_img = create_path('draw_text.png')
    restart_text_img = create_path('restart_text.png')
    icon_img = create_path('icon.png')

    top_panel_img = create_path('top_panel.png')
    restart_button_imgs = (create_path('restart_button.png'),
                           create_path('restart_button_hovered.png'))
    settings_button_imgs = (create_path('settings_button.png'),
                            create_path('settings_button_hovered.png'))
    pentago_text_img = create_path('pentago_text.png')

    info_panel_img = create_path('rules.png')
    close_button_imgs = (create_path('close_button.png'),
                         create_path('close_button_hovered.png'))

    theme_button_frame_imgs = (create_path('theme_button_frame.png'),
                               create_path('theme_button_frame_hovered.png'),
                               create_path('theme_button_frame_clicked.png'))
    basic_theme_button_img = create_path('basic_theme_button.png')
    pink_theme_button_img = create_path('pink_theme_button.png')
    resolution_button_imgs = (create_path('resolution_button.png'),
                              create_path('resolution_button_hovered.png'),
                              create_path('resolution_button_clicked.png'))
    rules_button_imgs = (create_path('rules_button.png'),
                         create_path('rules_button_hovered.png'))
    screen_settings_text_img = create_path('screen_settings_text.png')
    settings_panel_img = create_path('settings_panel.png')

    # creating sprites
    cross_won_sprite = CordSpriteObject(x_won_text_img, (CENTER[0], CENTER[1] - 100))
    zero_won_sprite = CordSpriteObject(o_won_text_img, (CENTER[0], CENTER[1] - 100))
    draw_sprite = CordSpriteObject(draw_text_img, (CENTER[0], CENTER[1] - 100))
    restart_sprite = CordSpriteObject(restart_text_img, (CENTER[0], CENTER[1] + 100))
    icon_sprite = SpriteObject(icon_img)

    top_panel_sprite = CordSpriteObject(top_panel_img, (CENTER[0], CENTER[1] - CENTER[0] - 40))
    restart_button = Button(restart_button_imgs, (settings.width - 40, CENTER[1] - CENTER[0] - 40))
    settings_button = Button(settings_button_imgs, (55, CENTER[1] - CENTER[0] - 40))
    pentago_text = CordSpriteObject(pentago_text_img, (CENTER[0], CENTER[1] - CENTER[0] - 40))
    close_button = Button(close_button_imgs, (settings.width - 40, CENTER[1] - CENTER[0] - 40))
    info_panel = CordSpriteObject(info_panel_img, CENTER)

    settings_panel = CordSpriteObject(settings_panel_img,
                                      (160 * settings.scale, top_panel_sprite.rect.bottom + 152 * settings.scale))
    rules_button = Button(rules_button_imgs,
                          (settings_panel.rect.center[0], settings_panel.rect.top + 40 * settings.scale))
    screen_settings_text = CordSpriteObject(screen_settings_text_img, (settings_panel.rect.center[0],
                                                                       rules_button.rect.bottom + 100 * settings.scale))
    basic_theme_button = CordSpriteObject(basic_theme_button_img,
                                          (70 * settings.scale, screen_settings_text.rect.bottom + 30 * settings.scale))
    pink_theme_button = CordSpriteObject(pink_theme_button_img,
                                         (150 * settings.scale, screen_settings_text.rect.bottom + 30 * settings.scale))
    basic_theme_button_frame = ChoiceButton(theme_button_frame_imgs,
                                            (70 * settings.scale,
                                             screen_settings_text.rect.bottom + 30 * settings.scale),
                                            settings.theme == 'basic')
    pink_theme_button_frame = ChoiceButton(theme_button_frame_imgs,
                                           (150 * settings.scale,
                                            screen_settings_text.rect.bottom + 30 * settings.scale),
                                           settings.theme == 'pale pink')
    resolution_1x_button = ChoiceButton(resolution_button_imgs,
                                        (42 * settings.scale, 247 * settings.scale),
                                        settings.scale == 1)
    resolution_2x_button = ChoiceButton(resolution_button_imgs,
                                        (42 * settings.scale, 277 * settings.scale),
                                        settings.scale == 2)

    # setting up icon
    pygame.display.set_icon(icon_sprite.image)

    # creating groups
    settings_sprites = pygame.sprite.Group()
    info_sprites = pygame.sprite.Group()
    top_panel_sprites = pygame.sprite.Group()
    subfield_sprites = pygame.sprite.Group()
    arrow_sprites = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    all_sprites_list = []
    field = []
    arrows = []
    text_sprites = (cross_won_sprite, zero_won_sprite, draw_sprite, restart_sprite)

    # creating field
    top_panel_sprites.add(top_panel_sprite, restart_button, settings_button, pentago_text)
    info_sprites.add(info_panel, close_button)
    settings_sprites.add(settings_panel, rules_button, screen_settings_text, basic_theme_button, pink_theme_button,
                         resolution_1x_button, resolution_2x_button, basic_theme_button_frame, pink_theme_button_frame)
    count = 0
    for cords in SUBFIELD_CORDS:
        subfield = SubField(count, subfield_img)
        field.append(subfield)
        subfield_sprites.add(subfield)
        arrow1 = Arrow(ARROW_CORDS_OPERATIONS[count][0](cords),
                       arrow_files[count][0], subfield, False)
        arrow2 = Arrow(ARROW_CORDS_OPERATIONS[count][1](cords),
                       arrow_files[count][1], subfield, True)
        arrow_sprites.add(arrow1, arrow2)
        arrows.extend([arrow1, arrow2])
        count += 1

    all_sprites.add(subfield_sprites, arrow_sprites, top_panel_sprites)
    all_sprites_list.extend(subfield_sprites)
    all_sprites_list.extend(arrow_sprites)
    all_sprites_list.extend(top_panel_sprites)
    all_sprites_list.extend(info_sprites)
    all_sprites_list.extend(settings_sprites)

    restart()

    # Цикл игры
    running = True
    while running:
        # Держим цикл на правильной скорости
        clock.tick(FPS)
        # Ввод процесса (события)
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                with open('settings.pkl', 'wb') as file:
                    pickle.dump(settings, file)
                running = False

            if event.type == pygame.MOUSEBUTTONUP:
                cords = pygame.mouse.get_pos()

                if settings_opened or info_panel_opened:
                    if settings_opened:
                        if collide(cords, rules_button):
                            all_sprites.remove(restart_button)
                            all_sprites.remove(settings_sprites)
                            all_sprites.add(info_sprites)
                            settings_opened = False
                            info_panel_opened = True

                        elif collide(cords, settings_button):
                            all_sprites.remove(settings_sprites)
                            settings_opened = False

                        elif collide(cords, resolution_1x_button):
                            settings.update_scale(1)
                            resolution_1x_button.clicked = True
                            resolution_2x_button.clicked = False

                        elif collide(cords, resolution_2x_button):
                            settings.update_scale(2)
                            resolution_1x_button.clicked = False
                            resolution_2x_button.clicked = True

                        elif collide(cords, basic_theme_button_frame):
                            settings.update_theme('basic')
                            basic_theme_button_frame.clicked = True
                            pink_theme_button_frame.clicked = False

                        elif collide(cords, pink_theme_button_frame):
                            settings.update_theme('pale pink')
                            basic_theme_button_frame.clicked = False
                            pink_theme_button_frame.clicked = True

                    if info_panel_opened:
                        if collide(cords, close_button):
                            all_sprites.remove(info_sprites)
                            all_sprites.add(restart_button)
                            all_sprites.add(settings_sprites)
                            settings_opened = True
                            info_panel_opened = False

                else:
                    if collide(cords, settings_button):
                        all_sprites.add(settings_sprites)
                        settings_opened = True

                    if collide(cords, restart_button):
                        restart()

                    if game_active:
                        if current_step == -1:
                            for subfield in subfield_sprites:
                                if collide(cords, subfield):
                                    add_sign(subfield, cords)
                            for arrow in arrows:
                                if collide(cords, arrow):
                                    arrow.click()

                        if current_step == 0:
                            for subfield in subfield_sprites:
                                if collide(cords, subfield):
                                    add_sign(subfield, cords)

                        if current_step == 1:
                            for arrow in arrows:
                                if collide(cords, arrow):
                                    arrow.click()

                        win_draw_check()
                        if cross_win_condition:
                            cross_won_sprite.add(all_sprites)
                            restart_sprite.add(all_sprites)
                            game_active = False
                        if zero_win_condition:
                            zero_won_sprite.add(all_sprites)
                            restart_sprite.add(all_sprites)
                            game_active = False
                        if draw_condition:
                            draw_sprite.add(all_sprites)
                            restart_sprite.add(all_sprites)
                            game_active = False

            if event.type == pygame.KEYDOWN:

                # debug settings changing
                if pygame.key.get_pressed()[pygame.K_HOME]:
                    settings.back_to_default()
                    with open('settings.pkl', 'wb') as file:
                        pickle.dump(settings, file)
                    running = False

                if pygame.key.get_pressed()[pygame.K_2]:
                    settings.update_scale(2)

                if pygame.key.get_pressed()[pygame.K_1]:
                    settings.update_scale(1)

                if pygame.key.get_pressed()[pygame.K_p]:
                    settings.update_theme('pale pink')

                if pygame.key.get_pressed()[pygame.K_b]:
                    settings.update_theme('basic')

                # restart after finish
                if not (game_active or settings_opened or info_panel_opened):
                    if pygame.key.get_pressed()[pygame.K_SPACE]:
                        restart()

        # update
        all_sprites.update()

        # render
        screen.fill(settings.get_color('background_color'))
        all_sprites.draw(screen)

        # return to display
        pygame.display.flip()

    pygame.quit()
