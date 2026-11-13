"""Build the fictitious dataset this lab works on.

Run this first, from the lab folder, before anything else:

    uv run scripts/make_lac_lab_data.py

It writes ``data/schools.csv``, ``data/pupils.csv`` and ``CODEBOOK.md``. None
of them ship with the folder, and nothing else here works until they exist.

The script needs no packages beyond the Python standard library, so it runs
whichever way you start it: ``uv run`` in the terminal, or the Run button in
VS Code. Everything is seeded, so every machine in the room produces exactly
the same numbers.

All values are invented. They resemble no real school, child or project, and
the villages are not real places in the sense the data implies.

The expected-results table is computed here, from the same arrays that produce
the CSVs, so the two can never drift apart. Never edit the expected numbers by
hand: run this script again. The codebook no longer includes it; the script
only prints it to the console.

Maintainer note: two copies of the expected table live elsewhere, in
``lac-workshops/session-plans.md`` and in the Session 2 deck, and nothing
enforces those. The script prints the table in deck form at the end so they can
be pasted rather than retyped.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
DATA = LAB / "data"

SEED = 20261106
MISSING_SCORE = -99

STUDY = "Lectura Temprana"

# The village code is the first two characters of every school_id, so these
# keys must stay exactly two characters long.
VILLAGES = {
    "AG": "Aguascalientes",
    "TQ": "Tequesquitengo",
    "MT": "Gotham",
}

# Two treated and two control schools per village. MT-04 deliberately gets no
# pupils, which leaves Gotham control with one school instead of two, so
# that cell is visibly smaller than every other cell in the collapse.
SCHOOLS: list[tuple[str, str, int, int, int]] = [
    # school_id, modality, treatment, teachers, rural
    ("AG-01", "intercultural bilingual", 1, 6, 1),
    ("AG-02", "bilingual", 0, 4, 1),
    ("AG-03", "intercultural bilingual", 1, 7, 1),
    ("AG-04", "bilingual", 0, 5, 0),
    ("TQ-01", "intercultural bilingual", 1, 8, 1),
    ("TQ-02", "bilingual", 0, 3, 1),
    ("TQ-03", "intercultural bilingual", 1, 5, 0),
    ("TQ-04", "bilingual", 0, 6, 1),
    ("MT-01", "intercultural bilingual", 1, 4, 0),
    ("MT-02", "intercultural bilingual", 1, 9, 0),
    ("MT-03", "bilingual", 0, 5, 0),
    ("MT-04", "bilingual", 0, 3, 1),
]

EMPTY_SCHOOL = "MT-04"
ORPHAN_SCHOOL = "AG-99"
ORPHAN_PUPILS = 5

# Two children appear twice in pupils.csv (same row, same pupil_id).
DUPLICATE_PUPILS = 2

# Roughly 500 children across the eleven schools that were visited.
PUPILS_MIN = 38
PUPILS_MAX = 50

# Share of matched pupils carrying each trap. Sampled with the seeded
# generator rather than hand-picked, so the traps land in every school
# instead of clustering in the first two.
NOT_ASSESSED_RATE = 0.10
NO_ATTENDANCE_RATE = 0.05

# Treated children are never weak readers or mathematicians: their scores are
# floored well above the control floor. Scores top out at the same ceiling.
CONTROL_FLOOR = 28
TREATED_FLOOR = 50
MAX_SCORE = 96

DROPOUT_LEVELS = ["Very likely", "Likely", "Unlikely", "Very unlikely"]


def build_schools() -> list[dict[str, object]]:
    """Build the school rows from the hand-specified table."""
    return [
        {
            "school_id": school_id,
            "village": VILLAGES[school_id[:2]],
            "modality": modality,
            "treatment": treatment,
            "teachers": teachers,
            "rural": rural,
        }
        for school_id, modality, treatment, teachers, rural in SCHOOLS
    ]


def build_pupils(schools: list[dict[str, object]]) -> list[dict[str, object]]:
    """Build every pupil row, then stamp the traps."""
    rng = random.Random(SEED)
    pupils: list[dict[str, object]] = []
    counter = 0

    for school in schools:
        if school["school_id"] == EMPTY_SCHOOL:
            continue
        treated = int(school["treatment"])
        rural = int(school["rural"])
        # Treated schools score higher, so the collapse shows something.
        centre = 72 if treated else 58
        for _ in range(rng.randint(PUPILS_MIN, PUPILS_MAX)):
            counter += 1
            pupils.append(
                _pupil(
                    rng,
                    f"P{counter:03d}",
                    str(school["school_id"]),
                    centre,
                    treated,
                    rural,
                )
            )

    matched_ids = [str(p["pupil_id"]) for p in pupils]

    # The orphans: real-looking children whose school is not in schools.csv.
    # They keep usable scores and attendance, so the only thing wrong with
    # them is the join. Their treatment status is unknown, so they are
    # generated like control children.
    for _ in range(ORPHAN_PUPILS):
        counter += 1
        pupils.append(
            _pupil(rng, f"P{counter:03d}", ORPHAN_SCHOOL, 60, 0, rng.randint(0, 1))
        )

    _stamp_traps(rng, pupils, matched_ids)
    _add_duplicates(rng, pupils, {str(s["school_id"]) for s in schools})
    return pupils


def _clip(value: int, floor: int) -> int:
    """Keep a score between its floor and the shared ceiling."""
    return min(MAX_SCORE, max(floor, value))


def _dropout_chance(
    rng: random.Random, treated: int, reading: int, attendance: float
) -> str:
    """Rate the chance that a child leaves school.

    Treated children are never likely to drop out. For everyone else the
    rating follows weak reading and low attendance, plus some noise.
    """
    if treated:
        return rng.choices(["Unlikely", "Very unlikely"], weights=[35, 65])[0]

    weakness = (MAX_SCORE - reading) / (MAX_SCORE - CONTROL_FLOOR)
    absence = (99.5 - attendance) / (99.5 - 61.0)
    risk = 0.6 * weakness + 0.4 * absence + rng.uniform(-0.15, 0.15)
    if risk > 0.62:
        return "Very likely"
    if risk > 0.50:
        return "Likely"
    if risk > 0.38:
        return "Unlikely"
    return "Very unlikely"


def _pupil(
    rng: random.Random,
    pupil_id: str,
    school_id: str,
    centre: int,
    treated: int,
    rural: int,
) -> dict[str, object]:
    """Build one pupil row with plausible scores, date and attendance."""
    floor = TREATED_FLOOR if treated else CONTROL_FLOOR
    reading = _clip(round(rng.gauss(centre, 11)), floor)
    # Maths tracks reading, with its own noise.
    maths = _clip(round(rng.gauss(centre - 2, 8) + 0.4 * (reading - centre)), floor)
    attendance = round(rng.uniform(72.0 if treated else 61.0, 99.5), 1)

    # English is likelier in urban schools and a little likelier when treated.
    p_english = 0.20 + (0.0 if rural else 0.25) + (0.10 if treated else 0.0)

    return {
        "pupil_id": pupil_id,
        "school_id": school_id,
        "grade": rng.choice([3, 4]),
        "sex": rng.choice(["f", "m"]),
        "attendance_pct": attendance,
        "reading_score": reading,
        "math_score": maths,
        "speaks_english": int(rng.random() < p_english),
        "dropout_chance": _dropout_chance(rng, treated, reading, attendance),
        "assessed_date": f"2026-09-{rng.randint(14, 25):02d}",
    }


def _stamp_traps(
    rng: random.Random, pupils: list[dict[str, object]], matched_ids: list[str]
) -> None:
    """Blank attendance and unset scores for a seeded share of matched pupils.

    A child who was not assessed has both scores unset.
    """
    not_assessed = set(
        rng.sample(matched_ids, round(len(matched_ids) * NOT_ASSESSED_RATE))
    )
    no_attendance = set(
        rng.sample(matched_ids, round(len(matched_ids) * NO_ATTENDANCE_RATE))
    )

    for pupil in pupils:
        if pupil["pupil_id"] in not_assessed:
            pupil["reading_score"] = MISSING_SCORE
            pupil["math_score"] = MISSING_SCORE
        if pupil["pupil_id"] in no_attendance:
            pupil["attendance_pct"] = ""


def _add_duplicates(
    rng: random.Random, pupils: list[dict[str, object]], known_schools: set[str]
) -> None:
    """Repeat a few usable children as exact copies at random positions.

    Only matched, assessed children are copied, so the duplicates always
    inflate the final table when they are not removed.
    """
    candidates = [
        p
        for p in pupils
        if p["school_id"] in known_schools and p["reading_score"] != MISSING_SCORE
    ]
    for pupil in rng.sample(candidates, DUPLICATE_PUPILS):
        pupils.insert(rng.randrange(len(pupils) + 1), dict(pupil))


def collapse(
    schools: list[dict[str, object]], pupils: list[dict[str, object]]
) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Compute the answer the exercise is checked against.

    Drops duplicate pupil rows, joins pupils to schools on school_id, drops
    unmatched pupils, drops not-assessed reading scores, then averages by
    village and treatment.
    """
    by_id = {s["school_id"]: s for s in schools}

    seen: set[object] = set()
    unique: list[dict[str, object]] = []
    extras: list[dict[str, object]] = []
    for pupil in pupils:
        if pupil["pupil_id"] in seen:
            extras.append(pupil)
        else:
            seen.add(pupil["pupil_id"])
            unique.append(pupil)

    matched = [p for p in unique if p["school_id"] in by_id]
    usable = [p for p in matched if p["reading_score"] != MISSING_SCORE]
    orphans = [p for p in unique if p["school_id"] not in by_id]
    orphans_usable = [p for p in orphans if p["reading_score"] != MISSING_SCORE]
    usable_ids = {p["pupil_id"] for p in usable}

    cells: dict[tuple[str, int], list[int]] = {}
    for pupil in usable:
        school = by_id[pupil["school_id"]]
        key = (str(school["village"]), int(school["treatment"]))
        cells.setdefault(key, []).append(int(pupil["reading_score"]))

    rows = [
        {
            "village": village,
            "treatment": treatment,
            "pupils": len(scores),
            "mean_reading_score": round(sum(scores) / len(scores), 1),
        }
        for (village, treatment), scores in sorted(cells.items())
    ]

    duplicates_kept = sum(1 for p in extras if p["pupil_id"] in usable_ids)
    checks = {
        "pupils_rows": len(pupils),
        "pupils_total": len(unique),
        "pupils_duplicated": len(extras),
        "pupils_matched": len(matched),
        "pupils_not_assessed": sum(
            1 for p in unique if p["reading_score"] == MISSING_SCORE
        ),
        "pupils_in_collapse": len(usable),
        "pupils_left_join": len(usable) + len(orphans_usable),
        "pupils_with_dupes": len(usable) + duplicates_kept,
        "pupils_orphaned": len(orphans),
        "attendance_blank": sum(1 for p in unique if p["attendance_pct"] == ""),
    }
    return rows, checks


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write rows to a UTF-8 CSV, creating the parent folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def expected_table(rows: list[dict[str, object]], pad: int) -> str:
    """Render the expected-results rows as markdown table body lines."""
    return "\n".join(
        f"  | {r['village']:<{pad}} | {r['treatment']:<11} | {r['pupils']:<7} | "
        f"{r['mean_reading_score']:<5} |"
        for r in rows
    )


