import json
import pygame
import os
from PIL import Image
from typing import Callable, Iterable


class Field:
    def __init__(self, game):
        self.game = game
        self._active = False
        self._current_step = 0
        self.current_sign = 0
        self.cross_won = False
        self.zero_won = False
        self.draw = False
        self.center = self.game.settings.field_center()
        subfield_center_dist = self.game.settings.subfield_center_distance()
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
        self.sign_cords = (self.game.settings.grid_width,
                           2 * self.game.settings.grid_width + self.game.settings.cell_width,
                           3 * self.game.settings.grid_width + 2 * self.game.settings.cell_width)
        try:
            with open('score.json') as file:
                self.score_values = json.load(file)

        except FileNotFoundError:
            self.score_values = {'cross': 0, 'zero': 0, 'draw': 0}

        arrow_filenames = (('arrow_left_up_lefter.png', 'arrow_left_up_upper.png'),
                           ('arrow_right_up_upper.png', 'arrow_right_up_righter.png'),
                           ('arrow_left_down_downer.png', 'arrow_left_down_lefter.png'),
                           ('arrow_right_down_righter.png', 'arrow_right_down_downer.png'))
        self.arrow_files = tuple(tuple(self.game.create_img_path(self.game.add_hovered(filename))
                                       for filename in filenames)
                                 for filenames in arrow_filenames)

        self.cross_won_sprite = CordSpriteObject(self.game, self.game.create_img_path('x_won_text.png'),
                                                 (self.center[0], self.center[1] - 100))
        self.zero_won_sprite = CordSpriteObject(self.game, self.game.create_img_path('o_won_text.png'),
                                                (self.center[0], self.center[1] - 100))
        self.draw_sprite = CordSpriteObject(self.game, self.game.create_img_path('draw_text.png'),
                                            (self.center[0], self.center[1] - 100))
        self.restart_sprite = CordSpriteObject(self.game, self.game.create_img_path('restart_text.png'),
                                               (self.center[0], self.center[1] + 100))
        self.text_sprites = pygame.sprite.Group(self.cross_won_sprite, self.zero_won_sprite,
                                                self.draw_sprite, self.restart_sprite)
        self.field = [SubField(i, self) for i in range(4)]
        self.game.all_sprites.add(self.field)
        for subfield in self.field:
            for row in subfield:
                self.game.all_sprites.add(*row)
                self.game.all_sprites_list.extend(row)
            self.game.all_sprites.add(subfield.counterclockwise_arrow, subfield.clockwise_arrow)
            self.game.all_sprites_list.extend((subfield.counterclockwise_arrow, subfield.clockwise_arrow))
        self.game.all_sprites_list.extend(self.text_sprites)

    def save_score(self):
        with open('score.json', 'w') as file:
            json.dump(self.score_values, file)

    def reset_score(self):
        self.score_values = {'cross': 0, 'zero': 0, 'draw': 0}
        self.game.bottom_panel.update_score()

    def update_scale(self):
        self.center = self.game.settings.field_center()
        subfield_center_dist = self.game.settings.subfield_center_distance()
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
        self.sign_cords = (self.game.settings.grid_width,
                           2 * self.game.settings.grid_width + self.game.settings.cell_width,
                           3 * self.game.settings.grid_width + 2 * self.game.settings.cell_width)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active: bool):
        print(f'changing field.active from {self._active} to {active}')
        if active == self._active:
            return
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
    def current_step(self, current_step: int):
        if current_step not in (-1, 0, 1):
            raise ValueError(f'invalid current_step: {current_step}')
        self._current_step = current_step
        self.update()

    def unite(self):
        res = [None] * 6
        for i in range(3):
            res[i] = self.field[0][i] + self.field[1][i]
            res[3 + i] = self.field[2][i] + self.field[3][i]
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

    def set_subfields_active(self, active: bool) -> None:
        print(self.__dict__)
        for subfield in self.field:
            subfield.set_active(active)

    def set_arrows_active(self, active: bool) -> None:
        for subfield in self.field:
            subfield.set_arrows_active(active)

    def win_draw_check(self):
        type_field = list(map(lambda x: [type(i) for i in x], self.unite()))
        old = (self.cross_won, self.zero_won, self.draw)

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

        new = (self.cross_won, self.zero_won, self.draw)
        if old == new:
            return

        if self.cross_won or self.zero_won or self.draw:
            self.game.all_sprites.add(self.restart_sprite)
            self.game.win_sound.play()
            if self.cross_won:
                self.game.all_sprites.add(self.cross_won_sprite)
                self.score_values['cross'] += 1
            elif self.zero_won:
                self.game.all_sprites.add(self.zero_won_sprite)
                self.score_values['zero'] += 1
            else:
                self.game.all_sprites.add(self.draw_sprite)
                self.score_values['draw'] += 1
            self.game.bottom_panel.update_score()

    def restart(self):
        self.game.all_sprites.remove(self.text_sprites)
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
    def __init__(self, action: Callable = None, *args):
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
    def __init__(self, game, img: str):
        super().__init__()
        self.game = game
        self.img_path = img
        self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.img_path)

    def update_theme(self) -> None:
        self.image = pygame.image.load(self.img_path)


