import os
import math
import time
import pygame
import random
import multiprocessing


REF_W, REF_H = 800, 480
MAX_W, MAX_H = 1920, 1080
FPS = 60

COR_FUNDO = (10, 10, 10)
COR_TEXTO_ZZZ = (100, 200, 255)


class VegapunkFace:
    def __init__(self, cmd_queue):
        self.cmd_queue = cmd_queue
        self.appearances = {}
        self.current_mode = None
        self.state = "sleeping"

        self._init_display()
        self._init_animation_state()

    def _init_display(self):
        pygame.init()
        pygame.font.init()

        sw, sh = pygame.display.Info().current_w, pygame.display.Info().current_h
        self.W, self.H, flags = self._resolve_display_mode(sw, sh)

        try:
            self.tela = pygame.display.set_mode((self.W, self.H), flags)
        except pygame.error:
            self.tela = pygame.display.set_mode((self.W, self.H), pygame.NOFRAME)

        pygame.display.set_caption("Vegapunk")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()

        self.scale = min(self.W / REF_W, self.H / REF_H)
        self.cx, self.cy = self.W // 2, self.H // 2

        font_size = max(20, int(60 * self.scale))
        try:
            self.fonte_zz = pygame.font.SysFont("arial", font_size, bold=True)
        except Exception:
            self.fonte_zz = pygame.font.Font(None, font_size)

    def _resolve_display_mode(self, sw, sh):
        if sw <= MAX_W and sh <= MAX_H:
            return sw, sh, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        return MAX_W, MAX_H, pygame.NOFRAME

    def _init_animation_state(self):
        self.proximo_piscar = time.time() + random.uniform(2, 6)
        self.piscando = False
        self.tempo_inicio_pisque = 0
        self.altura_pisque = 0
        self.offset_boca_y = 0
        self.tempo_animacao = 0
        self.iris_offset_x = 0
        self.direcao_olhar = 1
        self.tempo_zz = 0

    def s(self, val):
        return val * self.scale

    def run(self):
        rodando = True
        while rodando:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    rodando = False

            if not self._process_commands():
                rodando = False

            self._update_animation()
            self._render_frame()
            self.clock.tick(FPS)

        pygame.quit()

    def _process_commands(self):
        while not self.cmd_queue.empty():
            try:
                cmd_type, value = self.cmd_queue.get_nowait()
            except Exception:
                break

            if cmd_type == "appearances":
                self.appearances = value
            elif cmd_type == "mode" and value in self.appearances:
                self.current_mode = value
            elif cmd_type == "state":
                self.state = value
            elif cmd_type == "quit":
                return False

        return True

    def _update_animation(self):
        ap = self._get_appearance()

        if ap is None or self.state == "sleeping":
            self.tempo_zz += 0.05
            return

        if self.state in ("listening", "idle"):
            self._update_blinking()
        elif self.state == "speaking":
            self._update_speaking()
        elif self.state == "thinking":
            self._update_thinking()

    def _update_blinking(self):
        agora = time.time()

        if not self.piscando and agora > self.proximo_piscar:
            self.piscando = True
            self.tempo_inicio_pisque = agora

        if self.piscando:
            progresso = (agora - self.tempo_inicio_pisque) / 0.15
            if progresso < 0.5:
                self.altura_pisque = progresso * 2 * 100
            elif progresso < 1.0:
                self.altura_pisque = (1.0 - progresso) * 2 * 100
            else:
                self.altura_pisque = 0
                self.piscando = False
                self.proximo_piscar = agora + random.uniform(2, 6)
        else:
            self.altura_pisque = 0

        self.iris_offset_x = 0
        self.offset_boca_y = 0

    def _update_speaking(self):
        self.piscando = False
        self.altura_pisque = 0
        self.tempo_animacao += 0.6
        self.offset_boca_y = math.sin(self.tempo_animacao) * 12

    def _update_thinking(self):
        self.piscando = False
        self.altura_pisque = 30
        self.iris_offset_x += 3 * self.direcao_olhar
        if abs(self.iris_offset_x) > 30:
            self.direcao_olhar *= -1
        self.offset_boca_y = 0

    def _get_appearance(self):
        if self.current_mode and self.current_mode in self.appearances:
            return self.appearances[self.current_mode]
        return None

    def _render_frame(self):
        ap = self._get_appearance()

        if ap is None or self.state == "sleeping":
            self._render_sleeping()
        else:
            self._render_active_face(ap)

        pygame.display.flip()

    def _render_sleeping(self):
        self.tela.fill(COR_FUNDO)
        draw_sleeping_overlay(
            self.tela, self.W, self.H, self.cx, self.cy,
            self.fonte_zz, self.tempo_zz, self.s,
        )

    def _render_active_face(self, ap):
        bg = ap.get('background_color', COR_FUNDO)
        self.tela.fill(bg)

        if ap['has_mouth']:
            self._render_mouth(ap)

        self._render_eyes(ap)

    def _render_eyes(self, ap):
        s = self.s
        wo = s(ap['eye_width'])
        ho = s(ap['eye_height'])
        dist = s(ap['eye_distance'])
        yo = self.cy + s(ap['eye_y_offset'])
        ir = s(ap['iris_radius'])
        iox = s(self.iris_offset_x)

        bp = s(ap['base_eyelid'])
        hp = max(s(self.altura_pisque), bp)
        if self.state == "thinking":
            hp += s(20)

        eye_color = ap.get('eye_color', (255, 255, 255))
        iris_color = ap.get('iris_color', (0, 0, 0))
        eyelid_color = ap['eyelid_color']

        for side in (-1, 1):
            draw_eye(
                self.tela,
                self.cx + side * dist - wo / 2, yo,
                wo, ho, iox, ir,
                iris_color, eye_color,
                hp, eyelid_color,
            )

    def _render_mouth(self, ap):
        draw_mouth(self.tela, self.W, self.H, ap['mouth_color'], self.offset_boca_y, self.s)



