import unittest
import pygame
from src.tutorial import TutorialPopup

class TestTutorialPopup(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((800, 600), pygame.HIDDEN)
        self.tutorial = TutorialPopup(800, 600)

    def test_initialization(self):
        """Verify initial state is hidden and starts on page 0."""
        self.assertFalse(self.tutorial.visible)
        self.assertEqual(self.tutorial.page, 0)

    def test_navigation_next(self):
        """Should increment page index but stay within bounds."""
        self.tutorial.show(0)
        self.tutorial._next_page()
        self.assertEqual(self.tutorial.page, 1)
        
        # Jump to last page and trigger next
        self.tutorial.page = len(self.tutorial.PAGES) - 1
        self.tutorial._next_page()
        # Tutorial should hide itself when 'Next' is pressed on the last page
        self.assertFalse(self.tutorial.visible)

    def test_navigation_prev(self):
        """Should decrement page index but not go below 0."""
        self.tutorial.show(2)
        self.tutorial._prev_page()
        self.assertEqual(self.tutorial.page, 1)
        
        self.tutorial._prev_page()
        self.tutorial._prev_page() # Try to go below 0
        self.assertEqual(self.tutorial.page, 0)

    def test_show_hide(self):
        """Verify visibility toggles."""
        self.tutorial.show()
        self.assertTrue(self.tutorial.visible)
        self.tutorial.hide()
        self.assertFalse(self.tutorial.visible)