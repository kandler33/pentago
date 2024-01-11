import pygame
import os
from PIL import Image
import pickle
import time
from typing import Callable, Any, Iterable, Tuple


class Field:
    def __init__(self, parent):
        self.parent = parent
        self._active = False
        self._current_step = 0
        self.current_sign = 0
        self.cross_won = False
        self.zero_won = False
        self.draw = False
        self.center = self.parent.settings.field_center()
        subfield_center_dist = self.parent.settings.subfield_center_distance()
        self.subfield_cords = ((self.center[0] - subfield_center_dist, self.center[1] - subfield_center_dist),
                               (self.center[0] + subfield_center_dist, self.center[1] - subfield_center_dist),
                               (self.center[0] - subfield_center_dist, self.center[1] + subfield_center_dist),
                               (self.center[0] + subfield_center_dist, self.center[1] + subfield_center_dist)
                               )
        self.arrow_cords_from_subfield_cords = ((lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1]),
                                                 lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25))),
                                                (lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25)),
                                                 lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1])),
                                                (lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)),
                                                 lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1])),
                                                (lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1]),
                                                 lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)))
                                                )
        self.sign_cords = (self.parent.settings.grid_width, 2 * self.parent.settings.grid_width + self.parent.settings.cell_width,
                           3 * self.parent.settings.grid_width + 2 * self.parent.settings.cell_width)


    def sprites_init(self):
        arrow_filenames = (('arrow_left_up_lefter.png', 'arrow_left_up_upper.png'),
                           ('arrow_right_up_upper.png', 'arrow_right_up_righter.png'),
                           ('arrow_left_down_downer.png', 'arrow_left_down_lefter.png'),
                           ('arrow_right_down_righter.png', 'arrow_right_down_downer.png'))
        self.arrow_files = tuple(tuple(self.parent.create_img_path(self.parent.add_hovered(filename))
                                       for filename in filenames)
                                 for filenames in arrow_filenames)

        self.cross_won_sprite = CordSpriteObject(self.parent.create_img_path('x_won_text.png'),
                                                 (self.center[0], self.center[1] - 100))
        self.zero_won_sprite = CordSpriteObject(self.parent.create_img_path('o_won_text.png'),
                                                (self.center[0], self.center[1] - 100))
        self.draw_sprite = CordSpriteObject(self.parent.create_img_path,
                                            (self.center[0], self.center[1] - 100))
        self.restart_sprite = CordSpriteObject(self.parent.create_img_path('restart_text.png'),
                                               (self.center[0], self.center[1] + 100))
        self.text_sprites = pygame.sprite.Group(self.cross_won_sprite, self.zero_won_sprite,
                                                self.draw_sprite, self.restart_sprite)
        self.field = [SubField(i, self) for i in range(4)]
        self.parent.all_sprites.add(self.field)
        for subfield in self.field:
            for row in subfield:
                self.parent.all_sprites.add(*row)
                self.parent.all_sprites_list.extend(row)
            self.parent.all_sprites.add(subfield.counterclockwise_arrow, subfield.clockwise_arrow)
            self.parent.all_sprites_list.extend((subfield.counterclockwise_arrow, subfield.clockwise_arrow))

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active: bool):
        print(f'changing field.active from {self._active} to {active}')
        self._active = active
        if not self.active:
            self.set_subfields_active(False)
            self.set_arrows_active(False)
        else:
            self.update()

    @property
    def current_step(self):
        return self._current_step

    @current_step.setter
    def current_step(self, current_step):
        if current_step not in (-1, 0, 1):
            raise ValueError(f'invalid current_step: {current_step}')
        self._current_step = current_step
        self.update()

    def unite(self):
        res = [None] * 6
        for i in range(3):
            res[i] = self.field[0][i] + self.field[1][i]
            res[3+i] = self.field[2][i] + self.field[3][i]
        return res

    def is_any_empty_subfields(self):
        return any([subfield.is_empty() for subfield in self.field])

    def update(self):
        self.set_subfields_active(False)
        self.set_arrows_active(False)

        if self.current_step in (-1, 0):
            self.set_subfields_active(True)

        if self.current_step in (-1, 1):
            self.set_arrows_active(True)

        self.win_draw_check()

        if self.cross_won or self.zero_won or self.draw:
            self.active = False
            self.parent.all_sprites.add(self.restart_sprite)
            if self.cross_won:
                self.parent.all_sprites.add(self.cross_won_sprite)
            elif self.zero_won:
                self.parent.all_sprites.add(self.zero_won_sprite)
            else:
                self.parent.all_sprites.add(self.draw_sprite)

    def set_subfields_active(self, active: bool) -> None:
        for subfield in self.field:
            subfield.set_active(active)

    def set_arrows_active(self, active: bool) -> None:
        for subfield in self.field:
            subfield.set_arrows_active(active)

    def win_draw_check(self):
        type_field = list(map(lambda x: [type(i) for i in x], self.unite()))

        for i in range(6):
            # horizontal
            if [type_field[i][j] for j in range(5)].count(Cross) == 5 or [type_field[i][j] for j in range(1, 6)].count(
                    Cross) == 5:
                self.cross_won = True
            if ([type_field[i][j] for j in range(5)].count(Zero) == 5 or
                    [type_field[i][j] for j in range(1, 6)].count(Zero) == 5):
                self.zero_won = True

            # vertical
            if ([type_field[j][i] for j in range(5)].count(Cross) == 5 or
                    [type_field[j][i] for j in range(1, 6)].count(Cross) == 5):
                self.cross_won = True
            if ([type_field[j][i] for j in range(5)].count(Zero) == 5 or
                    [type_field[j][i] for j in range(1, 6)].count(Zero) == 5):
                self.zero_won = True

        # main diagonals
        if any(([type_field[i][i + 1] for i in range(5)].count(Cross) == 5,
                [type_field[i][i] for i in range(5)].count(Cross) == 5,
                [type_field[i][i] for i in range(1, 6)].count(Cross) == 5,
                [type_field[i + 1][i] for i in range(5)].count(Cross) == 5)):
            self.cross_won = True

        if any(([type_field[i][i + 1] for i in range(5)].count(Zero) == 5,
                [type_field[i][i] for i in range(5)].count(Zero) == 5,
                [type_field[i][i] for i in range(1, 6)].count(Zero) == 5,
                [type_field[i + 1][i] for i in range(5)].count(Zero) == 5)):
            self.zero_won = True

        # side diagonals
        if any(([type_field[5 - i][i + 1] for i in range(5)].count(Cross) == 5,
                [type_field[5 - i][i] for i in range(5)].count(Cross) == 5,
                [type_field[5 - i][i] for i in range(1, 6)].count(Cross) == 5,
                [type_field[4 - i][i] for i in range(5)].count(Cross) == 5)):
            self.zero_won = True

        if any(([type_field[5 - i][i + 1] for i in range(5)].count(Zero) == 5,
                [type_field[5 - i][i] for i in range(5)].count(Zero) == 5,
                [type_field[5 - i][i] for i in range(1, 6)].count(Zero) == 5,
                [type_field[4 - i][i] for i in range(5)].count(Zero) == 5)):
            self.zero_won = True

        # draw check
        if all([all([i != Cell for i in row]) for row in type_field]):
            self.draw = True

        if self.cross_won and self.zero_won:
            self.cross_won, self.zero_won = False, False
            self.draw = True

    def restart(self):
        self.parent.all_sprites.remove(self.text_sptites)
        for subfield in self.field:
            subfield.restart()
        self.cross_won = False
        self.zero_won = False
        self.draw = False
        self.current_sign = 1
        self.current_step = 0
        self.active = True
        self.update()

    def get_conditions(self):
        return self.cross_won, self.zero_won, self.draw


