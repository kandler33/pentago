import os
import dataclasses

from settings import settings
from images import ImageCreator
from database import database


@dataclasses.dataclass
class Asset:
    id: int
    name: str
    themeable: bool
    hoverable: bool
    clickable: bool
    base_filename: str
    base_clicked_filename: str = None
    normal_filename: str = None
    hovered_filename: str = None
    clicked_filename: str = None

    @property
    def normal_path(self) -> str:
        return os.path.join(settings.img_path, self.normal_filename)

    @property
    def hovered_path(self) -> str:
        return os.path.join(settings.img_path, self.hovered_filename)

    @property
    def base_path(self) -> str:
        return os.path.join(settings.base_img_path, self.base_filename)

    @property
    def base_clicked_path(self) -> str:
        return os.path.join(settings.base_img_path, self.base_clicked_filename)

    @property
    def clicked_path(self) -> str:
        return os.path.join(settings.img_path, self.clicked_filename)


class Assets:
    def __init__(self) -> None:
        self.db = database
        self.img_creator = ImageCreator()
        self.assets = {}

    def get_asset(self, asset_name: str) -> Asset:
        if asset_name in self.assets:
            return self.assets[asset_name]

        data = self.db.get_from("asset", name=asset_name)
        asset = Asset(**data)
        self._create_imgs(asset)

        self.assets[asset.name] = asset
        return asset

    def _create_imgs(self, asset: Asset) -> None:
        save_flag = False
        if (
            asset.normal_filename is None
            or not os.path.exists(asset.normal_path)
        ):
            self._create_normal_img(asset)
            save_flag = True

        if asset.hoverable and (
                asset.hovered_filename is None
                or not os.path.exists(asset.hovered_path)
        ):
            self._create_hovered_img(asset)
            save_flag = True

        if asset.clickable and (
            asset.clicked_filename is None
            or not os.path.exists(asset.clicked_path)
        ):
            self._create_clicked_img(asset)
            save_flag = True

        if save_flag:
            self._save_asset(asset)

    def _create_normal_img(self, asset: Asset) -> None:
        normal_filename = self._normal_filename(asset.name)
        input_path = asset.base_path
        output_path = os.path.join(settings.img_path, normal_filename)
        if asset.themeable:
            self.img_creator.create_themeable_img(input_path, output_path)
        else:
            self.img_creator.create_non_themeable_img(input_path, output_path)

        asset.normal_filename = normal_filename

    def _create_hovered_img(self, asset: Asset) -> None:
        hovered_filename = self._hovered_filename(asset.name)
        input_path = asset.base_path
        output_path = os.path.join(settings.img_path, hovered_filename)

        self.img_creator.create_hovered_img(input_path, output_path)
        asset.hovered_filename = hovered_filename

    def _create_clicked_img(self, asset: Asset) -> None:
        clicked_filename = asset.base_clicked_filename
        input_path = asset.base_clicked_path
        output_path = os.path.join(settings.img_path, clicked_filename)
        self.img_creator.create_themeable_img(input_path, output_path)
        asset.clicked_filename = clicked_filename

    def _save_asset(self, asset: Asset) -> None:
        self.db.update(
            "asset", asset.id,
            normal_filename=asset.normal_filename,
            hovered_filename=asset.hovered_filename,
            clicked_filename=asset.clicked_filename,
        )

    def update_assets(self) -> None:
        for asset in self.assets.values():
            self._create_normal_img(asset)
            if asset.hoverable:
                self._create_hovered_img(asset)
            if asset.clickable:
                self._create_clicked_img(asset)

    @staticmethod
    def _normal_filename(asset_name: str) -> str:
        return f"{asset_name}_normal.png"

    @staticmethod
    def _hovered_filename(asset_name: str) -> str:
        return f"{asset_name}_hovered.png"


assets = Assets()
