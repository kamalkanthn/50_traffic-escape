import pygame

RIVER_TOP=250    # y of the top edge of the river band
RIVER_H=80       # band height (one lane thick, taller than the 60px player)
LOG_W=140
LOG_COUNT=3
LOG_SPEED=2      # px per frame, positive = moves right
WATER=(40,90,160)
WAVE=(70,120,190)
LOG_COLOR=(140,95,50)
LOG_DARK=(100,65,30)

class Log:
    def __init__(self,x,speed):
        # the rect fills the whole band height, so "centre inside the rect" == "standing on the log"
        self.rect=pygame.Rect(x,RIVER_TOP,LOG_W,RIVER_H)
        self.speed=speed

    def update(self,width):
        self.rect.x+=self.speed
        cycle=width+LOG_W
        # leave one side completely, then re-enter from the other (keeps the spacing constant)
        if self.speed>0 and self.rect.left>=width: self.rect.x-=cycle
        elif self.speed<0 and self.rect.right<=0: self.rect.x+=cycle

    def draw(self,screen):
        body=self.rect.inflate(0,-16)
        pygame.draw.rect(screen,LOG_COLOR,body,border_radius=14)
        pygame.draw.rect(screen,LOG_DARK,body,3,border_radius=14)
        for gx in range(body.x+24,body.right-12,28):
            pygame.draw.line(screen,LOG_DARK,(gx,body.y+10),(gx,body.bottom-10),2)

class River:
    def __init__(self,width):
        self.width=width
        self.rect=pygame.Rect(0,RIVER_TOP,width,RIVER_H)
        spacing=(width+LOG_W)//LOG_COUNT
        self.logs=[Log(-LOG_W+i*spacing,LOG_SPEED) for i in range(LOG_COUNT)]

    def update(self):
        for log in self.logs: log.update(self.width)

    def contains(self,point):
        # True if the point is over the water band (log or not)
        return self.rect.collidepoint(point)

    def log_at(self,point):
        # the log under the point, or None
        for log in self.logs:
            if log.rect.collidepoint(point): return log
        return None

    def draw(self,screen):
        pygame.draw.rect(screen,WATER,self.rect)
        for y in range(self.rect.top+14,self.rect.bottom,24):
            for x in range(0,self.width,40):
                pygame.draw.line(screen,WAVE,(x,y),(x+16,y),2)
        for log in self.logs: log.draw(screen)