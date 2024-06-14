from typing import Callable, Iterable

import pygame

from data import data


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
    def __init__(self, asset_name):
        super().__init__()
        self.asset = data.assets.get_asset(asset_name)
        self.image = pygame.image.load(self.asset.normal_path)
        self.rect = self.image.get_rect()

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.image = pygame.image.load(self.asset.normal_path)

    def update_theme(self) -> None:
        self.image = pygame.image.load(self.asset.normal_path)


class CordSpriteObject(SpriteObject):
    def __init__(self, asset_name, cords: (int, int)):
        super().__init__(asset_name)
        self.rect.center = cords

    def set_pos(self, cords: (int, int)) -> None:
        self.rect.center = cords

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        super().update_scale(old_scale, new_scale)
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def collide(self, cords: (int, int)) -> bool:
        x, y = cords
        if self.rect.left <= x <= self.rect.right and self.rect.top <= y <= self.rect.bottom:
            return True
        return False


class Number(CordSpriteObject):
    asset_names = [f'num_{i}' for i in range(10)]

    def __init__(self, cords: (int, int), value: int = 0):
        if not 0 <= value <= 9:
            raise ValueError()
        self.value = value
        super().__init__(self.asset_names[value], cords)

    def change_value(self, value: int):
        if not 0 <= value <= 9:
            raise ValueError()
        self.value = value
        self.asset = data.assets.get_asset(self.asset_names[value])
        self.update_theme()


class Button(CordSpriteObject):
    def __init__(self, asset_name, cords: (int, int), action: Callable = None):
        super().__init__(asset_name, cords)
        self.active = True
        self.basic_image = self.image
        self.hovered_image = pygame.image.load(self.asset.hovered_path)
        if action is None:
            self.action = lambda: None
        else:
            self.action = action

    def connect(self, action: Callable) -> None:
        self.action = action

    def set_active(self, active: bool) -> None:
        self.active = active

    def update(self, event: pygame.event.Event = None) -> None:
        if self.active and self.collide(pygame.mouse.get_pos()):
            if self.image is not self.hovered_image:
                self.image = self.hovered_image
        else:
            if self.image is not self.basic_image:
                self.image = self.basic_image
        if (
            event is not None
            and event.type == pygame.MOUSEBUTTONUP
            and self.active
            and self.collide(event.pos)
        ):
            # TODO
            # self.game.click_sound.play()
            self.action()

    def update_scale(self, old_scale: int, new_scale: int) -> None:
        self.load_images()
        old_topleft = self.rect.topleft
        self.rect = self.image.get_rect()
        self.rect.topleft = [i * (new_scale / old_scale) for i in old_topleft]

    def update_theme(self) -> None:
        self.load_images()

    def load_images(self) -> None:
        self.basic_image = pygame.image.load(self.asset.normal_path)
        self.hovered_image = pygame.image.load(self.asset.hovered_path)
        self.image = self.basic_image


class ChoiceButton(Button):
    def __init__(
        self,
        asset_name: str,
        cords: (int, int),
        clicked: bool,
        choice_group: Choice,
        click_args: Iterable,
    ):
        super().__init__(asset_name, cords)
        self.clicked_image = pygame.image.load(self.asset.clicked_path)
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

        if (
            event is not None
            and not self.clicked
            and event.type == pygame.MOUSEBUTTONUP
            and self.collide(event.pos)
        ):
            self.choice_group.on_click(self, *self.click_args)

    def load_images(self) -> None:
        super().load_images()
        self.clicked_image = pygame.image.load(self.asset.clicked_path)
        if self.clicked:
            self.image = self.clicked_image
        else:
            self.image = self.basic_image


