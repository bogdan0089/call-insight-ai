# call insight — фронт

UI контролю якості дзвінків поверх API з кореня репозиторію.

## Запуск

```bash
npm install
npm run dev        # http://localhost:3100
```

Бек має бути піднятий на `http://localhost:8090`:

```bash
docker compose up -d postgres redis rabbitmq
python -m uvicorn app.main:app --port 8090
```

Адреса API береться з `NEXT_PUBLIC_API_URL` (див. `.env.example`). Бек має дозволити
походження фронта — змінна `CORS_ORIGINS` у `.env` бекенда, за замовчуванням
`http://localhost:3100`.

## Структура

```
app/
  layout.tsx      оболонка: навігація + контейнер
  globals.css     токени в CSS-змінних, типографіка, поля
  page.tsx        «Огляд»
components/
  nav.tsx         верхня навігація
lib/
  theme.ts        кольори, радіуси, відступи
```

Порт **3100**, щоб не битись із іншими локальними проєктами.
