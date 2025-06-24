from datetime import datetime
from sqlalchemy import func, select
from core.services.base import get_session
from core.db.models import InteractionLog, ScenarioResult

class ScenarioAnalytics:
    @staticmethod
    async def build_and_save(user_id: int, scenario_id: str, outcome_key: str, *, run_id: str):
        async with get_session() as session:
            # -----------------------------------------------------------
            # 1. Все записи этой попытки, сортировка по времени
            # -----------------------------------------------------------
            stmt = (
                select(
                    InteractionLog.step_id,
                    InteractionLog.scenario_rating,
                    InteractionLog.ts,
                )
                .where(
                    InteractionLog.user_id == user_id,
                    InteractionLog.run_id == run_id,
                    InteractionLog.scenario_rating.isnot(None),
                )
                .order_by(InteractionLog.ts)
            )

            rows = (await session.execute(stmt)).all()
            if not rows:  # защита — вдруг логов нет
                return None

            started, finished = rows[0][2], rows[-1][2]

            # -----------------------------------------------------------
            # 2. Оставляем только ПОСЛЕДНИЙ рейтинг каждого шага
            # -----------------------------------------------------------
            last_by_step: dict[str, str] = {}
            attempts_per_step: dict[str, int] = {}

            for step_id, rating, _ in rows:
                # перезаписываем — значит, это более поздняя запись того же шага
                last_by_step[step_id] = rating
                attempts_per_step[step_id] = attempts_per_step.get(step_id, 0) + 1

            # -----------------------------------------------------------
            # 3. Считаем метрики
            # -----------------------------------------------------------
            correct = sum(1 for r in last_by_step.values() if r == "correct")
            partial = sum(1 for r in last_by_step.values() if r == "partial")
            incorrect = sum(1 for r in last_by_step.values() if r == "incorrect")

            total_steps = len(last_by_step)
            total_attempts = sum(attempts_per_step.values())

            avg_attempts = round(total_attempts / total_steps, 2) if total_steps else 0.0

            score_raw = (correct + 0.5 * partial) / total_steps if total_steps else 0.0
            skill_score = round(min(score_raw, 1.0) * 100, 1)  # clip ≤ 100

            # -----------------------------------------------------------
            # 4. Сохраняем агрегат
            # -----------------------------------------------------------
            res = ScenarioResult(
                user_id=user_id,
                scenario_id=scenario_id,
                started_at=started,
                finished_at=finished,
                correct_cnt=correct,
                partial_cnt=partial,
                incorrect_cnt=incorrect,
                total_steps=total_steps,
                avg_attempts=avg_attempts,
                skill_score=skill_score,
                outcome_key=outcome_key,
            )

            session.add(res)
            await session.commit()
            await session.refresh(res)
            return res
