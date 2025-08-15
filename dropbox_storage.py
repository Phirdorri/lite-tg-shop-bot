import dropbox
import os
import tempfile
import time

class DropboxStorage:
    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)
    
    def upload_image(self, file_bytes, file_name):
        """Загрузка изображения в Dropbox и получение публичной ссылки"""
        try:
            # Создаем уникальное имя файла
            unique_name = f"{int(time.time())}_{file_name}"
            dropbox_path = f"/{unique_name}"
            
            # Загружаем файл
            self.dbx.files_upload(file_bytes, dropbox_path)
            
            # Получаем публичную ссылку
            shared_link = self.dbx.sharing_create_shared_link(dropbox_path).url
            return shared_link.replace('dl=0', 'raw=1')
        except Exception as e:
            print(f"Ошибка загрузки в Dropbox: {e}")
            return None
    
    def delete_image(self, url):
        """Удаление изображения из Dropbox по URL"""
        try:
            # Извлекаем путь из URL
            path = url.split('?')[0].replace('https://www.dropbox.com', '')
            self.dbx.files_delete_v2(path)
            return True
        except Exception as e:
            print(f"Ошибка удаления из Dropbox: {e}")
            return False