class Choice:
    def __init__(self, action=None, *args):
        self.buttons = list(args)
        if action is None:
            self.action = lambda *args: None
        else:
            self.action = action

    def add(self, *args):
        self.buttons.extend(args)

    def on_click(self, sender, *args):
        for button in self.buttons:
            button.clicked = button is sender
        self.action(*args)


class SpriteObject(pygame.sprite.Sprite):
    def __init__(self, img: str):
        super().__init__()
        self.img_path = img
        self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.img_path)

    def update_theme(self) -> None:
        self.image = pygame.image.load(self.img_path)


class CordSpriteObject(SpriteObject):
    def __init__(self, img: str, cords: (int, int)):
        super().__init__(img)
        self.rect.center = cords

    def set_pos(self, cords: (int, int)) -> None:
        self.rect.center = cords

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.img_path)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]


class Button(CordSpriteObject):
    def __init__(self, imgs: (str, str), cords: (int, int), action: Callable = None):
        super().__init__(imgs[0], cords)
        self.active = True
        self.imgs_path = imgs
        self.basic_image = pygame.image.load(imgs[0])
        self.hovered_image = pygame.image.load(imgs[1])
        self.image = self.basic_image
        if action is None:
            self.action = lambda: None
        else:
            self.action = action

    def connect(self, action: Callable) -> None:
        self.action = action

    def set_active(self, active: bool) -> None:
        self.active = active

    def update(self, event: pygame.event.Event = None) -> None:
        if self.active and collide(pygame.mouse.get_pos(), self):
            self.image = self.hovered_image
        else:
            self.image = self.basic_image
        if event is not None and event.type == pygame.MOUSEBUTTONUP and self.active and collide(event.pos, self):
            self.action()

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.image = self.basic_image
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self) -> None:
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.image = self.basic_image


