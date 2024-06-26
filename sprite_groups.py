import datetime
import json
import time
import typing

import pygame

from sprites import *
from data import data


class Panel:
    def __init__(self, sprite_groups):
        self.sprite_groups = sprite_groups
        self.sprite_groups_by_activity = {
            False: pygame.sprite.Group(),
            True: pygame.sprite.Group(),
        }
        self._active = False
        self.sprite_group = self.sprite_groups_by_activity[self.active]

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        print(self.__class__.__name__, active)
        if active == self.active:
            return
        self._active = active
        self.sprite_groups.remove(self.sprite_group)
        self.sprite_group = self.sprite_groups_by_activity[self.active]

    def add_sprite(self, *args, active_state: bool = None):
        for sprite in args:
            if active_state in (True, None):
                self.sprite_groups_by_activity[True].add(sprite)

            if active_state in (False, None):
                self.sprite_groups_by_activity[False].add(sprite)

    @property
    def sprites(self):
        sprites = self.sprite_groups_by_activity[True].copy()
        sprites.add(self.sprite_groups_by_activity[False])
        return sprites


class Field:
    def __init__(self, sprite_groups):
        self.sprite_groups = sprite_groups
        self.sprite_group = pygame.sprite.Group()
        self._active = False
        self._current_step = 0
        self.current_sign = 0
        self.cross_won = False
        self.zero_won = False
        self.draw = False
        self.center = data.settings.field_center
        subfield_center_dist = data.settings.subfield_center_distance
        self.subfield_cords = (
            (
                self.center[0] - subfield_center_dist,
                self.center[1] - subfield_center_dist,
            ),
            (
                self.center[0] + subfield_center_dist,
                self.center[1] - subfield_center_dist,
            ),
            (
                self.center[0] - subfield_center_dist,
                self.center[1] + subfield_center_dist,
            ),
            (
                self.center[0] + subfield_center_dist,
                self.center[1] + subfield_center_dist,
            ),
        )
        self.arrow_cords_from_subfield_cords = (
            (
                lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1]),
                lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25)),
            ),
            (
                lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25)),
                lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1]),
            ),
            (
                lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)),
                lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1]),
            ),
            (
                lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1]),
                lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)),
            ),
        )
        self.sign_cords = (
            data.settings.grid_width,
            2 * data.settings.grid_width + data.settings.cell_width,
            3 * data.settings.grid_width + 2 * data.settings.cell_width,
        )

        self.arrow_asset_names = (
            ("arrow_left_up_lefter", "arrow_left_up_upper"),
            ("arrow_right_up_upper", "arrow_right_up_righter"),
            ("arrow_left_down_downer", "arrow_left_down_lefter"),
            ("arrow_right_down_righter", "arrow_right_down_downer"),
        )

        self.cross_won_sprite = CordSpriteObject(
            "x_won_text",
            (self.center[0], self.center[1] - 100),
        )
        self.zero_won_sprite = CordSpriteObject(
            "o_won_text",
            (self.center[0], self.center[1] - 100),
        )
        self.draw_sprite = CordSpriteObject(
            "draw_text",
            (self.center[0], self.center[1] - 100),
        )
        self.restart_sprite = CordSpriteObject(
            "restart_text",
            (self.center[0], self.center[1] + 100),
        )
        self.text_sprites = pygame.sprite.Group(
            self.cross_won_sprite,
            self.zero_won_sprite,
            self.draw_sprite,
            self.restart_sprite,
        )
        self.field = [SubField(i, self) for i in range(4)]

    @property
    def sprites(self):
        sprites = self.sprite_group.copy()
        sprites.add(self.text_sprites)
        return sprites

    def save_score(self):
        with open("score.json", "w") as file:
            json.dump(self.score_values, file)

    def update_scale(self):
        self.center = data.settings.field_center
        subfield_center_dist = data.settings.subfield_center_distance
        self.subfield_cords = (
            (
                self.center[0] - subfield_center_dist,
                self.center[1] - subfield_center_dist,
            ),
            (
                self.center[0] + subfield_center_dist,
                self.center[1] - subfield_center_dist,
            ),
            (
                self.center[0] - subfield_center_dist,
                self.center[1] + subfield_center_dist,
            ),
            (
                self.center[0] + subfield_center_dist,
                self.center[1] + subfield_center_dist,
            ),
        )
        self.arrow_cords_from_subfield_cords = (
            (
                lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1]),
                lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25)),
            ),
            (
                lambda cords: (cords[0], cords[1] - (subfield_center_dist + 25)),
                lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1]),
            ),
            (
                lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)),
                lambda cords: (cords[0] - (subfield_center_dist + 25), cords[1]),
            ),
            (
                lambda cords: (cords[0] + (subfield_center_dist + 25), cords[1]),
                lambda cords: (cords[0], cords[1] + (subfield_center_dist + 25)),
            ),
        )
        self.sign_cords = (
            data.settings.grid_width,
            2 * data.settings.grid_width + data.settings.cell_width,
            3 * data.settings.grid_width + 2 * data.settings.cell_width,
        )

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active: bool):
        print(f"\nchanging field.active from {self._active} to {active}\n")
        if active == self.active:
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
            raise ValueError(f"invalid current_step: {current_step}")
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
        if any(self.get_conditions()):
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
        old = self.get_conditions()

        for i in range(6):
            # horizontal
            if [type_field[i][j] for j in range(5)].count(Cross) == 5 or [
                type_field[i][j] for j in range(1, 6)
            ].count(Cross) == 5:
                self.cross_won = True
            if [type_field[i][j] for j in range(5)].count(Zero) == 5 or [
                type_field[i][j] for j in range(1, 6)
            ].count(Zero) == 5:
                self.zero_won = True

            # vertical
            if [type_field[j][i] for j in range(5)].count(Cross) == 5 or [
                type_field[j][i] for j in range(1, 6)
            ].count(Cross) == 5:
                self.cross_won = True
            if [type_field[j][i] for j in range(5)].count(Zero) == 5 or [
                type_field[j][i] for j in range(1, 6)
            ].count(Zero) == 5:
                self.zero_won = True

        # main diagonals
        if any(
                (
                        [type_field[i][i + 1] for i in range(5)].count(Cross) == 5,
                        [type_field[i][i] for i in range(5)].count(Cross) == 5,
                        [type_field[i][i] for i in range(1, 6)].count(Cross) == 5,
                        [type_field[i + 1][i] for i in range(5)].count(Cross) == 5,
                )
        ):
            self.cross_won = True

        if any(
                (
                        [type_field[i][i + 1] for i in range(5)].count(Zero) == 5,
                        [type_field[i][i] for i in range(5)].count(Zero) == 5,
                        [type_field[i][i] for i in range(1, 6)].count(Zero) == 5,
                        [type_field[i + 1][i] for i in range(5)].count(Zero) == 5,
                )
        ):
            self.zero_won = True

        # side diagonals
        if any(
                (
                        [type_field[5 - i][i + 1] for i in range(5)].count(Cross) == 5,
                        [type_field[5 - i][i] for i in range(5)].count(Cross) == 5,
                        [type_field[5 - i][i] for i in range(1, 6)].count(Cross) == 5,
                        [type_field[4 - i][i] for i in range(5)].count(Cross) == 5,
                )
        ):
            self.zero_won = True

        if any(
                (
                        [type_field[5 - i][i + 1] for i in range(5)].count(Zero) == 5,
                        [type_field[5 - i][i] for i in range(5)].count(Zero) == 5,
                        [type_field[5 - i][i] for i in range(1, 6)].count(Zero) == 5,
                        [type_field[4 - i][i] for i in range(5)].count(Zero) == 5,
                )
        ):
            self.zero_won = True

        # draw check
        if all(all(i is not Cell for i in row) for row in type_field):
            self.draw = True

        if self.cross_won and self.zero_won:
            self.cross_won, self.zero_won = False, False
            self.draw = True

        new = self.get_conditions()
        if old == new:
            return

        if any(self.get_conditions()):
            self.sprite_group.add(self.restart_sprite)
            # TODO
            # self.game.win_sound.play()
            if self.cross_won:
                self.sprite_group.add(self.cross_won_sprite)
                data.score["cross"] += 1
            elif self.zero_won:
                self.sprite_group.add(self.zero_won_sprite)
                data.score["zero"] += 1
            else:
                self.sprite_group.add(self.draw_sprite)
                data.score["draw"] += 1

    def restart(self):
        self.sprite_group.remove(self.text_sprites)
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


