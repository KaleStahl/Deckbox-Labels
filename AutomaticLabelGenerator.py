'''
AutomaticLabelGenerator.py
Kale Stahl
Last Updated: 4/10/2026
'''
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

franklin_path = r"C:\Windows\Fonts\FRAHV.TTF"
pdfmetrics.registerFont(TTFont("FranklinGothicHeavy", franklin_path))

class Decklist:

    def __init__(self, name, format, flavor_text, background_color, top_image_path, bottom_image_path, decklist_link, printed = True):
        self.name = name
        self.flavor_text = flavor_text
        self.background_color = self.hex_to_color(background_color)
        self.top_image_path = top_image_path
        self.bottom_image_path = bottom_image_path
        self.format = format
        self.decklist_link = decklist_link
        self.qr_code_path = "Label QR Codes/"+ name+'_'+format+'_qrcode.png'
        self.printed = printed
        self.generate_qr()

    def generate_qr(self):
        import qrcode
        img = qrcode.make(self.decklist_link)
        img.save(self.qr_code_path)

    def hex_to_color(self, hex_code):
        hex_code = hex_code.lstrip("#")
        r = int(hex_code[0:2], 16) / 255.0
        g = int(hex_code[2:4], 16) / 255.0
        b = int(hex_code[4:6], 16) / 255.0
        return colors.Color(r, g, b)

class Container:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y

    def frame(self, rel_x, rel_y, w, h, **kwargs):
        return Frame(self.x + rel_x, self.y + rel_y, w, h, **kwargs)
    
    def translate(self, dx, dy):
        self.x += dx
        self.y += dy

    def draw_rect(self, rel_x, rel_y, w, h, background_color, fill=0, stroke=1):
        self.canvas.setFillColor(background_color)
        self.canvas.setStrokeColor(colors.black)
        self.canvas.setLineWidth(1)
        self.canvas.rect(self.x + rel_x, self.y + rel_y, w, h, fill=fill, stroke=stroke)

    def draw_image(self, image_path, rel_x, rel_y, width, height):
        try:
            img = ImageReader(image_path)
            self.canvas.drawImage(
                img,
                self.x + rel_x,
                self.y + rel_y,
                width,
                height
            )
        except Exception as e:
            print(f"Error loading image: {e}")

    def draw_paragraph(self, text, rel_x, rel_y, w, h, style):
        frame = self.frame(rel_x, rel_y, w, h)
        story = [Paragraph(text, style)]
        frame.addFromList(story, self.canvas)

    def draw_centered_textbox_fit_canvas(
    self,
    text,
    rel_x,
    rel_y,
    width,
    height,
    background_color,
    *,
    font_name="Helvetica",
    max_font_size=36,
    min_font_size=6,
    padding_left=10,
    padding_right=10
    ):
        # --- Compute dynamic text color based on background luminance ---
        r, g, b = background_color.red, background_color.green, background_color.blue
        luminance = 0.299*r + 0.587*g + 0.114*b
        text_color = colors.black if luminance > 0.5 else colors.white

        # Adjust width for horizontal padding
        usable_width = width - padding_left - padding_right
        if usable_width <= 0:
            usable_width = width  # fallback

        # Start from max font size, shrink until it fits width
        c = self.canvas
        font_size = max_font_size
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)
        
        while (text_width > usable_width) and (font_size > min_font_size):
            font_size -= 1
            c.setFont(font_name, font_size)
            text_width = c.stringWidth(text, font_name, font_size)

        # --- Compute centered coordinates ---
        x_center = self.x + rel_x + padding_left + usable_width / 2
        y_center = self.y + rel_y + height / 2

        # Draw the text
        c.setFillColor(text_color)
        c.setFont(font_name, font_size)
        c.drawCentredString(x_center, y_center - font_size / 4, text)

    def draw_wrapped_textbox(
        self,
        text,
        rel_x,
        rel_y,
        width,
        height,
        background_color,
        font_name="Helvetica",
        max_font_size=12,
        min_font_size=4,
        padding_left=5,
        padding_right=5,
        leading_factor=1.2,
        padding_top=2,
        padding_bottom=2
    ):

        r, g, b = background_color.red, background_color.green, background_color.blue
        luminance = 0.299*r + 0.587*g + 0.114*b
        text_color = colors.black if luminance > 0.5 else colors.white

        usable_width = max(width - padding_left - padding_right, 1)

        words = text.split()
        lines = []
        current_line = ""

        font_size = max_font_size

        while font_size >= min_font_size:
            lines = []
            current_line = ""

            for word in words:
                test_line = (current_line + " " + word).strip()
                if stringWidth(test_line, font_name, font_size) <= usable_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            total_height = len(lines) * font_size * leading_factor + padding_top + padding_bottom

            

            if total_height <= height:
                break

            font_size -= .5

        self.canvas.setFillColor(text_color)
        self.canvas.setFont(font_name, font_size)

        y = self.y + rel_y + height - font_size  # top-down draw

        for line in lines:
            line_width = stringWidth(line, font_name, font_size)

            x_centered = (
                self.x + rel_x + padding_left + (usable_width - line_width) / 2
            )

            self.canvas.drawString(
                x_centered,
                y,
                line
            )

            y -= font_size * leading_factor

