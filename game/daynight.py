import pygame

DAY_NIGHT_MS=30000   # switch between day and night every 30 seconds (real time, not frames)
FADE_MS=1000         # the screen fades to / from night over this long after each switch
NIGHT_TINT=(5,10,45)
NIGHT_ALPHA=145      # how dark the overlay is at full night (0-255)
BEAM_LEN=170         # headlight beam reaches this far past a car's front (a car is only 80px long)
LIGHT_W=56           # width of the glow around one headlight
LAMP_PAD=10          # rows of the light image that sit inside the car's nose

def phase(elapsed_ms):
    """Return (is_night, darkness) for the milliseconds elapsed since the run started.
    is_night flips exactly every DAY_NIGHT_MS. darkness (0 = day .. 1 = night) eases over FADE_MS."""
    is_night=(elapsed_ms//DAY_NIGHT_MS)%2==1
    fade=min(1.0,(elapsed_ms%DAY_NIGHT_MS)/FADE_MS)
    if is_night: return True,fade
    if elapsed_ms<DAY_NIGHT_MS: return False,0.0  # a run always starts in full daylight
    return False,1.0-fade

def draw_night(screen,darkness):
    # dark blue tint over the whole scene (the HUD is drawn afterwards, so it stays readable)
    ov=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
    ov.fill((*NIGHT_TINT,int(NIGHT_ALPHA*darkness)))
    screen.blit(ov,(0,0))

_lights={}

def _light(direction):
    # one lamp = a bright dot plus a cone that widens and fades with distance; built once, then reused
    if not _lights:
        down=pygame.Surface((LIGHT_W,LAMP_PAD+BEAM_LEN),pygame.SRCALPHA)
        mid=LIGHT_W//2
        for i in range(BEAM_LEN):
            t=i/BEAM_LEN
            half=int(7+17*t)
            alpha=int(120*(1-t)**1.3)
            pygame.draw.line(down,(255,240,170,alpha),(mid-half,LAMP_PAD+i),(mid+half,LAMP_PAD+i))
        pygame.draw.circle(down,(255,250,200),(mid,LAMP_PAD-5),5)
        _lights[1]=down                                        # heading down the screen
        _lights[-1]=pygame.transform.flip(down,False,True)     # heading up the screen
    return _lights[direction]

def draw_headlights(screen,rect,direction,strength=1.0):
    """Two headlights on the front of a car whose rect is `rect`, heading `direction` (1=down, -1=up).
    strength (0..1) scales the brightness so the lights fade in and out with the night."""
    img=_light(direction)
    img.set_alpha(int(255*strength))
    if direction>0: top=rect.bottom-LAMP_PAD    # front edge is the bottom
    else:           top=rect.top-BEAM_LEN       # front edge is the top
    inset=max(6,rect.width//4)
    for lx in (rect.left+inset,rect.right-inset):
        screen.blit(img,(lx-LIGHT_W//2,top))