class SubField:
    def __init__(self, num: int, field: Field):
        super().__init__()
        self.field = field
        self.active = False
        self.cords = field.subfield_cords[num]
        self.subfield_sprite = CordSpriteObject("subfield", self.cords)
        self.rect = self.subfield_sprite.rect
        self.field_list = [
            [Cell(self, i, j) for i in range(3)] for j in range(3)
        ]
        self.counterclockwise_arrow = Button(
            field.arrow_asset_names[num][0],
            field.arrow_cords_from_subfield_cords[num][0](self.cords),
            self.rotate_counterclockwise,
        )
        self.clockwise_arrow = Button(
            self.field.arrow_asset_names[num][1],
            field.arrow_cords_from_subfield_cords[num][1](self.cords),
            self.rotate_clockwise,
        )
        self.set_arrows_active(False)
        self.field.sprite_group.add(
            self.subfield_sprite,
            self.clockwise_arrow,
            self.counterclockwise_arrow
        )
        self.field.sprite_group.add(*self.field_list)

    def add_sign(self, x: int, y: int) -> None:
        if not isinstance(self.field_list[y][x], Cell):
            return

        self.field_list[y][x].kill()
        if self.field.current_sign == 1:
            self.field_list[y][x] = Cross(self, x, y)
            self.field.current_sign = 0
        else:
            self.field_list[y][x] = Zero(self, x, y)
            self.field.current_sign = 1
        self.field.sprite_group.add(self.field_list[y][x])

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
        self.field.current_step = 0

    def rotate_clockwise(self) -> None:
        new_field_list = [[None] * 3, [None] * 3, [None] * 3]
        for y in range(3):
            for x in range(3):
                new_field_list[y][x] = self.field_list[2 - x][y]
                new_field_list[y][x].change_pos(x, y)

        self.field_list = new_field_list
        self.field.current_step = 0

    def restart(self) -> None:
        for row in self.field_list:
            for cell in row:
                cell.kill()
        self.field_list = [
            [Cell(self, i, j) for i in range(3)] for j in range(3)
        ]
        self.field.sprite_group.add(*self.field_list)

    def hovered(self) -> None:
        pass

    def is_empty(self) -> bool:
        return all([all([type(i) is Cell for i in row]) for row in self])

    def set_active(self, active: bool) -> None:
        print(f"changing {str(self)}.active from {self.active} to {active}")
        self.active = active
        for row in self.field_list:
            for cell in row:
                cell.set_active(active)

    def set_arrows_active(self, active: bool) -> None:
        self.counterclockwise_arrow.set_active(active)
        self.clockwise_arrow.set_active(active)

    def __str__(self) -> str:
        return f"SubField {self.field.field.index(self)}"

    def __getitem__(self, key):
        return self.field_list[key]


