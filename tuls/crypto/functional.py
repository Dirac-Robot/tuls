import io

from cryptography.fernet import Fernet


def encrypt_text(text, key=None):
    key = key or Fernet.generate_key()
    fernet = Fernet(key)
    if isinstance(text, str):
        text = text.encode('utf-8')
    return dict(key=key, encrypted_text=fernet.encrypt(text))


def decrypt_text(text, key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    fernet = Fernet(key)
    if isinstance(text, str):
        text = text.encode('utf-8')
    return dict(key=key, decrypted_text=fernet.decrypt(text).decode('utf-8'))


def encrypt_image(image_path, key=None):
    key = key or Fernet.generate_key()
    fernet = Fernet(key)
    with open(image_path, 'rb') as f:
        raw_image = f.read()
    return dict(key=key, encrypted_image=fernet.encrypt(raw_image))


def decrypt_image(image_path, key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    fernet = Fernet(key)
    with open(image_path, 'rb') as f:
        raw_image = f.read()
    image_io = io.BytesIO()
    decrypted_image = fernet.decrypt(raw_image)
    image_io.write(decrypted_image)
    image_io.seek(0)
    return dict(key=key, decrypted_image=image_io)


