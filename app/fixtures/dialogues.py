from app.models.transcripts import Speaker

GOOD_CALL = {
    "name": "good",
    "expected_passed": [
        "greeting",
        "needs",
        "price_named",
        "delivery",
        "no_interrupt",
        "closing",
    ],
    "segments": [
        (Speaker.OPERATOR, "Добрий день, мене звати Настя, компанія Ювелір Плюс."),
        (Speaker.CLIENT, "Вітаю, я дивилась у вас ланцюжок, срібний."),
        (Speaker.OPERATOR, "Підкажіть, це для себе чи в подарунок?"),
        (Speaker.CLIENT, "У подарунок мамі, на день народження."),
        (Speaker.OPERATOR, "Тоді раджу модель з плетінням бісмарк, вона у нас найпопулярніша."),
        (Speaker.CLIENT, "А скільки вона коштує?"),
        (Speaker.OPERATOR, "Ціна дев'ятсот вісімдесят гривень, у подарунковій коробочці."),
        (Speaker.CLIENT, "Добре, підходить."),
        (Speaker.OPERATOR, "Доставку зробимо Новою поштою, у яке місто відправляти?"),
        (Speaker.CLIENT, "У Львів, відділення дванадцять."),
        (
            Speaker.OPERATOR,
            "Записала. Оформлю замовлення зараз, номер накладної надішлю в СМС сьогодні.",
        ),
        (Speaker.CLIENT, "Дякую."),
    ],
}

BAD_CALL = {
    "name": "bad",
    "expected_passed": ["price_named"],
    "segments": [
        (Speaker.OPERATOR, "Алло."),
        (Speaker.CLIENT, "Доброго дня, я хотіла запитати про..."),
        (Speaker.OPERATOR, "Що саме вам треба, кажіть швидше."),
        (Speaker.CLIENT, "Ну я дивилась сережки, там було..."),
        (Speaker.OPERATOR, "Сережки шістсот гривень."),
        (Speaker.CLIENT, "А є інші кольори?"),
        (Speaker.OPERATOR, "Що є на сайті, те і є."),
        (Speaker.CLIENT, "Зрозуміло, я подумаю."),
        (Speaker.OPERATOR, "Добре."),
    ],
}

MIXED_CALL = {
    "name": "mixed",
    "expected_passed": ["greeting", "needs", "price_named", "no_interrupt"],
    "segments": [
        (Speaker.OPERATOR, "Добрий день, це Артем, компанія Ювелір Плюс."),
        (Speaker.CLIENT, "Вітаю, цікавить каблучка."),
        (Speaker.OPERATOR, "Який розмір потрібен і на яку суму орієнтуєтесь?"),
        (Speaker.CLIENT, "Розмір сімнадцять, до півтори тисячі."),
        (Speaker.OPERATOR, "Є варіант за тисячу двісті, срібло з фіанітом."),
        (Speaker.CLIENT, "Виглядає непогано, я подумаю."),
        (Speaker.OPERATOR, "Добре, гарного дня."),
    ],
}

DIALOGUES = [GOOD_CALL, BAD_CALL, MIXED_CALL]
