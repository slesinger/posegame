# PoseGame
This game uses Coral TPU with camera and PoseNet model to detect body position. Player can move in front of the camera and navigate a goal to punch smiley objects to gain points. Hitting a sad-face object removes 5 points.

The game can run on a main computer attached to a big screen or wall projector, while TPU camera is detached and can be positioned as needed. TPU sends body position over network to the main computer.

# Installation
```
pip3 install --pre --extra-index-url https://archive.panda3d.org/ panda3d
```

# Coral Installation
Panda3D cannot be installed from repository on coral device. Make it from source. Follow https://github.com/panda3d/panda3d/blob/master/README.md

```
python3 makepanda/makepanda.py --nothing --use-python --installer --wheel --use-direct
```

Do not use --threads as compiler will run out of memory.


# Coral PoseNet
https://github.com/google-coral/project-posenet

# Further Ideas
Score multiplier

Make the game episodic with a timebox 

Play using both hands

Move the camera to follow nose

Generate walls to force player to move more as a whole

(1 - gauss) probability of smiley position generation, center of screen being less probable
