# Оружие из пака Ravi-Rutgers/airsoft-3d-model-pack, CC0

34 модели. Исходник: https://github.com/Ravi-Rutgers/airsoft-3d-model-pack (публичный репозиторий, models.json и LICENSES/ тоже скопированы в эту папку).

## Важно

- Модели НЕ реалистичные. В манифесте все 34 помечены `generic_comparable`. Часть стилизованная (Flat Guns), часть силуэты Quaternius, которые названы по реальным моделям (AK-74, M24 и др.), но без привязки к производителю. Текстур нет, материалы однотонные.
- Полигоны не уменьшались. Все исходники уже меньше 10 000 треугольников (от 954 до 4353), поэтому упрощение не применялось.
- Что сделано: дедупликация, очистка неиспользуемых данных и пересборка по правилам glTF Transform. Без квантования и без упрощения геометрии.
- Сохранено: все атрибуты (UV, нормали, скин, веса), анимации и скины. Треугольники и габариты совпадают с исходниками. Валидатор Khronos: 0 ошибок.
- Исходные UV в одиннадцати файлах в первой версии удалялись. Исправлено: сейчас UV на месте.
- Пункт про реалистичность не закрыт. Реалистичные CC0 модели из этой среды скачать не удалось: заблокированы хосты itch.io, OpenGameArt, Sketchfab, Poly Haven.

## Таблица

| Файл | Название | Тип | Треугольников | Размер | Лицензия | Заметки |
|---|---|---|---|---|---|---|
| `pistol-compact-west.glb` | Stylized Compact Pistol (West) | pistol | 1 244 | 135 КБ | CC0-1.0 |  |
| `pistol-full-west.glb` | Stylized Full Pistol (West) | pistol | 1 434 | 149 КБ | CC0-1.0 |  |
| `rifle-assault-west.glb` | Stylized Assault Rifle (West) | rifle | 4 353 | 436 КБ | CC0-1.0 |  |
| `rifle-battle-west.glb` | Stylized Battle Rifle (West) | rifle | 3 173 | 319 КБ | CC0-1.0 |  |
| `smg-compact-west.glb` | Stylized Compact SMG (West) | smg | 2 201 | 224 КБ | CC0-1.0 |  |
| `smg-full-west.glb` | Stylized Full SMG (West) | smg | 2 030 | 207 КБ | CC0-1.0 |  |
| `shotgun-auto-west.glb` | Stylized Automatic Shotgun (West) | shotgun | 1 540 | 160 КБ | CC0-1.0 |  |
| `shotgun-pump-west.glb` | Stylized Pump Shotgun (West) | shotgun | 1 071 | 113 КБ | CC0-1.0 |  |
| `sniper-material-west.glb` | Stylized Sniper Rifle - Material (West) | sniper | 3 676 | 352 КБ | CC0-1.0 |  |
| `sniper-rifle-west.glb` | Stylized Sniper Rifle (West) | sniper | 3 208 | 313 КБ | CC0-1.0 |  |
| `pistol-compact-east.glb` | Stylized Compact Pistol (East) | pistol | 1 263 | 114 КБ | CC0-1.0 |  |
| `pistol-full-east.glb` | Stylized Full Pistol (East) | pistol | 1 216 | 108 КБ | CC0-1.0 |  |
| `rifle-assault-east.glb` | Stylized Assault Rifle (East) | rifle | 3 271 | 291 КБ | CC0-1.0 |  |
| `rifle-battle-east.glb` | Stylized Battle Rifle (East) | rifle | 3 143 | 283 КБ | CC0-1.0 |  |
| `smg-compact-east.glb` | Stylized Compact SMG (East) | smg | 1 685 | 148 КБ | CC0-1.0 |  |
| `smg-full-east.glb` | Stylized Full SMG (East) | smg | 2 146 | 189 КБ | CC0-1.0 |  |
| `shotgun-auto-east.glb` | Stylized Automatic Shotgun (East) | shotgun | 1 930 | 172 КБ | CC0-1.0 |  |
| `shotgun-pump-east.glb` | Stylized Pump Shotgun (East) | shotgun | 1 508 | 133 КБ | CC0-1.0 | Предупреждение валидатора NODE_SKINNED_MESH_NON_ROOT есть уже в исходнике. |
| `sniper-material-east.glb` | Stylized Sniper Rifle - Material (East) | sniper | 2 452 | 219 КБ | CC0-1.0 |  |
| `sniper-rifle-east.glb` | Stylized Sniper Rifle (East) | sniper | 2 943 | 260 КБ | CC0-1.0 |  |
| `ak74-quaternius.glb` | AK-74 (Quaternius Ultimate Guns silhouette) | rifle | 1 388 | 75 КБ | CC0-1.0 |  |
| `scarl-quaternius.glb` | SCAR-L (Quaternius Ultimate Guns silhouette) | rifle | 1 930 | 129 КБ | CC0-1.0 |  |
| `m24-quaternius.glb` | M24 (Quaternius Ultimate Guns silhouette) | sniper | 1 382 | 73 КБ | CC0-1.0 |  |
| `axmc-quaternius.glb` | AXMC (Quaternius Ultimate Guns silhouette) | sniper | 1 722 | 91 КБ | CC0-1.0 |  |
| `awm-quaternius.glb` | AWM (Quaternius Ultimate Guns silhouette) | sniper | 1 688 | 91 КБ | CC0-1.0 |  |
| `m1911-quaternius.glb` | M1911 (Quaternius Ultimate Guns silhouette) | pistol | 1 442 | 76 КБ | CC0-1.0 |  |
| `mp5a5-quaternius.glb` | MP5A5 (Quaternius Ultimate Guns silhouette) | smg | 1 374 | 68 КБ | CC0-1.0 |  |
| `p226-quaternius.glb` | P226 (Quaternius Ultimate Guns silhouette) | pistol | 968 | 51 КБ | CC0-1.0 |  |
| `p90-quater-animated.glb` | P90 (Quaternius Animated Guns) | smg | 954 | 44 КБ | CC0-1.0 | В имени реальное название FN P90. В манифесте производитель null  модель обобщенная. Материалы объединены: все они одинаковые по свойствам. |
| `pistol-quater-animated.glb` | Pistol (Quaternius Animated Guns) | pistol | 1 491 | 64 КБ | CC0-1.0 | Лицензия под вопросом: poly.pizza указывает CC BY (нужна атрибуция)  манифест говорит CC0. Проверь страницу источника. Материалы объединены: все они одинаковые по свойствам. |
| `revolver-quater-animated.glb` | Revolver (Quaternius Animated Guns) | pistol | 2 812 | 127 КБ | CC0-1.0 | Материалы объединены: все они одинаковые по свойствам. |
| `rifle-quater-animated.glb` | Rifle (Quaternius Animated Guns) | rifle | 1 912 | 91 КБ | CC0-1.0 | Материалы объединены: все они одинаковые по свойствам. |
| `shotgun-quater-animated.glb` | Shotgun (Quaternius Animated Guns) | shotgun | 1 040 | 48 КБ | CC0-1.0 | Материалы объединены: все они одинаковые по свойствам. |
| `sniper-quater-animated.glb` | Sniper Rifle (Quaternius Animated Guns) | sniper | 1 710 | 80 КБ | CC0-1.0 | Материалы объединены: все они одинаковые по свойствам. |

