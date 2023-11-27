import pygame as pg
import numpy as np
from numba import njit

## Constans
hres = 120 # Horizontal resolution
vres = 100 # Vertical resolution /2 ,     # halfvres its vres
mod =  hres/60 # scaling factor (60° FOV)

# map
# Mapa del laberinto (1: pared, 0: espacio abierto)
maph = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1]
], dtype=np.int64)
# Tamaño del mapa
size = len(maph)

def main():
    pg.init()
    screen = pg.display.set_mode((640, 480))
    pg.mouse.set_visible(False)  # Oculta el cursor del mouse
    pg.event.set_grab(True)  # Asegura que el mouse permanezca dentro de la ventana


    running = True
    clock = pg.time.Clock()

    # Posición inicial del jugador en el centro del laberinto
    posx, posy, rot = size // 2, size // 2, 0
    frame = np.random.uniform(0, 1, (hres, vres*2, 3))

    # Texturas
    sky = pg.image.load("img/sky.jpg")
    sky = pg.surfarray.array3d(pg.transform.scale(sky, (360, vres*2)))

    floor = pg.surfarray.array3d(pg.image.load("img/floor.jpg"))/255
    wall = pg.surfarray.array3d(pg.image.load("img/wall.jpg"))/255

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        force_quit(pg.key.get_pressed())

        # Captura el movimiento del mouse
        mouse_x, _ = pg.mouse.get_rel()

        # Actualiza la posición y rotación del jugador
        posx, posy, rot = movement(posx, posy, rot, pg.key.get_pressed(), clock.tick(), mouse_x)

        # Renderiza el frame
        frame = new_frame(posx, posy, rot, frame, sky, floor, wall)

        surface = pg.surfarray.make_surface(frame*255)
        surface = pg.transform.scale(surface, (640, 480))
        fps = int(clock.get_fps())
        pg.display.set_caption(f"FPS: {fps}")

        screen.blit(surface, (0, 0))
        pg.display.update()

    pg.quit()



# render logic in one function, called new frame
@njit()
def new_frame(posx, posy, rot, frame, sky, floor, wall):
    for i in range(hres):
        roti = rot + np.deg2rad(i/mod - 30)
        sin, cos = np.sin(roti), np.cos(roti)

        # Ajuste en la proyección de rayos
        frame[i][:] = sky[int(np.rad2deg(roti) % 359)][:] / 255

        for j in range(vres):
            n = vres / (vres - j)  # Ajuste: Se elimina cos2
            x, y = posx + n * cos, posy + n * sin

            xx, yy = int(x * 2 % 1 * 100), int(y * 2 % 1 * 100)
            shade = 0.2 + 0.8 * (1 - j / vres)

            # Renderizado de las paredes
            if maph[int(x) % (size - 1)][int(y) % (size - 1)]:
                h = vres - j
                if x % 1 < 0.03 or x % 1 > 0.97:
                    xx = yy
                else:
                    xx = int(x * 2 % 1 * 100)

                yy = np.linspace(0, 198, h * 2) % 99

                for k in range(h * 2):
                    frame[i][vres - h + k] = shade * wall[xx][int(yy[k])]
                break
            else:
                frame[i][vres * 2 - j - 1] = shade * floor[xx][yy]
    return frame


def is_wall(x, y):
    """ Verifica si la posición (x, y) es una pared. """
    if x < 0 or x >= size or y < 0 or y >= size:
        return True
    return maph[int(x)][int(y)] == 1

def movement(posx, posy, rot, keys, et, mouse_x):
    movfactor = 0.005
    rot_speed = 0.002  # Ajusta esta velocidad según sea necesario
    wall_buffer = 0.9  # Distancia mínima a las paredes

    # Rotación con el mouse
    rot += mouse_x * rot_speed * et

    # Movimiento con teclado
    if keys[pg.K_a] or keys[pg.K_LEFT]:
        rot -= et * movfactor
    if keys[pg.K_d] or keys[pg.K_RIGHT]: 
        rot += et * movfactor
    if keys[pg.K_w] or keys[pg.K_UP]:
        new_x = posx + movfactor * et * np.cos(rot)
        new_y = posy + movfactor * et * np.sin(rot)
    elif keys[pg.K_s] or keys[pg.K_DOWN]:
        new_x = posx - movfactor * et * np.cos(rot)
        new_y = posy - movfactor * et * np.sin(rot)
    else:
        new_x, new_y = posx, posy

    # Verifica colisiones en múltiples direcciones
    if (not is_wall(new_x + wall_buffer * np.cos(rot), new_y + wall_buffer * np.sin(rot)) and
        not is_wall(new_x - wall_buffer * np.sin(rot), new_y + wall_buffer * np.cos(rot)) and
        not is_wall(new_x + wall_buffer * np.sin(rot), new_y - wall_buffer * np.cos(rot)) and
        not is_wall(new_x, new_y)):
        posx, posy = new_x, new_y

    return posx, posy, rot



#if esc is pressed, quit the game
def force_quit(keys):
    if keys[pg.K_ESCAPE]:
        pg.quit()
        quit()

def draw_minimap(screen, maph, posx, posy):
    minimap_scale = 5  # Factor de escala para el minimapa
    minimap_size = size * minimap_scale
    minimap_surf = pg.Surface((minimap_size, minimap_size))

    # Dibuja las paredes y espacios abiertos
    for y in range(size):
        for x in range(size):
            rect = (x * minimap_scale, y * minimap_scale, minimap_scale, minimap_scale)
            if maph[y][x] == 1:
                pg.draw.rect(minimap_surf, (255, 255, 255), rect)  # Paredes blancas
            else:
                pg.draw.rect(minimap_surf, (0, 0, 0), rect)  # Espacio abierto negro

    # Dibuja la posición del jugador
    player_pos = (int(posx * minimap_scale), int(posy * minimap_scale))
    pg.draw.circle(minimap_surf, (255, 0, 0), player_pos, minimap_scale // 2)  # Jugador en rojo

    # Dibuja el minimapa en la pantalla
    screen.blit(minimap_surf, (10, 10))  # Posición del minimapa en la pantalla

    

if __name__ == "__main__":
    main()
    pg.quit()