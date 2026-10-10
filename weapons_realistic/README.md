# Оружие для слотов Battlefield, до 10 000 треугольников

В папке 20 файлов `.glb`. 17 из них названы ключами из списка Battlefield и идут в игру. Остальные три (`ak47`, `uzi`, `sniper_quater_animated`) без ключа.

Реалистичные модели взяты из Sketchfab (загружены вами), из zip-архивов (SPAS и Barrett) и один AK-47 из репозитория thomas1568/ak47. Заглушки взяты из стилизованных CC0-паков Quaternius.

## Таблица слотов (17 ключей)

| Ключ | Battlefield | Файл | Статус | Треугольников | Длина, м |
|---|---|---|---|---|---|
| m433 | M433 | `m433.glb` | реалистичная, M16A3 (Sketchfab) | 9 655 | 1.006 |
| b36a4 | B36A4 | `b36a4.glb` | заглушка, Quaternius Rifle Battle West | 3 173 | 0.950 |
| m4a1 | M4A1 | `m4a1.glb` | заглушка, Quaternius SCAR-L (это не M4) | 1 930 | 0.838 |
| ak205 | AK-205 | `ak205.glb` | реалистичная, AK-103 (Sketchfab) | 9 108 | 0.943 |
| sgx | SGX | `sgx.glb` | реалистичная, Bizon (Sketchfab) | 7 938 | 0.690 |
| pw5a3 | PW5A3 | `pw5a3.glb` | реалистичная, KRISS Vector (Sketchfab) | 9 504 | 0.705 |
| l110 | L110 | `l110.glb` | заглушка, Quaternius AR (Ultimate) | 1 930 | 1.041 |
| m250 | M250 | `m250.glb` | заглушка, Quaternius Bullpup | 2 782 | 1.090 |
| m39_emr | M39 EMR | `m39_emr.glb` | заглушка, Quaternius Sniper | 1 346 | 1.020 |
| svdm | SVDM | `svdm.glb` | заглушка, Quaternius Sniper | 1 722 | 1.225 |
| m2010_esr | M2010 ESR | `m2010_esr.glb` | реалистичная, модель снайпера не определена (Sketchfab) | 9 422 | 1.100 |
| sv98 | SV-98 | `sv98.glb` | реалистичная, Barrett M82 из zip, назначение условное | 9 932 | 1.448 |
| m87a1 | M87A1 | `m87a1.glb` | заглушка, Quaternius Shotgun | 1 270 | 1.000 |
| m1014 | M1014 | `m1014.glb` | реалистичная, SPAS из zip, назван "fictional", назначение условное | 9 666 | 1.041 |
| p18 | P18 | `p18.glb` | реалистичная, Beretta 92FS (Sketchfab) | 9 448 | 0.216 |
| es57 | ES 5.7 | `es57.glb` | заглушка, Quaternius Pistol | 1 442 | 0.208 |
| m44 | M44 | `m44.glb` | реалистичная, Colt 1851 Navy (Sketchfab) | 9 004 | 0.331 |

Дополнительно лежат:
- `ak47.glb`: Stein Games AK-47 через thomas1568/ak47, 9 268 треугольников, 0.880 м.
- `uzi.glb`: Sketchfab, 3 525 треугольников, 0.650 м. Слота нет, свободного SMG-слота тоже нет.
- `sniper_quater_animated.glb`: стилизованный снайпер, 1 710 треугольников, 1.100 м, слота нет.

Длина в таблице это размер, по которому масштабировал файл. Измеренный размер сетки совпадает с ним. Справочные значения из поиска отличаются от таблицы не больше чем на 1 мм.

## Текстуры

- Sketchfab-модели: PBR-текстуры 1024 px, у `p18` 2048 px. У `ak205` в исходнике нет карты нормалей и AO, поэтому их нет и в файле.
- `ak47`: базовый цвет JPEG 2048, нормали PNG 2048, ORM PNG 2048. Нормаль из исходника (DirectX) переведена в glTF: зеленый канал инвертирован. ORM собран как R=AO, G=roughness, B=metallic. Проверено попиксельно против `T_AK47_N.png` и `T_AK47_RMAO.png`, совпадение 100%.
- `sv98` (Barrett): базовый цвет JPEG 2048, нормали PNG 1024, ORM PNG 2048. Карты `albedo66` и `ggg.jpg` не подключены. Нормаль подключена без инверсии зеленого канала, это не проверено.
- `m1014` (SPAS): текстур в исходнике нет, есть только цвета материалов.
- Заглушки: текстур нет, однотонные материалы.