class CordSpriteObject(SpriteObject):
    def __init__(self, game, img: str, cords: (int, int)):
        super().__init__(game, img)
        self.rect.center = cords

    def set_pos(self, cords: (int, int)) -> None:
        self.rect.center = cords

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.img_path)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]


class Number(CordSpriteObject):
    def __init__(self, game, cords: (int, int), value: int = 0):
        if not 0 <= value <= 9:
            raise ValueError()
        self.value = value
        img = game.create_img_path(f'{self.value}.png')
        super().__init__(game, img, cords)

    def change_value(self, value: int):
        if not 0 <= value <= 9:
            raise ValueError()
        self.value = value
        img = self.game.create_img_path(f'{self.value}.png')
        self.img_path = img
        self.update_theme()


class Button(CordSpriteObject):
    def __init__(self, game, imgs: (str, str), cords: (int, int), action: Callable = None):
        super().__init__(game, imgs[0], cords)
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
            if self.image is not self.hovered_image:
                self.image = self.hovered_image
        else:
            if self.image is not self.basic_image:
                self.image = self.basic_image
        if event is not None and event.type == pygame.MOUSEBUTTONUP and self.active and collide(event.pos, self):
            self.game.click_sound.play()
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
    def __init__(self, game, imgs: (str, str, str), cords: (int, int), clicked: bool,
                 choice_group: Choice, click_args: Iterable):
        super().__init__(game, imgs[:2], cords)
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
        self.img_path = field.game.create_img_path('subfield.png')
        self.image = pygame.image.load(self.img_path)
        self.rect = self.image.get_rect()
        self.rect.center = field.subfield_cords[num]
        self.field_list = [[Cell(field.game, self, i, j) for i in range(3)] for j in range(3)]
        self.counterclockwise_arrow = Arrow(self.field.game,
                                            field.arrow_cords_from_subfield_cords[num][0](field.subfield_cords[num]),
                                            field.arrow_files[num][0], self, False)
        self.clockwise_arrow = Arrow(self.field.game,
                                     field.arrow_cords_from_subfield_cords[num][1](field.subfield_cords[num]),
                                     field.arrow_files[num][1], self, True)

    def add_sign(self, x: int, y: int) -> None:
        if type(self.field_list[y][x]) is not Cell:
            return

        self.field_list[y][x].kill()
        if self.field.current_sign == 1:
            self.field_list[y][x] = Cross(self.field.game, self, x, y)
            self.field.current_sign = 0
        else:
            self.field_list[y][x] = Zero(self.field.game, self, x, y)
            self.field.current_sign = 1
        self.field.game.all_sprites.add(self.field_list[y][x])
        if self.field.is_any_empty_subfields():
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
        self.field_list = [[Cell(self.field.game, self, i, j) for i in range(3)] for j in range(3)]
        for row in self.field_list:
            self.field.game.all_sprites.add(*row)

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
        return f'SubField {self.field.field.index(self)}'

    def __getitem__(self, key):
        return self.field_list[key]


class Arrow(Button):
    def __init__(self, game, cords: (int, int), imgs: (str, str), subfield: SubField, clockwise: bool):
        super().__init__(game, imgs, cords)
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

    def __str__(self) -> str:
        return f'({"clockwise" if self.clockwise else "counterclockwise"} Arrow of {str(self.subfield)})'