class Cell(pygame.sprite.Sprite):
    def __init__(self, subfield, x: int, y: int):
        super().__init__()
        self.subfield = subfield
        self.active = False
        self.cords = (x, y)
        self.load_images()
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            self.subfield.rect.topleft[0] + subfield.field.sign_cords[self.cords[0]],
            self.subfield.rect.topleft[1] + subfield.field.sign_cords[self.cords[1]],
        )

    def set_active(self, active: bool) -> None:
        self.active = active

    def get_cords(self) -> (int, int):
        return self.cords

    def change_pos(self, x: int, y: int):
        self.cords = (x, y)
        self.rect.topleft = (
            self.subfield.rect.topleft[0]
            + self.subfield.field.sign_cords[self.cords[0]],
            self.subfield.rect.topleft[1]
            + self.subfield.field.sign_cords[self.cords[1]],
        )

    def update(self, event=None):
        super().update(event)
        if self.active and self.collide(pygame.mouse.get_pos()):
            if self.image is not self.hovered_image:
                self.image = self.hovered_image
        else:
            if self.image is not self.basic_image:
                self.image = self.basic_image

        if event is not None and event.type == pygame.MOUSEBUTTONUP:
            if self.active and self.collide(event.pos):
                # TODO
                # self.game.click_sound.play()
                self.subfield.add_sign(*self.cords)

    def update_scale(self, *args):
        self.load_images()
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            self.subfield.rect.topleft[0]
            + self.subfield.field.sign_cords[self.cords[0]],
            self.subfield.rect.topleft[1]
            + self.subfield.field.sign_cords[self.cords[1]],
        )

    def update_theme(self):
        self.load_images()

    def __str__(self) -> str:
        return f"(Cell[{self.cords[1]}][{self.cords[0]}] of {str(self.subfield)})"

    def load_images(self):
        self.basic_image = pygame.Surface(
            (data.settings.cell_width, data.settings.cell_width)
        )
        self.basic_image.fill(data.themes[data.settings.theme]["background_color"])
        self.hovered_image = pygame.Surface(
            (data.settings.cell_width, data.settings.cell_width)
        )
        self.hovered_image.fill(data.themes[data.settings.theme]["hovered_color"])
        self.image = self.basic_image

    def collide(self, cords: (int, int)) -> bool:
        x, y = cords
        if self.rect.left <= x <= self.rect.right and self.rect.top <= y <= self.rect.bottom:
            return True
        return False


class Sign(Cell):
    def __init__(self, asset_name, subfield, x: int, y: int):
        super().__init__(subfield, x, y)
        self.asset = data.assets.get_asset(asset_name)
        self.image = pygame.image.load(self.asset.normal_path)

    def update(self, event=None):
        pass

    def update_scale(self, *args):
        self.image = pygame.image.load(self.asset.normal_path)

        self.rect = self.image.get_rect()
        self.rect.topleft = (
            self.subfield.rect.topleft[0]
            + self.subfield.field.sign_cords[self.cords[0]],
            self.subfield.rect.topleft[1]
            + self.subfield.field.sign_cords[self.cords[1]],
        )

    def update_theme(self):
        self.image = pygame.image.load(self.asset.normal_path)


class Cross(Sign):
    def __init__(self, field, x: int, y: int):
        super().__init__("cross", field, x, y)


class Zero(Sign):
    def __init__(self, field, x: int, y: int):
        super().__init__("zero", field, x, y)


class Score:
    def __init__(self, cords: (int, int), value: int = 0):
        self.cords = cords
        if value < 0:
            value = 0
        if value > 99:
            value = 99
        self.value = value
        self.nums = [
            Number(
                (self.cords[0] - 22.5 * data.settings.scale, self.cords[1]),
                self.value // 10,
            ),
            Number(
                (self.cords[0] + 22.5 * data.settings.scale, self.cords[1]),
                self.value % 10,
            ),
        ]

    def change_value(self, value: int):
        if value < 0:
            value = 0
        if value > 99:
            value = 99
        self.value = value
        self.nums[0].change_value(self.value // 10)
        self.nums[1].change_value(self.value % 10)
