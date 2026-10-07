import pygame
import random
from game.player import Player,LANE_W
from game.traffic import Car,make_car
from game.river import River,RIVER_TOP,RIVER_H

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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r: self.reset()
        return True

    def update(self):
        if self.game_over or self.won: return
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
        if self.invuln==0 or (self.invuln//6)%2==0:
            self.player.draw(self.screen)
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
        pygame.display.flip()

    def _msg(self,text,color):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        self.screen.blit(ov,(0,0))
        m=self.big_font.render(text,True,color)
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//2-40))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+20))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()