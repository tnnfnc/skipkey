# Settings for widget standardization
#:kivy 1.11
## IMPORT
#:import Factory kivy.factory.Factory
#:import Color kivy.graphics.Color
#:import Rectangle kivy.graphics.Rectangle
#:import Line kivy.graphics.Line

from kivy.metrics import dp

## PAGE
page_h = page_height = dp(800)
page_w = page_width = dp(428)

## SCREEN & BOX
screen_padding = (dp(2), dp(2), dp(2), dp(2))
box_padding = (dp(2), dp(2), dp(2), dp(2))

## FONT
font_norm = dp(15)
font_small = 0.8 * font_norm
font_big = title_font_size = 1.2*font_norm
font_bigger = 1.5*font_norm

## LABELS
label_y = label_height = 2*font_norm
label_small_y = 2*font_small
label_big_y =  2*font_big
label_bigger_y = 2*font_bigger

## FIELD WIDTH
field_x = field_width_small = dp(100)
field_small_x =  dp(50)
field_big_x = field_width_med = dp(200)
field_bigger_x = field_width_long = dp(300)

## FIELD SIZE for normal font
field_y        = label_y
field_small_y  = label_small_y
field_big_y    = label_big_y
field_bigger_y = label_bigger_y

## BUTTONS
button_y = label_y
button_x = field_x

nav_button_x = button_x
nav_button_y = 1.5*button_y

## SMALL BUTTON fits label height
small_button_x = field_small_x
small_button_y = field_small_y


## SPINNER
spinner_x = field_big_x
spinner_y = field_big_y

## COLORS
frame_color = (68/255.0, 164/255.0, 201/255.0)
table_color = (190/255.0, 190/255.0, 190/255.0)




