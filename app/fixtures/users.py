SEED_PASSWORD = "devpass123"

USERS = [
    {
        "email": "admin@example.com",
        "first_name": "Ольга",
        "last_name": "Шевченко",
        "role": "owner",
        "manager_email": None,
    },
    {
        "email": "manager@example.com",
        "first_name": "Ігор",
        "last_name": "Бондар",
        "role": "manager",
        "manager_email": None,
    },
    {
        "email": "nastia@example.com",
        "first_name": "Настя",
        "last_name": "Коваль",
        "role": "operator",
        "manager_email": "manager@example.com",
    },
    {
        "email": "artem@example.com",
        "first_name": "Артем",
        "last_name": "Мельник",
        "role": "operator",
        "manager_email": "manager@example.com",
    },
]
