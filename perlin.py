import random

import pygame
import pygame.locals

# Persistance affects the overall net amplitude of all points.
# Default value from the referenced article is 0.5
#
# Octaves are the number of times to smooth the noise. Each
# octave is applied at half the blending value of the previous,
# so more octaves == a smoother noise output but far less variation
# Default value from the referenced article is undefined, but I like 4

CONF = {
    "width": 1600,
    "height": 1050,
    "grid_width": 300,
    "grid_height": 220,
    "octaves": 5,
    "persistance": 0.55,
    "cell_size": 4,
    "smooth_gradient": False,
    "error_color": (255, 20, 147, 1)
}

# Terrain-ish?
# Obviously there are not even distributions of these things
# in the real world. You'd want a manually defined scale or
# set of scales to indicate what the amplitude really means.
# This is just a visualization to help you imagine the possibilities.
# You could also invert the scale. We're inventing meaning in the amplitudes
# where none exists.

# NOTE(mdietz): You want smooth_gradient == False with these
TERRAIN = [(0, 0, 255), # Blue - Deep Water
           (64, 224, 228), # Light Blue - Shallow Water
           (238, 221, 130), # Yellow - Sand
           (0, 224, 0), # Darker green - low lands
           (0, 255, 0), # lighter green - high lands
           (160, 82, 45), # Brown - Mountains
           (255, 255, 255)] # white - Mountain peaks

# Grayscale, use with smooth_gradient == True
GRAYSCALE = [(0, 0, 0), (255, 255, 255)]

COLORS = TERRAIN
GRADIENT = None


def lerp(x0, x1, alpha):
    return x0 * (1 - alpha) + alpha * x1


class Gradient(object):
    def __init__(self, colors):
        self._bounds = []
        self._colors = colors
        self._calculate_range()

    def _calculate_range(self):
        # If we're not smoothing, we need to return all of the
        # colors available as a range
        step_offset = 0
        if CONF["smooth_gradient"]:
            step_offset = 1

        frequency_step = 1.0 / (len(self._colors) - step_offset)
        last_bound = 0.0
        next_bound = frequency_step
        for color in self._colors:
            self._bounds.append((last_bound, next_bound))
            last_bound = next_bound
            next_bound += frequency_step
            if next_bound > 1.0:
                next_bound = 1.0

    def add_color(self, color):
        self._colors.append(color)
        self._calculate_range()

    def get_color(self, amplitude):
        for color_idx, bounds in enumerate(self._bounds):
            if bounds[1] >= amplitude >= bounds[0]:
                if CONF["smooth_gradient"]:
                    low_color = self._colors[color_idx]
                    high_color = self._colors[color_idx + 1]
                    r = int(lerp(low_color[0], high_color[0], amplitude))
                    g = int(lerp(low_color[1], high_color[1], amplitude))
                    b = int(lerp(low_color[2], high_color[2], amplitude))
                else:
                    r,g,b = self._colors[color_idx]
                return pygame.Color(r, g, b, 1)

        # NOTE(mdietz): This shouldn't happen after normalization
        return pygame.Color(*CONF["error_color"])

        

def generate_base_noise():
    base_noise = []
    grid_width = CONF["width"] / CONF["cell_size"]
    grid_height = CONF["height"] / CONF["cell_size"]
    for i in xrange(grid_height):
        base_noise.append([])
        for j in xrange(grid_width):
            base_noise[i].append(random.random())
    return base_noise


def generate_smooth_noise_at_octave(base_noise, octave):
    smooth_noise = []

    # Did you know bitshift actually worked in Python?
    sample_period = 1 << octave
    sample_frequency = 1.0 / sample_period

    grid_width = CONF["width"] / CONF["cell_size"]
    grid_height = CONF["height"] / CONF["cell_size"]

    for i in xrange(grid_height):
        smooth_noise.append([])
        sample_i0 = int((i / sample_period) * sample_period)
        sample_i1 = int((sample_i0 + sample_period) % grid_height)
        vertical_blend = (i - sample_i0) * sample_frequency

        for j in xrange(grid_width):
            sample_j0 = int((j / sample_period) * sample_period)
            sample_j1 = int((sample_j0 + sample_period) % grid_width)
            horizontal_blend = (j - sample_j0) * sample_frequency

            top = lerp(base_noise[sample_i0][sample_j0],
                       base_noise[sample_i0][sample_j1], horizontal_blend)

            bottom = lerp(base_noise[sample_i1][sample_j0],
                          base_noise[sample_i1][sample_j1], horizontal_blend)

            smooth_noise[i].append(lerp(top, bottom, vertical_blend))

    return smooth_noise


def generate_smooth_noise(base_noise):
    # Ooohhh yeah, smooth noise
    smooth_noise = []
    for i in xrange(CONF["octaves"]):
        smooth_noise.append(generate_smooth_noise_at_octave(base_noise, i)) 
    return smooth_noise


def generate_perlin_noise(smooth_noise):
    blended = []
    amplitude = 1.0
    total_amplitude = 0.0

    grid_width = CONF["width"] / CONF["cell_size"]
    grid_height = CONF["height"] / CONF["cell_size"]

    for i in xrange(grid_height):
        blended.append([])
        for j in xrange(grid_width):
            blended[i].append(0.0)

    for octave in xrange(CONF["octaves"]-1, -1, -1):
        amplitude *= CONF["persistance"]
        total_amplitude += amplitude
        for i in xrange(grid_height):
            for j in xrange(grid_width):
                blended[i][j] += smooth_noise[octave][i][j] * amplitude

    # normalize
    for i in xrange(grid_height):
        for j in xrange(grid_width):
            blended[i][j] /= total_amplitude
    return blended


def init_gradient():
    global GRADIENT
    GRADIENT = Gradient(COLORS)


def draw_noise(screen, noise):
    cell_size = CONF["cell_size"]
    grid_width = CONF["width"] / CONF["cell_size"]
    grid_height = CONF["height"] / CONF["cell_size"]

    for y in xrange(grid_height):
        for x in xrange(grid_width):
            rect = pygame.Rect(x * cell_size, y * cell_size, cell_size,
                               cell_size)
            color = GRADIENT.get_color(noise[y][x])
            pygame.draw.rect(screen, color, rect)


def run_noise(screen):
    clock = pygame.time.Clock()
    base_noise = generate_base_noise()
    smooth_noise = generate_smooth_noise(base_noise)
    final_noise = generate_perlin_noise(smooth_noise)

    grids = [base_noise]
    grids.extend(smooth_noise)
    grids.append(final_noise)
    display_idx = len(grids) - 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                return
            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_ESCAPE:
                    return
                if event.key == pygame.locals.K_SPACE:
                    base_noise = generate_base_noise()
                    smooth_noise = generate_smooth_noise(base_noise)
                    final_noise = generate_perlin_noise(smooth_noise)
                    grids = [base_noise]
                    grids.extend(smooth_noise)
                    grids.append(final_noise)
                    display_idx = len(grids) - 1
                if event.key == pygame.locals.K_LEFT:
                    display_idx -= 1
                    if display_idx < 0:
                        display_idx = len(grids) - 1
                if event.key == pygame.locals.K_RIGHT:
                    display_idx += 1
                    if display_idx == len(grids):
                        display_idx = 0

        if display_idx == 0:
            caption = "Base noise"
        elif display_idx == len(grids) - 1:
            caption = "Perlin Noise"
        else:
            caption = "Smooth Noise"

        pygame.display.set_caption(caption)
        draw_noise(screen, grids[display_idx])
        pygame.event.pump()
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((CONF['width'], CONF['height']), 0)
    init_gradient()
    run_noise(screen)
