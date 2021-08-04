import datetime
import argparse
import math
import sys
import os
import cairo

DOC_WIDTH = 1872  # 26 inches
DOC_HEIGHT = 2880  # 40 inches
DOC_NAME = "life_calendar.pdf"

KEY_YEARS_DESC = [
    "Childhood (0 - 12)",
    "Adolescence (13 - 19)",
    "Early Adulthood (20 - 34)",
    "Middle Adulthood (35 - 49)",
    "Mature Adulthood (50 - 79)",
    "Late Adulthood (80 - 100)"
]

AGE_COLORS = [
    (0.867, 0.488, 0.293),
    (0.797, 0.231, 0.276),
    (0.673, 0.101, 0.334),
    (0.523, 0.096, 0.659),
    (0.016, 0.374, 0.782),
    (0.066, 0.737, 0.22)
]

XAXIS_DESC = "Weeks of the year"
YAXIS_DESC = "Years of your life"

FONT = "Brocha"
BIGFONT_SIZE = 40
SMALLFONT_SIZE = 16
TINYFONT_SIZE = 14

MAX_TITLE_SIZE = 30
DEFAULT_TITLE = "LIFE CALENDAR"

NUM_ROWS = 100
NUM_COLUMNS = 52

Y_MARGIN = 144
BOX_MARGIN = 6

BOX_LINE_WIDTH = 3
BOX_SIZE = ((DOC_HEIGHT - (Y_MARGIN + 36)) / NUM_ROWS) - BOX_MARGIN
X_MARGIN = (DOC_WIDTH - ((BOX_SIZE + BOX_MARGIN) * NUM_COLUMNS)) / 2

ARROW_HEAD_LENGTH = 36
ARROW_HEAD_WIDTH = 8


def parse_date(date):
    formats = ['%d/%m/%Y', '%d-%m-%Y']
    stripped = date.strip()

    for f in formats:
        try:
            ret = datetime.datetime.strptime(date, f)
        except:
            continue
        else:
            return ret

    raise ValueError("Incorrect date format: must be dd-mm-yyyy or dd/mm/yyyy")


def draw_square(ctx, pos_x, pos_y, color=(1, 1, 1)):
    """
    Draws a square at pos_x,pos_y
    """

    ctx.set_line_width(BOX_LINE_WIDTH)
    ctx.set_source_rgb(*color)
    ctx.move_to(pos_x + BOX_SIZE / 2, pos_y)

    ctx.arc(pos_x, pos_y, BOX_SIZE / 2, 0, 2 * math.pi)
    ctx.stroke_preserve()

    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.fill()


def text_size(ctx, text):
    _, _, width, height, _, _ = ctx.text_extents(text)
    return width, height


def is_current_week(now, month, day):
    end = now + datetime.timedelta(weeks=1)
    date1 = datetime.datetime(now.year, month, day)
    date2 = datetime.datetime(now.year + 1, month, day)

    return (now <= date1 < end) or (now <= date2 < end)


def draw_row(ctx, pos_y, birthdate, date, color):
    """
    Draws a row of 52 squares, starting at pos_y
    """

    pos_x = X_MARGIN + BOX_SIZE / 2

    for i in range(NUM_COLUMNS):
        fill = color

        draw_square(ctx, pos_x, pos_y, color=fill)
        pos_x += BOX_SIZE + BOX_MARGIN
        date += datetime.timedelta(weeks=1)


def draw_key_item(ctx, pos_x, pos_y, desc, colour):
    draw_square(ctx, pos_x + BOX_SIZE / 2, pos_y + BOX_SIZE / 2, color=colour)
    pos_x += BOX_SIZE + (BOX_SIZE / 2)

    ctx.set_source_rgb(0, 0, 0)
    w, h = text_size(ctx, desc)
    ctx.move_to(pos_x, pos_y + (BOX_SIZE / 2) + (h / 2))
    ctx.show_text(desc)

    return pos_x + w + (BOX_SIZE * 2)


def get_color(year):
    if year < 13:
        return AGE_COLORS[0]
    if year < 20:
        return AGE_COLORS[1]
    if year < 35:
        return AGE_COLORS[2]
    if year < 50:
        return AGE_COLORS[3]
    if year < 80:
        return AGE_COLORS[4]
    return AGE_COLORS[5]


