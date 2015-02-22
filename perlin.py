import random

import pygame
import pygame.locals


CONF = {
    "width": 1600,
    "height": 1050,
    "grid_width": 220,
    "grid_height": 220,
    "octaves": 4,
    "persistance": 0.5,
    "cell_size": 4,
    
}

COLORS = [(0, 0, 255), (255, 255, 0), (0, 255, 0), (255, 255, 255)]
GRADIENT = None


class Gradient(object):
    def __init__(self, colors):
        self._bounds = []
        self._colors = colors
        self._calculate_range()

    def _calculate_range(self):
        frequency_step = 1.0 / (len(self._colors) - 1)
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
                low_color = self._colors[color_idx]
                high_color = self._colors[color_idx + 1]
                break

        alpha = 1 - amplitude
        r = int(low_color[0] * alpha + high_color[0] * amplitude)
        g = int(low_color[1] * alpha + high_color[1] * amplitude)
        b = int(low_color[2] * alpha + high_color[2] * amplitude)
        return pygame.Color(r, g, b, 1)
        

def generate_base_noise():
    base_noise = []
    for i in xrange(CONF["grid_height"]):
        base_noise.append([])
        for j in xrange(CONF["grid_width"]):
            base_noise[i].append(random.random())
    return base_noise


def lerp(x0, x1, alpha):
    return x0 * (1 - alpha) + alpha * x1


def generate_smooth_noise_at_octave(base_noise, octave):
    smooth_noise = []
    sample_period = 1 << octave
    sample_frequency = 1.0 / sample_period
    for i in xrange(CONF["grid_height"]):
        smooth_noise.append([])
        sample_i0 = int((i / sample_period) * sample_period)
        sample_i1 = int((sample_i0 + sample_period) % CONF["grid_height"])
        vertical_blend = (i - sample_i0) * sample_frequency

        for j in xrange(CONF["grid_width"]):
            sample_j0 = int((j / sample_period) * sample_period)
            sample_j1 = int((sample_j0 + sample_period) % CONF["grid_width"])
            horizontal_blend = (j - sample_j0) * sample_frequency

            top = lerp(base_noise[sample_j0][sample_i0],
                       base_noise[sample_j1][sample_i0], horizontal_blend)
            bottom = lerp(base_noise[sample_j0][sample_i1],
                          base_noise[sample_j1][sample_i1], horizontal_blend)

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

    for i in xrange(CONF["grid_height"]):
        blended.append([])
        for j in xrange(CONF["grid_width"]):
            blended[i].append(0.0)

    for octave in xrange(CONF["octaves"]-1, -1, -1):
        amplitude *= CONF["persistance"]
        total_amplitude += amplitude
        for i in xrange(CONF["grid_height"]):
            for j in xrange(CONF["grid_width"]):
                blended[i][j] += smooth_noise[octave][i][j] * amplitude

    # normalize
    for i in xrange(CONF["grid_height"]):
        for j in xrange(CONF["grid_width"]):
            blended[i][j] / total_amplitude
    return blended


def init_gradient():
    global GRADIENT
    GRADIENT = Gradient(COLORS)


def draw_noise(screen, noise):
    cell_size = CONF["cell_size"]
    for y in xrange(CONF["grid_height"]):
        for x in xrange(CONF["grid_width"]):
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
    grid_width = CONF["width"]
    grid_height = CONF["height"]
    init_gradient()
    run_noise(screen)
