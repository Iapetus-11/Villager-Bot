import base64
import io
import json
import os
import random
import time

import cv2
import imageio
import numpy as np

cimport numpy as np

ctypedef np.uint8_t NPUINT8_t


cdef class Tiler:
    cdef dict palette_bi
    cdef dict palette_quad
    cdef dict palette_oct
    cdef dict palette_map

    cdef signed int xi
    cdef signed int yi

    def __init__(self, palette_file: str):
        with open(palette_file, "r") as d:
            data = json.load(d)

        self.palette_bi = {tuple(entry[0]): entry[1] for entry in data["bi"]}
        self.palette_quad = {tuple(entry[0]): entry[1] for entry in data["quad"]}
        self.palette_oct = {tuple(entry[0]): entry[1] for entry in data["oct"]}
        self.palette_map = {k: self.image_from_bytes(base64.b64decode(v)) for k, v in data["palette"].items()}

        self.xi = data["dims"][0]
        self.yi = data["dims"][1]

    cdef np.ndarray[NPUINT8_t, ndim=3] image_from_bytes(self, bytes b):
        return cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)

    cdef void draw_image(self, np.ndarray[NPUINT8_t, ndim=3] canvas, np.ndarray[NPUINT8_t, ndim=3] img, signed int x, signed int y):
        canvas[y : y + img.shape[0], x : x + img.shape[1]] = img

    cdef np.ndarray[NPUINT8_t, ndim=3] prep_image(self, np.ndarray[NPUINT8_t, ndim=3] source, double max_dim, bint detailed):
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

        return cv2.resize(source, (source.shape[1] // self.xi, source.shape[0] // self.yi))

    cdef np.ndarray[NPUINT8_t, ndim=3] _convert_image(self, np.ndarray[NPUINT8_t, ndim=3] source):
        cdef np.ndarray[NPUINT8_t, ndim=3] canvas = np.zeros((source.shape[0] * self.xi, source.shape[1] * self.yi, 3), np.uint8)

        cdef signed int x = 0
        cdef signed int y = 0
        cdef np.ndarray row
        cdef signed int b, g, r
        cdef str pal_key

        for row in source:
            x = 0

            for r, g, b in row:
                pal_key = self.palette_oct.get((r // 32, g // 32, b // 32))

                if pal_key is None:
                    pal_key = self.palette_quad.get((r // 64, g // 64, b // 64))

                    if pal_key is None:
                        pal_key = self.palette_bi.get((r // 128, g // 128, b // 128))

                        if pal_key is None:
                            pal_key = self.palette_oct[random.choice(tuple(self.palette_oct.keys()))]

                self.draw_image(canvas, self.palette_map[pal_key], x, y)

                x += self.xi
            y += self.yi

        return canvas

    cpdef object convert_image(self, bytes source_bytes, double max_dim, bint detailed):
        cdef np.ndarray[NPUINT8_t, ndim=3] source = self.image_from_bytes(source_bytes)
        del source_bytes  # saves memory
        source = self.prep_image(source, max_dim, detailed)

        return io.BytesIO(cv2.imencode(".png", self._convert_image(source))[1])

    cpdef object convert_video(self, bytes source_bytes, double max_dim, bint detailed):
        cdef str video_fp = f"{time.time()}.{random.randint(0, 1000000)}.temp"

        cdef object video_capture
        cdef list out_frames = []
        cdef bint success
        cdef np.ndarray[NPUINT8_t, ndim=3] frame
        cdef int frame_counter = 0
        cdef int fps

        try:
            with open(video_fp, "wb+") as video_file:
                video_file.write(source_bytes)
                del source_bytes

            video_capture = cv2.VideoCapture(video_fp)
            fps = video_capture.get(cv2.CAP_PROP_FPS) or 15

            while True:
                success, frame = video_capture.read()

                if not success:
                    break

                frame = cv2.cvtColor(self.prep_image(frame, max_dim, detailed), cv2.COLOR_BGR2RGB)
                out_frames.append(self._convert_image(frame))
                frame_counter += 1
        finally:
            try:
                video_capture.release()
            except Exception:
                pass

            try:
                os.remove(video_fp)
            except FileNotFoundError:
                pass
        
        cdef object out_bytes_io = io.BytesIO()
        imageio.mimwrite(out_bytes_io, out_frames, format="gif", fps=fps)
        out_bytes_io.seek(0)
        
        # used for debugging purposes
        # with open("heh.gif", "wb+") as f:
        #     f.write(out_bytes_io.read())
        
        # out_bytes_io.seek(0)

        return out_bytes_io
