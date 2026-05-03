from ursina import *


walk_sound = Audio("assets/sounds/walk.wav", loop=True, volume=0)
walk_sound.stop()
hit_sound = Audio("assets/sounds/hit.wav", loop=True)
hit_sound.stop()
pop_sound = Audio("assets/sounds/pop.wav", volume=5)
pop2_sound = Audio("assets/sounds/pop2.wav", volume=5)
pop3_sound = Audio("assets/sounds/pop3.wav", volume=5)
place_sound = Audio("assets/sounds/place.wav", volume=10)
place2_sound = Audio("assets/sounds/place2.wav", volume=10)

music = Audio("assets/sounds/music.wav", loop=True, volume=.3)
music.play()