class Cell(pygame.sprite.Sprite):
    def __init__(self, game, subfield: SubField, x: int, y: int):
        super().__init__()
        self.game = game
        self.subfield = subfield
        self.active = False
        self.cords = (x, y)
        self.basic_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.basic_image.fill(self.game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.hovered_image.fill(self.game.settings.get_color('hovered_color'))
        self.image = self.basic_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + subfield.field.sign_cords[self.cords[0]],
                             self.subfield.rect.topleft[1] + subfield.field.sign_cords[self.cords[1]])
        self.game.all_sprites_list.append(self)

    def set_active(self, active: bool) -> None:
        self.active = active

    def get_cords(self) -> (int, int):
        return self.cords

    def change_pos(self, x: int, y: int):
        self.cords = (x, y)
        self.rect.topleft = (self.subfield.rect.topleft[0] + self.subfield.field.sign_cords[self.cords[0]],
                             self.subfield.rect.topleft[1] + self.subfield.field.sign_cords[self.cords[1]])

    def update(self, event=None):
        if self.active and collide(pygame.mouse.get_pos(), self):
            if self.image is not self.hovered_image:
                self.image = self.hovered_image
        else:
            if self.image is not self.basic_image:
                self.image = self.basic_image

        if event is not None and event.type == pygame.MOUSEBUTTONUP:
            if self.active and collide(event.pos, self):
                self.game.click_sound.play()
                self.subfield.add_sign(*self.cords)

    def update_scale(self, *args):
        self.basic_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.basic_image.fill(self.game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.hovered_image.fill(self.game.settings.get_color('hovered_color'))
        self.image = self.basic_image

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + self.subfield.field.sign_cords[self.cords[0]],
                             self.subfield.rect.topleft[1] + self.subfield.field.sign_cords[self.cords[1]])

    def update_theme(self):
        self.basic_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.basic_image.fill(self.game.settings.get_color('background_color'))
        self.hovered_image = pygame.Surface((self.game.settings.cell_width, self.game.settings.cell_width))
        self.hovered_image.fill(self.game.settings.get_color('hovered_color'))
        self.image = self.basic_image

    def __str__(self) -> str:
        return f'(Cell[{self.cords[1]}][{self.cords[0]}] of {str(self.subfield)})'


class Sign(Cell):
    def __init__(self, game, field: SubField, image: str, x: int, y: int):
        super().__init__(game, field, x, y)
        self.img_path = image
        self.image = pygame.image.load(self.img_path)

    def update(self, event=None):
        pass

    def update_scale(self, *args):
        self.image = pygame.image.load(self.img_path)

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.subfield.rect.topleft[0] + self.subfield.field.sign_cords[self.cords[0]],
                             self.subfield.rect.topleft[1] + self.subfield.field.sign_cords[self.cords[1]])

    def update_theme(self):
        self.image = pygame.image.load(self.img_path)


class Cross(Sign):
    def __init__(self, game, field: SubField, x: int, y: int):
        super().__init__(game, field, game.create_img_path('cross.png'), x, y)


class Zero(Sign):
    def __init__(self, game, field: SubField, x: int, y: int):
        super().__init__(game, field, game.create_img_path('zero.png'), x, y)


class Panel:
    def __init__(self, game):
        self.game = game
        self.sprite_group = pygame.sprite.Group()
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool):
        self._active = active
        if self.active:
            self.open()
        else:
            self.close()

    def add(self, *args):
        self.sprite_group.add(*args)

    def open(self):
        self.game.all_sprites.add(self.sprite_group)

    def close(self):
        self.game.all_sprites.remove(self.sprite_group)


