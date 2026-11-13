# Programa Lectura Temprana: descripción del tratamiento

> Nota: este documento describe un programa **ficticio** que acompaña los datos de enseñanza del taller de IPA LAC. Ninguna escuela, niño ni resultado es real. Clasificación de datos: Pública.

## Qué buscamos

Lectura Temprana es un programa sencillo que busca **mejorar el desempeño escolar** de los niños de tercer y cuarto grado, sobre todo en lectura y matemáticas, y **reducir el abandono escolar**.

## En qué consiste el tratamiento

Las escuelas tratadas reciben tres componentes durante el año escolar:

1. **Apoyo a docentes.** Una capacitación corta en enseñanza de la lectura y visitas breves de acompañamiento en el aula.
2. **Material y tiempo de lectura.** Libros y guías de actividades adaptados a cada modalidad (bilingüe o intercultural bilingüe), y 30 minutos de lectura guiada al día.
3. **Seguimiento a la asistencia.** Los docentes identifican a los niños que faltan con frecuencia y conversan con sus familias para evitar que dejen la escuela.

Las escuelas de control continúan con sus actividades habituales.

## Cómo lo medimos

El tratamiento se asignó **por escuela** (variable `treatment` en `schools.csv`), no por niño. Comparamos a los niños de escuelas tratadas con los de escuelas de control. Los resultados que seguimos son:

| Objetivo | Variable en los datos |
| --- | --- |
| Mejorar el aprendizaje | `reading_score`, `math_score` |
| Mejorar la asistencia | `attendance_pct` |
| Reducir el abandono | `dropout_chance` (valoración del docente) |

Los resultados pueden desagregarse por aldea, grado, sexo y condición rural. Para ello hay que unir `pupils.csv` y `schools.csv` por `school_id`. Antes de calcular promedios conviene leer los problemas conocidos del [libro de códigos](../CODEBOOK.md).

## Dónde se implementó

Se realizó un **piloto** en las 12 escuelas primarias de las tres aldeas descritas en el libro de códigos: **Aguascalientes, Tequesquitengo y Gotham**. La evaluación a los niños se hizo entre el 14 y el 25 de septiembre de 2026.

## Próximos pasos

Estamos analizando los datos del piloto y esperamos **compartir los resultados con los socios lo antes posible**.