class ChoiceButton(Button):
    def __init__(self, imgs: (str, str, str), cords: (int, int), clicked: bool,
                 choice_group: Choice, click_args: Iterable):
        super().__init__(imgs[:2], cords)
        self.imgs_path = imgs
        self.clicked_image = pygame.image.load(self.imgs_path[2])
        self.clicked = clicked
        self.choice_group = choice_group
        self.choice_group.add(self)
        self.click_args = click_args
        if self.clicked:
            self.image = self.clicked_image

    def update(self, event: pygame.event.Event = None) -> None:
        if self.clicked:
            self.image = self.clicked_image
        else:
            super().update()

        if event is not None and not self.clicked and event.type == pygame.MOUSEBUTTONUP and collide(event.pos, self):
            self.choice_group.on_click(self, *self.click_args)

    def update_scale(self, old_scale: int, new_scale: int) -> None:
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

    def update_theme(self) -> None:
        self.basic_image = pygame.image.load(self.imgs_path[0])
        self.hovered_image = pygame.image.load(self.imgs_path[1])
        self.clicked_image = pygame.image.load(self.imgs_path[2])
        if self.clicked:
            self.image = self.clicked_image
        else:
            self.image = self.basic_image


class SubField(pygame.sprite.Sprite):
    def __init__(self, num: int, field: Field):
        super().__init__()
        self.field = field
        self.active = False
        self.img_path = field.parent.create_img_path('subfield.png')
        self.image = pygame.image.load(self.img_path)
        self.rect = self.image.get_rect()
        self.rect.center = SUBFIELD_CORDS[num]
        self.field_list = [[Cell(self, i, j) for i in range(3)] for j in range(3)]
        self.counterclockwise_arrow = Arrow(field.arrow_cords_from_subfield_cords[num][0](field.subfield_cords[num]),
                                            field.arrow_files[num][0], self, False)
        self.clockwise_arrow = Arrow(field.arrow_cords_from_subfield_cords[num][1](field.subfield_cords[num]),
                                     field.arrow_files[num][1], self, True)

    def add_sign(self, x: int, y: int) -> None:
        if type(self.field_list[y][x]) is not Cell:
            return

        self.field_list[y][x].kill()
        if self.field.current_sign == 1:
            self.field_list[y][x] = Cross(self, x, y)
            self.field.current_sign = 0
        else:
            self.field_list[y][x] = Zero(self, x, y)
            self.field.current_sign = 1
        self.field.parent.all_sprites.add(self.field_list[y][x])
        if field.is_any_empty_subfields():
            self.field.current_step = -1
        else:
            self.field.current_step = 1

    def rotate_counterclockwise(self) -> None:
        new_field_list = [[None] * 3, [None] * 3, [None] * 3]
        for y in range(3):
            for x in range(3):
                new_field_list[y][x] = self.field_list[x][2 - y]
                new_field_list[y][x].change_pos(x, y)
        self.field_list = new_field_list

    def rotate_clockwise(self) -> None:
        new_field_list = [[None] * 3, [None] * 3, [None] * 3]
        for y in range(3):
            for x in range(3):
                new_field_list[y][x] = self.field_list[2 - x][y]
                new_field_list[y][x].change_pos(x, y)
        self.field_list = new_field_list

    def restart(self) -> None:
        for row in self.field_list:
            for cell in row:
                cell.kill()
        self.field_list = [[Cell(self, i, j) for i in range(3)] for j in range(3)]
        for row in self.field_list:
            field.parent.all_sprites.add(*row)

    def hovered(self) -> None:
        pass

    def is_empty(self) -> bool:
        return all([all([type(i) is Cell for i in row]) for row in self])

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.img_path)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self) -> None:
        self.image = pygame.image.load(self.img_path)

    def update(self, event: pygame.event.Event = None) -> None:
        pass

    def set_active(self, active: bool) -> None:
        print(f'changing {str(self)}.active from {self.active} to {active}')
        self.active = active
        for row in self.field_list:
            for cell in row:
                cell.set_active(active)

    def set_arrows_active(self, active: bool) -> None:
        self.counterclockwise_arrow.set_active(active)
        self.clockwise_arrow.set_active(active)

    def __str__(self) -> str:
        return f'SubField {field.field.index(self)}'

    def __getitem__(self, key):
        return self.field_list[key]