class SettingsPanel(Panel):
    def __init__(self, game):
        super().__init__(game)
        settings_panel_sprite = CordSpriteObject(self.game, self.game.create_img_path('settings_panel.png'),
                                                 (32 * 5 * self.game.settings.scale,
                                                  self.game.top_panel.top_panel_sprite.rect.bottom +
                                                  43 * 5 * self.game.settings.scale))
        rules_button = Button(self.game, self.game.create_img_path(self.game.add_hovered('rules_button.png')),
                              (settings_panel_sprite.rect.center[0],
                               settings_panel_sprite.rect.top + 7.5 * 5 * self.game.settings.scale),
                              self.game.open_info_panel)
        screen_settings_text = CordSpriteObject(self.game, self.game.create_img_path('screen_settings_text.png'),
                                                (settings_panel_sprite.rect.center[0],
                                                 rules_button.rect.bottom + 19.5 * 5 * self.game.settings.scale))
        basic_theme_button = CordSpriteObject(self.game, self.game.create_img_path('basic_theme_button.png'),
                                              (70 * self.game.settings.scale,
                                               screen_settings_text.rect.bottom + 30 * self.game.settings.scale))
        pink_theme_button = CordSpriteObject(self.game, self.game.create_img_path('pink_theme_button.png'),
                                             (150 * self.game.settings.scale,
                                              screen_settings_text.rect.bottom + 30 * self.game.settings.scale))
        blue_theme_button = CordSpriteObject(self.game, self.game.create_img_path('blue_theme_button.png'),
                                             (47 * 5 * self.game.settings.scale,
                                              screen_settings_text.rect.bottom + 30 * self.game.settings.scale))
        game_settings_text = CordSpriteObject(self.game, self.game.create_img_path('game_text.png'),
                                              (settings_panel_sprite.rect.center[0],
                                               basic_theme_button.rect.bottom + 7.5 * 5 * self.game.settings.scale))
        reset_settings_button = Button(self.game,
                                       self.game.create_img_path(self.game.add_hovered('reset_settings_button.png')),
                                       (29 * 5 * self.game.settings.scale,
                                        game_settings_text.rect.bottom + 4.5 * 5 * self.game.settings.scale),
                                       self.reset_settings_button_click)
        reset_score_button = Button(self.game,
                                    self.game.create_img_path(self.game.add_hovered('reset_score_button.png')),
                                    (23.5 * 5 * self.game.settings.scale,
                                     reset_settings_button.rect.bottom + 4.5 * 5 * self.game.settings.scale),
                                    self.game.field.reset_score)

        self.theme_choice = Choice(self.game.settings.update_theme)
        self.basic_theme_button_frame = ChoiceButton(self.game,
                                                     self.game.create_img_path(
                                                         self.game.add_hovered_clicked('theme_button_frame.png')),
                                                     (70 * self.game.settings.scale,
                                                      screen_settings_text.rect.bottom + 30 * self.game.settings.scale),
                                                     self.game.settings.theme == 'basic',
                                                     self.theme_choice,
                                                     ('basic',))
        pink_theme_button_frame = ChoiceButton(self.game,
                                               self.game.create_img_path(
                                                   self.game.add_hovered_clicked('theme_button_frame.png')),
                                               (150 * self.game.settings.scale,
                                                screen_settings_text.rect.bottom + 30 * self.game.settings.scale),
                                               self.game.settings.theme == 'pale pink',
                                               self.theme_choice,
                                               ('pale pink',))
        blue_theme_button_frame = ChoiceButton(self.game,
                                               self.game.create_img_path(
                                                   self.game.add_hovered_clicked('theme_button_frame.png')),
                                               (47 * 5 * self.game.settings.scale,
                                                screen_settings_text.rect.bottom + 30 * self.game.settings.scale),
                                               self.game.settings.theme == 'blue',
                                               self.theme_choice,
                                               ('blue',))

        self.resolution_choice = Choice(self.game.settings.update_scale)
        self.resolution_1x_button = ChoiceButton(self.game,
                                                 self.game.create_img_path(
                                                     self.game.add_hovered_clicked('resolution_button.png')),
                                                 (42 * self.game.settings.scale,
                                                  screen_settings_text.rect.top + 19.5 * 5 * self.game.settings.scale),
                                                 self.game.settings.scale == 1,
                                                 self.resolution_choice,
                                                 (1,))
        resolution_2x_button = ChoiceButton(self.game,
                                            self.game.create_img_path(
                                                self.game.add_hovered_clicked('resolution_button.png')),
                                            (42 * self.game.settings.scale,
                                             screen_settings_text.rect.top + 25.5 * 5 * self.game.settings.scale),
                                            self.game.settings.scale == 2,
                                            self.resolution_choice,
                                            (2,))
        self.add(settings_panel_sprite, rules_button, screen_settings_text, basic_theme_button,
                 pink_theme_button, blue_theme_button, self.resolution_1x_button, resolution_2x_button,
                 self.basic_theme_button_frame, pink_theme_button_frame, blue_theme_button_frame,
                 game_settings_text, reset_settings_button, reset_score_button)
        self.game.all_sprites_list.extend(self.sprite_group)

    def reset_settings_button_click(self):
        self.theme_choice.on_click(self.basic_theme_button_frame, 'basic')
        self.resolution_choice.on_click(self.resolution_1x_button, 1)
        self.game.settings.back_to_default()


