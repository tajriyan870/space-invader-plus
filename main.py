import asyncio
import pygame
import sys
import random
import math

# ── Constants ──────────────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 700
FPS = 60

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   255, 0)
RED        = (255, 50,  50)
YELLOW     = (255, 220, 0)
CYAN       = (0,   220, 255)
ORANGE     = (255, 140, 0)
PURPLE     = (180, 0,   255)
DARK_GREEN = (0,   180, 0)
GRAY       = (120, 120, 120)
LIGHT_BLUE = (100, 180, 255)
PINK       = (255, 100, 180)
DIM_GRAY   = (60,  60,  60)

PLAYER_SPEED     = 5
BULLET_SPEED     = 10
ALIEN_ROWS       = 4
ALIEN_COLS       = 10
ALIEN_H_GAP      = 60
ALIEN_V_GAP      = 50
ALIEN_DROP       = 18
SHIELD_COUNT     = 4
CHARGE_MAX       = 90
GRAVITY_INTERVAL = 1200
GRAVITY_DURATION = 90
MAX_NAME_LEN     = 10

# ── Sound generator ────────────────────────────────────────
def make_sound(freq, duration_ms, volume=0.3, wave='square', fade_ms=10):
    """Generate a simple synthesized sound using pygame mixer."""
    try:
        sample_rate = 22050
        n_samples   = int(sample_rate * duration_ms / 1000)
        buf         = []
        for i in range(n_samples):
            t = i / sample_rate
            if wave == 'square':
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            elif wave == 'sine':
                val = math.sin(2 * math.pi * freq * t)
            elif wave == 'noise':
                val = random.uniform(-1, 1)
            elif wave == 'descend':
                f   = freq * (1 - i / n_samples * 0.7)
                val = math.sin(2 * math.pi * f * t)
            else:
                val = math.sin(2 * math.pi * freq * t)

            # Fade in/out
            fade_samples = int(sample_rate * fade_ms / 1000)
            if i < fade_samples:
                val *= i / fade_samples
            elif i > n_samples - fade_samples:
                val *= (n_samples - i) / fade_samples

            sample = int(val * volume * 32767)
            sample = max(-32768, min(32767, sample))
            buf.append(sample)

        import array as arr
        raw = arr.array('h', buf)
        # Stereo: duplicate channel
        stereo = arr.array('h')
        for s in raw:
            stereo.append(s)
            stereo.append(s)
        sound = pygame.sndarray.make_sound(
            __import__('numpy').array(stereo, dtype='int16').reshape(-1, 2)
        )
        return sound
    except Exception:
        return None

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.sounds  = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._load()
        except Exception:
            self.enabled = False

    def _load(self):
        try:
            import numpy as np
            sr = 22050

            def gen(freq, dur, vol, shape='sine', chirp=None):
                n = int(sr * dur)
                t = __import__('numpy').linspace(0, dur, n, False)
                if chirp:
                    f = __import__('numpy').linspace(freq, chirp, n)
                else:
                    f = freq
                if shape == 'square':
                    wave = __import__('numpy').sign(__import__('numpy').sin(2 * math.pi * f * t))
                elif shape == 'noise':
                    wave = __import__('numpy').random.uniform(-1, 1, n)
                else:
                    wave = __import__('numpy').sin(2 * math.pi * f * t)
                # envelope
                env = __import__('numpy').ones(n)
                fade = min(int(sr * 0.01), n // 4)
                env[:fade] = __import__('numpy').linspace(0, 1, fade)
                env[-fade:] = __import__('numpy').linspace(1, 0, fade)
                wave = (wave * env * vol * 32767).astype(__import__('numpy').int16)
                stereo = __import__('numpy').column_stack([wave, wave])
                return pygame.sndarray.make_sound(stereo)

            self.sounds['shoot']        = gen(1200, 0.12, 0.70, 'square')
            self.sounds['shoot_charge'] = gen(300,  0.22, 0.80, 'square', chirp=1800)
            self.sounds['alien_hit']    = gen(200,  0.08, 0.30, 'sine',   chirp=80)
            self.sounds['player_hit']   = gen(120,  0.25, 0.45, 'noise')
            self.sounds['alien_shoot']  = gen(300,  0.07, 0.18, 'square')
            self.sounds['wave_clear']   = gen(660,  0.35, 0.35, 'sine',   chirp=1320)
            self.sounds['game_over']    = gen(220,  0.60, 0.40, 'sine',   chirp=55)
            self.sounds['gravity']      = self._make_gravity_boom(sr)
            self.sounds['menu_move']    = gen(440,  0.05, 0.20, 'sine')
            self.sounds['menu_select']  = gen(880,  0.10, 0.25, 'square')
        except Exception:
            self.enabled = False

    def _make_gravity_boom(self, sr):
        """Dramatic gravity wave: deep rumble + rising sweep + crash."""
        try:
            import numpy as np
            dur = 1.2
            n   = int(sr * dur)
            t   = np.linspace(0, dur, n, False)

            # Layer 1: deep sub-bass rumble (60 Hz)
            rumble = np.sin(2 * math.pi * 60 * t) * 0.5

            # Layer 2: sweeping tone 80 -> 600 Hz
            sweep_f = np.linspace(80, 600, n)
            sweep   = np.sin(2 * math.pi * sweep_f * t) * 0.6

            # Layer 3: white noise burst at the peak (hits hard at 0.15s)
            noise   = np.random.uniform(-1, 1, n) * 0.4
            noise_env = np.exp(-np.abs(t - 0.15) * 20)
            noise   *= noise_env

            # Layer 4: high metallic crash (3000 Hz, short decay)
            crash   = np.sin(2 * math.pi * 3000 * t) * np.exp(-t * 18) * 0.35

            wave    = rumble + sweep + noise + crash

            # Master envelope: hard attack, long tail
            env     = np.ones(n)
            attack  = int(sr * 0.02)
            env[:attack] = np.linspace(0, 1, attack)
            decay_start  = int(sr * 0.3)
            env[decay_start:] = np.linspace(1, 0, n - decay_start)

            wave   *= env
            # Normalize
            peak    = np.max(np.abs(wave))
            if peak > 0:
                wave = wave / peak * 0.85 * 32767
            wave    = wave.astype(np.int16)
            stereo  = np.column_stack([wave, wave])
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def play(self, name):
        if self.enabled and name in self.sounds and self.sounds[name]:
            try:
                self.sounds[name].play()
            except Exception:
                pass

# ── Star background ────────────────────────────────────────
class Star:
    def __init__(self):
        self.reset(True)

    def reset(self, init=False):
        self.x          = random.randint(0, SCREEN_W)
        self.y          = random.randint(0, SCREEN_H) if init else 0
        self.speed      = random.uniform(0.2, 0.8)
        self.size       = random.randint(1, 2)
        self.brightness = random.randint(100, 255)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_H:
            self.reset()

    def draw(self, surf):
        c = self.brightness
        pygame.draw.circle(surf, (c, c, c), (int(self.x), int(self.y)), self.size)

# ── Player ─────────────────────────────────────────────────
class Player:
    WIDTH  = 40
    HEIGHT = 30

    def __init__(self, x, color, controls, name):
        self.x              = float(x)
        self.y              = float(SCREEN_H - 70)
        self.color          = color
        self.controls       = controls
        self.name           = name
        self.lives          = 3
        self.score          = 0
        self.bullets        = []
        self.charge         = 0
        self.charging       = False
        self.shoot_cooldown = 0
        self.invincible     = 0
        self.alive          = True
        self.explode_timer  = 0
        self.particles      = []

    def handle_input(self, keys, sounds=None):
        if not self.alive:
            return
        if keys[self.controls['left']]:
            self.x -= PLAYER_SPEED
        if keys[self.controls['right']]:
            self.x += PLAYER_SPEED
        self.x = max(self.WIDTH // 2, min(SCREEN_W - self.WIDTH // 2, self.x))

        if keys[self.controls['charge']]:
            self.charging = True
            self.charge   = min(self.charge + 1, CHARGE_MAX)
        else:
            if self.charging and self.charge > 0:
                self._fire_charge()
                if sounds: sounds.play('shoot_charge')
            self.charging = False
            self.charge   = 0

        if keys[self.controls['fire']] and not self.charging:
            if self.shoot_cooldown <= 0:
                self._fire_normal()
                self.shoot_cooldown = 18
                if sounds: sounds.play('shoot')

    def _fire_normal(self):
        self.bullets.append(Bullet(self.x, self.y - self.HEIGHT // 2,
                                   -BULLET_SPEED, self.color, power=1))

    def _fire_charge(self):
        ratio = self.charge / CHARGE_MAX
        power = 1 + int(ratio * 3)
        speed = BULLET_SPEED + ratio * 4
        size  = 4 + int(ratio * 8)
        self.bullets.append(Bullet(self.x, self.y - self.HEIGHT // 2,
                                   -speed, YELLOW, power=power,
                                   size=size, charged=True))
        return ratio

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        for b in self.bullets[:]:
            b.update()
            if b.y < 0:
                self.bullets.remove(b)
        for p in self.particles[:]:
            p['x'] += p['vx']; p['y'] += p['vy']; p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)
        if self.explode_timer > 0:
            self.explode_timer -= 1

    def hit(self):
        if self.invincible > 0:
            return
        self.lives -= 1
        self.invincible = 120
        self._spawn_particles(self.color)
        if self.lives <= 0:
            self.alive = False
            self.explode_timer = 60
            self._spawn_particles(RED, count=30)

    def _spawn_particles(self, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd   = random.uniform(1, 5)
            self.particles.append({
                'x': self.x, 'y': self.y,
                'vx': math.cos(angle) * spd,
                'vy': math.sin(angle) * spd,
                'life': random.randint(20, 50),
                'color': color, 'size': random.randint(2, 5)
            })

    def draw(self, surf):
        for p in self.particles:
            alpha = max(0, p['life'] / 50)
            c = tuple(int(ch * alpha) for ch in p['color'])
            pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), p['size'])
        if not self.alive:
            return
        if self.invincible > 0 and (self.invincible // 6) % 2 == 0:
            return
        cx, cy = int(self.x), int(self.y)
        hw, hh  = self.WIDTH // 2, self.HEIGHT // 2
        pts = [(cx, cy - hh), (cx - hw, cy + hh), (cx + hw, cy + hh)]
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)
        pygame.draw.circle(surf, YELLOW, (cx, cy + hh), 4)
        if self.charging and self.charge > 0:
            ratio = self.charge / CHARGE_MAX
            bar_w = int(self.WIDTH * ratio)
            pygame.draw.rect(surf, YELLOW, (cx - hw, cy + hh + 6, bar_w, 5))
            pygame.draw.rect(surf, WHITE,  (cx - hw, cy + hh + 6, self.WIDTH, 5), 1)
        for b in self.bullets:
            b.draw(surf)

