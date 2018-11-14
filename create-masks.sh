convert -size 120x160 xc:transparent -fill white -stroke white -draw "ellipse 60,80 50,70 0,360" first-mask-ellipse.png

convert -size 120x160 -define gradient:radii=128,64 -define gradient:angle=45 radial-gradient:black-white radial_gradient_ellipse_angle45.png