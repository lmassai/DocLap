import os

class Logger:
    def __init__(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.file_path = file_path
        if os.path.exists(file_path):
            os.remove(file_path)

        self.file = open(file_path, 'w', encoding='utf-8')
        self.file.close()

        self.file = open(file_path, 'a', encoding='utf-8')

    def log(self, message):
        self.file.write(message + '\n')

    def close(self):
        self.file.close()