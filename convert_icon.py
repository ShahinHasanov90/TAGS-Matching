from PIL import Image
import cairosvg

# SVG'yi PNG'ye çevir
cairosvg.svg2png(url='app_icon.svg', write_to='app_icon.png', output_width=256, output_height=256)

# PNG'yi ICO'ya çevir
img = Image.open('app_icon.png')
img.save('app_icon.ico', format='ICO')