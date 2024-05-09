# AOE-II-Image-Map-Generator
Make AOE II DE Maps from Images.

Image goes in.

AOE II DE map comes out. Magic.

...although technically right now all the script does is ingest an image, rotates it, makes it square if it isn't already, then asks the user:

1. What size map they want to create (script downscales image)
2. how many colors they want the image to be
3. how simplified the image should be (runs a gaussian filter)

![image](https://github.com/inertiacreeping/AOE-II-Image-Map-Generator/assets/98634109/e7ba664d-1f51-42ae-a0d1-9fb1df5ccf54)

the user then assigns terrain types to each colour on the map (ie, blue = water etc) using the dropdown boxes on the right

then the script shits out a RMS script (but not really correctly formatted) with a list of pixel locations and what terrain type should be at that location - like so:

/* Random Map Script /
/ Automatically generated /

create_land {
    base_terrain GRASS
    land_percent 100
    terrain_type GRASS
    other_zone_avoidance_distance 0
}

/ Terrain at (0, 0): Water, Medium /
/ Terrain at (1, 0): Water, Medium /
/ Terrain at (2, 0): Water, Medium /
/ Terrain at (3, 0): Water, Medium /
/ Terrain at (4, 0): Water, Medium /
/ Terrain at (5, 0): Water, Medium */

(I'm still working on it, please be gentle)
