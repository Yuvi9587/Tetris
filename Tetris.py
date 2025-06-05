import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QFrame)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QKeyEvent, QFont
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QSize

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BLOCK_SIZE = 30
INITIAL_SPEED = 500

TETROMINOES = {
    'I': {
        'rotations': [
            [(0, -1), (0, 0), (0, 1), (0, 2)],
            [(-1, 0), (0, 0), (1, 0), (2, 0)]
        ],
        'color': QColor(Qt.GlobalColor.cyan)
    },
    'O': {
        'rotations': [
            [(0, 0), (0, 1), (1, 0), (1, 1)]
        ],
        'color': QColor(Qt.GlobalColor.yellow)
    },
    'T': {
        'rotations': [
            [(0, -1), (0, 0), (0, 1), (-1, 0)],
            [(-1, 0), (0, 0), (1, 0), (0, 1)],
            [(0, -1), (0, 0), (0, 1), (1, 0)],
            [(-1, 0), (0, 0), (1, 0), (0, -1)]
        ],
        'color': QColor(Qt.GlobalColor.magenta)
    },
    'S': {
        'rotations': [
            [(0, -1), (0, 0), (1, 0), (1, 1)],
            [(-1, 0), (0, 0), (0, 1), (1, 1)]
        ],
        'color': QColor(Qt.GlobalColor.green)
    },
    'Z': {
        'rotations': [
            [(0, 1), (0, 0), (1, 0), (1, -1)],
            [(-1, 1), (0, 1), (0, 0), (1, 0)]
        ],
        'color': QColor(Qt.GlobalColor.red)
    },
    'J': {
        'rotations': [
            [(-1, -1), (0, -1), (0, 0), (0, 1)],
            [(-1, 1), (-1, 0), (0, 0), (1, 0)],
            [(1, 1), (0, 1), (0, 0), (0, -1)],
            [(1, -1), (1, 0), (0, 0), (-1, 0)]
        ],
        'color': QColor(Qt.GlobalColor.blue)
    },
    'L': {
        'rotations': [
            [(-1, 1), (0, 1), (0, 0), (0, -1)],
            [(-1, -1), (-1, 0), (0, 0), (1, 0)],
            [(1, -1), (0, -1), (0, 0), (0, 1)],
            [(1, 1), (1, 0), (0, 0), (-1, 0)]
        ],
        'color': QColor(Qt.GlobalColor.darkYellow)
    }
}

class Piece:
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.shape_data = TETROMINOES[shape_name]
        self.rotations = self.shape_data['rotations']
        self.color = self.shape_data['color']
        self.rotation_index = 0
        self.current_shape_coords = self.rotations[self.rotation_index]
        self.x = 0
        self.y = 0

    def rotate(self):
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.current_shape_coords = self.rotations[self.rotation_index]

    def get_block_positions(self, x_offset=0, y_offset=0, shape_coords_override=None):
        active_coords = shape_coords_override if shape_coords_override is not None else self.current_shape_coords
        blocks = []
        for r_off, c_off in active_coords:
            blocks.append((self.y + r_off + y_offset, self.x + c_off + x_offset))
        return blocks

    def get_next_rotation_shape_coords(self):
        next_rotation_idx = (self.rotation_index + 1) % len(self.rotations)
        return self.rotations[next_rotation_idx]

def draw_block_util(painter, x_pixel, y_pixel, color, is_ghost=False):
    if not isinstance(color, QColor):
        painter.setBrush(QColor(color))
    else:
        painter.setBrush(QBrush(color))

    if is_ghost:
        painter.setPen(QPen(color.darker(120), 1))
    else:
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
    
    rect = QRect(int(x_pixel), int(y_pixel), BLOCK_SIZE, BLOCK_SIZE)
    painter.drawRect(rect)
    
    if not is_ghost:
        painter.setPen(QPen(color.lighter(130), 1))
        painter.drawLine(rect.topLeft() + QPoint(1,1) , rect.topRight() + QPoint(-1,1))
        painter.drawLine(rect.topLeft() + QPoint(1,1), rect.bottomLeft() + QPoint(1,-1))

        painter.setPen(QPen(color.darker(130), 1))
        painter.drawLine(rect.topRight() + QPoint(-1,1), rect.bottomRight() + QPoint(-1,-1))
        painter.drawLine(rect.bottomLeft() + QPoint(1,-1), rect.bottomRight() + QPoint(-1,-1))

