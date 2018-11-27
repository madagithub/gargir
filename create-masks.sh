# Replace COLOR with 0.0 - 1.0 gray component ratio to get several masks
# convert -size 87x142 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (COLOR * 2) * (1-rr*4 < 0.5) + COLOR * (1-rr*4 >= 0.5)' radial-gradient: first-mask-ellipse.png
convert -size 87x142 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.95 * 2) * (1-rr*4 < 0.5) + 0.95 * (1-rr*4 >= 0.5)' radial-gradient: first-mask-ellipse-0.95.png
convert -size 87x142 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.9 * 2) * (1-rr*4 < 0.5) + 0.9 * (1-rr*4 >= 0.5)' radial-gradient: first-mask-ellipse-0.9.png
convert -size 87x142 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.85 * 2) * (1-rr*4 < 0.5) + 0.85 * (1-rr*4 >= 0.5)' radial-gradient: first-mask-ellipse-0.85.png
convert -size 87x142 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.8* 2) * (1-rr*4 < 0.5) + 0.8 * (1-rr*4 >= 0.5)' radial-gradient: first-mask-ellipse-0.8.png

# Replace COLOR with 0.0 - 1.0 gray component ratio to get several masks
# convert -size 85x121 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (COLOR * 2) * (1-rr*4 < 0.5) + COLOR * (1-rr*4 >= 0.5)' radial-gradient: second-mask-ellipse-COLOR.png
convert -size 85x121 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.95 * 2) * (1-rr*4 < 0.5) + 0.95 * (1-rr*4 >= 0.5)' radial-gradient: second-mask-ellipse-0.95.png
convert -size 85x121 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.9 * 2) * (1-rr*4 < 0.5) + 0.9 * (1-rr*4 >= 0.5)' radial-gradient: second-mask-ellipse-0.9.png
convert -size 85x121 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.85 * 2) * (1-rr*4 < 0.5) + 0.85 * (1-rr*4 >= 0.5)' radial-gradient: second-mask-ellipse-0.85.png
convert -size 85x121 -fx 'xx=i/w-.5; yy=j/h-.5; rr=xx*xx+yy*yy; (1-rr*4) * (0.8 * 2) * (1-rr*4 < 0.5) + 0.8 * (1-rr*4 >= 0.5)' radial-gradient: second-mask-ellipse-0.8.png
