"""A small, self-contained icon for the game window."""
import pygame


def make_icon():
    icon = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(icon, (15, 27, 39), (2, 2, 60, 60), border_radius=15)
    pygame.draw.rect(icon, (71, 220, 210), (2, 2, 60, 60), 3, border_radius=15)
    for x, y, length in ((9, 42, 21), (8, 48, 15), (12, 54, 12)):
        pygame.draw.line(icon, (51, 131, 146), (x, y), (x + length, y - 5), 3)
    pygame.draw.circle(icon, (46, 187, 203), (37, 30), 17)
    pygame.draw.circle(icon, (178, 255, 239), (37, 30), 17, 2)
    pygame.draw.circle(icon, (255, 255, 255), (39, 25), 3)
    pygame.draw.circle(icon, (255, 255, 255), (47, 29), 3)
    pygame.draw.polygon(icon, (255, 207, 97), [(34, 46), (42, 36), (40, 44), (49, 41), (36, 56), (39, 47)])
    return icon