class Arrow(Button):
    def __init__(self, cords, imgs, subfield, clockwise):
        super().__init__(imgs, cords)
        self.subfield = subfield
        self.clockwise = clockwise
        if self.clockwise:
            self.action = self.clockwise_action
        else:
            self.action = self.counterclockwise_action

    def clockwise_action(self):
        self.subfield.rotate_clockwise()
        self.subfield.field.current_step = 0

    def counterclockwise_action(self):
        self.subfield.rotate_counterclockwise()
        self.subfield.field.current_step = 0

    def __str__(self):
        return f'({"clockwise" if self.clockwise else "counterclockwise"} Arrow of {str(self.subfield)})'


class Cell(pygame.sprite.Sprite):
    def __init__(self, subfield, x, y):
        super().__init__()
        self.subfield = subfield
        self.active = False
        self.cords = (x, y)
        self.basic_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.basic_image.fill(game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.hovered_image.fill(game.settings.get_color('hovered_color'))
        self.image = self.basic_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + game.field.sign_cords[self.cords[0]],
                             self.subfield.rect.topleft[1] + game.field.sign_cords[self.cords[1]])
        game.all_sprites_list.append(self)

    def set_active(self, active: bool) -> None:
        self.active = active

    def get_cords(self):
        return self.cords

    def change_pos(self, x, y):
        self.cords = (x, y)
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update(self, event=None):
        if self.active and collide(pygame.mouse.get_pos(), self):
            self.image = self.hovered_image
        else:
            self.image = self.basic_image

        if event is not None and event.type == pygame.MOUSEBUTTONUP:
            if self.active and collide(event.pos, self):
                self.subfield.add_sign(*self.cords)

    def update_scale(self, *args):
        self.basic_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.basic_image.fill(game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.hovered_image.fill(game.settings.get_color('hovered_color'))
        self.image = self.basic_image

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update_theme(self):
        self.basic_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.basic_image.fill(game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((game.settings.cell_width, game.settings.cell_width))
        self.hovered_image.fill(game.settings.get_color('hovered_color'))
        self.image = self.basic_image

    def __str__(self):
        return f'(Cell[{self.cords[1]}][{self.cords[0]}] of {str(self.subfield)})'


class Sign(Cell):
    def __init__(self, field, image, x, y):
        super().__init__(field, x, y)
        self.img_path = image
        self.image = pygame.image.load(self.img_path)

    def update(self, event=None):
        pass

    def update_scale(self, *args):
        self.image = pygame.image.load(self.img_path)

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + SIGN_CORDS[self.cords[0]],
                             self.subfield.rect.topleft[1] + SIGN_CORDS[self.cords[1]])

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)


