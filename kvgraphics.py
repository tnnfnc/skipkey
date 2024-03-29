# Settings for widget standardization
from kivy.metrics import dp

# PAGE
page_h = dp(800)
page_w = dp(428)

# SCREEN & BOX
screen_padding = (dp(2), dp(2), dp(2), dp(2))
box_padding = (dp(4), dp(4), dp(4), dp(4))
right_padding = (dp(4), dp(0))
box_spacing = (dp(4), dp(4))

# FONT
font_norm = dp(15)
font_small = 0.8 * font_norm
font_big = 1.2 * font_norm
font_bigger = 1.5 * font_norm

# LABELS
label_y = 2 * font_norm
label_small_y = 2 * font_small
label_big_y = 2 * font_big
label_bigger_y = 2 * font_bigger

# FRAME TITLE
frame_title_y = label_big_y 

# FIELD WIDTH
field_x = dp(100)
field_small_x = dp(60)
field_big_x = dp(200)
field_bigger_x = dp(300)

# FIELD SIZE for normal font
field_y = label_y
field_small_y = label_small_y
field_big_y = label_big_y
field_bigger_y = label_bigger_y
field_small_size = (field_x, field_y)
field_size = (field_small_x, field_y)
field_big_size = (field_big_x, field_y)
field_bigger_size = (field_bigger_x, field_y)

# BUTTONS
button_y = label_y
button_x = field_x
button_size = (button_x, button_y)

nav_button_x = button_x
nav_button_y = 1.5*button_y
nav_button_size = (nav_button_x, nav_button_y)

# SMALL BUTTON fits label height
small_button_x = field_small_x
small_button_y = field_small_y


# SPINNER
spinner_x = dp(160)
spinner_y = nav_button_y
spinner_size = (spinner_x, spinner_y)

# COLORS
frame_color = (68/255.0, 164/255.0, 201/255.0)
table_color = (190/255.0, 190/255.0, 190/255.0)
