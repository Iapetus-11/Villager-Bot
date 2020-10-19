import numpy as np
import random
import base64
import json
import cv2

def im_from_bytes(bytes):
    return cv2.imdecode(np.frombuffer(bytes, np.uint8), cv2.IMREAD_COLOR)

# def draw_image(canvas, img, x, y):
#     for i, row in enumerate(img):
#         for j, pix in enumerate(row):
#             canvas[i+y][j+x] = pix

def draw_image(canvas, img, x, y):
    canvas[y:y+img.shape[0], x:x+img.shape[1]] = img

with open('data/block_palette.json', 'r') as d:
    data = json.load(d)

palette_bi = dict([(tuple(entry[0]), entry[1]) for entry in data['bi']])
palette_quad = dict([(tuple(entry[0]), entry[1]) for entry in data['quad']])
palette_oct = dict([(tuple(entry[0]), entry[1]) for entry in data['oct']])
palette_map = {k: im_from_bytes(base64.b64decode(v)) for k, v in data['palette'].items()}

xi = data['dims'][0]
yi = data['dims'][1]

def generate(source_bytes, max_dim, detailed):
    source = im_from_bytes(source_bytes)

    sw = source.shape[1]
    sh = source.shape[0]

    t = 512

    # rescale if too big
    if sw > max_dim or sh > max_dim or detailed:
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
    elif sw < t or sh < t:
        ratio = sw/sh

        if sw > sh:
            new_w = t
            new_h = new_w/ratio
        elif sw == sh:
            new_w = t
            new_h = t
        else:
            new_h = t
            new_w = new_h*ratio

        source = cv2.resize(source, (int(new_w), int(new_h)))

    source = cv2.resize(source, (int(source.shape[1]/xi), int(source.shape[0]/yi)))
    #source = cv2.blur(source, (2, 2))

    canvas = np.zeros((source.shape[0]*xi, source.shape[1]*yi, 3), np.uint8)

    y = 0

    for row in source:
        x = 0
        for pix in row: # bgr
            r = pix[2]
            g = pix[1]
            b = pix[0]

            # pal_key = palette_oct.get((int(r/32), int(g/32), int(b/32)))
            #
            # if pal_key is None:
            pal_key = palette_quad.get((int(r/64), int(g/64), int(b/64)))

            if pal_key is None:
                pal_key = palette_bi.get((int(r/128), int(g128), int(b/128)))

            if pal_key is None:
                pal_key = palette_oct[random.choice((*palette_oct.keys(),))]

            draw_image(canvas, palette_map[pal_key], x, y)

            x += xi
        y += yi

    return cv2.imencode('.png', canvas)
