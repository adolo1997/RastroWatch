# RastroWatch

RastroWatch es una aplicación web privada para registrar, consultar y valorar relojes de segunda mano vistos en rastrillos, Wallapop, tiendas o particulares.

> **RastroWatch:** “Escanea, registra y aprende el valor real de relojes de segunda mano.”

## Stack

- Backend: FastAPI
- Frontend: React + Vite servido con Nginx
- Base de datos: PostgreSQL
- Despliegue: Docker Compose
- Imágenes: carpeta local `./uploads` montada en `/app/uploads`
- Acceso: login simple con usuario administrador definido por variables de entorno

## Estructura recomendada en Ubuntu

```text
/opt/rastrowatch
├── backend
├── frontend
├── uploads
├── docker-compose.yml
├── .env.example
└── README.md
```

## Puesta en marcha

```bash
cd /opt/rastrowatch
cp .env.example .env
nano .env
```

Cambia al menos `POSTGRES_PASSWORD`, `ADMIN_PASSWORD` y `SESSION_SECRET`.

Levantar la app:

```bash
docker compose up -d --build
```

Acceder desde el navegador:

```text
http://IP_DEL_SERVIDOR:8085
```

## Comandos útiles

Parar la app:

```bash
docker compose down
```

Ver logs de todos los servicios:

```bash
docker compose logs -f
```

Ver logs del backend:

```bash
docker compose logs -f backend
```

Reiniciar tras cambios:

```bash
docker compose up -d --build
```

## Backups

Crear backup de PostgreSQL:

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backups/rastrowatch-$(date +%F).sql
```

Crear copia de imágenes:

```bash
tar -czf backups/uploads-$(date +%F).tar.gz uploads
```

Restaurar base de datos desde un backup:

```bash
cat backups/rastrowatch-AAAA-MM-DD.sql | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Restaurar imágenes:

```bash
tar -xzf backups/uploads-AAAA-MM-DD.tar.gz
```

## Funcionalidades incluidas

- Login privado con credenciales de entorno.
- Dashboard responsive con buscador por marca, modelo, referencia y notas.
- Tarjetas con imagen principal, precio recomendado o visto, oportunidad y riesgo.
- CRUD completo de relojes con campos técnicos, valoración, fuentes y notas de aprendizaje.
- Formulario rápido “Reloj visto” con foto, marca/modelo opcionales, precio, ubicación y notas.
- Página de detalle con fotos, datos técnicos, valoración, máximo recomendado, alertas e identificación.
- Valoración básica sin IA real:
  - Precio bajo mínimo estimado: oportunidad muy buena.
  - Precio entre mínimo y medio: buena.
  - Precio entre medio y máximo: normal.
  - Precio por encima del máximo: mala / evitar.
  - Estado “sin probar”: reduce la valoración.
  - Riesgo de falsificación alto: muestra advertencia fuerte.
- Endpoint preparado para IA futura: `POST /api/ai/analyze`, actualmente responde `IA pendiente de configurar`.

## Notas de despliegue

- El frontend se expone en el puerto externo `8085`.
- El backend queda accesible internamente para Nginx y Docker Compose.
- Los ficheros subidos persisten en `./uploads`.
- PostgreSQL persiste en el volumen Docker `postgres_data`.
- No se usan servicios externos, APIs de pago ni IA real.
