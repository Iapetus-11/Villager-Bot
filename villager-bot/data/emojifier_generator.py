from multiprocessing import Pool
import base64
import json
import cv2
import os


class Palette:
    def __init__(self, *, resolution: int = 16, source_dir: str = ".", verbose: bool = False):
        self.source_dir = source_dir + ("" if source_dir.endswith("/") or source_dir.endswith("\\") else "\\")
        self.dest_dims = (resolution, resolution)
        self.data = None
        self.verbose = verbose

    def generate(self):
        if self.verbose:
            print("Processing images...")

        image_files = [
            *filter((lambda file: (file.endswith(".png") or file.endswith(".jpg"))), next(os.walk(self.source_dir))[2])
        ]

        with Pool(8) as pool:
            raw_p = [*filter((lambda e: bool(e)), pool.map(self.pal_from_image, image_files))]

        map_bi = []
        map_quad = []
        map_oct = []
        palette = {}

        for res in raw_p:
            map_bi.append(res[0])
            map_quad.append(res[1])
            map_oct.append(res[2])
            palette.update(res[3])

        self.data = {"dims": self.dest_dims, "bi": map_bi, "quad": map_quad, "oct": map_oct, "palette": palette}

        if self.verbose:
            print(f'Done! ({len(self.data["palette"])})')

    def pal_from_image(self, image_file):
        if self.verbose:
            print(f"Processing: {image_file}")

        img = cv2.imread(self.source_dir + image_file, cv2.IMREAD_UNCHANGED)

        p_count = 0
        avgs = [0, 0, 0]  # bgr

        for row in img:
            for pixel in row:
                if len(pixel) > 3 and pixel[3] < 255:
                    return

                avgs[0] += pixel[0]
                avgs[1] += pixel[1]
                avgs[2] += pixel[2]

                p_count += 1

        avgs[0] /= p_count
        avgs[1] /= p_count
        avgs[2] /= p_count

        avgs.reverse()  # turn into rgb

        return (
            [[int(avg / 128) for avg in avgs], image_file],
            [[int(avg / 64) for avg in avgs], image_file],
            [[int(avg / 32) for avg in avgs], image_file],
            {image_file: base64.b64encode(cv2.imencode(".png", img)[1]).decode("utf-8")},
        )


if __name__ == "__main__":
    p = Palette(verbose=True)
    p.generate()

    with open("0UT.json", "w+") as f:
        json.dump(p.data, f)