def draw_eye(surface, x, y, w, h, iris_ox, iris_r, iris_color, eye_color, palp_h, palp_cor):
    wi, hi = int(w), int(h)
    if wi < 4 or hi < 4:
        return

    eye_surf = pygame.Surface((wi, hi), pygame.SRCALPHA)
    pygame.draw.ellipse(eye_surf, eye_color, (0, 0, wi, hi))

    ecx, ecy = wi // 2, hi // 2
    pygame.draw.circle(eye_surf, iris_color, (ecx + int(iris_ox), ecy), max(2, int(iris_r)))

    if palp_h > 0:
        _apply_eyelid(eye_surf, wi, hi, palp_h, palp_cor)

    surface.blit(eye_surf, (int(x), int(y)))


def _apply_eyelid(eye_surf, wi, hi, palp_h, palp_cor):
    palp_surf = pygame.Surface((wi, hi), pygame.SRCALPHA)
    pygame.draw.rect(palp_surf, palp_cor, (0, 0, wi, min(int(palp_h), hi)))

    mask = pygame.Surface((wi, hi), pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), (0, 0, wi, hi))
    palp_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    eye_surf.blit(palp_surf, (0, 0))


def draw_mouth(surface, w_total, mouth_y, mouth_color, offset_y, scale_fn):
    ab = scale_fn(130)
    y = (mouth_y - ab) + scale_fn(offset_y)

    pygame.draw.rect(surface, mouth_color, (0, int(y), w_total, int(ab + scale_fn(250))))

    hc = scale_fn(120)
    pygame.draw.ellipse(surface, mouth_color,
                        (-int(scale_fn(20)), int(y - hc / 2), w_total + int(scale_fn(40)), int(hc)))


def draw_sleeping_overlay(surface, w, h, cx, cy, font, tempo_zz, scale_fn):
    veu = pygame.Surface((w, h))
    veu.fill((0, 0, 0))
    surface.blit(veu, (0, 0))

    txt = font.render("ZzzZzzzzZzzz", True, COR_TEXTO_ZZZ)
    oy = scale_fn(math.sin(tempo_zz) * 20)
    rot = math.cos(tempo_zz * 0.5) * 5
    tr = pygame.transform.rotate(txt, rot)
    r = tr.get_rect(center=(cx, int(cy + oy)))
    surface.blit(tr, r)


def _face_entry(q):
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
    VegapunkFace(q).run()
    

def start_face():
    q = multiprocessing.Queue(maxsize=50)
    p = multiprocessing.Process(target=_face_entry, args=(q,), daemon=True, name="vegapunk-face")
    p.start()
    print(f"Face UI iniciada (PID: {p.pid})")
    return q


def send_face(queue, cmd_type, value=None):
    if queue is None:
        return
    try:
        queue.put_nowait((cmd_type, value))
    except Exception:
        pass