class Cross(Sign):
    def __init__(self, field, x, y):
        super().__init__(field, game.create_img_path('cross.png'), x, y)


class Zero(Sign):
    def __init__(self, field, x, y):
        super().__init__(field, game.create_img_path('zero.png'), x, y)


class Panel:
    def __init__(self, parent):
        self.parent = parent
        self.sprite_group = pygame.sprite.Group()
        self._active = False

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        self._active = active
        if self.active:
            self.open()
        else:
            self.close()

    def add(self, *args):
        self.sprite_group.add(*args)

    def open(self):
        self.parent.all_sprites.add(self.sprite_group)

    def close(self):
        self.parent.all_sprites.remove(self.sprite_group)


class SettingsPanel(Panel):
    def __init__(self, parent):
        super().__init__(parent)
        settings_panel_sprite = CordSpriteObject(self.parent.create_img_path('settings_panel.png'),
                                                 (160 * self.parent.settings.scale,
                                                  self.parent.top_panel.top_panel_sprite.rect.bottom +
                                                  152 * self.parent.settings.scale))
        rules_button = Button(parent.create_img_path(self.parent.add_hovered('rules_button.png')),
                              (settings_panel_sprite.rect.center[0],
                               settings_panel_sprite.rect.top + 40 * self.parent.settings.scale),
                               self.rules_button_action)
        screen_settings_text = CordSpriteObject(parent.create_img_path('screen_settings_text.png'),
                                                (settings_panel_sprite.rect.center[0],
                                                 rules_button.rect.bottom + 100 * self.parent.settings.scale))
        basic_theme_button = CordSpriteObject(self.parent.create_img_path('basic_theme_button.png'),
                                              (70 * self.parent.settings.scale,
                                               screen_settings_text.rect.bottom + 30 * self.parent.settings.scale))
        pink_theme_button = CordSpriteObject(self.parent.create_img_path('pink_theme_button.png'),
                                             (150 * self.parent.settings.scale,
                                              screen_settings_text.rect.bottom + 30 * self.parent.settings.scale))

        theme_choice = Choice(self.parent.settings.update_theme)
        basic_theme_button_frame = ChoiceButton(
            parent.create_img_path(parent.add_hovered_clicked('theme_button_frame.png')),
            (70 * game.settings.scale, screen_settings_text.rect.bottom + 30 * game.settings.scale),
            game.settings.theme == 'basic',
            theme_choice,
            ('basic',))
        pink_theme_button_frame = ChoiceButton(parent.create_img_path(parent.add_hovered_clicked('theme_button_frame.png')),
                                               (150 * game.settings.scale,
                                                screen_settings_text.rect.bottom + 30 * game.settings.scale),
                                               game.settings.theme == 'pale pink',
                                               theme_choice,
                                               ('pale pink',))
        resolution_choice = Choice(game.settings.update_scale)
        resolution_1x_button = ChoiceButton(parent.create_img_path(parent.add_hovered_clicked('resolution_button.png')),
                                            (42 * game.settings.scale, 247 * game.settings.scale),
                                            game.settings.scale == 1,
                                            resolution_choice,
                                            (1,))
        resolution_2x_button = ChoiceButton(parent.create_img_path(parent.add_hovered_clicked('resolution_button.png')),
                                            (42 * game.settings.scale, 277 * game.settings.scale),
                                            game.settings.scale == 2,
                                            resolution_choice,
                                            (2,))
        self.add(settings_panel_sprite, rules_button, screen_settings_text, basic_theme_button,
                 pink_theme_button, resolution_1x_button, resolution_2x_button,
                 basic_theme_button_frame, pink_theme_button_frame)
        self.parent.all_sprites_list.extend(self.sprite_group)

    def rules_button_action(self):
        self.parent.info_panel.open_button_action()

    def button_action(self):
        self.active = not self.active

    def open(self):
        super().open()
        game.info_panel.active = False
        field.active = False

    def close(self):
        super().close()
        field.active = True


