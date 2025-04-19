import os
import sys
import pygame

# Initialize paths
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

def init_game():
    """Initialize pygame and game resources."""
    pygame.init()
    pygame.display.set_caption("Chess Game")
    
    # Initialize and export globals
    import utils
    
    # Load assets using correct paths
    utils.MUSIC_PATH = os.path.join(bundle_dir, "Music")
    utils.IMAGE_PATH = os.path.join(bundle_dir, "Image")
    utils.FONT_PATH = os.path.join(bundle_dir, "Font")
    
    utils.screen = pygame.display.set_mode((utils.WIDTH, utils.HEIGHT))
    utils.game_font = pygame.font.Font(os.path.join(utils.FONT_PATH, "turok.ttf"), 40)
    
    # Load images
    utils.images = {}
    pieces = ["P", "N", "B", "R", "Q", "K"]
    for color in ["w", "b"]:
        for p in pieces:
            name = color + p
            utils.images[name] = pygame.transform.scale(
                pygame.image.load(os.path.join(utils.IMAGE_PATH, f"{name}.png")),
                (utils.SQUARE_SIZE, utils.SQUARE_SIZE)
            )
    
    # Load background
    utils.menu_background = pygame.image.load(os.path.join(utils.IMAGE_PATH, "landscape4.png"))
    utils.menu_background = pygame.transform.scale(utils.menu_background, (utils.WIDTH, utils.HEIGHT))
    
    # Initialize audio
    pygame.mixer.init()
    pygame.mixer.music.load(os.path.join(utils.MUSIC_PATH, "chessmusic.mp3"))
    pygame.mixer.music.play(-1)
    
    utils.sounds = {
        'move': pygame.mixer.Sound(os.path.join(utils.MUSIC_PATH, "Move.mp3")),
        'capture': pygame.mixer.Sound(os.path.join(utils.MUSIC_PATH, "Capture.mp3")),
        'check': pygame.mixer.Sound(os.path.join(utils.MUSIC_PATH, "Check.mp3")),
        'checkmate': pygame.mixer.Sound(os.path.join(utils.MUSIC_PATH, "Checkmate.mp3"))
    }

def main():
    """Main entry point."""
    init_game()
    from main_menu import main_menu
    main_menu()

if __name__ == "__main__":
    main()