def codebook(
    schools: list[dict[str, object]],
    pupils: list[dict[str, object]],
    checks: dict[str, int],
) -> str:
    """Render CODEBOOK.md."""
    names = ", ".join(VILLAGES.values())
    reading = [
        int(p["reading_score"]) for p in pupils if p["reading_score"] != MISSING_SCORE
    ]
    maths = [
        int(p["math_score"]) for p in pupils if p["math_score"] != MISSING_SCORE
    ]
    attendance = [
        float(p["attendance_pct"]) for p in pupils if p["attendance_pct"] != ""
    ]
    dates = sorted(str(p["assessed_date"]) for p in pupils)
    last_id = max(str(p["pupil_id"]) for p in pupils)

    return f"""# Libro de códigos: evaluación {STUDY} (ficticia)

## 1. Qué es esto

Datos de enseñanza para un taller de IPA LAC. Todos los valores son inventados.
No corresponden a ninguna escuela, niño ni proyecto real, no se realizó ninguna
evaluación real y las aldeas que aparecen abajo no son lugares reales en el
sentido que este archivo sugiere. Clasificación de datos: Pública.

Dos archivos describen una evaluación ficticia de lectura y matemáticas en {len(schools)}
escuelas primarias de tres aldeas: {names}.

## 2. Los dos archivos y cómo se relacionan

`pupils.csv` tiene una fila por niño. `schools.csv` tiene una fila por escuela.
Muchos alumnos pertenecen a una misma escuela, y la unión se hace por
`school_id`. La aldea, el tratamiento y la condición rural solo están en
`schools.csv`, y los puntajes solo están en `pupils.csv`, así que cualquier
resultado desagregado por aldea, tratamiento o condición rural necesita ambos
archivos.

## 3. schools.csv ({len(schools)} filas)

  | Variable    | Tipo   | Valores                                | Etiqueta                           |
  | ----------- | ------ | -------------------------------------- | ---------------------------------- |
  | `school_id` | texto  | `{SCHOOLS[0][0]}` a `{SCHOOLS[-1][0]}`                      | Código de escuela, único           |
  | `village`   | texto  | {names} | Aldea                              |
  | `modality`  | texto  | intercultural bilingual, bilingual     | Modalidad de enseñanza             |
  | `treatment` | entero | 0, 1                                   | 1 si la escuela fue tratada        |
  | `teachers`  | entero | 3 a 9                                  | Docentes en plantilla              |
  | `rural`     | entero | 0, 1                                   | 1 si la escuela está en zona rural |

## 4. pupils.csv ({len(pupils)} filas)

  | Variable         | Tipo     | Valores                                      | Etiqueta                                       |
  | ---------------- | -------- | -------------------------------------------- | ---------------------------------------------- |
  | `pupil_id`       | texto    | `P001` a `{last_id}`                              | Código de niño, ver problema 5                 |
  | `school_id`      | texto    | Se une a `schools.school_id`                 | Escuela a la que asiste el niño                |
  | `grade`          | entero   | 3, 4                                         | Grado                                          |
  | `sex`            | texto    | f, m                                         | Sexo                                           |
  | `attendance_pct` | numérico | {min(attendance):.1f} a {max(attendance):.1f}, puede estar vacío               | Asistencia, porcentaje de días                 |
  | `reading_score`  | entero   | {min(reading)} a {max(reading)}, o {MISSING_SCORE}                               | Puntaje de lectura, {MISSING_SCORE} si no fue evaluado     |
  | `math_score`     | entero   | {min(maths)} a {max(maths)}, o {MISSING_SCORE}                               | Puntaje de matemáticas, {MISSING_SCORE} si no fue evaluado |
  | `speaks_english` | entero   | 0, 1                                         | 1 si el niño habla inglés                      |
  | `dropout_chance` | texto    | {", ".join(DROPOUT_LEVELS)} | Valoración del docente sobre la probabilidad de que el niño abandone la escuela |
  | `assessed_date`  | fecha    | {dates[0]} a {dates[-1]}                      | Fecha de evaluación, formato ISO               |

## 5. Problemas conocidos

Cinco cosas en estos datos te darán una respuesta equivocada si las ignoras.

1. **`reading_score` y `math_score` usan {MISSING_SCORE} para "no evaluado".** No es un
   puntaje. Todos los lenguajes lo leen como un número, así que un promedio que
   lo incluya está mal. Un niño que no fue evaluado tiene ambos puntajes en
   {MISSING_SCORE}. Hay {checks["pupils_not_assessed"]} niños afectados.
2. **`attendance_pct` está vacío para {checks["attendance_blank"]} niños.** Es un dato genuinamente
   faltante, no un cero. R, Stata y pandas lo tratan de forma distinta en un
   promedio.
3. **La escuela `{EMPTY_SCHOOL}` no tiene alumnos.** Es una escuela real de la muestra que
   nunca fue visitada, así que debe seguir apareciendo en los conteos de
   escuelas, pero no aporta a ningún promedio de alumnos. Es una de las dos
   escuelas de control de {VILLAGES[EMPTY_SCHOOL[:2]]}, y por eso la celda de
   control de esa aldea tiene aproximadamente la mitad del tamaño de las demás.
4. **{checks["pupils_orphaned"]} alumnos pertenecen a la escuela `{ORPHAN_SCHOOL}`, que no está en `schools.csv`.**
   Un inner join descarta a esos niños en silencio. Un left join los conserva
   sin aldea, lo que aparece como una fila extra y sin nombre.
5. **{checks["pupils_duplicated"]} niños aparecen dos veces en `pupils.csv`.** Las dos filas son copias
   exactas con el mismo `pupil_id`, así que el archivo tiene {checks["pupils_rows"]} filas pero
   solo {checks["pupils_total"]} niños. Contar filas en lugar de niños infla esas celdas.

## 6. Para el agente

No abras los archivos CSV para averiguar cuáles son las variables. Todo lo que
necesitas está en este archivo. Si necesitas una fila de ejemplo para probar
código, invéntala a partir de la tabla de arriba.
"""


def main() -> None:
    """Generate both CSVs and the codebook, then print what to paste."""
    schools = build_schools()
    pupils = build_pupils(schools)
    rows, checks = collapse(schools, pupils)
    pad = max(len(v) for v in VILLAGES.values())

    write_csv(DATA / "schools.csv", schools)
    write_csv(DATA / "pupils.csv", pupils)
    (LAB / "CODEBOOK.md").write_text(
        codebook(schools, pupils, checks), encoding="utf-8"
    )

    print(f"schools.csv  {len(schools)} rows")
    print(f"pupils.csv   {len(pupils)} rows")
    print("CODEBOOK.md  written")
    for key, value in checks.items():
        print(f"  {key:22} {value}")

    print("\nExpected results (not part of CODEBOOK.md):\n")
    print(f"  | Aldea {' ' * (pad - 5)}| Tratamiento | Alumnos | Media |")
    print(f"  | {'-' * pad} | ----------- | ------- | ----- |")
    print(expected_table(rows, pad))


if __name__ == "__main__":
    main()
