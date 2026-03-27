from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

hash = bcrypt.generate_password_hash("admin123").decode("utf-8")

print(hash)