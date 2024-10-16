import argparse
import curses
import sys


class Buffer:
    def __init__(self, lines):
        self.lines = lines

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    @property
    def bottom(self):
        return len(self)-1

    def insert(self, cursor, string):
        row, col = cursor.row, cursor.col
        try:
            current = self.lines.pop(row)
        except IndexError:
            current = ''
        new_line = current[:col]+string+current[col:]
        self.lines.insert(row, new_line)

    def split(self, cursor):
        row, col = cursor.row, cursor.col
        current_line = self.lines.pop(row)
        self.lines.insert(row, current_line[:col])
        self.lines.insert(row+1, current_line[col:])

    def backspace(self, cursor):
        row, col = cursor.row, cursor.col
        if (row, col) < (self.bottom, len(self[row])):
            current = self.lines.pop(row)
            if col < len(current):
                new_line = current[:col]+current[col+1:]
                self.lines.insert(row, new_line)
            else:
                next_line = self.lines.pop(row)
                new_line = current+next_line
                self.lines.insert(row, new_line)

    def page_up(self, window, cursor):
        cursor.row = max(0, cursor.row-window.n_rows)
        window.row = cursor.row
        window.horizontal_scroll(cursor)

    def page_down(self, window, cursor):
        cursor.row = min(self.bottom, cursor.row+window.n_rows)
        window.row = cursor.row
        window.horizontal_scroll(cursor)


def clamp(x, lower, upper):
    if x < lower:
        return lower
    if x > upper:
        return upper
    return x


class Cursor:
    def __init__(self, row=0, col=0, col_hint=None):
        self.row = row
        self._col = col
        self._col_hint = col if col_hint is None else col_hint

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_hint = col

    def _clamp_col(self, buffer):
        self._col = min(self._col_hint, len(buffer[self.row]))

    def up(self, buffer):
        if self.row > 0:
            self.row -= 1
            self._clamp_col(buffer)

    def down(self, buffer):
        if self.row < len(buffer)-1:
            self.row += 1
            self._clamp_col(buffer)

    def left(self, buffer):
        if self.col > 0:
            self.col -= 1
        elif self.row > 0:
            self.row -= 1
            self.col = len(buffer[self.row])

    def right(self, buffer):
        if self.col < len(buffer[self.row]):
            self.col += 1
        elif self.row < len(buffer)-1:
            self.row += 1
            self.col = 0


class Window:
    def __init__(self, n_rows, n_cols, row=0, col=0):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row = row
        self.col = col

    @property
    def bottom(self):
        return self.row+self.n_rows-1

    def up(self, cursor):
        if cursor.row == self.row-1 and self.row > 0:
            self.row -= 1

    def down(self, buffer, cursor):
        if cursor.row == self.bottom+1 and self.bottom < len(buffer)-1:
            self.row += 1

    def horizontal_scroll(self, cursor, left_margin=5, right_margin=2):
        n_pages = cursor.col//(self.n_cols-right_margin)
        self.col = max(n_pages*self.n_cols-right_margin-left_margin, 0)

    def translate(self, cursor):
        return cursor.row-self.row, cursor.col-self.col


def left(window, buffer, cursor):
    cursor.left(buffer)
    window.up(cursor)
    window.horizontal_scroll(cursor)


def right(window, buffer, cursor):
    cursor.right(buffer)
    window.down(buffer, cursor)
    window.horizontal_scroll(cursor)


def main(stdscr, file_path, start_line=0):
    with open(file_path) as f:
        buffer = Buffer(f.read().splitlines())

    window = Window(curses.LINES-1, curses.COLS-1)
    cursor = Cursor()
    cursor.row = start_line
    window.row = start_line
    window.horizontal_scroll(cursor)

    while True:
        stdscr.erase()
        for row, line in enumerate(buffer[window.row:window.row+window.n_rows]):
            if row == cursor.row-window.row and window.col > 0:
                line = '«'+line[window.col+1:]
            if len(line) > window.n_cols:
                line = line[:window.n_cols-1]+'»'
            stdscr.addstr(row, 0, line)
        stdscr.move(*window.translate(cursor))

        k = stdscr.getkey()
        if k == 'q':
            return
        elif k == 'KEY_LEFT':
            left(window, buffer, cursor)
        elif k == 'KEY_DOWN':
            cursor.down(buffer)
            window.down(buffer, cursor)
            window.horizontal_scroll(cursor)
        elif k == 'KEY_UP':
            cursor.up(buffer)
            window.up(cursor)
            window.horizontal_scroll(cursor)
        elif k == 'KEY_RIGHT':
            right(window, buffer, cursor)
        elif k == 'KEY_PPAGE':
            buffer.page_up(window, cursor)
        elif k == 'KEY_NPAGE':
            buffer.page_down(window, cursor)
        elif k == '\n':
            buffer.split(cursor)
            right(window, buffer, cursor)
        elif k in ('KEY_DC', '\x04'):
            buffer.backspace(cursor)
        elif k in ('KEY_BACKSPACE', '\x7f'):
            if (cursor.row, cursor.col) > (0, 0):
                left(window, buffer, cursor)
                buffer.backspace(cursor)
        else:
            buffer.insert(cursor, k)
            for _ in k:
                right(window, buffer, cursor)


def open_editor(file_path, start_line=0):
    return curses.wrapper(main, file_path=file_path, start_line=start_line)


if __name__ == '__main__':
    curses.wrapper(main, file_path='./tuls/debug/editor.py')