class InfoPanel(Panel):
    def __init__(self, parent):
        super().__init__(parent)
        info_panel_sprite = CordSpriteObject(game.create_img_path('rules.png'),
                                             game.field.center)
        close_button = Button(game.create_img_path(game.add_hovered('close_button.png')),
                              (game.settings.width - 40, game.field.center[1] - game.field.center[0] - 40),
                              self.close_button_action)
        self.add(info_panel_sprite, close_button)
        self.parent.all_sprites_list.extend(self.sprite_group)


    def open_button_action(self):
        self.active = True

    def close_button_action(self):
        self.active = False

    def open(self):
        super().open()
        game.all_sprites.remove(game.top_panel.restart_button)
        game.settings_panel.active = False
        field.active = False

    def close(self):
        super().close()
        game.all_sprites.add(game.top_panel.restart_button)
        field.active = True


class TopPanel(Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.top_panel_sprite = CordSpriteObject(self.parent.create_img_path('top_panel.png'),
                                            (self.parent.field.center[0],
                                             self.parent.field.center[1] - self.parent.field.center[0] - 40))
        restart_button = Button(self.parent.create_img_path(self.parent.add_hovered('restart_button.png')),
                                (self.parent.settings.width - 40,
                                 self.parent.field.center[1] - self.parent.field.center[0] - 40),
                                self.parent.restart)
        settings_button = Button(self.parent.create_img_path(self.parent.add_hovered('settings_button.png')),
                                 (55, self.parent.field.center[1] - self.parent.field.center[0] - 40),
                                 self.settings_button_action)
        pentago_text = CordSpriteObject(self.parent.create_img_path('pentago_text.png'),
                                        (self.parent.field.center[0],
                                         self.parent.field.center[1] - self.parent.field.center[0] - 40))
        self.add(self.top_panel_sprite, restart_button, settings_button, pentago_text)
        self.active = True
        self.parent.all_sprites_list.extend(self.sprite_group)

    def settings_button_action(self):
        self.parent.settings_panel.button_action()


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

    def field_center(self):
        return self.width // 2, self.width // 2 + 80 * self.scale

    def subfield_center_distance(self):
        return int(self.grid_width * 2.5 + self.cell_width * 1.5)


class Pentago:
    def __init__(self):
        try:
            with open('settings.pkl', 'rb') as file:
                self.settings = pickle.load(file)
        except FileNotFoundError:
            self.settings = Settings()

        update_images(self.settings.get_color_palet(), self.settings.scale)

        # creating game and window
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.settings.width, self.settings.height))
        pygame.display.set_caption("")
        self.clock = pygame.time.Clock()

        # loading images
        self.folder = os.path.dirname(__file__)
        self.img_folder = os.path.join(self.folder, 'pentago_img')

        # creating groups
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites_list = []

        self.field = Field(self)
        self.top_panel = TopPanel(self)
        self.settings_panel = SettingsPanel(self)
        self.info_panel = InfoPanel(self)

        # setting up icon
        icon_sprite = SpriteObject(self.create_img_path('icon.png'))
        pygame.display.set_icon(icon_sprite.image)

        self.FPS = 30

    def create_img_path(self, filenames: str | Iterable[str]) -> str | tuple[str, ...]:
        if type(filenames) is str:
            return os.path.join(self.img_folder, filenames)
        return tuple(os.path.join(self.img_folder, filename) for filename in filenames)

    @staticmethod
    def add_hovered(filename: str) -> tuple[str, str]:
        return filename, f'{filename.split(".")[0]}_hovered.png'

    @staticmethod
    def add_hovered_clicked(filename: str) -> tuple[str, str, str]:
        return filename, f'{filename.split(".")[0]}_hovered.png', f'{filename.split(".")[0]}_clicked.png'

    def restart(self):
        self.info_panel.active = False
        self.settings_panel.active = False
        field.restart()

    def run(self):
        self.restart()

        running = True
        while running:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                # check for closing window
                if event.type == pygame.QUIT:
                    with open('settings.pkl', 'wb') as file:
                        pickle.dump(self.settings, file)
                    running = False

                self.all_sprites.update(event)
                if event.type == pygame.KEYDOWN:

                    # debug settings changing
                    if pygame.key.get_pressed()[pygame.K_HOME]:
                        self.settings.back_to_default()
                        with open('settings.pkl', 'wb') as file:
                            pickle.dump(self.settings, file)
                        running = False

                    if pygame.key.get_pressed()[pygame.K_2]:
                        self.settings.update_scale(2)

                    if pygame.key.get_pressed()[pygame.K_1]:
                        self.settings.update_scale(1)

                    if pygame.key.get_pressed()[pygame.K_p]:
                        self.settings.update_theme('pale pink')

                    if pygame.key.get_pressed()[pygame.K_b]:
                        self.settings.update_theme('basic')

                    # restart after finish
                    if any(self.field.get_conditions()):
                        if pygame.key.get_pressed()[pygame.K_SPACE]:
                            restart()

            # update
            self.all_sprites.update()

            # render
            self.screen.fill(self.settings.get_color('background_color'))
            self.all_sprites.draw(self.screen)

            # return to display
            pygame.display.flip()


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


