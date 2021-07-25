import numpy as np
import random
import base64
import json
import cv2
import io

cimport numpy as np

ctypedef np.uint8_t NPUINT8_t


cdef class TilerRGBA:
    cdef dict palette_bi
    cdef dict palette_quad
    cdef dict palette_oct
    cdef dict palette_map

    cdef signed int xi
    cdef signed int yi

    def __init__(self, palette: str):
        with open(palette, "r") as d:
            data = json.load(d)

        self.palette_bi = {tuple(entry[0]): entry[1] for entry in data["bi"]}
        self.palette_quad = {tuple(entry[0]): entry[1] for entry in data["quad"]}
        self.palette_oct = {tuple(entry[0]): entry[1] for entry in data["oct"]}
        self.palette_map = {k: self.im_from_bytes(base64.b64decode(v)) for k, v in data["palette"].items()}

        self.xi = data["dims"][0]
        self.yi = data["dims"][1]

    cdef np.ndarray[NPUINT8_t, ndim=3] im_from_bytes(self, b: bytes):
        return cv2.cvtColor(cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGBA)

    cdef void draw_image(self, np.ndarray[NPUINT8_t, ndim=3] canvas, np.ndarray[NPUINT8_t, ndim=3] img, signed int x, signed int y):
        canvas[y : y + img.shape[0], x : x + img.shape[1]] = img

    cpdef object generate(self, source_bytes: bytes, max_dim: double, detailed: bint):
        cdef np.ndarray[NPUINT8_t, ndim=3] source = self.im_from_bytes(source_bytes)

        cdef double sw = source.shape[1]
        cdef double sh = source.shape[0]

        cdef double t = 512

        cdef double ratio
        cdef double new_w, new_h

        # rescale if too big
        if sw > max_dim or sh > max_dim or detailed:
            ratio = sw / sh

            if sw > sh:
                new_w = max_dim
                new_h = new_w / ratio
            elif sw == sh:
                new_w = max_dim
                new_h = max_dim
            else:
                new_h = max_dim
                new_w = new_h * ratio

            source = cv2.resize(source, (int(new_w), int(new_h)))
        elif sw < t or sh < t:
            ratio = sw / sh

            if sw > sh:
                new_w = t
                new_h = new_w / ratio
            elif sw == sh:
                new_w = t
                new_h = t
            else:
                new_h = t
                new_w = new_h * ratio

            source = cv2.resize(source, (int(new_w), int(new_h)))

        source = cv2.resize(source, (source.shape[1] // self.xi, source.shape[0] // self.yi))
        cdef np.ndarray[NPUINT8_t, ndim=3] canvas = np.zeros((source.shape[0] * self.xi, source.shape[1] * self.yi, 4), np.uint8)

        cdef signed int x = 0
        cdef signed int y = 0
        cdef np.ndarray row
        cdef signed int r, g, b, a
        cdef str pal_key

        for row in source:
            x = 0

            for r, g, b, a in row:
                pal_key = self.palette_oct.get((r // 32, g // 32, b // 32, a // 32))

                if pal_key is None:
                    pal_key = self.palette_quad.get((r // 64, g // 64, b // 64, a // 64))

                    if pal_key is None:
                        pal_key = self.palette_bi.get((r // 128, g // 128, b // 128, a // 128))

                        if pal_key is None:
                            pal_key = self.palette_oct[random.choice(tuple(self.palette_oct.keys()))]

                self.draw_image(canvas, self.palette_map[pal_key], x, y)

                x += self.xi
            y += self.yi

        return io.BytesIO(cv2.imencode(".png", canvas)[1])
