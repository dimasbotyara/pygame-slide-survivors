"""Per-tick dynamic broad phase for enemy separation (no AI throttling)."""
import math


class EnemyGrid:
    def __init__(self, enemies, cell_size=128):
        self.cell_size = cell_size
        self.cells = {}
        self.positions = {}
        self.order = {enemy: i for i, enemy in enumerate(enemies)}
        self.max_size = max((e.size for e in enemies), default=0)
        for enemy in enemies:
            self.update(enemy)

    def update(self, enemy):
        key = (math.floor(enemy.x/self.cell_size), math.floor(enemy.y/self.cell_size))
        old = self.positions.get(enemy)
        if old != key:
            if old is not None:
                self.cells[old].remove(enemy)
                if not self.cells[old]:
                    del self.cells[old]
            self.cells.setdefault(key, []).append(enemy)
            self.positions[enemy] = key
        self.max_size = max(self.max_size, enemy.size)

    def nearby(self, enemy):
        radius = enemy.size+self.max_size
        size = self.cell_size
        candidates = []
        for y in range(math.floor((enemy.y-radius)/size), math.floor((enemy.y+radius)/size)+1):
            for x in range(math.floor((enemy.x-radius)/size), math.floor((enemy.x+radius)/size)+1):
                candidates.extend(self.cells.get((x, y), ()))
        # Preserve accumulation order and sequential movement of the old list scan.
        return sorted(candidates, key=self.order.__getitem__)
