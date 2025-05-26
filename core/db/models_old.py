from sqlalchemy import sql, Column, PrimaryKeyConstraint, Sequence

from core.db.database import db


# Модель данных для сообщений на 1 этапе
class First_stage_msg(db.Model):
    __tablename__ = 'first_stage_msgs'

    id = Column(db.Integer, Sequence("user_id_seq"), primary_key=True)
    text = Column(db.String())  # Текст сообщения
    photo_path = Column(db.String(250))  # Путь к фото

    #Функция вывода сообщения
    def __repr__(self):
        return f"{self.text}"



# Модель данных для уроков на 2 этапе
class Lesson(db.Model):
    __tablename__ = "lessons"

    # Составной первичный ключ (номер урока, код сферы обучения, код раздела)
    __table_args__ = (PrimaryKeyConstraint('id', 'study_area_code', 'study_section_code', name='lesson_pk'),)
    query: sql.Select

    id = Column(db.Integer)  # Номер урока
    study_area_code = Column(db.String(20))  # Код сферы обучения
    study_area_name = Column(db.String(60))  # Название сферы обучения

    study_section_code = Column(db.String(20))  # Код раздела обучения
    study_section_name = Column(db.String(60))  # Название раздела обучения

    name = Column(db.String(60))  # Название урока
    text = Column(db.String())  # Текст урока



# Функция вывода урока
    def __repr__(self):
        return f"Урок №{self.id}.\n{self.name}.\n\n{self.text}"
