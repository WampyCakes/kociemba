# kociemba
A slightly modified adaptation of [Herbert Kociemba's Two Phase Rubik's Cube Solving Algorithm](https://github.com/hkociemba/RubiksCube-TwophaseSolver) for use with [manim-rubikscube](https://github.com/WampyCakes/manim-rubikscube).

# License
This is licensed under the GPLv3.0 license ([see LICENSE file](https://github.com/WampyCakes/kociemba/blob/main/LICENSE)) in cooperation with Kociemba's algorithm license.

As per the license, changes made to Kociemba's source are:


* Removed anything unnecessary for solving such as examples, GUI, vision, and server files
* Commented out print statements
* Changed import statements
* Changed the way tables are written and read to be OS-independent (avoiding `EOFError: read() didn't return enough bytes`)