Лицензии: `LICENSES/*.md`, полный манифест: `models.json`.

## Замены загруженных моделей

Загруженные пользователем 5 моделей заменены на самые похожие из этой папки. Причины: четыре из пяти не проходят лимит 10 000 треугольников (от 7 938 до 22 911 в исходниках, у ak_103 22 911, у sniper 13 087, у revolver 12 492, у vector_smg 11 881). Сходство считалось по пропорциям габаритов и по визуальному сравнению рендеров.

| Загруженный файл | Треугольников | Замена в папке | Треугольников | Комментарий |
|---|---|---|---|---|
| `revolver_navy_colt_1851_silver.glb` | 12 492 | `pistol-full-west.glb` | 1 434 | Револьвера в папке нет. `revolver-quater-animated.glb` не подходит: одна часть длиной 421 единица занимает 71% треугольников, на рендере модель почти пустая |
| `bizon_smg.glb` | 7 938 | `smg-full-west.glb` | 2 030 | Самый близкий по силуэту SMG с прикладом и магазином. По пропорциям ближе `p90-quater-animated`, но визуально это другой силуэт |
| `vector_smg.glb` | 11 881 | `smg-compact-west.glb` | 2 201 | Компактный SMG. По пропорциям близко, но не точно |
| `sniper.glb` | 13 087 | `axmc-quaternius.glb` | 1 722 | Болтовая винтовка с прицелом, по пропорциям одна из самых близких |
| `ak_103.glb` | 22 911 | `ak74-quaternius.glb` | 1 388 | Самое близкое совпадение: расстояние по пропорциям 0.010 |

Загруженные файлы в репозиторий не добавлены. Их можно упростить тем же способом, что и исходники, если нужна реалистичность.

## Заменено реалистичными моделями

Слоты Battlefield заменены моделями из `../weapons_realistic/`. Стилизованные файлы ниже оставлены как запасные, их можно удалить.

| Слот Battlefield | Стилизованный файл здесь | Замена |
|---|---|---|
| AK-205 | `ak74-quaternius.glb` | `weapons_realistic/ak205.glb` |
| M44 | `pistol-full-west.glb` | `weapons_realistic/m44.glb` |
| SGX | `smg-full-west.glb` | `weapons_realistic/sgx.glb` |
| PW5A3 | `smg-compact-west.glb` | `weapons_realistic/pw5a3.glb` |
| M2010 ESR | `axmc-quaternius.glb` | `weapons_realistic/m2010_esr.glb` |