def create_top_label(canvas, xpos, ypos, decklist):
    ### Label Size Constants
    top_label_width = 3.75*inch
    top_label_height = 1.5*inch
    top_image_height = top_label_height
    top_image_width = top_image_height*7/5  # 7:5 aspect ratio
    format_text_height = 0.125*inch
    name_text_height = 0.5*inch
    text_buffer = 0.125*inch/2

    # Create label container and set background color
    container = Container(canvas, xpos, ypos)
    container.draw_rect(0, 0, top_label_width, top_label_height, decklist.background_color, fill=1, stroke=1)

    # Insert image
    top_image_x = top_label_width - top_image_width
    top_image_y = 0
    container.draw_image(decklist.top_image_path, top_image_x, top_image_y, top_image_width, top_image_height)

    # Insert text
    # format
    container.draw_centered_textbox_fit_canvas(
        decklist.format,
        0, 
        top_label_height-format_text_height - text_buffer,  
        top_label_width - top_image_width,
        format_text_height,
        decklist.background_color,
        font_name="FranklinGothicHeavy",
        max_font_size=10,
        min_font_size=6
    )
    #deck name
    container.draw_centered_textbox_fit_canvas(
        decklist.name,
        0,
        top_label_height-name_text_height-format_text_height-text_buffer,
        top_label_width - top_image_width,
        name_text_height,
        decklist.background_color,
        font_name="FranklinGothicHeavy",
        max_font_size=28,
        min_font_size=10
    )
    #Flavor text
    container.draw_wrapped_textbox(
        decklist.flavor_text,
        0,
        0,
        top_label_width - top_image_width,
        top_label_height - name_text_height - format_text_height-text_buffer,
        decklist.background_color,
        font_name="FranklinGothicHeavy",
        max_font_size=12,
        min_font_size=0,
        padding_left=5,
        padding_right=5
    )
    return container

def create_side_label(canvas, xpos, ypos, decklist):
    ### Label Size Constants
    side_label_width = 3.75*inch
    side_label_height = 2.625*inch
    side_image_height = side_label_height/2
    side_image_width = side_image_height*7/5  # 7:5 aspect ratio
    format_text_height = 0.125*inch
    name_text_height = 0.5*inch
    text_buffer = 0.125*inch/2
    qr_size = 1.5*inch # square QR code

    # Create label container and set background color
    container = Container(canvas, xpos, ypos)
    container.draw_rect(0, 0, side_label_width, side_label_height, decklist.background_color, fill=1, stroke=1)

    # Insert images
    bottom_image_x = side_label_width - side_image_width
    bottom_image_y = 0
    top_image_x = side_label_width - side_image_width
    top_image_y = side_image_height
    container.draw_image(decklist.bottom_image_path, bottom_image_x, bottom_image_y, side_image_width, side_image_height)
    container.draw_image(decklist.top_image_path, top_image_x, top_image_y, side_image_width, side_image_height)

    # Insert QR code
    qr_code_buffer = (side_label_width -side_image_width- qr_size)/2
    container.draw_image(decklist.qr_code_path, qr_code_buffer, qr_code_buffer, qr_size, qr_size)

    # Insert text
    container.draw_centered_textbox_fit_canvas(
        decklist.format,
        0, 
        side_label_height-format_text_height-text_buffer,  
        side_label_width - side_image_width,
        format_text_height,
        decklist.background_color,
        font_name="FranklinGothicHeavy",
        max_font_size=10,
        min_font_size=6
    )
    container.draw_centered_textbox_fit_canvas(
        decklist.name,
        0,
        side_label_height-name_text_height-format_text_height-text_buffer,
        side_label_width - side_image_width,
        name_text_height,
        decklist.background_color,
        font_name="FranklinGothicHeavy",
        max_font_size=28,
        min_font_size=10
    )
    return container

def create_full_label(canvas, xpos, ypos, decklist):
        create_top_label(canvas, xpos, ypos, decklist)
        create_side_label(canvas, xpos, ypos+1.5*inch, decklist)

def create_pdf(output_path):
    
    MARGIN = 0.5*inch

    # Create canvas
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    print("Reading decklists from CSV...", end = " ")
    decklists = read_decklists_from_csv("Label_Data.csv")
    label_num = 1
    num_pages = 1
    total_label = 0
    print("Done.")
    print("Generating labels...", end = " ")
    for decklist in decklists:
        if(not decklist.printed):
            continue
        if(label_num==1):
            create_full_label(c, MARGIN, MARGIN, decklist)
        elif(label_num==2):
            create_full_label(c, MARGIN+3.75*inch, MARGIN, decklist)
        elif(label_num==3):
            create_full_label(c, MARGIN, MARGIN+(1.5+2.625)*inch, decklist)
        elif(label_num==4):
            create_full_label(c, MARGIN+3.75*inch, MARGIN+(1.5+2.625)*inch, decklist)
            c.showPage()
            num_pages+=1
            label_num=0
        label_num+=1
        total_label+=1
    print("Done.")
    print(f"Generated {total_label} labels across {num_pages} pages.")

    # Save and Open PDF
    c.save()

    import os

    full_path = os.path.abspath(output_path)

    print("PDF saved to:", full_path)

    if os.path.exists(full_path):
        print("Now opening PDF.")
        os.startfile(full_path)
    else:
        print("ERROR: file not found")

def read_decklists_from_csv(csv_path):
    import csv
    decklists = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                decklist = Decklist(
                    name=row['name'],
                    format=row['format'],
                    flavor_text=row['flavor_text'],
                    background_color=row['background_color'],
                    top_image_path=row['top_image_path'],
                    bottom_image_path=row['bottom_image_path'],
                    decklist_link=row['decklist_link'],
                    printed=row['printed'].lower() == 'true'
                )
                decklists.append(decklist)
    except Exception as e:
        print(f"Error reading csv: {e}")
    return decklists

if __name__ == "__main__":
    create_pdf("output.pdf")

