import os

import pygame

from sprite_groups import SpriteGroups
from sprites import SpriteObject
from data import data


class Pentago:
    def __init__(self):
        # creating game and window
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode(
            (data.settings.width, data.settings.height)
        )
        pygame.display.set_caption("")
        self.clock = pygame.time.Clock()

        # creating groups
        self.all_sprites = SpriteGroups(
            self,
            self.update_theme,
            self.update_scale,
            self.reset_settings,
        )

        # sound effects
        # TODO
        # self.hover_sound = pygame.mixer.Sound(
        #     os.path.join(self.sound_folder, "hover.wav")
        # )
        # self.click_sound = pygame.mixer.Sound(
        #     os.path.join(self.sound_folder, "click.wav")
        # )
        # self.open_panel_sound = pygame.mixer.Sound(
        #     os.path.join(self.sound_folder, "open_panel.wav")
        # )
        # self.win_sound = pygame.mixer.Sound(os.path.join(self.sound_folder, "win.wav"))

        # setting up icon
        icon_sprite = SpriteObject("icon")
        pygame.display.set_icon(icon_sprite.image)

        self.FPS = 30

    def start(self):
        print(self.all_sprites)
        while True:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    data.save()
                    return 1

                if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP):
                    return 0

            # update
            self.all_sprites.update()

            # render
            self.screen.fill(self.background_color)
            self.all_sprites.draw(self.screen)

            # return to display
            pygame.display.flip()

    def run(self):
        start_response = self.start()
        if start_response == 1:
            return
        self.all_sprites.run()

        running = True
        while running:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                self.all_sprites.update(event)
                # check for closing window
                if event.type == pygame.QUIT:
                    data.save()
                    running = False

                if event.type == pygame.KEYDOWN:

                    # debug settings changing
                    if pygame.key.get_pressed()[pygame.K_HOME]:
                        data.settings.back_to_default()
                        data.save()
                        running = False

                    if pygame.key.get_pressed()[pygame.K_2]:
                        self.update_scale(2)

                    if pygame.key.get_pressed()[pygame.K_1]:
                        self.update_scale(1)

                    if pygame.key.get_pressed()[pygame.K_p]:
                        self.update_theme("pale pink")

                    if pygame.key.get_pressed()[pygame.K_b]:
                        self.update_theme("basic")

                    # TODO
                    # if pygame.key.get_pressed()[pygame.K_a]:
                    #     self.hover_sound.play()

            # update
            self.all_sprites.update()

            # render
            self.screen.fill(self.background_color)
            self.all_sprites.draw(self.screen)

            # return to display
            pygame.display.flip()

    def update_scale(self, new_scale: int) -> None:
        if new_scale == data.settings.scale:
            return

        old_scale = data.settings.scale
        data.settings.scale = new_scale
        data.assets.update_assets()
        pygame.display.set_mode((data.settings.width, data.settings.height))

        self.all_sprites.update_scale(old_scale, new_scale)

    def update_theme(self, new_theme: str) -> None:
        if new_theme == data.settings.theme:
            return

        data.settings.theme = new_theme
        data.assets.update_assets()

        self.all_sprites.update_theme()

    def reset_settings(self):
        old_scale = data.settings.scale
        old_theme = data.settings.theme
        data.settings.back_to_default()

        if old_theme != data.settings.theme or old_scale != data.settings.scale:
            data.assets.update_assets()
            if old_scale != data.settings.scale:
                self.all_sprites.update_scale(old_scale, data.settings.scale)
            else:
                self.all_sprites.update_theme()

    @property
    def background_color(self):
        return data.themes.get_color(data.settings.theme, "background_color")


if __name__ == "__main__":
    pentago = Pentago()
    pentago.run()
    pygame.quit()