class SettingsPanel(Panel):
    def __init__(
            self,
            sprite_groups,
            rules_button_action: typing.Callable,
            reset_score_button_action: typing.Callable,
            update_theme_action: typing.Callable,
            update_scale_action: typing.Callable,
            reset_settings_action: typing.Callable
    ):
        super().__init__(sprite_groups)
        settings_panel_sprite = CordSpriteObject(
            "settings_panel",
            (
                32 * 5 * data.settings.scale,
                self.sprite_groups.top_panel.top_panel_sprite.rect.bottom
                + 43 * 5 * data.settings.scale,
            ),
        )
        rules_button = Button(
            "rules_button",
            (
                settings_panel_sprite.rect.center[0],
                settings_panel_sprite.rect.top + 7.5 * 5 * data.settings.scale,
            ),
            rules_button_action,
        )
        screen_settings_text = CordSpriteObject(
            "screen_settings_text",
            (
                settings_panel_sprite.rect.center[0],
                rules_button.rect.bottom + 19.5 * 5 * data.settings.scale,
            ),
        )
        basic_theme_button = CordSpriteObject(
            "basic_theme_button",
            (
                70 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
        )
        pink_theme_button = CordSpriteObject(
            "pink_theme_button",
            (
                150 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
        )
        blue_theme_button = CordSpriteObject(
            "blue_theme_button",
            (
                47 * 5 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
        )
        game_settings_text = CordSpriteObject(
            "game_text",
            (
                settings_panel_sprite.rect.center[0],
                basic_theme_button.rect.bottom + 7.5 * 5 * data.settings.scale,
            ),
        )
        reset_settings_button = Button(
            "reset_settings_button",
            (
                29 * 5 * data.settings.scale,
                game_settings_text.rect.bottom + 4.5 * 5 * data.settings.scale,
            ),
            reset_settings_action,
        )
        reset_score_button = Button(
            "reset_score_button",
            (
                23.5 * 5 * data.settings.scale,
                reset_settings_button.rect.bottom + 4.5 * 5 * data.settings.scale,
            ),
            reset_score_button_action,
        )

        self.theme_choice = Choice(update_theme_action)
        self.basic_theme_button_frame = ChoiceButton(
            "theme_button_frame",
            (
                70 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
            data.settings.theme == "basic",
            self.theme_choice,
            ("basic",),
        )
        pink_theme_button_frame = ChoiceButton(
            "theme_button_frame",
            (
                150 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
            data.settings.theme == "pale pink",
            self.theme_choice,
            ("pale pink",),
        )
        blue_theme_button_frame = ChoiceButton(
            "theme_button_frame",
            (
                47 * 5 * data.settings.scale,
                screen_settings_text.rect.bottom + 30 * data.settings.scale,
            ),
            data.settings.theme == "blue",
            self.theme_choice,
            ("blue",),
        )

        self.resolution_choice = Choice(update_scale_action)
        self.resolution_1x_button = ChoiceButton(
            "resolution_button",
            (
                42 * data.settings.scale,
                screen_settings_text.rect.top + 19.5 * 5 * data.settings.scale,
            ),
            data.settings.scale == 1,
            self.resolution_choice,
            (1,),
        )
        resolution_2x_button = ChoiceButton(
            "resolution_button",
            (
                42 * data.settings.scale,
                screen_settings_text.rect.top + 25.5 * 5 * data.settings.scale,
            ),
            data.settings.scale == 2,
            self.resolution_choice,
            (2,),
        )
        self.add_sprite(
            settings_panel_sprite,
            rules_button,
            screen_settings_text,
            basic_theme_button,
            pink_theme_button,
            blue_theme_button,
            self.resolution_1x_button,
            resolution_2x_button,
            self.basic_theme_button_frame,
            pink_theme_button_frame,
            blue_theme_button_frame,
            game_settings_text,
            reset_settings_button,
            reset_score_button,
            active_state=True,
        )


class InfoPanel(Panel):
    def __init__(
            self,
            sprite_groups,
            close_info_button_action: typing.Callable,
    ):
        super().__init__(sprite_groups)
        info_panel_sprite = CordSpriteObject(
            "rules",
            data.settings.field_center
        )
        close_button = Button(
            "close_button",
            (
                data.settings.width - 8.5 * 5 * data.settings.scale,
                7.5 * 5 * data.settings.scale,
            ),
            close_info_button_action,
        )
        self.add_sprite(info_panel_sprite, close_button, active_state=True)


class TopPanel(Panel):
    def __init__(
            self,
            sprite_groups,
            restart_button_action: typing.Callable,
            settings_button_action: typing.Callable,
    ):
        super().__init__(sprite_groups)
        self.top_panel_sprite = CordSpriteObject(
            "top_panel",
            (data.settings.field_center[0], 40 * data.settings.scale),
        )
        self.restart_button = Button(
            "restart_button",
            (
                data.settings.width - 7.5 * 5 * data.settings.scale,
                7.5 * 5 * data.settings.scale,
            ),
            restart_button_action,
        )
        settings_button = Button(
            "settings_button",
            (8.5 * 5 * data.settings.scale, 7.5 * 5 * data.settings.scale),
            settings_button_action,
        )
        pentago_text = CordSpriteObject(
            "pentago_text",
            (data.settings.field_center[0], 7.5 * 5 * data.settings.scale),
        )
        self.add_sprite(self.top_panel_sprite, settings_button, pentago_text)
        self.add_sprite(self.restart_button, active_state=True)


class BottomPanel(Panel):
    def __init__(self, sprite_groups):
        super().__init__(sprite_groups)
        self.bottom_panel_sprite = CordSpriteObject(
            "bottom_panel",
            (data.settings.field_center[0], data.settings.height - 40),
        )
        y_center = self.bottom_panel_sprite.rect.top + 42 * data.settings.scale
        cross_icon = CordSpriteObject(
            "cross_icon",
            (38 * data.settings.scale, y_center),
        )
        zero_icon = CordSpriteObject(
            "zero_icon",
            ((52 * 5 - 2) * data.settings.scale, y_center),
        )
        draw_icon = CordSpriteObject(
            "draw_icon",
            ((94 * 5 - 2) * data.settings.scale, y_center),
        )
        self.scores = {
            "cross": Score(
                (23 * 5 * data.settings.scale, y_center),
                data.score["cross"],
            ),
            "zero": Score(
                (66 * 5 * data.settings.scale, y_center),
                data.score["zero"],
            ),
            "draw": Score(
                (109 * 5 * data.settings.scale, y_center),
                data.score["draw"],
            ),
        }
        self.add_sprite(self.bottom_panel_sprite)
        self.add_sprite(cross_icon, zero_icon, draw_icon, active_state=True)
        for score in self.scores.values():
            self.add_sprite(score.nums, active_state=True)

    def update_score(self):
        for i in ("cross", "zero", "draw"):
            if self.scores[i].value != data.score[i]:
                self.scores[i].change_value(data.score[i])


class StartPanel(Panel):
    def __init__(self, sprite_groups):
        super().__init__(sprite_groups)
        start_panel_sprite = CordSpriteObject(
            "start", data.settings.field_center
        )
        self.add_sprite(start_panel_sprite, active_state=True)
        self.active = True


class SpriteGroups(pygame.sprite.Group):
    def __init__(
            self,
            game,
            update_theme_action,
            update_scale_action,
            reset_settings_action,
    ):
        super().__init__()
        self.game = game
        self.field = Field(self)
        self.top_panel = TopPanel(self, self.restart_button_action, self.settings_button_action)
        self.settings_panel = SettingsPanel(
            self,
            self.open_info_panel,
            self.reset_score_button_action,
            update_theme_action,
            update_scale_action,
            reset_settings_action,
        )
        self.info_panel = InfoPanel(self, self.open_field)
        self.bottom_panel = BottomPanel(self)
        self.start_panel = StartPanel(self)
        self.groups = (
            self.field, self.top_panel, self.settings_panel,
            self.info_panel, self.bottom_panel, self.start_panel,
        )

    def open_info_panel(self):
        self.info_panel.active = True
        self.settings_panel.active = False
        self.top_panel.active = False
        self.field.active = False

    def open_settings_panel(self):
        self.field.active = False
        self.info_panel.active = False
        self.top_panel.active = True
        self.settings_panel.active = True

    def open_field(self):
        self.field.active = True
        self.top_panel.active = True
        self.settings_panel.active = False
        self.info_panel.active = False

    def settings_button_action(self):
        if self.settings_panel.active:
            self.open_field()
        else:
            self.open_settings_panel()

    def reset_score_button_action(self):
        data.score.reset()
        self.bottom_panel.update_score()

    def restart_button_action(self):
        self.start_panel.active = False
        self.info_panel.active = False
        self.settings_panel.active = False
        self.field.restart()

    def run(self):
        self.top_panel.active = True
        self.bottom_panel.active = True
        self.restart_button_action()

    def update(self, event: pygame.event.Event = None) -> None:
        if any(self.field.get_conditions()):
            self.bottom_panel.update_score()
            if event is not None and event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_SPACE]:
                self.restart_button_action()

        for group in self.groups:
            self.add(group.sprite_group)
            self.remove(sprite for sprite in group.sprites if sprite not in group.sprite_group)
        super().update(event)

    def update_scale(self, old_scale: int, new_scale: int):
        self.field.update_scale()
        for group in self.groups:
            for sprite in group.sprites:
                sprite.update_scale(old_scale, new_scale)

    def update_theme(self):
        for group in self.groups:
            for sprite in group.sprites:
                sprite.update_theme()
