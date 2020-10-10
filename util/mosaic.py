import numpy as np
import random
import base64
import json
import cv2

def im_from_b64(b64_data):
    return cv2.imdecode(np.frombuffer(base64.b64decode(b64_data), np.uint8), cv2.IMREAD_COLOR)

def draw_image(canvas, img, x, y):
    for i, row in enumerate(img):
        for j, pix in enumerate(row):
            canvas[i+y][j+x] = pix

with open('../data/block_palette.json', 'r') as d:
    data = json.load(d)

palette_bi = dict([(tuple(entry[0]), entry[1]) for entry in data['bi']])
palette_quad = dict([(tuple(entry[0]), entry[1]) for entry in data['quad']])
palette_oct = dict([(tuple(entry[0]), entry[1]) for entry in data['oct']])
palette_map = {k: im_from_b64(v) for k, v in data['palette'].items()}

xi = data['dims'][0]
yi = data['dims'][1]

def generate(img_src: str, max_dim: int):
    source = cv2.imread(img_src)

    sw = source.shape[1]
    sh = source.shape[0]

    if sw > max_dim or sh > max_dim:
        ratio = sw/sh

        if sw > sh:
            new_w = max_dim
            new_h = new_w/ratio
        elif sw == sh:
            new_w = max_dim
            new_h = max_dim
        else:
            new_h = max_dim
            new_w = new_h*ratio

        source = cv2.resize(source, (int(new_w), int(new_h)))

    source = cv2.resize(source, (int(xi), int(yi)))
    source = cv2.blur(source, (2, 2))

    canvas = []

    y = 0

    for row in source:
        x = 0
        for pix in row: # bgr
            pal_key = palette_oct.get((int(pix[2]/32), int(pix[1]/32), int(pix[0]/32)))

            if pal_key is None:
                pal_key = palette_quad.get((int(pix[2]/64), int(pix[1]/64), int(pix[0]/64)))

            if pal_key is None:
                pal_key = palette_bi.get((int(pix[2]/128), int(pix[1]/128), int(pix[0]/128)))

            if pal_key is None:
                print(f'No match for pixel ({pix[2]}, {pix[1]}, {pix[0]}) found, using random.')
                pal_key = palette_oct[random.choice([*palette_oct.keys()])]

            draw_image(canvas, palette_map[pal_key], x, y)

            x += xi
        y += yi

    return canvas
