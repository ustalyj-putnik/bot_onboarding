from datetime import datetime
from sqlalchemy import (
    Column, Integer, SmallInteger, JSON, String, Text, DateTime, Boolean, ForeignKey, Float
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)              # telegram user_id
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"))
    title = Column(String(128), nullable=False)
    body = Column(Text, nullable=False)
    media = Column(String, nullable=True)
    order = Column(Integer, default=1)
    section = relationship("Section", backref="lessons")

class Direction(Base):
    __tablename__ = "directions"
    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    intro_text = Column(Text)
    is_visible = Column(Boolean, default=True)

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    direction_id = Column(Integer, ForeignKey("directions.id", ondelete="CASCADE"))
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    order = Column(Integer, default=1)
    direction = relationship("Direction", backref="sections")
    is_visible = Column(Boolean, default=True)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)          # list[str]
    correct_option = Column(Integer, nullable=False)

class InteractionLog(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scenario_id = Column(String, nullable=True)
    step_id = Column(String, nullable=True)
    attempt_no = Column(Integer, nullable=True)
    sim_score = Column(Float, nullable=True)  # храню для аналитики
    scenario_rating = Column(String, nullable=True)   # correct|partial|incorrect
    msg_in = Column(Text)
    msg_out = Column(Text)
    is_ai = Column(Boolean, default=False)
    ts = Column(DateTime, default=datetime.utcnow)
    rating = Column(SmallInteger, nullable=True)  # 1=👍, 0=👎, NULL=не оценено
    latency_ms = Column(Integer, nullable=True)
    run_id = Column(String(36), index=True, nullable=True)

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"))
    lesson_index = Column(Integer, default=0)
    quiz_passed = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    last_question_index = Column(Integer, default=0)

class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, index=True)
    scenario_id  = Column(String, index=True)
    started_at   = Column(DateTime, nullable=False)
    finished_at  = Column(DateTime, nullable=False)

    correct_cnt  = Column(Integer)
    partial_cnt  = Column(Integer)
    incorrect_cnt= Column(Integer)
    total_steps  = Column(Integer)

    avg_attempts = Column(Float)          # среднее попыток на шаг
    skill_score  = Column(Float)          # 0-100 (см. §4.2)

    outcome_key  = Column(String)         # какой финал (outcome_…)