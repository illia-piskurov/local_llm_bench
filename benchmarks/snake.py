from pathlib import Path

from benchmarks.base import Benchmark, Level, TestResult

LEVEL1_PROMPT = """\
Реализуй классическую игру "Змейка" в одном HTML файле (HTML + CSS + JS всё внутри
одного файла, без внешних библиотек, CDN и подключений через интернет).

Требования:
- Управление змейкой стрелками на клавиатуре (или WASD).
- Змейка растёт при поедании еды; столкновение со стеной или с собой — game over.
- Отображение текущего счёта на экране.
- Возможность перезапустить игру после game over (например, по нажатию клавиши).
- Файл должен открываться и работать сразу после сохранения и открытия в браузере
  двойным кликом — без сборки, без сервера, без npm.

В ответе верни только код одним блоком ```html ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию визуальными эффектами, не меняя базовую механику игры:
- анимации/плавные переходы движения змейки или появления еды;
- эффект при поедании еды (вспышка, частицы, изменение цвета и т.п.);
- красиво оформленный экран Game Over (с анимацией);
- любые другие визуальные улучшения на твой вкус (тени, градиенты, свечение и т.п.).

Игра должна остаться полностью рабочей и по-прежнему быть одним HTML файлом без
внешних зависимостей.

В ответе верни только код одним блоком ```html ... ```, без дополнительных пояснений вне блока.
"""


class SnakeBenchmark(Benchmark):
    id = "snake"
    name = "Змейка на HTML (оценивается вручную)"
    short = "Snake"
    file_ext = "html"
    code_lang = "html"
    answers_dir_name = "html_answers"
    manual_levels = frozenset({"level1", "level2"})
    levels = [
        Level(id="level1", name="Level 1 (базовая игра)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (визуальные эффекты)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        raise NotImplementedError("SnakeBenchmark levels are manual-only")
