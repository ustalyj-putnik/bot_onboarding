#!/usr/bin/env bash
set -e
# ждём, пока Postgres ответит
echo "⏳ Waiting for Postgres..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Postgres is ready"
# миграции
echo "🔄 Alembic upgrade"
#alembic revision --autogenerate -m "initial migration"
poetry run alembic upgrade head

# (опционально) сиды уроков
if [ "$SEED_LESSONS" = "true" ]; then
  echo "🌱 Seeding lessons"
  poetry run python scripts/seed_lessons.py
  poetry run python scripts/seed_lessons_2.py
fi

# запуск бота
echo "🚀 Starting bot"
exec poetry run python app.py