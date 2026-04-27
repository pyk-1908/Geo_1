import os
import logging

class FolderLogger(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        super().__init__(filename, mode, encoding, delay)