def draw_grid(ctx, date, birthdate):
    """
    Draws the whole grid of 52x90 squares
    """
    start_date = date
    pos_x = X_MARGIN
    pos_y = Y_MARGIN - BOX_SIZE * 3.5

    # Draw the key for circle colours
    ctx.set_font_size(TINYFONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)

    for i in range(len(KEY_YEARS_DESC)):
        pos_x = draw_key_item(ctx, pos_x, pos_y, KEY_YEARS_DESC[i], AGE_COLORS[i])

    # draw week numbers above top row
    ctx.set_font_size(TINYFONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)

    pos_x = X_MARGIN
    pos_y = Y_MARGIN
    for i in range(NUM_COLUMNS):
        text = str(i + 1)
        w, h = text_size(ctx, text)
        ctx.move_to(pos_x + (BOX_SIZE / 2) - (w / 2), pos_y - BOX_SIZE)
        ctx.show_text(text)
        pos_x += BOX_SIZE + BOX_MARGIN

    ctx.set_font_size(TINYFONT_SIZE)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_ITALIC,
                         cairo.FONT_WEIGHT_NORMAL)

    for i in range(1, NUM_ROWS + 1):
        # Generate string for current date
        ctx.set_source_rgb(0, 0, 0)
        date_str = f'{i}'
        w, h = text_size(ctx, date_str)

        # Draw it in front of the current row
        ctx.move_to(X_MARGIN - w - BOX_SIZE,
                    pos_y + ((BOX_SIZE / 2) + (h / 2)))
        ctx.show_text(date_str)

        # Draw the current row
        draw_row(ctx, pos_y + BOX_SIZE / 2, birthdate, date, get_color(i))

        # Increment y position and current date by 1 row/year
        pos_y += BOX_SIZE + BOX_MARGIN
        date += datetime.timedelta(weeks=52)


def gen_calendar(birthdate, title, filename):
    if len(title) > MAX_TITLE_SIZE:
        raise ValueError("Title can't be longer than %d characters"
                         % MAX_TITLE_SIZE)

    # Fill background with white
    surface = cairo.PDFSurface(filename, DOC_WIDTH, DOC_HEIGHT)
    ctx = cairo.Context(surface)

    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, DOC_WIDTH, DOC_HEIGHT)
    ctx.fill()

    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD)
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_font_size(BIGFONT_SIZE)
    w, h = text_size(ctx, title)
    ctx.move_to((DOC_WIDTH / 2) - (w / 2), (Y_MARGIN / 2) - (h / 2))
    ctx.show_text(title)

    # Back up to the last monday
    date = birthdate
    while date.weekday() != 0:
        date -= datetime.timedelta(days=1)

    # Draw 52x90 grid of squares
    draw_grid(ctx, date, birthdate)
    ctx.show_page()


def parse_date(date):
    formats = ['%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

    for f in formats:
        try:
            ret = datetime.datetime.strptime(date.strip(), f)
        except ValueError:
            continue
        else:
            return ret

    raise argparse.ArgumentTypeError("incorrect date format")


def main():
    parser = argparse.ArgumentParser(description='\nGenerate a personalized "Life '
                                                 ' Calendar", inspired by the calendar with the same name from the '
                                                 'waitbutwhy.com store')

    parser.add_argument(type=parse_date, dest='date', help='starting date; your birthday,'
                                                           'in either yyyy/mm/dd or dd/mm/yyyy format (dashes \'-\' may also be used in '
                                                           'place of slashes \'/\')')

    parser.add_argument('-f', '--filename', type=str, dest='filename',
                        help='output filename', default=DOC_NAME)

    parser.add_argument('-t', '--title', type=str, dest='title',
                        help='Calendar title text (default is "%s")' % DEFAULT_TITLE,
                        default=DEFAULT_TITLE)

    parser.add_argument('-e', '--end', type=parse_date, dest='enddate',
                        help='end date; If this is set, then a calendar with a different start date'
                             ' will be generated for each day between the starting date and this date')

    args = parser.parse_args()

    doc_name = '%s.pdf' % (os.path.splitext(args.filename)[0])

    if args.enddate:
        start = args.date

        while start <= args.enddate:
            date_str = start.strftime('%d-%m-%Y')
            name = "life_calendar_%s.pdf" % date_str

            try:
                gen_calendar(start, args.title, name)
            except Exception as e:
                print("Error: %s" % e)
                return

            start += datetime.timedelta(days=1)

    else:
        try:
            gen_calendar(args.date, args.title, doc_name)
        except Exception as e:
            print("Error: %s" % e)
            return

        print('Created %s' % doc_name)


if __name__ == "__main__":
    main()
