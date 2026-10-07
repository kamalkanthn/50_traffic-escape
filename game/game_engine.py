import pygame
import random
from game.player import Player,LANE_W
from game.traffic import Car,make_car
from game.river import River,RIVER_TOP,RIVER_H
from game.highscores import load_scores,save_scores,add_score
from game.daynight import phase,draw_night,draw_headlights

LANES=8
WIDTH=LANES*LANE_W
HEIGHT=600
FPS=60
BG=(60,60,60)
START_LIVES=3
INVULN_FRAMES=90  # ~1.5s of protection after being hit

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Traffic Escape")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("monospace",24,bold=True)
        self.big_font=pygame.font.SysFont("monospace",44,bold=True)
        self.high_scores=load_scores()  # loaded once at start-up; survives R restarts
        self.reset()

    def reset(self):
        self.start_pos=(WIDTH//2,HEIGHT-80)
        self.player=Player(*self.start_pos)
        self.lives=START_LIVES
        self.invuln=0
        self.river=River(WIDTH)
        self.cars=[]
        self.timer=0
        self.spawn_interval=50
        self.speed=3
        self.score=0
        self.game_over=False
        self.won=False
        self.score_rank=None  # where this run's score landed in the table (None = not in top 5)
        self.cycle_start=pygame.time.get_ticks()  # day/night clock restarts (in daylight) with every new run
        self.night=False
        self.darkness=0.0  # 0 = full day, 1 = full night

    def handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r: self.reset()
        return True

    def update(self):
        if self.game_over or self.won: return
        # day/night follows real elapsed milliseconds, so it doesn't depend on the frame rate
        self.night,self.darkness=phase(pygame.time.get_ticks()-self.cycle_start)
        keys=pygame.key.get_pressed()
        self.player.move(keys,0,WIDTH)
        self.timer+=1
        if self.timer>=self.spawn_interval:
            lane=random.randint(0,LANES-1)
            self.cars.append(make_car(lane,HEIGHT,self.speed))
            self.timer=0
            self.spawn_interval=max(22,self.spawn_interval-0.2)
        if self.invuln>0: self.invuln-=1
        for c in self.cars:
            c.update()
        # at most ONE life is lost per frame, and none while invulnerable
        if self.invuln==0 and any(self.car_hits_player(c) for c in self.cars):
            self.lose_life()
        self.update_river()
        self.cars=[c for c in self.cars if not c.off_screen(HEIGHT)]
        self.score+=1
        if self.score%300==0: self.speed=min(10,self.speed+0.5)
        if self.player.rect.top<=10:
            self.won=True
        if self.game_over or self.won:
            self.finish_run()

    def car_hits_player(self,c):
        # cars run underneath the river, so overlap that lies inside the river band doesn't count
        if not c.rect.colliderect(self.player.rect): return False
        o=c.rect.clip(self.player.rect)
        return o.top<RIVER_TOP or o.bottom>RIVER_TOP+RIVER_H

    def update_river(self):
        if self.game_over: return
        # the log the player is standing on (looked up before the logs move this frame)
        log=self.river.log_at(self.player.rect.center)
        self.river.update()
        if log:
            # ride the log, but never leave the screen sideways
            r=self.player.rect
            r.x=max(0,min(WIDTH-r.width,r.x+log.speed))
        # over the water with no log underneath -> fell in (costs a life, no invulnerability exemption)
        centre=self.player.rect.center
        if self.river.contains(centre) and not self.river.log_at(centre):
            self.lose_life()

    def lose_life(self):
        self.lives-=1
        if self.lives<=0:
            self.lives=0
            self.game_over=True
        else:
            self.player.respawn(*self.start_pos)
            self.invuln=INVULN_FRAMES

    def finish_run(self):
        # runs exactly once per run: update() returns early on every frame after game_over / won
        self.high_scores,self.score_rank=add_score(self.high_scores,self.score//10)
        if self.score_rank is not None:
            save_scores(self.high_scores)

    def draw(self):
        self.screen.fill(BG)
        # road markings
        for i in range(LANES+1):
            pygame.draw.line(self.screen,(100,100,100),(i*LANE_W,0),(i*LANE_W,HEIGHT),2)
        for y in range(0,HEIGHT,60):
            for i in range(LANES):
                pygame.draw.rect(self.screen,(200,200,100),pygame.Rect(i*LANE_W+LANE_W//2-3,y,6,30))
        # sidewalks
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,HEIGHT-50,WIDTH,50))
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,0,WIDTH,30))
        for c in self.cars: c.draw(self.screen)
        self.river.draw(self.screen)  # drawn over the cars: they pass underneath it
        # blink the player while invulnerable after a hit
        show_player=self.invuln==0 or (self.invuln//6)%2==0
        if show_player:
            self.player.draw(self.screen)
        if self.darkness>0:
            self._draw_night(show_player)
        hud=pygame.Rect(0,0,WIDTH,30)
        pygame.draw.rect(self.screen,(20,20,20),hud)
        s=self.font.render(f"Score: {self.score//10}  GOAL: top!  R=Restart",True,(220,220,220))
        self.screen.blit(s,(6,4))
        lv=self.font.render(f"Lives: {self.lives}",True,(255,90,90))
        self.screen.blit(lv,(WIDTH-lv.get_width()-6,4))
        if self.game_over:
            self._msg("CRASHED!",(220,60,60))
        if self.won:
            self._msg("YOU MADE IT!",(80,220,80))
        if self.game_over or self.won:
            self._draw_scores()
        pygame.display.flip()

    def _draw_night(self,show_player):
        draw_night(self.screen,self.darkness)
        # cars run underneath the river, so keep their lights out of the river band
        for area in (pygame.Rect(0,0,WIDTH,RIVER_TOP),pygame.Rect(0,RIVER_TOP+RIVER_H,WIDTH,HEIGHT)):
            self.screen.set_clip(area)
            for c in self.cars:
                draw_headlights(self.screen,c.rect,c.direction,self.darkness)
        self.screen.set_clip(None)
        if show_player:
            draw_headlights(self.screen,self.player.rect,-1,self.darkness)  # the player drives up the screen

    def _msg(self,text,color):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        self.screen.blit(ov,(0,0))
        m=self.big_font.render(text,True,color)
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//2-40))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+20))

    def _draw_scores(self):
        panel=pygame.Surface((360,228),pygame.SRCALPHA)  # dark backing so the table is easy to read
        pygame.draw.rect(panel,(0,0,0,170),panel.get_rect(),border_radius=12)
        self.screen.blit(panel,(WIDTH//2-180,348))
        def line(text,y,color):
            t=self.font.render(text,True,color)
            self.screen.blit(t,(WIDTH//2-t.get_width()//2,y))
        line(f"Final score: {self.score//10}",356,(220,220,220))
        line("HIGH SCORES",396,(240,200,60))
        for i,sc in enumerate(self.high_scores):
            mine=(i==self.score_rank)
            color=(80,220,80) if mine else (200,200,200)
            t=self.font.render(f"{i+1}. {sc:>6}",True,color)
            x=WIDTH//2-t.get_width()//2
            y=428+i*28
            self.screen.blit(t,(x,y))
            if mine: self.screen.blit(self.font.render("<- you",True,color),(x+t.get_width()+12,y))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()