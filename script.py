import os

import sqlite3

# game_folder = os.path.join(os.path.dirname(__file__), 'data')
# img_folder = os.path.join(game_folder, "resized")
#
# base_img_folder = os.path.join(game_folder, "base_img")
# themeable_folder = os.path.join(base_img_folder, "themeable")
# hoverable_folder = os.path.join(themeable_folder, "hoverable")
#
# con = sqlite3.connect(os.path.join(game_folder, "db.sqlite3"))
# header = ("name", "themeable", "hoverable", "clickable",
#           "base_filename", "base_clicked_filename", "normal_filename",
#           "hovered_filename", "clicked_filename")
# data = []
# clickable = {}
#
# for filename in os.listdir(base_img_folder):
#     path = os.path.join(base_img_folder, filename)
#     if os.path.isfile(path):
#         name = filename.split('.')[0]
#         data.append((name, False, False, False, filename, None, None, None, None))
#
#
# for filename in os.listdir(themeable_folder):
#     path = os.path.join(themeable_folder, filename)
#     if os.path.isfile(path):
#         name = filename.split('.')[0]
#         if name.endswith('_clicked'):
#             clickable[name[:name.index('_clicked')]] = filename
#         data.append((name, True, False, False, filename, None, None, None, None))
#
# for filename in os.listdir(hoverable_folder):
#     path = os.path.join(hoverable_folder, filename)
#     if os.path.isfile(path):
#         clickable_b = False
#         name = filename.split('.')[0]
#         if name in clickable:
#             clickable_b = True
#
#         data.append((name, True, True, clickable_b, filename, clickable.get(name, None), None, None, None))
#
# sql_string = (
#     f"INSERT INTO asset {repr(header)}\nVALUES\n" +
#     ",\n".join(repr(i).replace('None', 'NULL') for i in data) + ';'
# )
# print(sql_string)
#
# cur = con.cursor()
#
# cur.execute(sql_string)
# con.commit()
# cur.close()
# con.close()

game_folder = os.path.join(os.path.dirname(__file__), 'data')
con = sqlite3.connect(os.path.join(game_folder, "db.sqlite3"))
cur = con.cursor()

themes = {
    "basic": (
        (255, 255, 255, 255),
        (170, 220, 175, 255),
        (93, 143, 98, 255),
        (0, 0, 0, 255),
        (180, 180, 180, 255),
        (9, 56, 13, 255),
    ),
    "pale pink": (
        (254, 245, 239, 255),
        (220, 193, 196, 255),
        (157, 92, 99, 255),
        (88, 75, 83, 255),
        (202, 155, 114, 255),
        (75, 29, 34, 255),
    ),
    "blue": (
        (201, 231, 255, 255),
        (139, 191, 247, 255),
        (4, 135, 226, 255),
        (16, 14, 63, 255),
        (157, 217, 242, 255),
        (4, 45, 131, 255),
    ),
}

header = ("r", "g", "b", "a")
sqlstring = (
    f"INSERT INTO color {repr(header)}\nVALUES\n" +
    ",\n".join(repr(color) for theme in themes.values() for color in theme) + ';'
)
print(sqlstring)

cur.execute(sqlstring)
con.commit()