class InfoPanel(Panel):
    def __init__(self, game):
        super().__init__(game)
        info_panel_sprite = CordSpriteObject(self.game, self.game.create_img_path('rules.png'),
                                             self.game.field.center)
        close_button = Button(self.game, self.game.create_img_path(self.game.add_hovered('close_button.png')),
                              (self.game.settings.width - 8.5 * 5 * self.game.settings.scale,
                               7.5 * 5 * self.game.settings.scale),
                              self.game.open_field)
        self.add(info_panel_sprite, close_button)
        self.game.all_sprites_list.extend(self.sprite_group)

    def open_button_action(self):
        self.active = True

    def close_button_action(self):
        self.active = False

    def open(self):
        super().open()
        self.game.all_sprites.remove(self.game.top_panel.restart_button)

    def close(self):
        super().close()
        self.game.all_sprites.add(self.game.top_panel.restart_button)


class TopPanel(Panel):
    def __init__(self, game):
        super().__init__(game)
        self.top_panel_sprite = CordSpriteObject(self.game, self.game.create_img_path('top_panel.png'),
                                                 (self.game.field.center[0],
                                                  40 * self.game.settings.scale))
        self.restart_button = Button(self.game, self.game.create_img_path(self.game.add_hovered('restart_button.png')),
                                     (self.game.settings.width - 7.5 * 5 * self.game.settings.scale,
                                      7.5 * 5 * self.game.settings.scale),
                                     self.game.restart)
        settings_button = Button(self.game, self.game.create_img_path(self.game.add_hovered('settings_button.png')),
                                 (8.5 * 5 * game.settings.scale, 7.5 * 5 * self.game.settings.scale),
                                 self.game.settings_button_action)
        pentago_text = CordSpriteObject(self.game, self.game.create_img_path('pentago_text.png'),
                                        (self.game.field.center[0],
                                         7.5 * 5 * self.game.settings.scale))
        self.game.all_sprites.add(self.top_panel_sprite, pentago_text)
        self.add(self.restart_button, settings_button)
        self.game.all_sprites_list.extend(self.sprite_group)

    def settings_button_action(self):
        self.game.settings_panel.button_action()


class BottomPanel(Panel):
    def __init__(self, game):
        super().__init__(game)
        self.bottom_panel_sprite = CordSpriteObject(self.game, self.game.create_img_path('bottom_panel.png'),
                                                    (self.game.field.center[0], self.game.settings.height - 40))
        y_center = self.bottom_panel_sprite.rect.top + 42 * self.game.settings.scale
        cross_icon = CordSpriteObject(self.game, self.game.create_img_path('cross_icon.png'),
                                      (38 * self.game.settings.scale, y_center))
        zero_icon = CordSpriteObject(self.game, self.game.create_img_path('zero_icon.png'),
                                     ((52 * 5 - 2) * self.game.settings.scale, y_center))
        draw_icon = CordSpriteObject(self.game, self.game.create_img_path('draw_icon.png'),
                                     ((94 * 5 - 2) * self.game.settings.scale, y_center))
        score_values = self.game.field.score_values
        self.scores = {'cross': Score(self.game, (23 * 5 * self.game.settings.scale, y_center),
                                      score_values['cross']),
                       'zero': Score(self.game, (66 * 5 * self.game.settings.scale, y_center),
                                     score_values['zero']),
                       'draw': Score(self.game, (109 * 5 * self.game.settings.scale, y_center),
                                     score_values['draw'])}
        self.game.all_sprites.add(self.bottom_panel_sprite)
        self.add(cross_icon, zero_icon, draw_icon)
        for score in self.scores.values():
            self.add(score.nums)
        self.game.all_sprites_list.extend(self.sprite_group)

    def update_score(self):
        for i in ('cross', 'zero', 'draw'):
            if self.scores[i].value != self.game.field.score_values[i]:
                self.scores[i].change_value(self.game.field.score_values[i])


class StartPanel(Panel):
    def __init__(self, game):
        super().__init__(game)
        start_panel_sprite = CordSpriteObject(self.game, self.game.create_img_path('start.png'),
                                              self.game.field.center)
        self.add(start_panel_sprite)
        self.game.all_sprites_list.extend(self.sprite_group)
        self.active = True