## Лицензии и авторы

Для Sketchfab-моделей автор, лицензия и ссылка взяты из метаданных GLB (`asset.extras`). Файлы изменены: масштаб, упрощение, для AK-47 еще и текстуры. CC-BY-4.0 требует указания автора, ссылки на модель и лицензии (http://creativecommons.org/licenses/by/4.0/).

| Файл | Автор | Лицензия | Страница |
|---|---|---|---|
| `ak205.glb` | Frostoise | CC-BY-4.0 | https://sketchfab.com/3d-models/ak-103-863dbd7b0aa54a839ccdfe43d98c778a |
| `m44.glb` | Johan Pindeville | CC-BY-4.0 | https://sketchfab.com/3d-models/revolver-navy-colt-1851-silver-c254bb8ee01a4d9db9e6bbdc652d6c11 |
| `sgx.glb` | TORI106 | CC-BY-4.0 | https://sketchfab.com/3d-models/bizon-smg-bb157e507b7444ccabd75490366fb618 |
| `pw5a3.glb` | TORI106 | CC-BY-4.0 | https://sketchfab.com/3d-models/vector-smg-7f682fa9310044c1836850a58a96139f |
| `m2010_esr.glb` | DJMaesen | CC-BY-4.0 | https://sketchfab.com/3d-models/sniper-cdefd833b4b5407ba32c53c9e7f50cae |
| `m433.glb` | Mateusz Woliński | CC-BY-4.0 | https://sketchfab.com/3d-models/m16-assault-rifle-339d0f7b21024387853dd926a5d51b50 |
| `uzi.glb` | creationwasteland | CC-BY-4.0 | https://sketchfab.com/3d-models/uzi-fde60adc8aff4c61b6a8bea1f9e0743f |
| `p18.glb` | geyges | SKETCHFAB Standard, не CC-BY | https://sketchfab.com/3d-models/beretta-92fs-inox-9x19-cfb492b120c24644ba3e99ea98e6fe0a |
| `m1014.glb`, `sv98.glb` | не указан, файлы из zip без метаданных | не подтверждена | не указана |
| `ak47.glb` | Stein Games | CC0 1.0 по README thomas1568/ak47, LICENSE-файла в репозитории нет, метаданных в GLB нет | https://stein-indie.itch.io/classic-weapons-pack (не открывалась) |
| заглушки (`b36a4`, `m4a1`, `l110`, `m250`, `m39_emr`, `svdm`, `m87a1`, `es57`) | Quaternius | CC0 по записи пака, для этих файлов не подтверждено, метаданных в GLB нет | https://quaternius.com |
| `sniper_quater_animated.glb` | не указан | CC0 по записи пака, не подтверждено | не указана |

Важно:
- `p18.glb` под лицензией Sketchfab Standard, а не CC-BY. Такие модели обычно нельзя передавать как файл, решение за владельцем.
- `m1014.glb` и `sv98.glb` без автора и лицензии, перед публикацией их нужно проверить.

## Размеры: источники

Значения взяты из результатов поиска. Первичные страницы не всегда открывались.

- M16A3: 1006 мм. Valka.cz (1006 мм), GlobalSecurity (39.6 дюйма).
- Beretta 92FS: 216 мм у большинства источников. Vedder: https://www.vedderholsters.com/beretta-92fs-m9
- SPAS-12: 1041 мм с прикладом. https://en.wikipedia.org/wiki/Franchi_SPAS-12. Модель названа "fictional", размер взят у SPAS-12.
- Barrett M82A1: 57 дюймов (1448 мм) при стволе 29 дюймов, 48 дюймов (1219 мм) при стволе 20 дюймов. https://en.wikipedia.org/wiki/Barrett_M82
- AK-103: 943 мм с прикладом. https://en.wikipedia.org/wiki/AK-103
- AK-47: 880 мм с прикладом. Small Arms Survey: https://www.smallarmssurvey.org/sites/default/files/SAS-weapons-assault-rifles-Kalashnikov-AK-47.pdf
- Colt Model 1851 Navy: 13 дюймов (330 мм) при стволе 7.5 дюйма. Дилерские спецификации, не заводские.
- PP-19 Bizon: 690 мм с прикладом (Bizon-2). https://en.wikipedia.org/wiki/PP-19_Bizon. Если модель оказалась исходным Bizon (660 мм), разница 4%.
- KRISS Vector: 706 мм с прикладом (Gen 2 SMG). https://kriss-usa.com/vector-smg-gen-2-5-5-black
- Uzi: 650 мм с выдвинутым прикладом. Small Arms Survey: https://www.smallarmssurvey.org/sites/default/files/SAS_weapons-sub-machine-guns-Uzi.pdf
- AK-205: отдельного источника нет. Слот получил длину AK-103 (943 мм), это допущение.
- Sniper (M2010 ESR): 1.100 м условно, модель не определена.

Заглушки: длины заданы по памяти, без поиска. M4 (838 мм), M249 (1041 мм, на L110), M60 (1090 мм, на M250), M39 EMR (1020 мм), SVD (1225 мм, на SVDM), Remington 870 (1000 мм, на M87A1), Five-seveN (208 мм), B36A4 (950 мм, условно). Эти значения нужно проверить.

## Что сделано

- Масштаб: все узлы и вершины умножены на один коэффициент, иерархия сохранена.
- Упрощение: `gltf-transform simplify` (meshopt), UV и материалы сохранены. Треугольники, длина и валидатор проверены для всех 17 ключей.
- Валидатор Khronos: ошибок нет у всех 20 файлов. Предупреждения: у `sv98` 7 (нормали, сгенерированы рантаймом), у `ak47` 2 (то же самое).

## Что не сделано или не проверено

- Мелкая геометрия (болты, винты, фаски) при упрощении потеряна. Для сохранения деталей нужна запеченная нормаль с исходной высокополигональной модели.
- Пункт Barrett (`sv98`): нормаль без инверсии зеленого канала, не проверено.
- Ориентация: длинная ось у моделей разная, см. ниже. Сторона ствола и точка опоры не проверялись.

## Ориентация

Длинная ось Z: `ak205`, `ak47`, `b36a4`, `m1014`, `m2010_esr`, `m433`, `p18`, `sv98`, `uzi`, `sniper_quater_animated`.

Длинная ось X: `m44`, `pw5a3`, `sgx`, `m4a1`, `l110`, `m250`, `m39_emr`, `svdm`, `m87a1`, `es57`.

Перед вставкой в игру модели нужно выровнять к одной оси.

## Файлы из вашего первого архива

`M433.fbx`, `B36A4.fbx` и `m4a1.glb` не используются. Они не совпадают ни с одним ключом. Файл `m4a1.glb` имеет масштаб около 18.7 м в своей системе координат, что в 22 раза больше M4A1. Слоты B36A4 и M4A1 сейчас заняты заглушками.

Заглушки из `weapons/` и `weapons_cc0_optimized/` не пересекаются с вашими загрузками. В тех папках лежат другие модели с теми же именами файлов (`ak205.glb`, `m44.glb` и др.). Это старые аналоги другого масштаба, в этой папке актуальны файлы отсюда.

## Открыто

- AK-205 или AK-203: в списке Battlefield есть AK-205, поэтому назначен он. Если имелся в виду AK-203, поменяю слот.
- Uzi не получил слот. Свободного SMG-слота нет: SGX и PW5A3 уже заняты Bizon и Vector.
- SV-98 назначен Barrett условно. Это антиматериальная винтовка, в списке Battlefield такого нет.
- M1014 назначен SPAS условно. Модель названа "fictional". Для помпового M87A1 переименую.
- Снайпер M2010 ESR: модель не определена, размер условный.
- `p18.glb`: лицензия Sketchfab Standard, решение за владельцем.
- Заглушки: для всех восьми нужны реалистичные модели, если они появятся.