class BoardWidget(QWidget):
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game = game_logic
        self.setFixedSize(BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE)
        self.setStyleSheet("background-color: #1E1E1E;")

    def paintEvent(self, event):
        painter = QPainter(self)
        
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                if self.game.board[r][c] != 0:
                    color = self.game.board[r][c]
                    draw_block_util(painter, c * BLOCK_SIZE, r * BLOCK_SIZE, color)

        if self.game.current_piece and not self.game.game_over:
            for r_board, c_board in self.game.current_piece.get_block_positions():
                if r_board < BOARD_HEIGHT:
                     draw_block_util(painter, c_board * BLOCK_SIZE, r_board * BLOCK_SIZE, self.game.current_piece.color)
        
        if self.game.current_piece and not self.game.game_over and self.game.ghost_y > self.game.current_piece.y:
            ghost_color = QColor(self.game.current_piece.color)
            ghost_color.setAlpha(70)
            for r_off, c_off in self.game.current_piece.current_shape_coords:
                 c_board_ghost = self.game.current_piece.x + c_off
                 if 0 <= c_board_ghost < BOARD_WIDTH:
                    draw_block_util(painter, c_board_ghost * BLOCK_SIZE, 
                                     (self.game.ghost_y + r_off) * BLOCK_SIZE, ghost_color, is_ghost=True)

        if self.game.game_over:
            self.draw_overlay_text(painter, "GAME OVER")
        elif self.game.is_paused:
            self.draw_overlay_text(painter, "PAUSED")

    def draw_overlay_text(self, painter, text):
        painter.setPen(QColor(Qt.GlobalColor.white))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        bg_color = QColor(0, 0, 0, 150)
        painter.fillRect(self.rect(), bg_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

class NextPieceWidget(QWidget):
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game = game_logic
        self.widget_block_dim = 4
        self.setFixedSize(self.widget_block_dim * BLOCK_SIZE, self.widget_block_dim * BLOCK_SIZE)
        self.setStyleSheet("background-color: #1E1E1E;")

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.game.next_piece:
            piece = self.game.next_piece
            
            min_r_off, max_r_off, min_c_off, max_c_off = 0, 0, 0, 0
            if piece.current_shape_coords:
                min_r_off = min(r for r, c in piece.current_shape_coords)
                max_r_off = max(r for r, c in piece.current_shape_coords)
                min_c_off = min(c for r, c in piece.current_shape_coords)
                max_c_off = max(c for r, c in piece.current_shape_coords)

            shape_width_blocks = max_c_off - min_c_off + 1
            shape_height_blocks = max_r_off - min_r_off + 1

            start_x_pixel = (self.width() - shape_width_blocks * BLOCK_SIZE) / 2
            start_y_pixel = (self.height() - shape_height_blocks * BLOCK_SIZE) / 2

            for r_off, c_off in piece.current_shape_coords:
                draw_c = c_off - min_c_off 
                draw_r = r_off - min_r_off
                
                x_pixel = start_x_pixel + draw_c * BLOCK_SIZE
                y_pixel = start_y_pixel + draw_r * BLOCK_SIZE
                draw_block_util(painter, x_pixel, y_pixel, piece.color)

class TetrisGame:
    def __init__(self):
        self.board = []
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.is_paused = False
        self.ghost_y = 0
        self.reset_game()

    def reset_game(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.is_paused = False
        self.current_piece = self._generate_random_piece()
        self.spawn_new_piece()
        self.calculate_ghost_piece_position()

    def spawn_new_piece(self):
        self.current_piece = self.next_piece if self.next_piece else self._generate_random_piece()
        self.next_piece = self._generate_random_piece()
        
        self.current_piece.x = BOARD_WIDTH // 2
        min_r_offset = min(r for r, c in self.current_piece.current_shape_coords)
        self.current_piece.y = -min_r_offset 

        if not self._is_valid_position(self.current_piece):
            self.game_over = True
            self.current_piece = None
        else:
            self.calculate_ghost_piece_position()

    def _generate_random_piece(self):
        shape_name = random.choice(list(TETROMINOES.keys()))
        return Piece(shape_name)

    def _is_valid_position(self, piece, x_offset=0, y_offset=0, shape_coords_to_check=None):
        if piece is None: return False
            
        for r_board, c_board in piece.get_block_positions(x_offset, y_offset, shape_coords_override=shape_coords_to_check):
            if not (0 <= c_board < BOARD_WIDTH):
                return False
            if r_board >= BOARD_HEIGHT:
                return False
            if r_board >= 0:
                if self.board[r_board][c_board] != 0:
                    return False
        return True

    def move_left(self):
        if self.game_over or self.is_paused or not self.current_piece: return False
        if self._is_valid_position(self.current_piece, x_offset=-1):
            self.current_piece.x -= 1
            self.calculate_ghost_piece_position()
            return True
        return False

    def move_right(self):
        if self.game_over or self.is_paused or not self.current_piece: return False
        if self._is_valid_position(self.current_piece, x_offset=1):
            self.current_piece.x += 1
            self.calculate_ghost_piece_position()
            return True
        return False

    def move_down(self):
        if self.game_over or self.is_paused or not self.current_piece: return False
        if self._is_valid_position(self.current_piece, y_offset=1):
            self.current_piece.y += 1
            return True
        else:
            self._fix_piece_to_board()
            self._clear_lines()
            self.spawn_new_piece()
            return False

    def drop_piece(self):
        if self.game_over or self.is_paused or not self.current_piece: return
        if self.current_piece:
            self.current_piece.y = self.ghost_y
            self._fix_piece_to_board()
            self._clear_lines()
            self.spawn_new_piece()

    def rotate_piece(self):
        if self.game_over or self.is_paused or not self.current_piece: return False
        
        next_rotation_coords = self.current_piece.get_next_rotation_shape_coords()
        
        for kick_x in [0, -1, 1, -2, 2]: 
            if self._is_valid_position(self.current_piece, x_offset=kick_x, shape_coords_to_check=next_rotation_coords):
                self.current_piece.x += kick_x
                self.current_piece.rotate()
                self.calculate_ghost_piece_position()
                return True
        return False

    def _fix_piece_to_board(self):
        if not self.current_piece: return
        for r_board, c_board in self.current_piece.get_block_positions():
            if 0 <= r_board < BOARD_HEIGHT and 0 <= c_board < BOARD_WIDTH:
                self.board[r_board][c_board] = self.current_piece.color

    def _clear_lines(self):
        lines_to_clear_indices = [r for r in range(BOARD_HEIGHT) if all(self.board[r][c] != 0 for c in range(BOARD_WIDTH))]

        if lines_to_clear_indices:
            num_cleared = len(lines_to_clear_indices)
            self.lines_cleared_total += num_cleared
            
            score_bonuses = {1: 40, 2: 100, 3: 300, 4: 1200}
            self.score += score_bonuses.get(num_cleared, 0) * self.level

            new_level = (self.lines_cleared_total // 10) + 1
            if new_level > self.level:
                self.level = new_level

            for r_idx in sorted(lines_to_clear_indices, reverse=True):
                del self.board[r_idx]
                self.board.insert(0, [0 for _ in range(BOARD_WIDTH)])
    
    def calculate_ghost_piece_position(self):
        if not self.current_piece:
            self.ghost_y = -1 
            return

        temp_y_offset = 0
        while self._is_valid_position(self.current_piece, y_offset=temp_y_offset + 1):
            temp_y_offset += 1
        self.ghost_y = self.current_piece.y + temp_y_offset

    def toggle_pause(self):
        if not self.game_over:
            self.is_paused = not self.is_paused

    def update_game_tick(self):
        if not self.game_over and not self.is_paused:
            self.move_down()

class TetrisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game = TetrisGame()
        self.init_ui()
        self.start_game_flow()

    def init_ui(self):
        self.setWindowTitle('PyQt6 Tetris')
        self.setStyleSheet("background-color: #333; color: white;")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.board_widget = BoardWidget(self.game)
        main_layout.addWidget(self.board_widget)

        right_panel_layout = QVBoxLayout()
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel_layout)
        right_panel_widget.setFixedWidth(180)
        right_panel_layout.setSpacing(10)
        main_layout.addWidget(right_panel_widget)

        font_info = QFont("Consolas", 14)
        self.score_label = QLabel()
        self.score_label.setFont(font_info)
        right_panel_layout.addWidget(self.score_label)

        self.level_label = QLabel()
        self.level_label.setFont(font_info)
        right_panel_layout.addWidget(self.level_label)
        
        self.lines_label = QLabel()
        self.lines_label.setFont(font_info)
        right_panel_layout.addWidget(self.lines_label)

        right_panel_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))

        next_piece_title = QLabel("Next:")
        next_piece_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_panel_layout.addWidget(next_piece_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.next_piece_widget = NextPieceWidget(self.game)
        right_panel_layout.addWidget(self.next_piece_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        right_panel_layout.addStretch(1)

        button_font = QFont("Arial", 12)
        self.restart_button = QPushButton("Restart (R)")
        self.restart_button.setFont(button_font)
        self.restart_button.clicked.connect(self.start_game_flow)
        right_panel_layout.addWidget(self.restart_button)
        
        self.pause_button = QPushButton("Pause (P)")
        self.pause_button.setFont(button_font)
        self.pause_button.clicked.connect(self.toggle_pause_game)
        right_panel_layout.addWidget(self.pause_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop_tick)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.adjustSize()

    def start_game_flow(self):
        self.game.reset_game()
        self.update_ui_elements()
        self.timer.start(self.get_current_speed_interval())
        self.board_widget.update()
        self.next_piece_widget.update()
        self.pause_button.setText("Pause (P)")
        self.pause_button.setEnabled(True)
        self.setFocus()

    def game_loop_tick(self):
        if self.game.game_over:
            self.timer.stop()
            self.board_widget.update()
            self.pause_button.setText("Game Over")
            self.pause_button.setEnabled(False)
            return

        if not self.game.is_paused:
            self.game.update_game_tick()
            self.update_ui_elements()
            current_interval = self.get_current_speed_interval()
            if self.timer.interval() != current_interval:
                self.timer.setInterval(current_interval)

        self.board_widget.update()
        self.next_piece_widget.update()

    def update_ui_elements(self):
        self.score_label.setText(f"Score: {self.game.score:>6}")
        self.level_label.setText(f"Level: {self.game.level:>6}")
        self.lines_label.setText(f"Lines: {self.game.lines_cleared_total:>6}")

    def get_current_speed_interval(self):
        speed_reduction = (self.game.level - 1) * 40
        interval = max(50, INITIAL_SPEED - speed_reduction)
        return interval

    def toggle_pause_game(self):
        if self.game.game_over: return
        
        self.game.toggle_pause()
        if self.game.is_paused:
            self.timer.stop()
            self.pause_button.setText("Resume (P)")
        else:
            self.timer.start(self.get_current_speed_interval())
            self.pause_button.setText("Pause (P)")
        self.board_widget.update()
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_R:
            self.start_game_flow()
            return

        if self.game.game_over: return

        if event.key() == Qt.Key.Key_P:
            self.toggle_pause_game()
            return

        if self.game.is_paused: return

        action_taken = False
        if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_A:
            action_taken = self.game.move_left()
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_D:
            action_taken = self.game.move_right()
        elif event.key() == Qt.Key.Key_Down or event.key() == Qt.Key.Key_S:
            self.game.move_down() 
            action_taken = True 
        elif event.key() == Qt.Key.Key_Up or event.key() == Qt.Key.Key_W or event.key() == Qt.Key.Key_X:
            action_taken = self.game.rotate_piece()
        elif event.key() == Qt.Key.Key_Space:
            self.game.drop_piece()
            action_taken = True

        if action_taken:
            self.update_ui_elements()
            self.board_widget.update()
            self.next_piece_widget.update()
        
        super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    window = TetrisWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