def restart():
    global field, text_sprites
    global info_panel_opened, settings_opened
    for sprite in text_sprites:
        sprite.kill()

    info_panel_opened = False
    settings_opened = False
    field.restart()


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
                new_img = Image.new('RGBA', (base_img.width * scale, base_img.height * scale))
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
                new_img = Image.new('RGBA', (base_img.width * scale * coef, base_img.height * scale * coef))
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
    CENTER = (game.settings.width // 2, game.settings.width // 2 + 80 * game.settings.scale)
    CENTER_SUBFIELD_CENTER_DIST = int(game.settings.grid_width * 2.5 + game.settings.cell_width * 1.5)
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

    SIGN_CORDS = (game.settings.grid_width, 2 * game.settings.grid_width + game.settings.cell_width,
                  3 * game.settings.grid_width + 2 * game.settings.cell_width)

    pygame.display.set_mode((game.settings.width, game.settings.height))

    all_sprites_list.extend(filter(lambda sprite: sprite not in all_sprites_list, game.all_sprites))
    all_sprites_list.sort(key=lambda x: type(x) is not SubField)

    for sprite in all_sprites_list:
        sprite.update_scale(old_scale, new_scale)


def update_screen_theme():
    """Updates all sprites with current theme setting"""

    all_sprites_list.extend(filter(lambda sprite: sprite not in all_sprites_list, game.all_sprites))
    all_sprites_list.sort(key=lambda x: type(x) is not SubField)

    for sprite in all_sprites_list:
        sprite.update_theme()


if __name__ == '__main__':
    game = Pentago()
    game.run()
    pygame.quit()