class Score:
    def __init__(self, game, coords: (int, int), value: int = 0):
        super().__init__()
        self.game = game
        self.coords = coords
        if value < 0:
            value = 0
        if value > 99:
            value = 99
        self.value = value
        self.nums = [Number(self.game,
                            (self.coords[0] - 22.5 * self.game.settings.scale, self.coords[1]),
                            self.value // 10),
                     Number(self.game,
                            (self.coords[0] + 22.5 * self.game.settings.scale, self.coords[1]),
                            self.value % 10)]

    def change_value(self, value: int):
        if value < 0:
            value = 0
        if value > 99:
            value = 99
        self.value = value
        self.nums[0].change_value(self.value // 10)
        self.nums[1].change_value(self.value % 10)


class Settings:
    def __init__(self, game):
        self.game = game
        self.basic_settings = {'width': 600, 'height': 760, 'scale': 1, 'theme': 'basic',
                               'cell_width': 65, 'grid_width': 10}
        self.themes = {'basic': ((255, 255, 255, 255), (170, 220, 175, 255), (93, 143, 98, 255),
                                 (0, 0, 0, 255), (180, 180, 180, 255), (9, 56, 13, 255)),
                       'pale pink': ((254, 245, 239, 255), (220, 193, 196, 255), (157, 92, 99, 255),
                                     (88, 75, 83, 255), (202, 155, 114, 255), (75, 29, 34, 255)),
                       'blue': ((201, 231, 255, 255), (139, 191, 247, 255), (4, 135, 226, 255),
                                (16, 14, 63, 255), (157, 217, 242, 255), (4, 45, 131))}
        try:
            with open('settings.json', 'r') as file:
                saved_settings = json.load(file)
                self.width = saved_settings['width']
                self.height = saved_settings['height']
                self.scale = saved_settings['scale']
                self.theme = saved_settings['theme']
                self.cell_width = saved_settings['cell_width']
                self.grid_width = saved_settings['grid_width']

        except FileNotFoundError:
            self.width = self.basic_settings['width']
            self.height = self.basic_settings['height']
            self.scale = self.basic_settings['scale']
            self.theme = self.basic_settings['theme']
            self.cell_width = self.basic_settings['cell_width']
            self.grid_width = self.basic_settings['grid_width']

    def get_color(self, color_name: str) -> tuple[int, int, int, int]:
        colors = ('background_color', 'non_clickable_color',
                  'clickable_color', 'text_color', 'hovered_color', 'interface_color')
        return self.themes[self.theme][colors.index(color_name)]

    def get_color_palet(self, palet_name: str = None) -> ((int, int, int, int) * 6):
        if palet_name is None:
            return self.themes[self.theme]
        return self.themes[palet_name]

    def update_scale(self, new_scale: int) -> None:
        if new_scale == self.scale:
            return
        old_scale = self.scale
        self.scale = new_scale
        self.width = self.basic_settings['width'] * self.scale
        self.height = self.basic_settings['height'] * self.scale
        self.cell_width = self.basic_settings['cell_width'] * self.scale
        self.grid_width = self.basic_settings['grid_width'] * self.scale
        update_images(self.themes[self.theme], self.scale)
        self.game.update_screen_scale(old_scale, new_scale)

    def update_theme(self, new_theme: str) -> None:
        if new_theme == self.theme:
            return
        self.theme = new_theme
        update_images(self.themes[self.theme], self.scale)
        print(self.__dict__)
        self.game.update_screen_theme()

    def back_to_default(self) -> None:
        self.update_scale(1)
        self.update_theme('basic')

    def field_center(self) -> (int, int):
        return self.width // 2, self.width // 2 + 80 * self.scale

    def subfield_center_distance(self) -> int:
        return int(self.grid_width * 2.5 + self.cell_width * 1.5)

    def save(self) -> None:
        with open('settings.json', 'w') as file:
            settings = {'width': self.width, 'height': self.height, 'scale': self.scale,
                        'theme': self.theme, 'cell_width': self.cell_width, 'grid_width': self.grid_width}
            json.dump(settings, file)


class Pentago:
    def __init__(self):
        self.settings = Settings(self)

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
        self.sound_folder = os.path.join(self.folder, 'sound')

        # creating groups
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites_list = []

        self.field = Field(self)
        self.top_panel = TopPanel(self)
        self.settings_panel = SettingsPanel(self)
        self.info_panel = InfoPanel(self)
        self.bottom_panel = BottomPanel(self)
        self.start_panel = StartPanel(self)

        # sound effects
        self.hover_sound = pygame.mixer.Sound(os.path.join(self.sound_folder, 'hover.wav'))
        self.click_sound = pygame.mixer.Sound(os.path.join(self.sound_folder, 'click.wav'))
        self.open_panel_sound = pygame.mixer.Sound(os.path.join(self.sound_folder, 'open_panel.wav'))
        self.win_sound = pygame.mixer.Sound(os.path.join(self.sound_folder, 'win.wav'))

        # setting up icon
        icon_sprite = SpriteObject(self, self.create_img_path('icon.png'))
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
        self.start_panel.active = False
        self.info_panel.active = False
        self.settings_panel.active = False
        self.field.restart()

    def start(self):
        print(self.all_sprites)
        while True:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.settings.save()
                    self.field.save_score()
                    return 1

                if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP):
                    return 0

            # update
            self.all_sprites.update()

            # render
            self.screen.fill(self.settings.get_color('background_color'))
            self.all_sprites.draw(self.screen)

            # return to display
            pygame.display.flip()

    def run(self):
        start_response = self.start()
        if start_response == 1:
            return
        self.top_panel.active = True
        self.bottom_panel.active = True
        self.restart()

        running = True
        while running:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                # check for closing window
                if event.type == pygame.QUIT:
                    self.settings.save()
                    self.field.save_score()
                    running = False

                self.all_sprites.update(event)
                if event.type == pygame.KEYDOWN:

                    # debug settings changing
                    if pygame.key.get_pressed()[pygame.K_HOME]:
                        self.settings.back_to_default()
                        self.settings.save()
                        running = False

                    if pygame.key.get_pressed()[pygame.K_2]:
                        self.settings.update_scale(2)

                    if pygame.key.get_pressed()[pygame.K_1]:
                        self.settings.update_scale(1)

                    if pygame.key.get_pressed()[pygame.K_p]:
                        self.settings.update_theme('pale pink')

                    if pygame.key.get_pressed()[pygame.K_b]:
                        self.settings.update_theme('basic')

                    if pygame.key.get_pressed()[pygame.K_a]:
                        self.hover_sound.play()

                    # restart after finish
                    if any(self.field.get_conditions()):
                        if pygame.key.get_pressed()[pygame.K_SPACE]:
                            self.restart()

            # update
            self.all_sprites.update()

            # render
            self.screen.fill(self.settings.get_color('background_color'))
            self.all_sprites.draw(self.screen)

            # return to display
            pygame.display.flip()

    def update_screen_scale(self, old_scale: int, new_scale: int) -> None:
        """Updates screen and all sprites with current scale setting"""

        self.field.update_scale()
        pygame.display.set_mode((self.settings.width, self.settings.height))

        self.all_sprites_list.extend(filter(lambda sprite: sprite not in self.all_sprites_list, self.all_sprites))
        self.all_sprites_list.sort(key=lambda x: type(x) is not SubField)

        for sprite in self.all_sprites_list:
            sprite.update_scale(old_scale, new_scale)

    def update_screen_theme(self):
        """Updates all sprites with current theme setting"""

        self.all_sprites_list.extend(filter(lambda sprite: sprite not in self.all_sprites_list, self.all_sprites))
        self.all_sprites_list.sort(key=lambda x: type(x) is not SubField)

        for sprite in self.all_sprites_list:
            sprite.update_theme()

    def open_settings_panel(self):
        self.settings_panel.active = True
        self.info_panel.active = False
        self.field.active = False

    def open_info_panel(self):
        self.info_panel.active = True
        self.settings_panel.active = False
        self.field.active = False

    def open_field(self):
        self.field.active = True
        self.settings_panel.active = False
        self.info_panel.active = False

    def settings_button_action(self):
        if self.settings_panel.active:
            self.open_field()
        else:
            self.open_settings_panel()


def split_by_len(obj, num):
    for i in range(num, len(obj) + 1, num):
        yield obj[i - num:i]


def scaled_data_gen(data, scale):
    for row in data:
        new_row = []
        for pixel in row:
            for _ in range(scale):
                new_row.append(pixel)
        for _ in range(scale):
            yield from new_row


def collide(cords, obj):
    x, y = cords
    if obj.rect.left <= x <= obj.rect.right and obj.rect.top <= y <= obj.rect.bottom:
        return True
    return False


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


if __name__ == '__main__':
    pentago = Pentago()
    pentago.run()
    pygame.quit()