# ── Bullet ─────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, vy, color, power=1, size=4, charged=False):
        self.x = float(x); self.y = float(y)
        self.vy = vy; self.vx = 0.0
        self.color = color; self.power = power
        self.size = size; self.charged = charged

    def update(self):
        self.x += self.vx; self.y += self.vy

    def draw(self, surf):
        if self.charged:
            pygame.draw.circle(surf, WHITE,  (int(self.x), int(self.y)), self.size + 2)
            pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(surf, ORANGE, (int(self.x), int(self.y)), self.size - 2)
        else:
            pygame.draw.rect(surf, self.color,
                             (int(self.x) - 2, int(self.y) - self.size, 4, self.size * 2))

# ── Alien ──────────────────────────────────────────────────
ALIEN_TYPES = {
    0: (GREEN,  10, 1, 'A'),
    1: (CYAN,   20, 1, 'B'),
    2: (PURPLE, 30, 2, 'C'),
}

class Alien:
    SIZE = 32
    def __init__(self, col, row, x, y):
        self.col = col; self.row = row
        self.x = float(x); self.y = float(y)
        self.atype = 2 if row == ALIEN_ROWS-1 else (1 if row == ALIEN_ROWS-2 else 0)
        color, self.points, self.hp, self.shape = ALIEN_TYPES[self.atype]
        self.color = color; self.alive = True
        self.anim = 0; self.anim_timer = 0; self.hit_flash = 0

    def update(self):
        self.anim_timer += 1
        if self.anim_timer >= 30:
            self.anim = 1 - self.anim; self.anim_timer = 0
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        s = self.SIZE // 2
        color = WHITE if self.hit_flash > 0 else self.color
        if self.shape == 'A':
            pts = [(cx, cy-s),(cx-s, cy),(cx-s+6, cy+s),(cx+s-6, cy+s),(cx+s, cy)]
            pygame.draw.polygon(surf, color, pts)
            ey = cy - 4 + self.anim * 3
            pygame.draw.circle(surf, BLACK, (cx-8, ey), 4)
            pygame.draw.circle(surf, BLACK, (cx+8, ey), 4)
            for tx in [-12,-4,4,12]:
                pygame.draw.line(surf, color, (cx+tx, cy+s), (cx+tx, cy+s+6+self.anim*4), 2)
        elif self.shape == 'B':
            pygame.draw.ellipse(surf, color, (cx-s, cy-s//2, self.SIZE, s))
            off = self.anim * 5
            pygame.draw.line(surf, color, (cx-s, cy), (cx-s-8, cy-off), 3)
            pygame.draw.line(surf, color, (cx+s, cy), (cx+s+8, cy-off), 3)
            pygame.draw.circle(surf, BLACK, (cx-8, cy-4), 3)
            pygame.draw.circle(surf, BLACK, (cx+8, cy-4), 3)
        elif self.shape == 'C':
            pygame.draw.circle(surf, color, (cx, cy), s)
            pygame.draw.circle(surf, BLACK, (cx-7, cy-3), 4)
            pygame.draw.circle(surf, BLACK, (cx+7, cy-3), 4)
            for i, tx in enumerate([-12,-6,0,6,12]):
                w = (self.anim*5) if i%2==0 else -(self.anim*5)
                pygame.draw.line(surf, color, (cx+tx, cy+s-4), (cx+tx+w//2, cy+s+10), 2)
        if self.hp > 1:
            for i in range(self.hp):
                pygame.draw.circle(surf, YELLOW, (cx-6+i*8, cy+s+14), 3)

# ── Alien bullet ───────────────────────────────────────────
class AlienBullet:
    def __init__(self, x, y, targeted=False, tx=0):
        self.x = float(x); self.y = float(y)
        self.vy = 4.5; self.vx = 0.0
        if targeted:
            dx = tx - x
            self.vx = (dx / max(abs(dx), 1)) * 2

    def update(self, gravity_active=False, gravity_cx=0):
        self.x += self.vx; self.y += self.vy
        if gravity_active:
            self.vx += (gravity_cx - self.x) * 0.004

    def draw(self, surf):
        pygame.draw.rect(surf, RED, (int(self.x)-2, int(self.y), 4, 12))

# ── Shield ─────────────────────────────────────────────────
class Shield:
    BLOCK_SIZE = 8
    SHAPE = [
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,0,0,0,0,0,1,1,1],
        [1,1,1,0,0,0,0,0,1,1,1],
    ]
    def __init__(self, cx, cy):
        bs = self.BLOCK_SIZE
        cols = len(self.SHAPE[0]); rows = len(self.SHAPE)
        ox = cx - (cols*bs)//2; oy = cy - (rows*bs)//2
        self.blocks = []
        for r, row in enumerate(self.SHAPE):
            for c, cell in enumerate(row):
                if cell:
                    self.blocks.append(pygame.Rect(ox+c*bs, oy+r*bs, bs, bs))

    def hit(self, rect):
        for b in self.blocks[:]:
            if b.colliderect(rect):
                self.blocks.remove(b); return True
        return False

    def draw(self, surf):
        for b in self.blocks:
            pygame.draw.rect(surf, DARK_GREEN, b)
            pygame.draw.rect(surf, GREEN, b, 1)

# ── Gravity wave ───────────────────────────────────────────
class GravityWave:
    def __init__(self):
        self.active = False; self.timer = 0; self.duration = 0
        self.cx = SCREEN_W//2; self.radius = 0; self.warning = 0
        self.just_triggered = False

    def update(self):
        self.just_triggered = False
        self.timer += 1
        if self.timer >= GRAVITY_INTERVAL - 120:
            self.warning = (self.timer // 15) % 2
        if self.timer >= GRAVITY_INTERVAL:
            self.active = True; self.duration = GRAVITY_DURATION
            self.radius = 0; self.timer = 0; self.warning = 0
            self.cx = random.randint(200, SCREEN_W-200)
            self.just_triggered = True
        if self.active:
            self.radius += 8; self.duration -= 1
            if self.duration <= 0:
                self.active = False

    def draw(self, surf):
        if self.active:
            alpha = max(0, self.duration / GRAVITY_DURATION)
            r, g, bl = int(80*alpha), int(180*alpha), int(255*alpha)
            for ring in range(3):
                rad = self.radius - ring*25
                if rad > 0:
                    pygame.draw.circle(surf, (r,g,bl), (self.cx, SCREEN_H//2), rad, 2)
            pygame.draw.line(surf, CYAN, (self.cx,0), (self.cx, SCREEN_H), 1)
        elif self.warning:
            pygame.draw.line(surf, (60,60,200), (self.cx,0), (self.cx, SCREEN_H), 2)

# ── Icon helpers ───────────────────────────────────────────
def draw_planet_icon(surf, cx, cy, r=10):
    pygame.draw.circle(surf, (100,160,255), (cx,cy), r)
    pygame.draw.ellipse(surf, (180,220,255), (cx-r-5, cy-3, (r+5)*2, 6), 2)

def draw_bolt_icon(surf, cx, cy):
    pts = [(cx,cy-10),(cx+5,cy-2),(cx+1,cy-2),(cx+6,cy+10),(cx-1,cy+2),(cx-5,cy+2)]
    pygame.draw.polygon(surf, YELLOW, pts)

def draw_alien_icon(surf, cx, cy):
    pygame.draw.circle(surf, GREEN, (cx,cy), 8)
    pygame.draw.circle(surf, BLACK, (cx-3,cy-1), 2)
    pygame.draw.circle(surf, BLACK, (cx+3,cy-1), 2)
    for tx in [-6,-2,2,6]:
        pygame.draw.line(surf, GREEN, (cx+tx,cy+8), (cx+tx,cy+13), 2)

# ── HUD ────────────────────────────────────────────────────
def draw_hud(surf, font, font_sm, players, wave, gravity, two_player):
    pygame.draw.rect(surf, (20,20,20), (0, SCREEN_H-62, SCREEN_W, 62))
    if two_player:
        pygame.draw.line(surf, GRAY, (SCREEN_W//2, SCREEN_H-60), (SCREEN_W//2, SCREEN_H), 1)
        p1, p2 = players
        # P1 left
        p1_score = font.render(f"{p1.name}: {p1.score}", True, p1.color)
        surf.blit(p1_score, (10, SCREEN_H-55))
        for i in range(p1.lives):
            _draw_mini_ship(surf, 10+i*22, SCREEN_H-25, p1.color)
        # P2 right
        p2_score = font.render(f"{p2.name}: {p2.score}", True, p2.color)
        surf.blit(p2_score, (SCREEN_W - p2_score.get_width()-10, SCREEN_H-55))
        for i in range(p2.lives):
            _draw_mini_ship(surf, SCREEN_W-20-i*22, SCREEN_H-25, p2.color)
    else:
        p1 = players[0]
        p1_score = font.render(f"{p1.name}: {p1.score}", True, p1.color)
        surf.blit(p1_score, (10, SCREEN_H-55))
        for i in range(p1.lives):
            _draw_mini_ship(surf, 10+i*22, SCREEN_H-25, p1.color)

    wave_txt = font.render(f"WAVE {wave}", True, WHITE)
    surf.blit(wave_txt, (SCREEN_W//2 - wave_txt.get_width()//2, SCREEN_H-55))

    if gravity.warning:
        warn = font_sm.render("!! GRAVITY WAVE INCOMING !!", True, CYAN)
        surf.blit(warn, (SCREEN_W//2 - warn.get_width()//2, 8))

    for p in players:
        if p.alive and p.charging:
            ratio = p.charge / CHARGE_MAX
            left  = (p.x < SCREEN_W//2)
            label = font_sm.render(f"CHARGE {int(ratio*100)}%", True, YELLOW)
            xpos  = 10 if left else SCREEN_W - label.get_width()-10
            surf.blit(label, (xpos, SCREEN_H-80))

def _draw_mini_ship(surf, x, y, color):
    pygame.draw.polygon(surf, color, [(x,y-8),(x-8,y+4),(x+8,y+4)])

# ── Rounded rect helper ────────────────────────────────────
def draw_box(surf, rect, fill, border, radius=12, border_w=2):
    pygame.draw.rect(surf, fill,   rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=radius)

# ── Main menu ──────────────────────────────────────────────
def draw_main_menu(surf, font_big, font, font_sm, selected):
    title = font_big.render("SPACE INVADERS +", True, GREEN)
    surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 80))

    sub = font_sm.render("A game about defending Earth — with a friend or alone", True, GRAY)
    surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 148))

    options = ["1 PLAYER", "2 PLAYERS"]
    for i, opt in enumerate(options):
        active = (i == selected)
        bx = SCREEN_W//2 - 160
        by = 220 + i*80
        color  = CYAN   if active else DIM_GRAY
        tcol   = WHITE  if active else GRAY
        draw_box(surf, pygame.Rect(bx, by, 320, 55), (10,10,30) if active else (10,10,20), color)
        txt = font.render(opt, True, tcol)
        surf.blit(txt, (SCREEN_W//2 - txt.get_width()//2, by+14))
        if active:
            pygame.draw.polygon(surf, CYAN,
                [(bx-20, by+27),(bx-8, by+20),(bx-8, by+34)])

    # Features
    feature_y = 420
    features  = [
        ("GRAVITY WAVES  -  bullets bend mid-flight", "planet"),
        ("CHARGE SHOT    -  hold SHIFT for power blast","bolt"),
        ("ALIEN MUTATIONS - tougher aliens each wave",  "alien"),
    ]
    for i, (text, icon) in enumerate(features):
        fy = feature_y + i*36
        ix = SCREEN_W//2 - 220
        if icon == "planet": draw_planet_icon(surf, ix, fy+8)
        elif icon == "bolt":  draw_bolt_icon(surf, ix, fy+8)
        elif icon == "alien": draw_alien_icon(surf, ix, fy+8)
        ft = font_sm.render(text, True, YELLOW)
        surf.blit(ft, (ix+22, fy))

    nav = font_sm.render("UP/DOWN to select   SPACE/ENTER to confirm   ESC to quit", True, GRAY)
    surf.blit(nav, (SCREEN_W//2 - nav.get_width()//2, SCREEN_H-30))

# ── Name entry screen ──────────────────────────────────────
def draw_name_entry(surf, font_big, font, font_sm, two_player,
                    names, active_field, tick):
    title = font_big.render("ENTER YOUR NAME", True, CYAN)
    surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 100))

    fields = 2 if two_player else 1
    colors = [LIGHT_BLUE, PINK]
    labels = ["Player 1 Name", "Player 2 Name"]

    for i in range(fields):
        fy     = 230 + i*130
        active = (i == active_field)
        color  = colors[i]
        border = WHITE if active else GRAY
        lbl    = font.render(labels[i], True, color)
        surf.blit(lbl, (SCREEN_W//2 - lbl.get_width()//2, fy))
        # Input box
        bx = SCREEN_W//2 - 200
        draw_box(surf, pygame.Rect(bx, fy+36, 400, 50),
                 (15,15,35) if active else (10,10,20), border)
        name_txt = font.render(names[i], True, WHITE)
        surf.blit(name_txt, (bx+16, fy+48))
        # Blinking cursor
        if active and (tick//30)%2 == 0:
            cur_x = bx + 16 + name_txt.get_width() + 2
            pygame.draw.rect(surf, WHITE, (cur_x, fy+50, 2, 26))
        # Char count
        cnt = font_sm.render(f"{len(names[i])}/{MAX_NAME_LEN}", True, GRAY)
        surf.blit(cnt, (bx+370, fy+50))

    if two_player and active_field < fields-1:
        hint = font_sm.render("Press ENTER to continue to next player", True, GRAY)
    else:
        hint = font_sm.render("Press ENTER to start the game!", True, GREEN)
    surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H-80))

    back = font_sm.render("ESC = back to menu", True, GRAY)
    surf.blit(back, (SCREEN_W//2 - back.get_width()//2, SCREEN_H-50))

# ── Game over screen ───────────────────────────────────────
def draw_game_over(surf, font_big, font, font_sm, players, wave, two_player):
    surf.fill(BLACK)
    go = font_big.render("GAME OVER", True, RED)
    surf.blit(go, (SCREEN_W//2 - go.get_width()//2, 140))

    wt = font.render(f"Reached Wave {wave}", True, WHITE)
    surf.blit(wt, (SCREEN_W//2 - wt.get_width()//2, 220))

    if two_player:
        p1, p2 = players
        t1 = font.render(f"{p1.name}: {p1.score}", True, p1.color)
        t2 = font.render(f"{p2.name}: {p2.score}", True, p2.color)
        surf.blit(t1, (SCREEN_W//2 - t1.get_width()//2, 290))
        surf.blit(t2, (SCREEN_W//2 - t2.get_width()//2, 330))
        total = font.render(f"Combined Score: {p1.score+p2.score}", True, YELLOW)
        surf.blit(total, (SCREEN_W//2 - total.get_width()//2, 390))
        wc = p1.color if p1.score >= p2.score else p2.color
        wn = p1.name  if p1.score >= p2.score else p2.name
        win = font.render(f"*  {wn} wins!  *", True, wc)
        surf.blit(win, (SCREEN_W//2 - win.get_width()//2, 450))
    else:
        p = players[0]
        st = font.render(f"Score: {p.score}", True, YELLOW)
        surf.blit(st, (SCREEN_W//2 - st.get_width()//2, 300))

    r = font_sm.render("SPACE/ENTER = Play Again     ESC = Main Menu", True, GRAY)
    surf.blit(r, (SCREEN_W//2 - r.get_width()//2, SCREEN_H-60))

# ── Wave banner ────────────────────────────────────────────
def draw_wave_banner(surf, font_big, wave):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0,0,0,120))
    surf.blit(ov, (0,0))
    txt = font_big.render(f"WAVE  {wave}", True, YELLOW)
    surf.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2-40))

# ── Quit confirm ───────────────────────────────────────────
def draw_quit_confirm(surf, font_big, font):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0,0,0,180))
    surf.blit(ov, (0,0))
    bx, by, bw, bh = SCREEN_W//2-250, SCREEN_H//2-110, 500, 220
    draw_box(surf, pygame.Rect(bx, by, bw, bh), (30,30,50), CYAN)
    q = font_big.render("QUIT TO MENU?", True, WHITE)
    surf.blit(q, (SCREEN_W//2 - q.get_width()//2, by+25))
    yes = font.render("[Y]  Yes, go to main menu", True, RED)
    no  = font.render("[N]  No, resume game",      True, GREEN)
    surf.blit(yes, (SCREEN_W//2 - yes.get_width()//2, by+105))
    surf.blit(no,  (SCREEN_W//2 - no.get_width()//2,  by+150))

# ── Build helpers ──────────────────────────────────────────
def build_aliens(wave):
    aliens = []
    start_x = 80; start_y = 80 + min(wave-1,4)*5
    for row in range(ALIEN_ROWS):
        for col in range(ALIEN_COLS):
            a = Alien(col, row,
                      start_x + col*ALIEN_H_GAP,
                      start_y + row*ALIEN_V_GAP)
            a.hp += max(0, (wave-1)//2)
            aliens.append(a)
    return aliens

def build_shields():
    spacing = SCREEN_W // (SHIELD_COUNT+1)
    return [Shield(spacing*(i+1), SCREEN_H-145) for i in range(SHIELD_COUNT)]

# ── Main ───────────────────────────────────────────────────
async def main():
    pygame.init()
    screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Space Invaders+")
    clock    = pygame.time.Clock()
    sounds   = SoundManager()

    font_big = pygame.font.SysFont("monospace", 52, bold=True)
    font     = pygame.font.SysFont("monospace", 22)
    font_sm  = pygame.font.SysFont("monospace", 16)

    p1_controls = {'left': pygame.K_a,     'right': pygame.K_d,
                   'fire': pygame.K_SPACE, 'charge': pygame.K_LSHIFT}
    p2_controls = {'left': pygame.K_LEFT,  'right': pygame.K_RIGHT,
                   'fire': pygame.K_RETURN,'charge': pygame.K_RSHIFT}

    stars = [Star() for _ in range(120)]

    # ── State variables ──
    state       = 'menu'
    prev_state  = 'menu'
    menu_sel    = 0          # 0=1P, 1=2P
    two_player  = False
    name_field  = 0
    names       = ["Player1", "Player2"]
    tick        = 0
    cheat_p1    = 0    # counts V presses for P1
    cheat_p2    = 0    # counts P presses for P2

    players = []
    aliens  = []; shields = []; alien_bullets = []
    alien_dir = 1; alien_speed = 0.6; wave = 1
    alien_shoot_timer = 0; wave_banner_timer = 0
    gravity = GravityWave()

    def start_game():
        nonlocal players, aliens, shields, alien_bullets, \
                 alien_dir, alien_speed, wave, alien_shoot_timer, \
                 wave_banner_timer, gravity, state
        p1 = Player(SCREEN_W//4 if two_player else SCREEN_W//2,
                    LIGHT_BLUE, p1_controls, names[0])
        if two_player:
            p2 = Player(3*SCREEN_W//4, PINK, p2_controls, names[1])
            players = [p1, p2]
        else:
            players = [p1]
        wave = 1; alien_dir = 1; alien_speed = 0.6
        aliens = build_aliens(wave); shields = build_shields()
        alien_bullets = []; alien_shoot_timer = 0
        wave_banner_timer = 90; gravity = GravityWave()
        cheat_p1 = 0; cheat_p2 = 0
        state = 'playing'

    while True:
        clock.tick(FPS)
        tick += 1

        # ── Events ──────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:

                # ── Menu navigation ──
                if state == 'menu':
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_sel = (menu_sel - 1) % 2
                        sounds.play('menu_move')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_sel = (menu_sel + 1) % 2
                        sounds.play('menu_move')
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        two_player = (menu_sel == 1)
                        name_field = 0
                        names      = ["Player1", "Player2"]
                        state      = 'name_entry'
                        sounds.play('menu_select')
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

                # ── Name entry ──
                elif state == 'name_entry':
                    if event.key == pygame.K_ESCAPE:
                        state = 'menu'
                    elif event.key == pygame.K_RETURN:
                        if not two_player or name_field == 1:
                            sounds.play('menu_select')
                            start_game()
                        else:
                            name_field = 1
                            sounds.play('menu_move')
                    elif event.key == pygame.K_BACKSPACE:
                        names[name_field] = names[name_field][:-1]
                    else:
                        ch = event.unicode
                        if ch.isprintable() and len(names[name_field]) < MAX_NAME_LEN:
                            names[name_field] += ch

                # ── Quit confirm ──
                elif state == 'quit_confirm':
                    if event.key == pygame.K_y:
                        state = 'menu'
                        sounds.play('menu_select')
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        state = prev_state

                # ── Game over ──
                elif state == 'gameover':
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        sounds.play('menu_select')
                        start_game()
                    elif event.key == pygame.K_ESCAPE:
                        state = 'menu'

                # ── Playing ──
                elif state == 'playing':
                    if event.key == pygame.K_ESCAPE:
                        prev_state = 'playing'
                        state      = 'quit_confirm'
                    # Cheat codes — V x3 refills P1 lives, P x3 refills P2 lives
                    if event.key == pygame.K_v:
                        cheat_p1 += 1
                        if cheat_p1 >= 3:
                            players[0].lives = 3
                            players[0].alive = True
                            cheat_p1 = 0
                            sounds.play('wave_clear')
                    elif event.key != pygame.K_v:
                        cheat_p1 = 0
                    if event.key == pygame.K_p:
                        cheat_p2 += 1
                        if cheat_p2 >= 3 and len(players) > 1:
                            players[1].lives = 3
                            players[1].alive = True
                            cheat_p2 = 0
                            sounds.play('wave_clear')
                    elif event.key != pygame.K_p:
                        cheat_p2 = 0

        keys = pygame.key.get_pressed()

        # ── Background ──────────────────────────────────────
        screen.fill(BLACK)
        for star in stars:
            star.update(); star.draw(screen)

        # ════════════════════════════════════════════════════
        if state == 'menu':
            draw_main_menu(screen, font_big, font, font_sm, menu_sel)

        # ════════════════════════════════════════════════════
        elif state == 'name_entry':
            draw_name_entry(screen, font_big, font, font_sm,
                            two_player, names, name_field, tick)

        # ════════════════════════════════════════════════════
        elif state == 'playing':
            if wave_banner_timer > 0:
                wave_banner_timer -= 1

            # Input & update
            for p in players:
                p.handle_input(keys, sounds)
                p.update()

            # Gravity
            gravity.update()
            if gravity.just_triggered:
                sounds.play('gravity')
            gravity.draw(screen)

            # Alien movement
            alive_aliens = [a for a in aliens if a.alive]
            if alive_aliens:
                rightmost = max(a.x for a in alive_aliens)
                leftmost  = min(a.x for a in alive_aliens)
                moved_down = False
                if alien_dir == 1 and rightmost >= SCREEN_W-50:
                    alien_dir = -1; moved_down = True
                elif alien_dir == -1 and leftmost <= 50:
                    alien_dir = 1;  moved_down = True

                for a in alive_aliens:
                    a.x += alien_dir * alien_speed
                    if moved_down: a.y += ALIEN_DROP
                    a.update()

                # Alien shooting
                alien_shoot_timer -= 1
                if alien_shoot_timer <= 0:
                    alien_shoot_timer = max(25, 80 - wave*5)
                    shooter  = random.choice(alive_aliens)
                    alive_ps = [p for p in players if p.alive]
                    targeted = wave >= 3 and random.random() < 0.4 and alive_ps
                    if targeted:
                        target = random.choice(alive_ps)
                        ab = AlienBullet(shooter.x, shooter.y+20, True, target.x)
                    else:
                        ab = AlienBullet(shooter.x, shooter.y+20)
                    alien_bullets.append(ab)

                if max(a.y for a in alive_aliens) >= SCREEN_H-100:
                    sounds.play('game_over')
                    state = 'gameover'

            # Update alien bullets
            for ab in alien_bullets[:]:
                ab.update(gravity.active, gravity.cx)
                if ab.y > SCREEN_H:
                    alien_bullets.remove(ab)

            # Player bullets vs shields & aliens
            for player in players:
                for b in player.bullets[:]:
                    brect = pygame.Rect(b.x-b.size, b.y-b.size, b.size*2, b.size*2)
                    hit_sh = False
                    for sh in shields:
                        if sh.hit(brect):
                            player.bullets.remove(b); hit_sh = True; break
                    if hit_sh: continue
                    for a in alive_aliens:
                        arect = pygame.Rect(a.x-a.SIZE//2, a.y-a.SIZE//2, a.SIZE, a.SIZE)
                        if brect.colliderect(arect):
                            a.hp -= b.power; a.hit_flash = 8
                            sounds.play('alien_hit')
                            if a.hp <= 0:
                                a.alive = False
                                player.score += a.points * wave
                            if b in player.bullets:
                                player.bullets.remove(b)
                            break

            # Alien bullets vs shields & players
            for ab in alien_bullets[:]:
                abrect = pygame.Rect(ab.x-3, ab.y, 6, 12)
                hit_sh = False
                for sh in shields:
                    if sh.hit(abrect):
                        alien_bullets.remove(ab); hit_sh = True; break
                if hit_sh: continue
                for p in players:
                    if p.alive:
                        prect = pygame.Rect(p.x-p.WIDTH//2, p.y-p.HEIGHT//2,
                                            p.WIDTH, p.HEIGHT)
                        if abrect.colliderect(prect):
                            p.hit()
                            sounds.play('player_hit')
                            if ab in alien_bullets:
                                alien_bullets.remove(ab)
                            break

            # Draw
            for sh in shields: sh.draw(screen)
            for a in alive_aliens: a.draw(screen)
            for ab in alien_bullets: ab.draw(screen)
            for p in players: p.draw(screen)
            draw_hud(screen, font, font_sm, players, wave, gravity, two_player)

            if wave_banner_timer > 0:
                draw_wave_banner(screen, font_big, wave)

            # Wave clear
            if not alive_aliens:
                wave += 1; alien_speed = 0.6 + wave*0.12
                aliens = build_aliens(wave); shields = build_shields()
                alien_bullets.clear(); alien_shoot_timer = 0
                wave_banner_timer = 90; gravity.timer = 0
                sounds.play('wave_clear')

            # Game over
            if all(not p.alive for p in players):
                sounds.play('game_over')
                state = 'gameover'

        # ════════════════════════════════════════════════════
        elif state == 'gameover':
            draw_game_over(screen, font_big, font, font_sm,
                           players, wave, two_player)

        # ════════════════════════════════════════════════════
        elif state == 'quit_confirm':
            draw_quit_confirm(screen, font_big, font)

        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())
